
import pytest
import uuid

from datetime import datetime
from datetime import timedelta
from dateutil import tz
from lti import ToolConsumer
from random import randint

from django.conf import settings
from django.urls import reverse

from hx_lti_assignment.models import Assignment
from hx_lti_assignment.models import AssignmentTargets
from hx_lti_initializer.models import LTICourse
from hx_lti_initializer.utils import create_new_user
from target_object_database.models import TargetObject


@pytest.fixture
def user_profile_factory():
    def _user_profile_factory(roles=['Learner']):
        random_id = randint(0, 65534)
        random_name = 'user_{}'.format(random_id)
        display_name = 'User {}'.format(random_id)
        user, profile = create_new_user(
                anon_id=random_id,
                username=random_name,
                display_name=display_name,
                roles=roles,
                scope='some_random_scope',
        )
        return profile

    return _user_profile_factory


@pytest.fixture
def course_instructor_factory(user_profile_factory):
    def _course_instructor_factory(roles=['Instructor']):
        course_id = 'harvardX+ABC+{}'.format(randint(0, 65534))
        instructor = user_profile_factory(roles=roles)
        course = LTICourse.create_course(
                course_id, instructor,
                name='{}+title'.format(course_id))
        return course, instructor

    return _course_instructor_factory


@pytest.fixture
def assignment_target_factory():
    def _assignment_target_factory(course):
        target_object = TargetObject(
                target_title='{} Title'.format(uuid.uuid4().hex),
                target_author='John {}'.format(uuid.uuid4().int),
                )
        target_object.save()
        assignment = Assignment(
                course=course,
                assignment_name='Assignment {}'.format(uuid.uuid4().hex),
                pagination_limit=settings.ANNOTATION_PAGINATION_LIMIT_DEFAULT,
                # default from settings, this is set by UI
                annotation_database_url = settings.ANNOTATION_DB_URL,
                annotation_database_apikey = settings.ANNOTATION_DB_API_KEY,
                annotation_database_secret_token = settings.ANNOTATION_DB_SECRET_TOKEN,
        )
        assignment.save()
        assignment_target = AssignmentTargets(
                assignment=assignment,
                target_object=target_object,
                order=1,
                )
        assignment_target.save()
        return assignment_target

    return _assignment_target_factory


@pytest.fixture(scope='module')
def lti_path():
    return reverse('hx_lti_initializer:launch_lti')


@pytest.fixture(scope='module')
def lti_launch_url(lti_path):
    launch_url = 'http://testserver{}'.format(lti_path)
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
            ):
        params={
            'lti_message_type': 'basic-lti-launch-request',
            'lti_version': 'LTI-1p0',
            'resource_link_id': resource_link_id,
            'lis_person_sourcedid': user_name,
            'lis_outcome_service_url': 'fake_url',
            'user_id': user_id,
            'roles': user_roles,
            'context_id': course_id,
        }
        if course_name:
            params['context_title'] = course_name

        consumer = ToolConsumer(
                consumer_key=settings.CONSUMER_KEY,
                consumer_secret=settings.LTI_SECRET,
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
    user_roles = ['Learner']
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
    return(course, user, params)


@pytest.fixture
def annotatorjs_annotation_factory():
    def _annojs_factory(user_profile):
        annojs = make_annotatorjs_object(
                age_in_hours=1, user=user_profile.anon_id)
        return annojs

    return _annojs_factory


@pytest.fixture
def webannotation_annotation_factory():
    def _webann_factory(user_profile):
        wa = make_wa_object(
                age_in_hours=1, user=user_profile.anon_id)
        return wa

    return _webann_factory


@pytest.fixture
def catchpy_search_result_shell(
        user_profile_factory,
        annotatorjs_annotation_factory
        ):
    result = dict()
    result['total'] = 0
    result['size'] = 0
    result['limit'] = 50
    result['offset'] = 0
    result['size_failed'] = 0
    result['failed'] = []
    result['rows'] = []
    return result




#
# some of this is copied from catchpy/anno/tests/conftest.py
#
def get_past_datetime(age_in_hours):
    now = datetime.now(tz.tzutc())
    delta = timedelta(hours=age_in_hours)
    return (now - delta).replace(microsecond=0).isoformat()


def make_annotatorjs_object(
        age_in_hours=0, media='Text', user=None):
    creator_id = user if user else uuid.uuid4().int
    if age_in_hours > 0:
        created_at = get_past_datetime(age_in_hours)
        created = {
            'id': uuid.uuid4().int,
            'created': created_at,
            'updated': created_at,
            'user': {
                'id': creator_id,
                'name': 'user_{}'.format(creator_id),
            },
        }
    else:
        created = {}

    wa = {
        'contextId': 'fake_context',
        'collectionId': 'fake_collection',
        'permissions': {
            'read': [],
            'update': [creator_id],
            'delete': [creator_id],
            'admin': [creator_id],
        },
        'text': uuid.uuid4().hex,
        'totalComments': 0,
        'media': media.lower(),
        'tags': [],
        'ranges': [],
        'uri': 'http://fake-{}.com'.format(uuid.uuid4().int),
        'parent': '0',
    }

    wa.update(created)
    return wa


def make_wa_object(
        age_in_hours=0, media='Text', user=None):
    creator_id = user if user else uuid.uuid4().hex
    if age_in_hours > 0:
        created_at = get_past_datetime(age_in_hours)
        created = {
            'id': generate_uid(),
            'created': created_at,
            'modified': created_at,
            'creator': {
                'id': creator_id,
                'name': 'user_{}'.format(creator_id),
            },
            'platform': {
                'platform_name': 'CATCH_DEFAULT_PLATFORM_NAME',
                'context_id': 'fake_context',
                'collection_id': 'fake_collection',
                'target_source_id': 'internal_reference_123',
            },
        }
    else:
        created = {}

    body = {
        'type': 'List',
        'items': [{
            'type': 'TextualBody',
            'purpose': 'commenting',
            'format': 'text/html',
            'value': uuid.uuid4().hex,
        }],
    }
    target = {
        'type': 'List',
        'items': [{
            'type': media,
            'source': 'http://fake-{}.com'.format(uuid.uuid4().int),
            'selector': {
                'type': 'Choice',
                'items': [{
                    'type': 'RangeSelector',
                    'startSelector': {
                        'type': 'XPathSelector', 'value': 'xxx'},
                    'endSelector': {
                        'type': 'XPathSelector', 'value': 'yyy'},
                    'refinedBy': [{
                        'type': 'TextPositionSelector',
                        'start': randint(10, 300),
                        'end': randint(350, 750),
                    }]
                }, {
                    'type': 'TextQuoteSelector',
                    'exact': uuid.uuid4().hex
                }],
            },
        }],
    }
    wa = {
        '@context': 'CATCH_JSONLD_CONTEXT_IRI',
        'type': 'Annotation',
        'schema_version': 'catch v1.0',
        'permissions': {
            'can_read': [],
            'can_update': [creator_id],
            'can_delete': [creator_id],
            'can_admin': [creator_id],
        },
    }
    wa.update(created)
    wa['body'] = body
    wa['target'] = target
    return wa
