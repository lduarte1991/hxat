import importlib
import json
import logging
import re
import uuid

import channels.layers
from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.exceptions import BadRequest
from django.http import Http404, JsonResponse
from hx_lti_assignment.models import Assignment
from hxat.lti_validators import LTIRequestValidator
from lti.contrib.django import DjangoToolProvider

logger = logging.getLogger(__name__)


class AnnostoreFactory(object):
    @classmethod
    def get_instance(cls, request, col_id=None):
        if not hasattr(request, "LTI"):
            # needs session state in LTI object!
            msg = "cannot proceed: missing LTI dict in request"
            logger.error(msg)
            raise BadRequest(msg)

        asconfig = (  # default annostore config
            settings.ANNOTATION_DB_URL,
            settings.ANNOTATION_DB_API_KEY,
            settings.ANNOTATION_DB_SECRET_TOKEN,
        )

        # get collection_id from session for create, update
        collection_id = request.LTI.get("hx_collection_id", None)

        # if transfer, have to get collection_id from path
        if request.method == "POST" and "transfer" in request.path:
            collection_id = col_id if col_id else None

        # get collection_id from querystring: it's a search or grademe
        #   collection_id == None means multi-assign search,
        #   and forces to use default asconfig
        if request.method == "GET":
            collection_id = request.GET.get(
                "collection_id", request.GET.get("collectionId", None)
            )

        # at this point, should have a collection id from querystring or the session
        # otherwise, it's a multi-assign search, and the default asconfig holds
        if collection_id is not None:
            try:
                collection = Assignment.objects.get(assignment_id=collection_id)
            except Assignment.DoesNotExist:
                msg = "error fetching assignment({}): not found".format(collection_id)
                logger.error(msg)
                raise Http404(msg)
            else:  # assignment asconfig never null!
                asconfig = (
                    collection.annotation_database_url,
                    collection.annotation_database_apikey,
                    collection.annotation_database_secret_token,
                )
        logger.info(
            "asconfig: {} - {} - {}".format(
                request.LTI.get("hx_context_id", "na"), collection_id, asconfig
            )
        )

        # for now, we only support one backend
        (module_name, class_name) = ("annostore.store_backend", "CatchpyBackend")
        StoreClass = getattr(importlib.import_module(module_name), class_name)
        store_instance = StoreClass(request, asconfig)
        return store_instance


