
import pytest

from lti import ToolConsumer
from random import randint

from django.conf import settings
from django.urls import reverse

from hx_lti_initializer.models import LTICourse
from hx_lti_initializer.utils import create_new_user


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
    resource_link_id = 'some_string_to_be_the_FAKE_RESOURCE_link_id'
    params = lti_launch_params_factory(
            course_id=course.course_id,
            user_name=user.name,
            user_id=user.anon_id,
            user_roles=user_roles,
            resource_link_id=resource_link_id,
            launch_url=lti_launch_url,
    )
    return(course, user, params)


