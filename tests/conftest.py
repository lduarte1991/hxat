import uuid
from datetime import datetime, timedelta
from random import randint

import pytest
from dateutil import tz
from django.conf import settings
from django.urls import reverse
from hx_lti_assignment.models import Assignment, AssignmentTargets
from hx_lti_initializer.models import LTICourse
from hx_lti_initializer.utils import create_new_user
from lti import ToolConsumer
from lti.tool_outbound import ToolOutbound
from target_object_database.models import TargetObject


@pytest.fixture
def user_profile_factory():
    def _user_profile_factory(roles=["Learner"]):
        random_id = randint(0, 65534)
        random_name = "user_{}".format(random_id)
        display_name = "User {}".format(random_id)
        user, profile = create_new_user(
            anon_id=random_id,
            username=random_name,
            display_name=display_name,
            roles=roles,
            scope="some_random_scope",
        )
        return profile

    return _user_profile_factory


@pytest.fixture
def course_instructor_factory(user_profile_factory):
    def _course_instructor_factory(roles=["Instructor"]):
        course_id = "harvardX+ABC+{}".format(randint(0, 65534))
        instructor = user_profile_factory(roles=roles)
        course = LTICourse.create_course(
            course_id, instructor, name="{}+title".format(course_id)
        )
        return course, instructor

    return _course_instructor_factory


@pytest.fixture
def assignment_target_factory():
    def _assignment_target_factory(course, **kwargs):
        target_object = TargetObject.objects.create(
            target_title=kwargs.get(
                "target_title", "{} Title".format(uuid.uuid4().hex)
            ),
            target_author=kwargs.get(
                "target_author", "John {}".format(uuid.uuid4().int)
            ),
            target_type=kwargs.get("target_type", "tx"),
            target_content=kwargs.get("target_content", ""),
        )
        assignment = Assignment.objects.create(
            course=course,
            assignment_name=kwargs.get(
                "assignment_name", "Assignment {}".format(uuid.uuid4().hex)
            ),
            pagination_limit=settings.ANNOTATION_PAGINATION_LIMIT_DEFAULT,
            # default from settings, this is set by UI
            annotation_database_url=settings.ANNOTATION_DB_URL,
            annotation_database_apikey=settings.ANNOTATION_DB_API_KEY,
            annotation_database_secret_token=settings.ANNOTATION_DB_SECRET_TOKEN,
        )
        assignment_target = AssignmentTargets.objects.create(
            assignment=assignment,
            target_object=target_object,
            order=1,
            target_external_options=kwargs.get("target_external_options"),
        )
        return assignment_target

    return _assignment_target_factory


# from atg pr#109: starting-resource deleted
@pytest.fixture(scope="function")
def random_assignment_target():
    random_id = randint(0, 65534)
    random_name = "user_{}".format(random_id)
    random_course = "harvardX+ABC+{}".format(randint(0, 65534))
    user, profile = create_new_user(
        anon_id=random_id,
        username=random_name,
        display_name=random_name,
        roles=["Instructor"],
        scope="course123",
    )

    course = LTICourse.create_course(random_course, profile)

    target_object = TargetObject.objects.create(
        target_title=f"Text Number {random_id}",
        target_content="Lorem Ipsum",
        target_type="tx",
    )
    assignment = Assignment.objects.create(
        assignment_name=f"Assignment Number {random_id}",
        course=course,
        pagination_limit=100,
    )
    assignment_target = AssignmentTargets.objects.create(
        assignment=assignment,
        target_object=target_object,
        order=1,
    )

    return {
        "assignment_target": assignment_target,
        "assignment": assignment,
        "target_object": target_object,
        "user": user,
        "profile": profile,
        "course": course,
    }


@pytest.fixture(scope="module")
def lti_path():
    return reverse("hx_lti_initializer:launch_lti")


@pytest.fixture(scope="module")
def lti_launch_url(lti_path):
    launch_url = "http://testserver{}".format(lti_path)
    return launch_url


@pytest.fixture(scope="module")
def embed_lti_path():
    return reverse("hx_lti_initializer:embed_lti")


@pytest.fixture(scope="module")
def embed_lti_launch_url(embed_lti_path):
    launch_url = "http://testserver{}".format(embed_lti_path)
    return launch_url


