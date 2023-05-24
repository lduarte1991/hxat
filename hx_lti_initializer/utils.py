"""
These functions will be used for the initializer module, but may also be
helpful elsewhere.
"""
import datetime
import logging
import time
import urllib

import jwt
import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.urls import reverse

# import Sample Target Object Model
from hx_lti_assignment.models import Assignment
from target_object_database.models import TargetObject

from .models import LTICourse, LTIProfile

logger = logging.getLogger(__name__)


@transaction.atomic
def create_new_user(
    anon_id=None, username=None, display_name=None, roles=None, scope=None
):
    logger.debug(
        "create_new_user: anon_id=%s, username=%s, display_name=%s, roles=%s"
        % (anon_id, username, display_name, roles)
    )
    if anon_id is None or display_name is None or roles is None:
        raise Exception(
            "create_new_user missing required parameters: anon_id, display_name, roles"
        )

    lti_profile = LTIProfile(anon_id=anon_id)
    lti_profile.name = display_name
    lti_profile.roles = ",".join(roles)
    lti_profile.scope = scope
    lti_profile.save()

    if not username:
        username = "profile:{id}".format(id=lti_profile.id)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User.objects.create_user(username)
        user.is_superuser = False
        user.is_staff = len(set(roles) & set(settings.LTI_ADMIN_ROLES)) > 0
        user.set_unusable_password()
        user.save()
    except User.MultipleObjectsReturned:
        user = User.objects.filter(username=username).order_by("id")[0]

    lti_profile.user = user
    lti_profile.save(update_fields=["user"])

    logger.debug(
        "create_new_user: LTIProfile.%s associated with User.%s"
        % (lti_profile.id, user.id)
    )
    return user, lti_profile


def save_session(request, resource_link_id, **kwargs):
    session_map = {
        "user_id": ["hx_user_id", None],
        "user_name": ["hx_user_name", None],
        "user_scope": ["hx_user_scope", None],
        "context_id": ["hx_context_id", None],
        "course_id": ["hx_lti_course_id", None],
        "course_name": ["course_name", None],
        "collection_id": ["hx_collection_id", None],
        "object_id": ["hx_object_id", None],
        "object_uri": ["hx_object_uri", None],
        "roles": ["hx_roles", []],
        "is_staff": ["is_staff", False],
        "is_instructor": ["is_instructor", False],
        "resource_link_id": ["resource_link_id", None],
    }

    for k in kwargs:
        assert k in session_map, "save_session({}) kwarg=({}) is not valid!".format(
            resource_link_id, k
        )

    for kwarg in kwargs:
        session_key, default_value = session_map[kwarg]
        session_value = kwargs.get(kwarg, default_value)
        logger.debug("save_session: %s=%s" % (session_key, session_value))
        request.session["LTI_LAUNCH"][resource_link_id][session_key] = session_value
        request.session.modified = True


def get_session_value(request, key, default_value=None):
    resource_link_id = request.LTI["resource_link_id"]
    value = request.session["LTI_LAUNCH"][resource_link_id].get(key, default_value)
    return value


def get_lti_value(key, request):
    """Returns the LTI parameter from the request otherwise None."""
    value = request.LTI.get("lti_params", {}).get(key, None)
    logger.debug("get_lti_value: %s=%s" % (key, value))
    return value


def retrieve_token(userid, apikey, secret, ttl=1, override=None):
    """
    generates a jwt for the backend of annotations.

    default ttl = 1 sec
    override must be a list of strings
    """
    apikey = apikey
    secret = secret
    # the following five lines of code allows you to include the
    # defaulttimezone in the iso format
    # noqa for more information: http://stackoverflow.com/questions/3401428/how-to-get-an-isoformat-datetime-string-including-the-default-timezone

    def _now():
        return (
            datetime.datetime.utcnow()
            .replace(tzinfo=simple_utc())
            .replace(microsecond=0)
            .isoformat()
        )  # noqa

    payload = {"consumerKey": apikey, "userId": userid, "issuedAt": _now(), "ttl": ttl}
    if override:
        payload["override"] = [str(x) for x in override]
    token = jwt.encode(payload, secret)
    if isinstance(token, bytes):
        token = token.decode()
    return token


def get_admin_ids(context_id):
    """
    Returns a set of the user ids of all users with an admin role
    """
    course_object = LTICourse.get_course_by_id(context_id)
    admins = course_object.course_admins.all()
    admin_ids = [admin.get_id() for admin in admins]

    return admin_ids


