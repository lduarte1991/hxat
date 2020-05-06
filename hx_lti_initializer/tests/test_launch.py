#
# run these with pytest:
# $> DJANGO_SETTINGS_MODULE=annotationsx.settings.test pytest hx_lti_initializer/tests/test_launch.py  -v
#
import pytest

from lti import ToolConsumer
from random import randint

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from hx_lti_initializer.models import LTICourse
from hx_lti_initializer.models import LTIProfile
from .conftest import random_instructor


old_timestamp = '1580487110'


@pytest.mark.django_db
def test_launchLti_session_ok(random_course_instructor):
    instructor = random_course_instructor['profile']
    course = random_course_instructor['course']
    course.course_id = settings.TEST_COURSE  # force context_id
    target_path = reverse('hx_lti_initializer:launch_lti')
    launch_url = 'http://testserver{}'.format(target_path)
    resource_link_id = 'some_string_to_be_the_fake_resource_link_id'
    consumer = ToolConsumer(
            consumer_key=settings.CONSUMER_KEY,
            consumer_secret=settings.TEST_COURSE_LTI_SECRET,
            launch_url=launch_url,
            params={
                'lti_message_type': 'basic-lti-launch-request',
                'lti_version': 'LTI-1p0',
                'resource_link_id': resource_link_id,
                'lis_person_sourcedid': instructor.name,
                'lis_outcome_service_url': 'fake_url',
                'user_id': instructor.anon_id,
                'roles': ['Instructor', 'Administrator'],
                'context_id': course.course_id,
                },
            )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(
            target_path,
            data=params,
            )
    assert(response.status_code == 200)
    assert(response.cookies.get('sessionid'))

    # check some info in session
    assert(client.session is not None)
    assert(client.session.get('LTI_LAUNCH').get(resource_link_id).get('launch_params'))
    launch_params = client.session.get('LTI_LAUNCH').get(resource_link_id).get('launch_params')
    assert(launch_params.get('resource_link_id') == resource_link_id)
    assert(launch_params.get('context_id') == course.course_id)
    assert(launch_params.get('lis_person_sourcedid') == instructor.name)
    assert(launch_params.get('oauth_consumer_key') == settings.CONSUMER_KEY)

    # this will not print if test successful
    for key in launch_params.keys():
        print('************ launch_params: {} = {}'.format(key, launch_params.get(key)))

    for key in client.session.keys():
        print('************ SESSION: {} = {}'.format(key, client.session.get(key)))

    session_lti = client.session.get('LTI_LAUNCH', None)
    assert(session_lti is not None)
    for key in session_lti.keys():
        print('************ session LTI: {} = {}'.format(key, session_lti.get(key)))

    lti_params = session_lti[resource_link_id]
    assert(lti_params is not None)
    for key in lti_params.keys():
        print('************ LTI params: {} = {}'.format(key, lti_params.get(key)))

    # forces error to print above messages!
    #assert(response.context == 'hey')


@pytest.mark.django_db
def test_launchLti_user_course_ok():
    instructor_name = 'audre_lorde'
    instructor_edxid = '{}{}'.format(randint(1000, 65534), randint(1000, 65534))
    course_id = 'hx+FancyCourse+TermCode+Year'
    target_path = reverse('hx_lti_initializer:launch_lti')
    launch_url = 'http://testserver{}'.format(target_path)
    resource_link_id = 'some_string_to_be_the_fake_resource_link_id'
    consumer = ToolConsumer(
            consumer_key=settings.CONSUMER_KEY,
            consumer_secret=settings.LTI_SECRET,
            launch_url=launch_url,
            params={
                'lti_message_type': 'basic-lti-launch-request',
                'lti_version': 'LTI-1p0',
                'resource_link_id': resource_link_id,
                'lis_person_sourcedid': instructor_name,
                'lis_outcome_service_url': 'fake_url',
                'user_id': instructor_edxid,
                'roles': ['Instructor', 'Administrator'],
                #'roles': ['Learner'],
                'context_id': course_id,
                # 04feb20 naomi: context_title has to do with edx studio not
                # sending user_id in launch params to create course user.
                'context_title': '{}+title'.format(course_id),
                },
            )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(
            target_path,
            data=params,
            )
    assert(response.status_code == 200)
    assert(response.cookies.get('sessionid'))

    # check user was created
    user = User.objects.get(username=instructor_name)
    assert(user is not None)
    lti_profile = LTIProfile.objects.get(anon_id=instructor_edxid)
    assert(lti_profile is not None)
    assert(lti_profile.user.username == user.username)

    # check course was created
    course = LTICourse.get_course_by_id(course_id)
    assert(course is not None)
    assert(len(LTICourse.get_all_courses()) == 1)
    assert(course.course_admins.all()[0].anon_id == instructor_edxid)
    assert(course.course_name == '{}+title'.format(course_id))