@pytest.fixture
def lti_launch_params_factory():
    def _params_factory(
        course_id,
        user_name,
        user_id,
        user_roles,
        resource_link_id,
        launch_url,
        course_name=None,
        with_grade=False,
        consumer_key=None,
        consumer_secret=None,
        tool_consumer_instance_guid=None,
    ):
        params = {
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": resource_link_id,
            "lis_person_sourcedid": user_name,
            "user_id": user_id,
            "roles": user_roles,
            "context_id": course_id,
        }
        if course_name:
            params["context_title"] = course_name
        if with_grade:
            params["lis_outcome_service_url"] = "http://fake_url.com/"
            params["lis_result_sourcedid"] = "{}:{}:123".format(
                course_id, resource_link_id
            )
        if tool_consumer_instance_guid:
            params["tool_consumer_instance_guid"] = tool_consumer_instance_guid

        consumer = ToolConsumer(
            consumer_key=consumer_key if consumer_key else settings.CONSUMER_KEY,
            consumer_secret=consumer_secret if consumer_secret else settings.LTI_SECRET,
            launch_url=launch_url,
            params=params,
        )
        lti_params = consumer.generate_launch_data()
        return lti_params

    return _params_factory


@pytest.fixture
def lti_content_item_request_factory():
    def _params_factory(
        course_id,
        user_name,
        user_id,
        user_roles,
        launch_url,
        course_name=None,
        consumer_key=None,
        consumer_secret=None,
        tool_consumer_instance_guid=None,
    ):
        # See also:
        #   https://www.imsglobal.org/specs/lticiv1p0/specification
        # Note: The resource_link_id should NOT be passed.
        params = {
            "lti_message_type": "ContentItemSelectionRequest",
            "lti_version": "LTI-1p0",
            "accept_media_types": "image/*,text/html,application/vnd.ims.lti.v1.ltilink,*/*",
            "accept_presentation_document_targets": "embed,frame,iframe,window",
            "accept_unsigned": "true",
            "accept_multiple": "true",
            "auto_create": "false",
            "content_item_return_url": "https://lms.fake/courses/123456/external_content/success/external_tool_dialog",
            "lis_person_sourcedid": user_name,
            "user_id": user_id,
            "roles": user_roles,
            "context_id": course_id,
        }
        if course_name:
            params["context_title"] = course_name
        if tool_consumer_instance_guid:
            params["tool_consumer_instance_guid"] = tool_consumer_instance_guid

        # Using ToolOutbound instead of ToolConsumer because resource_link_id
        # will raise an required param exception otherwise.
        consumer = ToolOutbound(
            consumer_key=consumer_key if consumer_key else settings.CONSUMER_KEY,
            consumer_secret=consumer_secret if consumer_secret else settings.LTI_SECRET,
            launch_url=launch_url,
            params=params,
        )
        lti_params = consumer.generate_launch_data()
        return lti_params

    return _params_factory


@pytest.fixture
def course_user_lti_launch_params(
    user_profile_factory,
    course_instructor_factory,
    lti_path,
    lti_launch_url,
    lti_launch_params_factory,
):
    course, i = course_instructor_factory()
    user_roles = ["Learner"]
    user = user_profile_factory(roles=user_roles)
    resource_link_id = uuid.uuid4().hex
    params = lti_launch_params_factory(
        course_id=course.course_id,
        user_name=user.name,
        user_id=user.anon_id,
        user_roles=user_roles,
        resource_link_id=resource_link_id,
        launch_url=lti_launch_url,
    )
    return (course, user, params)


@pytest.fixture
def course_user_lti_launch_params_factory(
    user_profile_factory,
    course_instructor_factory,
    lti_path,
    lti_launch_url,
    lti_launch_params_factory,
):
    def _cupa_factory(is_staff=False):
        course, i = course_instructor_factory()
        if is_staff:
            user_roles = ["Instructor"]
            user = i
        else:
            user_roles = ["Learner"]
            user = user_profile_factory(roles=user_roles)
        resource_link_id = uuid.uuid4().hex
        params = lti_launch_params_factory(
            course_id=course.course_id,
            user_name=user.name,
            user_id=user.anon_id,
            user_roles=user_roles,
            resource_link_id=resource_link_id,
            launch_url=lti_launch_url,
        )
        return (course, user, params)

    return _cupa_factory


@pytest.fixture
def course_user_lti_launch_params_with_grade(
    user_profile_factory,
    course_instructor_factory,
    lti_path,
    lti_launch_url,
    lti_launch_params_factory,
):
    course, i = course_instructor_factory()
    course.course_id = settings.TEST_COURSE  # force secret from LTI_SECRET_DICT
    course.save()

    user_roles = ["Learner"]
    user = user_profile_factory(roles=user_roles)
    resource_link_id = uuid.uuid4().hex
    params = lti_launch_params_factory(
        course_id=course.course_id,
        user_name=user.name,
        user_id=user.anon_id,
        user_roles=user_roles,
        resource_link_id=resource_link_id,
        launch_url=lti_launch_url,
        with_grade=True,
        consumer_key=settings.CONSUMER_KEY,
        consumer_secret=settings.LTI_SECRET_DICT[settings.TEST_COURSE],
    )
    return (course, user, params)


@pytest.fixture
def annotatorjs_annotation_factory():
    def _annojs_factory(user_profile):
        annojs = make_annotatorjs_object(age_in_hours=1, user=user_profile.anon_id)
        return annojs

    return _annojs_factory