class simple_utc(datetime.tzinfo):
    def tzname(self):
        return "UTC"

    def utcoffset(self, dt):
        return datetime.timedelta(0)


def get_annotation_db_credentials_by_course(context_id):
    """
    Returns the distinct set of annotation database credentials (url, api key, secret token)
    for a given course.

    The credentials are stored on a per-assignment basis, and a course will have many assignments.
    The expected use case is that *one* credential (url, api key, secret token) will be
    used across all assignments in a course, but it's possible that might not be the case.

    Returns:

    [
        {
            'annotation_database_url': 'http://catch-database.localhost/catch/annotator',
            'annotation_database_apikey': 'Tpt7HaodxVDNQljaMjLz',
            'annotation_database_secret_token': u'GWoXMgXkprYL4ZtkELyq',
        },
        {
            'annotation_database_url': 'https://catch-database.localhost/catch/annotator',
            'annotation_database_apikey': '069fK9KTLHugO7uxjfwN',
            'annotation_database_secret_token': 'Xbi791aSsF4AVWjMhQnl',
        }
    ]
    """
    fields = [
        "annotation_database_url",
        "annotation_database_apikey",
        "annotation_database_secret_token",
    ]
    values = (
        Assignment.objects.filter(course__course_id=context_id)
        .values(*fields)
        .distinct(*fields)
        .order_by(*fields)
    )

    # The list of database entries might not be unique (despite the *select distinct*) if any of
    # the URLs contain whitespace. The code below accounts for that possibility.
    k, values_by_url = ("annotation_database_url", {})
    for row in values:
        row[k] = row[k].strip()
        if row[k] and row[k] not in values_by_url:
            values_by_url[row[k]] = row

    return values_by_url.values()


def fetch_annotations_by_course(context_id, user_id):
    """
    Fetches annotations for all assignments in a course as given by the LTI context ID.

    This function accounts for the fact that annotation database credentials are stored
    on a per-assignment level, so if course assignments have different annotation database
    settings, they will be included in the results. In general, it's expected that a
    course will have one annotation database setting used across assignments (URL, API KEY, SECRET),
    but it's possible that this assumption could change by the simple fact that the settings
    are saved on assignment models, and not on course models.

    Returns: [{"rows": [], "totalCount": 0 }]
    """
    annotation_db_credentials = get_annotation_db_credentials_by_course(context_id)

    results = {"rows": [], "totalCount": 0}
    for credential in annotation_db_credentials:
        db_url = credential["annotation_database_url"].strip()
        db_apikey = credential["annotation_database_apikey"]
        db_secret = credential["annotation_database_secret_token"]
        annotator_auth_token = retrieve_token(user_id, db_apikey, db_secret)
        logger.debug(
            "Fetching annotations with context_id=%s database_url=%s"
            % (context_id, db_url)
        )
        data = _fetch_annotations_by_course(context_id, db_url, annotator_auth_token)
        # logger.debug("Annotations fetched: %s" % data)
        if "rows" in data:
            results["rows"] += data["rows"]
        if "totalCount" in data:
            results["totalCount"] += int(data["totalCount"])
    return results


