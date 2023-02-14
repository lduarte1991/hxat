import importlib
import json
import logging
import re
import uuid

from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.http import Http404, JsonResponse
from hx_lti_assignment.models import Assignment
from hxat.lti_validators import LTIRequestValidator
from lti.contrib.django import DjangoToolProvider

logger = logging.getLogger(__name__)


class AnnostoreFactory(object):
    @classmethod
    def get_instance(cls, request):
        if not hasattr(request, "LTI"):
            # needs session state in LTI object!
            msg = "cannot proceed: missing LTI dict in request"
            logger.error(msg)
            raise SuspiciousOperation(msg)

        asconfig = (  # default annostore config
            settings.ANNOTATION_DB_URL,
            settings.ANNOTATION_DB_API_KEY,
            settings.ANNOTATION_DB_SECRET_TOKEN,
        )

        # try to get a collection_id
        collection_id = request.LTI.get("hx_collection_id", None)
        if request.method == "GET":  # search has priority to get collection_id
            if len(request.GET) > 0:
                c_id = request.GET.get(
                    "collection_id", request.GET.get("collectionId", None)
                )
                # collection_id == None force to use default asconfig
                # BEWARE that if a simple read comes with a querystring, it might be
                #   redirected to the default asconfig!
                collection_id = c_id if c_id else None

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

    def dispatcher(self, annotation_id=None):
        self.logger.info("annostore method: {}".format(self.request.method))

        if self.request.method == "GET":
            if annotation_id is None:
                self.logger.info("search params: {}".format(self.request.GET))
                self._verify_course(
                    self.request.GET.get(
                        "contextId", self.request.GET.get("context_id", None)
                    )
                )
                response = self.search()

                # retroactive participation grade
                is_graded = self.request.LTI["launch_params"].get(
                    "lis_outcome_service_url", False
                )
                if is_graded and self.did_retro_participation(response):
                    self.lti_grade_passback(score=1)
                return response

            else:  # this is a read
                response = self.read(annotation_id)
                return response

        # TODO: possible in the future that hxat does not have to understand
        # the annotation body? and behave as a dumb proxy?
        elif self.request.method in ["POST", "PUT"]:
            body = json.loads(str(self.request.body, "utf-8"))
            try:
                context_id = body["platform"]["context_id"]
            except KeyError:
                context_id = None
            self._verify_course(context_id)
            self._verify_user(body.get("user", body.get("creator", {})).get("id", None))

            if self.request.method == "POST":
                response = self.create(annotation_id)
                if response.status_code == 200:
                    is_graded = self.request.LTI["launch_params"].get(
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
        elif self.request.method == "DELETE":
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

    def _verify_course(self, context_id, raise_exception=True):
        expected = self.request.LTI["hx_context_id"]
        result = context_id == expected
        if not result:
            self.logger.warning(
                "Course verification failed. Expected({})  Actual({})".format(
                    expected, context_id
                )
            )
        if raise_exception and not result:
            raise PermissionDenied
        return result

    def _verify_user(self, user_id, raise_exception=True):
        expected = self.request.LTI["hx_user_id"]
        result = str(user_id) == str(expected) or self.request.LTI["is_staff"]
        if not result:
            self.logger.warning(
                "User verification failed. Expected({}) Actual({})".format(
                    expected, user_id
                )
            )
        if raise_exception and not result:
            raise PermissionDenied
        return result

    def _get_tool_provider(self):
        # 06oct22 nmaekawa: always return some toolProvider
        # the reasoning is that we are failing just the "grade_passback" not the create
        # or search/participation request; sadly, this error is just logged on file
        if "launch_params" in self.request.LTI:
            params = self.request.LTI["launch_params"]
            consumer_key = params["oauth_consumer_key"]
            context_id = self.request.LTI["hx_context_id"]
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
                    self.request.LTI["hx_user_id"], self.request.LTI["hx_collection_id"]
                )
            )
            return None
        self.logger.info(
            "lti_grade: user({}) assignment({}) score({})".format(
                self.request.LTI["hx_user_id"],
                self.request.LTI["hx_collection_id"],
                score,
            )
        )
        try:
            outcome = tool_provider.post_replace_result(score)
            self.logger.info(vars(outcome))
            if outcome.is_success():
                self.logger.info(
                    "lti_grade successful. user({}) assignment({}) score({}) desc({})".format(
                        self.request.LTI["hx_user_id"],
                        self.request.LTI["hx_collection_id"],
                        score,
                        outcome.description,
                    )
                )
            else:
                self.logger.error(
                    "lti_grade ERROR. user({}) assignment({}) score({}) desc({})".format(
                        self.request.LTI["hx_user_id"],
                        self.request.LTI["hx_collection_id"],
                        score,
                        outcome.description,
                    )
                )
        except Exception as e:
            self.logger.error(
                "lti_grade FAILED. user({}) assignment({}) score({}) exc({})".format(
                    self.request.LTI["hx_user_id"],
                    self.request.LTI["hx_collection_id"],
                    score,
                    e,
                )
            )
        # should return anything?
        return None

    def did_retro_participation(self, response):
        # to give participation grades retroactively after instructor
        # forgets to turn it on initially
        retrieved_self = self.request.LTI["launch_params"].get(
            "user_id", "*"
        ) in self.request.GET.getlist(
            "userid[]", self.request.GET.getlist("userid", [])
        )  # includes logged user in search?
        return retrieved_self and int(json.loads(response.content)["total"]) > 0

    def send_annotation_notification(self, message_type, annotation):
        # target_source_id from session guarantees it's a sequential integer id from
        # hxat db; image annotations have the uri as target_source_id in `platform`
        pat = re.compile("[^a-zA-Z0-9-.]")
        context_id = pat.sub("-", self.request.LTI["hx_context_id"])
        collection_id = pat.sub("-", self.request.LTI["hx_collection_id"])
        target_source_id = self.request.LTI["hx_object_id"]

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
for the rhetoric course, we setup a second annostoreto divide traffic and relieve the
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