@pytest.mark.django_db
def test_launchLti_user_course_ok_no_context_title():
    instructor_name = 'sylvia_plath'
    instructor_edxid = '{}{}'.format(randint(1000, 65534), randint(1000, 65534))
    course_id = 'hx+FANcyCourse+TermCode+Year'
    target_path = reverse('hx_lti_initializer:launch_lti')
    launch_url = 'http://testserver{}'.format(target_path)
    resource_link_id = 'some_string_to_be_THE_FAKE_resource_link_id'
    consumer = ToolConsumer(
            consumer_key=settings.CONSUMER_KEY,
            consumer_secret=settings.LTI_SECRET,
            launch_url=launch_url,
            params={
                'lti_message_type': 'basic-lti-launch-request',
                'lti_version': 'LTI-1p0',
                'resource_link_id': resource_link_id,
                'lis_person_sourcedid': instructor_name,
                'lis_outcome_service_url': 'fake_url',
                'user_id': instructor_edxid,
                'roles': ['Instructor', 'Administrator'],
                #'roles': ['Learner'],
                'context_id': course_id,
                # 04feb20 naomi: context_title has to do with edx studio not
                # sending user_id in launch params to create course user.
                #'context_title': '{}+title'.format(course_id),
                },
            )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(
            target_path,
            data=params,
            )
    assert(response.status_code == 200)
    assert(response.cookies.get('sessionid'))

    # check user was created
    user = User.objects.get(username=instructor_name)
    assert(user is not None)
    lti_profile = LTIProfile.objects.get(anon_id=instructor_edxid)
    assert(lti_profile is not None)
    assert(lti_profile.user.username == user.username)

    # check course was created
    course = LTICourse.get_course_by_id(course_id)
    assert(course is not None)
    assert(len(LTICourse.get_all_courses()) == 1)
    assert(course.course_admins.all()[0].anon_id == instructor_edxid)
    assert(course.course_name.startswith('noname-'))


@pytest.mark.django_db
def test_launchLti_expired_timestamp(random_instructor):
    instructor = random_instructor['profile']
    course_id = 'hx+FancyCourse+TermCode+Year'
    target_path = '/lti_init/launch_lti/'
    launch_url = 'http://testserver{}'.format(target_path)
    consumer = ToolConsumer(
            consumer_key=settings.CONSUMER_KEY,
            consumer_secret=settings.LTI_SECRET,
            launch_url=launch_url,
            params={
                'lti_message_type': 'basic-lti-launch-request',
                'lti_version': 'LTI-1p0',
                'resource_link_id': 'FakeResourceLinkID',
                'lis_person_sourcedid': instructor.name,
                'lis_outcome_service_url': 'fake_url',
                'user_id': instructor.anon_id,
                'roles': ['Instructor'],
                'context_id': course_id,
                'context_title': '{}-title'.format(course_id),
                },
            )
    params = consumer.generate_launch_data()
    #replace for old timestamp
    params['oauth_timestamp'] = old_timestamp

    client = Client(enforce_csrf_checks=False)
    response = client.post(
            target_path,
            data=params,
            )
    assert(response.status_code == 403)


@pytest.mark.django_db
def test_launchLti_unknown_consumer_value(random_course_instructor):
    instructor = random_course_instructor['profile']
    course = random_course_instructor['course']
    target_path = '/lti_init/launch_lti/'
    launch_url = 'http://testserver{}'.format(target_path)
    consumer = ToolConsumer(
            # even if it falls back to default LTI_SECRET, it's 403
            # because the oauth_consumer_key is unknown
            consumer_key='stark',
            consumer_secret=settings.LTI_SECRET,
            launch_url=launch_url,
            params={
                'lti_message_type': 'basic-lti-launch-request',
                'lti_version': 'LTI-1p0',
                'resource_link_id': 'FakeResourceLinkID',
                'lis_person_sourcedid': instructor.name,
                'lis_outcome_service_url': 'fake_url',
                'user_id': instructor.anon_id,
                'roles': ['Instructor'],
                'context_id': course.course_id,
                },
            )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(
            target_path,
            data=params,
            )
    assert(response.status_code == 403)


@pytest.mark.django_db
def test_launchLti_known_consumer_value(random_course_instructor):
    instructor = random_course_instructor['profile']
    course = random_course_instructor['course']
    target_path = '/lti_init/launch_lti/'
    launch_url = 'http://testserver{}'.format(target_path)
    consumer = ToolConsumer(
            # falls back to LTI_SECRET because the
            # context_id not found in LTI_SECRET_DICT
            # but oauth_consumer_key is known
            consumer_key=settings.CONSUMER_KEY,
            consumer_secret=settings.LTI_SECRET,
            launch_url=launch_url,
            params={
                'lti_message_type': 'basic-lti-launch-request',
                'lti_version': 'LTI-1p0',
                'resource_link_id': 'FakeResourceLinkID',
                'lis_person_sourcedid': instructor.name,
                'lis_outcome_service_url': 'fake_url',
                'user_id': instructor.anon_id,
                'roles': ['Instructor'],
                'context_id': course.course_id,
                },
            )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(
            target_path,
            data=params,
            )
    assert(response.status_code == 200)