def _fetch_annotations_by_course(
    context_id, annotation_db_url, annotator_auth_token, **kwargs
):
    """
    Fetches the annotations of a given course from the CATCH database
    """
    # build request
    headers = {
        "Authorization": "token {}".format(annotator_auth_token),
        "Content-Type": "application/json",
    }
    limit = kwargs.get("limit", 1000)  # Note: -1 means get everything there is
    encoded_context_id = urllib.parse.quote_plus(context_id)
    request_url = "%s/?context_id=%s&limit=%s" % (
        annotation_db_url,
        encoded_context_id,
        limit,
    )

    logger.debug("fetch_annotations_by_course(): url: %s" % request_url)

    # make request
    request_start_time = time.perf_counter()
    r = requests.get(request_url, headers=headers)
    request_end_time = time.perf_counter()
    request_elapsed_time = request_end_time - request_start_time

    logger.debug(
        "fetch_annotations_by_course(): annotation database response code: %s"
        % r.status_code
    )
    logger.debug(
        "fetch_annotations_by_course(): request time elapsed: %s seconds"
        % (request_elapsed_time)
    )

    try:
        # this gets the whole request, including such things as 'count'
        # however, that also means that the annotations come in as an object called 'rows,'
        # where each row represents an annotation object.
        # if more convenient, we could cut the top level and just return flat annotations.
        annotations = r.json()
        # Transform data body because we are hitting a v2 catchpy endpoint
        formatted_annotations = []
        parents_text_dict = {}
        total = annotations["total"] or 0
        result = {"totalCount": total}

        # Note: there are other fields i left out since it did not seem to be required for what we need
        for annote in annotations["rows"]:
            # add text to parent_text_dict text dict for quick lookup
            try:
                # look up index for correct nested catchpy object with accepted types due to uncertain order of dict in list
                index_of_target_items = find_target_object_index(
                    annote["target"]["items"]
                )
                if index_of_target_items is None:
                    raise KeyError("media type")
                id = annote["id"]
                text = annote["body"]["items"][0]["value"]
                parents_text_dict[id] = text
                created = annote["created"]
                updated = annote["modified"]
                text = text
                permissions = annote["permissions"]
                user = annote["creator"]
                totalComments = annote["totalReplies"]
                tags = []
                parent = "0"
                ranges = []
                contextId = annote["platform"]["context_id"]
                collectionId = annote["platform"]["collection_id"]
                uri = annote["platform"]["target_source_id"]
                media = annote["target"]["items"][index_of_target_items]["type"].lower()
                target_items = annote["target"]["items"]
                quote = ""
                formatted = {
                    "id": id,
                    "created": created,
                    "updated": updated,
                    "text": text,
                    "permissions": permissions,
                    "user": user,
                    "totalComments": totalComments,
                    "tags": tags,
                    "parent": parent,
                    "ranges": ranges,
                    "contextId": contextId,
                    "collectionId": collectionId,
                    "uri": uri,
                    "media": media,
                    "quote": quote,
                    # added manifest_url for better matching in get_target_id
                    "manifest_url": "",
                }
                if "selector" in target_items[index_of_target_items]:
                    for item in target_items[index_of_target_items]["selector"][
                        "items"
                    ]:
                        if "type" in item and item["type"] == "TextQuoteSelector":
                            formatted["quote"] = item["exact"]
                # check if the annotation has a parent text
                # parent id is written to "parent" key
                if target_items[index_of_target_items]["type"] == "Annotation":
                    formatted["parent"] = target_items[index_of_target_items]["source"]

                # check images annotation fields
                if media == "image":
                    # not guarenteed correct order
                    if (
                        index_of_target_items == 1
                        and target_items[0]["type"] == "Thumbnail"
                    ):
                        formatted["thumb"] = target_items[0]["source"]
                    elif target_items[1]["type"] == "Thumbnail":
                        formatted["thumb"] = target_items[1]["source"]
                    if "selector" in target_items[index_of_target_items]:
                        formatted["rangePosition"] = target_items[
                            index_of_target_items
                        ]["selector"]["items"]
                        # added field for image manifest for lookup in get_target_id function
                        bounds = ""
                        # Data structure is different between old highlighter and new highlighter e.g. newhighlighter assignment data does not have scope field
                        if "type" in formatted["rangePosition"][0]:
                            formatted["manifest_url"] = target_items[
                                index_of_target_items
                            ]["source"]
                            bounds = formatted["rangePosition"][0]["value"]
                        else:
                            formatted["manifest_url"] = formatted["rangePosition"][0][
                                "within"
                            ]["@id"]
                            bounds = target_items[index_of_target_items]["scope"][
                                "value"
                            ]
                        formatted_bounds = bounds.split("=")[1].split(",")
                        x, y, width, height = formatted_bounds
                        formatted["bounds"] = {
                            "x": x,
                            "y": y,
                            "width": width,
                            "height": height,
                        }

                formatted_annotations.append(formatted)
            except KeyError as e:
                logger.warning(f"key error={e}")
        # Loop through the formatted_annotations and add parent_text if parent !=0
        for formatted_annote in formatted_annotations:
            if formatted_annote["parent"] != "0":
                id = formatted_annote["parent"]
                formatted_annote["parent_text"] = parents_text_dict[id]
        result["rows"] = formatted_annotations
    except KeyError as ke:
        logger.error(f"missing {ke} field in response body")
    except Exception:
        # If there are no annotations, the database should return a dictionary with empty rows,
        # but in the event of another exception such as an authentication error, fail
        # gracefully by manually passing in that empty response
        annotations = {"rows": [], "totalCount": 0}
    return result


def get_distinct_users_from_annotations(annotations, sort_key=None):
    """
    Given a set of annotation objects returned by the CATCH database,
    this function returns a list of distinct user objects.
    """

    def _default_sort_key(user):
        return user["id"]

    rows = annotations["rows"]
    annotations_by_user = {}
    for r in rows:
        user_id = r["user"]["id"]
        if user_id not in annotations_by_user:
            annotations_by_user[user_id] = r["user"]
    users = list(
        sorted(
            annotations_by_user.values(),
            key=sort_key if sort_key else _default_sort_key,
        )
    )
    return users