@pytest.fixture
def webannotation_annotation_factory():
    def _webann_factory(user_profile):
        wa = make_wa_object(age_in_hours=1, user=user_profile.anon_id)
        return wa

    return _webann_factory


@pytest.fixture
def catchpy_search_result_shell(user_profile_factory, annotatorjs_annotation_factory):
    result = dict()
    result["total"] = 0
    result["size"] = 0
    result["limit"] = 50
    result["offset"] = 0
    result["size_failed"] = 0
    result["failed"] = []
    result["rows"] = []
    return result


@pytest.fixture
def make_lti_replaceResultResponse():
    resp = """<?xml version="1.0" encoding="UTF-8"?>
<imsx_POXEnvelopeResponse xmlns = "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
  <imsx_POXHeader>
    <imsx_POXResponseHeaderInfo>
      <imsx_version>V1.0</imsx_version>
      <imsx_messageIdentifier>4560</imsx_messageIdentifier>
      <imsx_statusInfo>
        <imsx_codeMajor>success</imsx_codeMajor>
        <imsx_severity>status</imsx_severity>
        <imsx_description>Score for 3124567 is now 0.92</imsx_description>
        <imsx_messageRefIdentifier>999999123</imsx_messageRefIdentifier>
        <imsx_operationRefIdentifier>replaceResult</imsx_operationRefIdentifier>
      </imsx_statusInfo>
    </imsx_POXResponseHeaderInfo>
  </imsx_POXHeader>
  <imsx_POXBody>
    <replaceResultResponse/>
  </imsx_POXBody>
</imsx_POXEnvelopeResponse>
"""
    return resp


#
# some of this is copied from catchpy/anno/tests/conftest.py
#
def get_past_datetime(age_in_hours):
    now = datetime.now(tz.tzutc())
    delta = timedelta(hours=age_in_hours)
    return (now - delta).replace(microsecond=0).isoformat()


def make_annotatorjs_object(age_in_hours=0, media="Text", user=None):
    creator_id = user if user else uuid.uuid4().int
    if age_in_hours > 0:
        created_at = get_past_datetime(age_in_hours)
        created = {
            "id": uuid.uuid4().int,
            "created": created_at,
            "updated": created_at,
            "user": {
                "id": creator_id,
                "name": "user_{}".format(creator_id),
            },
        }
    else:
        created = {}

    wa = {
        "contextId": "fake_context",
        "collectionId": "fake_collection",
        "permissions": {
            "read": [],
            "update": [creator_id],
            "delete": [creator_id],
            "admin": [creator_id],
        },
        "text": uuid.uuid4().hex,
        "totalComments": 0,
        "media": media.lower(),
        "tags": [],
        "ranges": [],
        "uri": "http://fake-{}.com".format(uuid.uuid4().int),
        "parent": "0",
    }

    wa.update(created)
    return wa


def make_wa_object(age_in_hours=0, media="Text", user=None):
    creator_id = user if user else uuid.uuid4().hex
    if age_in_hours > 0:
        created_at = get_past_datetime(age_in_hours)
        created = {
            "id": uuid.uuid4().hex,
            "created": created_at,
            "modified": created_at,
            "creator": {
                "id": creator_id,
                "name": "user_{}".format(creator_id),
            },
            "platform": {
                "platform_name": "CATCH_DEFAULT_PLATFORM_NAME",
                "context_id": "fake_context",
                "collection_id": "fake_collection",
                "target_source_id": "internal_reference_123",
            },
        }
    else:
        created = {}

    body = {
        "type": "List",
        "items": [
            {
                "type": "TextualBody",
                "purpose": "commenting",
                "format": "text/html",
                "value": uuid.uuid4().hex,
            }
        ],
    }
    target = {
        "type": "List",
        "items": [
            {
                "type": media,
                "source": "http://fake-{}.com".format(uuid.uuid4().int),
                "selector": {
                    "type": "Choice",
                    "items": [
                        {
                            "type": "RangeSelector",
                            "startSelector": {"type": "XPathSelector", "value": "xxx"},
                            "endSelector": {"type": "XPathSelector", "value": "yyy"},
                            "refinedBy": [
                                {
                                    "type": "TextPositionSelector",
                                    "start": randint(10, 300),
                                    "end": randint(350, 750),
                                }
                            ],
                        },
                        {"type": "TextQuoteSelector", "exact": uuid.uuid4().hex},
                    ],
                },
            }
        ],
    }
    wa = {
        "@context": "CATCH_JSONLD_CONTEXT_IRI",
        "type": "Annotation",
        "schema_version": "catch v1.0",
        "permissions": {
            "can_read": [],
            "can_update": [creator_id],
            "can_delete": [creator_id],
            "can_admin": [creator_id],
        },
    }
    wa.update(created)
    wa["body"] = body
    wa["target"] = target
    return wa