@pytest.mark.django_db
def test_launchLti_missing_context_id(random_course_instructor):
    instructor = random_course_instructor['profile']
    course = random_course_instructor['course']
    target_path = '/lti_init/launch_lti/'
    launch_url = 'http://testserver{}'.format(target_path)
    consumer = ToolConsumer(
            consumer_key=settings.CONSUMER_KEY,
            consumer_secret=settings.LTI_SECRET,
            launch_url=launch_url,
            params={
                'lti_message_type': 'basic-lti-launch-request',
                'lti_version': 'LTI-1p0',
                'resource_link_id': 'FakeResourceLinkID',
                'lis_person_sourcedid': instructor.name,
                'lis_outcome_service_url': 'fake_url',
                'user_id': instructor.anon_id,
                'roles': ['Instructor'],
                # context_id is mandatory to check LTI signature
                #'context_id': course.course_id,
                },
            )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(
            target_path,
            data=params,
            )
    assert(response.status_code == 403)


@pytest.mark.django_db
def test_launchLti_missing_required_param(random_course_instructor):
    instructor = random_course_instructor['profile']
    course = random_course_instructor['course']
    target_path = '/lti_init/launch_lti/'
    launch_url = 'http://testserver{}'.format(target_path)
    consumer = ToolConsumer(
            consumer_key=settings.CONSUMER_KEY,
            consumer_secret=settings.LTI_SECRET,
            launch_url=launch_url,
            params={
                'lti_message_type': 'basic-lti-launch-request',
                'lti_version': 'LTI-1p0',
                'resource_link_id': 'FakeResourceLinkID',
                #'lis_person_sourcedid': instructor.name,
                'lis_outcome_service_url': 'fake_url',
                'user_id': instructor.anon_id,
                'roles': ['Instructor'],
                'context_id': course.course_id,
                },
            )
    params = consumer.generate_launch_data()
    client = Client(enforce_csrf_checks=False)
    response = client.post(
            target_path,
            data=params,
            )

    assert(response.status_code == 400)


@pytest.mark.django_db
def test_launchLti_wrong_secret(random_course_instructor):
    instructor = random_course_instructor['profile']
    course = random_course_instructor['course']
    course.course_id = settings.TEST_COURSE
    target_path = '/lti_init/launch_lti/'
    launch_url = 'http://testserver{}'.format(target_path)
    consumer = ToolConsumer(
            consumer_key=settings.CONSUMER_KEY,
            consumer_secret=settings.LTI_SECRET,
            launch_url=launch_url,
            params={
                'lti_message_type': 'basic-lti-launch-request',
                'lti_version': 'LTI-1p0',
                'resource_link_id': 'FakeResourceLinkID',
                'lis_person_sourcedid': instructor.name,
                'lis_outcome_service_url': 'fake_url',
                'user_id': instructor.anon_id,
                'roles': ['Instructor'],
                'context_id': course.course_id,
                },
            )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(
            target_path,
            data=params,
            )

    assert(response.status_code == 403)

#
# TODO: not able to force a query string using django.test.Client
# debug messages in oauthlib/oauth1/rfc5849/signature.py:verify_hmac_sha1()
# prints request.uri with clear query strings...
#
@pytest.mark.skip
@pytest.mark.django_db
def test_launchLti_with_query_string(random_course_instructor):
    instructor = random_course_instructor['profile']
    course = random_course_instructor['course']
    target_path = '/lti_init/launch_lti/'
    launch_url = 'http://testserver{}?extra_param=blah&more_args=bloft'.format(target_path)
    print('mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm launch_url: {}'.format(launch_url))
    consumer = ToolConsumer(
            consumer_key=settings.CONSUMER_KEY,
            consumer_secret=settings.LTI_SECRET,
            launch_url=launch_url,
            params={
                'lti_message_type': 'basic-lti-launch-request',
                'lti_version': 'LTI-1p0',
                'resource_link_id': 'FakeResourceLinkID',
                'lis_person_sourcedid': instructor.name,
                'lis_outcome_service_url': 'fake_url',
                'user_id': instructor.anon_id,
                'roles': ['Instructor'],
                'context_id': course.course_id,
                },
            )
    params = consumer.generate_launch_data()
    print('mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm lti params: {}'.format(params))

    client = Client(enforce_csrf_checks=False)
    response = client.post(
            target_path,
            data=params,
            )

    print('mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm response content: {}'.format(response.content))
    assert(response.status_code == 403)
    assert(response.content == 'hey')