def get_distinct_assignment_objects(annotations):
    """
    Given a set of annotation objects returned by the CATCH database,
    this function returns a list of distinct course assignment objects identified
    by the tuple: (context_id, assignment_id, object_id)
    """
    rows = annotations["rows"]
    assignment_set = set()
    for r in rows:
        context_id = r["contextId"]
        assignment_id = r["collectionId"]
        object_id = str(r["uri"])
        assignment_tuple = (context_id, assignment_id, object_id)
        assignment_set.add(assignment_tuple)
    assignment_objects = list(sorted(assignment_set))
    return assignment_objects


def get_annotations_for_user_id(annotations, user_id):
    """
    Given a set of annotation objects returned by the CATCH database
    and an user ID, this functino returns all of the annotations
    for that user.
    """
    rows = annotations["rows"]
    return [r for r in rows if r["user"]["id"] == user_id]


def get_annotations_keyed_by_user_id(annotations):
    """
    Given a set of annotation objects returned by the CATCH database,
    this function returns a dictionary that maps user IDs to annotation objects.
    """
    rows = annotations["rows"]
    annotations_by_user = {}
    for r in rows:
        user_id = r["user"]["id"]
        annotations_by_user.setdefault(user_id, []).append(r)
    return annotations_by_user


def get_annotations_keyed_by_annotation_id(annotations):
    """
    Given a set of annotation objects returned by the CATCH database,
    this function returns a dictionary that maps annotation IDs to
    annotation objects.

    The intended usage is for when you have an annotation that is a
    reply to another annotation, and you want to lookup the parent
    annotation by its ID.
    """
    rows = annotations["rows"]
    return dict([(r["id"], r) for r in rows])