class Annostore(object):
    """Annostore implements a storage interface for annotations

    and is intended to abstract the details of the backend that is actually going to
    be storing the annotations.

    The backend determines where/how annotations are stored. In the past, hxat had to
    support the Common Annotation, Tagging, and Citation at Harvard (CATCH) project for
    AnnotatorJs format, as well as a local database. As of oct22, the only annotation
    store backend supported is catchpy (https://github.com/nmaekawa/catchpy)
    """

    def __init__(self, request, asconfig):
        self.request = request
        self.method = request.method
        self.LTI = request.LTI
        self.META = request.META
        self.asconfig = asconfig
        self.logger = logging.getLogger(
            "{module}.{cls}".format(module=__name__, cls=self.__class__.__name__)
        )
        self.channel_layer = channels.layers.get_channel_layer()  # ws notification

    def dispatcher(self, annotation_id=None):
        self.logger.info("annostore method: {}".format(self.request.method))

        if self.method == "GET":  # reads not supported!
            self.logger.info("search params: {}".format(self.request.GET))
            context_id = self.request.GET.get(
                "contextId", self.request.GET.get("context_id", None)
            )
            if not context_id:  # hxat does not do searches across courses
                msg = "search param missing: context_id"
                self.logger.error(msg)
                raise BadRequest(msg)
            collection_id = self.request.GET.get(
                "collectionI", self.request.GET.get("collection_id", None)
            )
            if not collection_id:
                self.logger.warning(
                    "search across assignments for course({})".format(context_id)
                )
            self._verify_course(context_id, collection_id)
            response = self.search()

            # retroactive participation grade
            is_graded = self.LTI["launch_params"].get("lis_outcome_service_url", False)
            if is_graded and self.did_retro_participation(response):
                self.lti_grade_passback(score=1)
            return response

        # TODO: possible in the future that hxat does not have to understand
        # the annotation body? and behave as a dumb proxy?
        elif self.method in ["POST", "PUT"]:
            body = json.loads(str(self.request.body, "utf-8"))
            try:
                context_id = body["platform"]["context_id"]
                collection_id = body["platform"]["collection_id"]
            except KeyError:
                msg = "anno({}) missing context_id and/or collection_id in request".format(
                    annotation_id
                )
                self.logger.error(msg)
                raise BadRequest(msg)

            self._verify_course(context_id, collection_id)
            self._verify_user(body.get("user", body.get("creator", {})).get("id", ""))

            if self.method == "POST":
                response = self.create(annotation_id)
                if response.status_code == 200:
                    is_graded = self.LTI["launch_params"].get(
                        "lis_outcome_service_url", False
                    )
                    if is_graded:  # participation grade
                        self.lti_grade_passback(score=1)
                    # ws notification
                    cleaned_annotation = json.loads(response.content.decode())
                    self.send_annotation_notification(
                        "annotation_created", cleaned_annotation
                    )
                return response
            else:  # request.method == "PUT"
                response = self.update(annotation_id)
                # ws notification
                cleaned_annotation = json.loads(response.content.decode())
                self.send_annotation_notification(
                    "annotation_updated", cleaned_annotation
                )
                return response
        elif self.method == "DELETE":
            # TODO: is there any way to verify_course? or verify_user????
            self.logger.info("delete annotation({})".format(annotation_id))
            response = self.delete(annotation_id)
            # ws notification
            cleaned_annotation = json.loads(response.content.decode())
            self.send_annotation_notification("annotation_deleted", cleaned_annotation)
            return response
        else:
            return JsonResponse(status=405)  # method not allowed

    def search(self):
        raise NotImplementedError

    def create(self, annotation_id=None):
        raise NotImplementedError

    def read(self, annotation_id):
        raise NotImplementedError

    def update(self, annotation_id):
        raise NotImplementedError

    def delete(self, annotation_id):
        raise NotImplementedError

    def transfer(self, source_collection_id):
        raise NotImplementedError

    def _verify_course(self, context_id, collection_id=None):
        """raises BadRequest if cannot verify course."""
        expected = self.LTI["hx_context_id"]
        if not context_id == expected:
            msg = "Course verification expected({}) but got({})".format(
                expected, context_id
            )
            self.logger.error(msg)
            raise BadRequest(
                "course verification failed - unexpected course({})".format(context_id)
            )
        if not collection_id:
            return

        try:
            collection = Assignment.objects.get(assignment_id=collection_id)
        except Assignment.DoesNotExist:
            msg = "Course verification failed: assignment({}) not found".format(
                collection_id
            )
            self.logger.error(msg)
            raise BadRequest(msg)
        else:
            is_course_inconsistent = False
            if getattr(collection.course, "course_id", None):
                if not collection.course.course_id == context_id:
                    is_course_inconsistent = True
                    self.logger.error(
                        "Course verification failed: collection({}) expected course({}), found({})".format(
                            collection.assignment_id,
                            collection.course.course_id,
                            context_id,
                        )
                    )
            else:
                is_course_inconsistent = True
                self.logger.error(
                    "Course verification failed: collection({}) not associated with any course".format(
                        collection_id
                    )
                )
            if settings.RAISE_COURSE_INCONSISTENT_EXCEPTION and is_course_inconsistent:
                raise BadRequest(
                    "inconsistent context_id({}) in request".format(context_id)
                )

        return  # all is well

    def _verify_user(self, user_id):
        """raises BadRequest if cannot verify user."""
        expected = self.LTI["hx_user_id"]
        result = str(user_id) == str(expected) or self.LTI["is_staff"]
        if not result:
            self.logger.warning(
                "User verification expected({}) but got({})".format(expected, user_id)
            )
            raise BadRequest("inconsistent user({}) in request".format(user_id))
        return  # all is well

    def _get_tool_provider(self):
        # 06oct22 nmaekawa: always return some toolProvider
        # the reasoning is that we are failing just the "grade_passback" not the create
        # or search/participation request; sadly, this error is just logged on file
        if "launch_params" in self.LTI:
            params = self.LTI["launch_params"]
            consumer_key = params["oauth_consumer_key"]
            context_id = self.LTI["hx_context_id"]
            lti_secret = LTIRequestValidator.fetch_lti_secret(
                client_key=consumer_key, context_id=context_id
            )

            # the middleware includes an LTI dict with all lti params for
            # lti_grade_passback() -- an lti request that is not a lti-launch.
            # py-lti only understands lti params that come directly in the POST
            mutable_post = self.request.POST.copy()
            mutable_post.update(params)
            self.request.POST = mutable_post

            return DjangoToolProvider.from_django_request(
                lti_secret, request=self.request
            )
        else:
            self.logger.warning(
                "missing launch_params in LTI session; using dummy secret"
            )
            lti_secret = uuid.uuid4().hex  # dummy secret
            return DjangoToolProvider.from_django_request(
                lti_secret, request=self.request
            )

    def lti_grade_passback(self, score=1.0):
        if score < 0 or score > 1.0 or isinstance(score, str):
            return
        tool_provider = self._get_tool_provider()
        if not tool_provider.is_outcome_service():
            self.logger.info(
                "LTI consumer not expecting grade for user({}) assignment({})".format(
                    self.LTI["hx_user_id"], self.LTI["hx_collection_id"]
                )
            )
            return None
        self.logger.info(
            "lti_grade: user({}) assignment({}) score({})".format(
                self.LTI["hx_user_id"],
                self.LTI["hx_collection_id"],
                score,
            )
        )
        try:
            outcome = tool_provider.post_replace_result(score)
            self.logger.info(vars(outcome))
            if outcome.is_success():
                self.logger.info(
                    "lti_grade successful. user({}) assignment({}) score({}) desc({})".format(
                        self.LTI["hx_user_id"],
                        self.LTI["hx_collection_id"],
                        score,
                        outcome.description,
                    )
                )
            else:
                self.logger.error(
                    "lti_grade ERROR. user({}) assignment({}) score({}) desc({})".format(
                        self.LTI["hx_user_id"],
                        self.LTI["hx_collection_id"],
                        score,
                        outcome.description,
                    )
                )
        except Exception as e:
            self.logger.error(
                "lti_grade FAILED. user({}) assignment({}) score({}) exc({})".format(
                    self.LTI["hx_user_id"],
                    self.LTI["hx_collection_id"],
                    score,
                    e,
                )
            )
        # should return anything?
        return None

    def did_retro_participation(self, response):
        # to give participation grades retroactively after instructor
        # forgets to turn it on initially
        retrieved_self = self.LTI["launch_params"].get(
            "user_id", "*"
        ) in self.request.GET.getlist(
            "userid[]", self.request.GET.getlist("userid", [])
        )  # includes logged user in search?
        return retrieved_self and int(json.loads(response.content)["total"]) > 0

    def send_annotation_notification(self, message_type, annotation):
        # target_source_id from session guarantees it's a sequential integer id from
        # hxat db; image annotations have the uri as target_source_id in `platform`
        pat = re.compile("[^a-zA-Z0-9-.]")
        context_id = pat.sub("-", self.LTI["hx_context_id"])
        collection_id = pat.sub("-", self.LTI["hx_collection_id"])
        target_source_id = self.LTI["hx_object_id"]

        group = "{}--{}--{}".format(
            re.sub("[^a-zA-Z0-9-.]", "-", context_id), collection_id, target_source_id
        )
        self.logger.info(
            "###### action({}) group({}) id({})".format(
                message_type, group, annotation.get("id", "unknown_id")
            )
        )
        try:
            async_to_sync(self.channel_layer.group_send)(
                group,
                {
                    "type": "annotation_notification",
                    "message": annotation,
                    "action": message_type,
                },
            )
        except Exception as e:
            # while transitioning to websockets, it might be that a redis backend is not
            # available and notifications are not really being used; to avoid clogging
            # logs, just printing error; to print the error stack set env var
            # "HXAT_NOTIFY_ERRORLOG=true"
            msg = "##### unable to notify: action({}) group({}) id({}): {}".format(
                message_type, group, annotation.get("id", "unknown_id"), e
            )
            self.logger.error(msg, exc_info=settings.HXAT_NOTIFY_ERRORLOG)


"""
13feb23 nmaekawa: annostore cfg in assignments
Annostore cfg in assignment was created as a way to debug annotations in production.
Debug assignments can be created in production and then manually made to point to a
test annostore. This was meant to be sparsely used but, in 2020, due to intense traffic
for the rhetoric course, we setup a second annostore to divide traffic and relieve the
main annostore database.

One assumption is that searches, in general, occur within an assignment. If no
assignment comes in the search querystring, it means the search is over multiple
assignments in the course -- this is a problem since each assignment might have its own
annostore config.

For now, searches over the course is a special case and always use the default annostore
config. In the future, this has to be changed:
    - annostore config should be associated by course (to support our rhetoric use case)
    - to select which annostore config: firt check course, then assignment
    - implement these configs in separate tables than course and assignment; the code
      then ignores configs within the assignment model. This makes the migration less
      convoluted and prone to error.

Searches over all assignments in the course are used by ATG in instructor dashboard, but
it is known that ATG configures one annostore per hxat. In HX case, we never use
searches ove all assignments in the course.
"""