class DashboardAnnotations(object):
    """
    This class is used to transform annotations retrieved from the CATCH DB into
    a data structure that can be rendered on the instructor dashboard.

    The intended use case is to take a set of course annotations, group them by user,
    and then augment them with additional information that is useful on the dashboard.
    That includes things like the Assignment and TargetObject names associated with the
    annotations, etc.

    Example usage:

        user_annotations = DashboardAnnotations(course_annotations).get_annotations_by_user()

    Notes:

    This class is designed to minimize database hits by loading data up front.
    The assumption is that the number of assignments and target objects in the tool
    is going to be small compared to the number of annotations, so the memory use
    should be negligible.
    """

    def __init__(self, request, annotations):
        self.request = request
        self.annotations = annotations
        self.annotation_by_id = self.get_annotations_by_id()
        self.distinct_users = self.get_distinct_users()
        self.assignment_name_of = self.get_assignments_dict()
        self.target_objects_list = self.get_target_objects_list()
        self.target_objects_by_id = {str(x["id"]): x for x in self.target_objects_list}
        self.target_objects_by_content = {
            x.get("target_content", "").strip(): x
            for x in self.target_objects_list
            if x["target_type"] == "ig"
        }
        self.preview_url_cache = {}

    def get_annotations_by_id(self):
        return get_annotations_keyed_by_annotation_id(self.annotations)

    def get_distinct_users(self):
        return get_distinct_users_from_annotations(
            self.annotations, sort_key=lambda user: user.get("name", "").strip().lower()
        )

    def get_assignments_dict(
        self,
    ):
        return dict(Assignment.objects.values_list("assignment_id", "assignment_name"))

    def get_target_objects_list(self):
        return TargetObject.objects.values(
            "id", "target_title", "target_content", "target_type"
        )

    def get_annotations_by_user(self):
        annotations_by_user = get_annotations_keyed_by_user_id(self.annotations)
        users = []
        for user in self.distinct_users:
            user_id = user["id"]
            user_name = user["name"]
            annotations = []
            for annotation in annotations_by_user[user_id]:
                if self.assignment_object_exists(annotation):
                    annotations.append(
                        {
                            "data": annotation,
                            "assignment_name": self.get_assignment_name(annotation),
                            "target_preview_url": self.get_target_preview_url(
                                annotation
                            ),
                            "target_object_name": self.get_target_object_name(
                                annotation
                            ),
                            "parent_text": self.get_annotation_parent_value(
                                annotation, "text"
                            ),
                        }
                    )
            if len(annotations) > 0:
                users.append(
                    {
                        "id": user_id,
                        "name": user_name,
                        "annotations": annotations,
                        "total_annotations": len(annotations),
                    }
                )
        return users

    """
    Edge cases for get_target_id function that can cause bugs from external manifest uri:
    Note: local testing(hxat and catchpy database) of these URI fails, will need to revisit if bugs pop up in the future
        Assignments using New highlighter images will only store the URI that has "Canvas" or "canvas" in catchpy.
        While the old highlighter will store the manifest URI in addition to the canvas URI
        New Highlighter example data:
        object_id=https://digital.library.villanova.edu/Item/vudl:92879/Canvas/p0
        target_objects_by_content key=https://digital.library.villanova.edu/Item/vudl:92879/Manifest
    """

    def get_target_id(self, media_type, object_id):
        object_id = str(
            object_id
        )  # ensure we have the target id as a string, not an int
        target_id = ""
        if media_type == "image":
            found = object_id.find("/canvas/")
            # in case there is capital letters in the URI
            index = found if found != -1 else object_id.find("/Canvas/")
            trimmed_object_id = object_id if index == -1 else object_id[0:index]
            # gets the data dict from the target_objects_by_content dictionary by trimmed_object_id else assign None
            if trimmed_object_id in self.target_objects_by_content:
                target_id = self.target_objects_by_content[trimmed_object_id]["id"]
        else:
            if object_id in self.target_objects_by_id:
                target_id = object_id
        return target_id

    def get_assignment_name(self, annotation):
        collection_id = annotation["collectionId"]
        if collection_id in self.assignment_name_of:
            return self.assignment_name_of[collection_id]
        return ""

    def get_target_object_name(self, annotation):
        media_type = annotation.get("media", None)
        object_id = annotation["uri"]
        # fix to find correct id using manifest_url instead
        if media_type == "image":
            object_id = annotation["manifest_url"]
        target_id = self.get_target_id(media_type, object_id)
        # the keys in self.target_objects_by_id are strings so the lookup will fail if we pass an int
        if isinstance(target_id, int):
            target_id = str(target_id)
        if target_id in self.target_objects_by_id:
            return self.target_objects_by_id[target_id]["target_title"]
        return ""

    def get_target_preview_url(self, annotation):
        annotation_id = annotation["id"]
        media_type = annotation.get("media", None)
        context_id = annotation["contextId"]
        collection_id = annotation["collectionId"]
        url_format = "{url}?resource_link_id={resource_link_id}&focus_on_id={focus_id}"
        preview_url = ""

        if media_type == "image":
            target_id = self.get_target_id(media_type, annotation["manifest_url"])
            logger.info(f"canvas in={'/canvas/' in  annotation['manifest_url']}")
        else:
            target_id = annotation["uri"]

        if target_id:
            url_cache_key = "%s%s%s" % (context_id, collection_id, target_id)
            if url_cache_key in self.preview_url_cache:
                preview_url = self.preview_url_cache[url_cache_key]
            else:
                preview_url = reverse(
                    "hx_lti_initializer:access_annotation_target",
                    kwargs={
                        "course_id": context_id,
                        "assignment_id": collection_id,
                        "object_id": target_id,
                    },
                )
                self.preview_url_cache[url_cache_key] = preview_url

        if preview_url:
            resource_link_id = self.request.LTI["resource_link_id"]
            preview_url = url_format.format(
                url=preview_url,
                resource_link_id=resource_link_id,
                focus_id=annotation_id,
            )

        return preview_url

    def assignment_object_exists(self, annotation):
        media_type = annotation.get("media", None)
        collection_id = annotation["collectionId"]
        object_id = annotation["uri"]
        if media_type == "image":
            object_id = annotation["manifest_url"]
        target_id = self.get_target_id(media_type, object_id)
        return (collection_id in self.assignment_name_of) and target_id

    def get_annotation_parent_value(self, annotation, attr):
        parent_value = None
        if "parent" in annotation and annotation["parent"]:
            parent_id = annotation["parent"]
            parent_annotation = self.get_annotation_by_id(parent_id)
            if parent_annotation is not None and attr in parent_annotation:
                parent_value = parent_annotation[attr]
        return parent_value

    def get_annotation_by_id(self, annotation_id):
        if annotation_id in self.annotation_by_id:
            return self.annotation_by_id[annotation_id]
        return None


def find_target_object_index(anno_target_items):
    # note: left out "Thumbnail" and "Annotations"
    # help with finding the correct types in the data response
    # TODO: add to constants?
    accepted_catchpy_types = ["Image", "Audio", "Image", "Text", "Video"]
    for index, d in enumerate(anno_target_items):
        if d["type"] in accepted_catchpy_types:
            return index
    return None
