import re
from http import cookies
from random import randint

import pytest
from channels.exceptions import DenyConnection
from channels.routing import URLRouter
from channels.testing import HttpCommunicator, WebsocketCommunicator
from django.conf import settings
from django.test import Client
from django.urls import re_path, reverse
from lti import ToolConsumer
from notification.consumers import NotificationConsumer
from notification.middleware import SessionAuthMiddleware


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_wsauth_missing_querystring():

    application = URLRouter([
        re_path(r'^ws/notification/(?P<room_name>[^/]+)/$',
            NotificationConsumer),
        ])
    mut = SessionAuthMiddleware(application)

    mock_scope = {
            'type': 'websocket',
            'path': '/ws/notification/course--ad10b1d2--1/',
            'query_string': b'',
            'headers': [],
            'subprotocols': [],
    }
    inner_consumer = mut.__call__(scope=mock_scope)

    assert 'hxat_auth' in mock_scope
    assert mock_scope['hxat_auth'] == '403: missing querystring'


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_wsauth_missing_session():

    application = URLRouter([
        re_path(r'^ws/notification/(?P<room_name>[^/]+)/$',
            NotificationConsumer),
        ])
    mut = SessionAuthMiddleware(application)

    mock_scope = {
            'type': 'websocket',
            'path': '/ws/notification/course--ad10b1d2--1/',
            'query_string': 'utm_source=1&resource_link_id=',
            'headers': [],
            'subprotocols': [],
    }
    inner_consumer = mut.__call__(scope=mock_scope)

    assert 'hxat_auth' in mock_scope
    assert mock_scope['hxat_auth'] == '403: missing session-id or resource-link-id'


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_wsauth_unknown_session():

    application = URLRouter([
        re_path(r'^ws/notification/(?P<room_name>[^/]+)/$',
            NotificationConsumer),
        ])
    mut = SessionAuthMiddleware(application)
    utm_source = '333333'
    resource_link_id = 'fake_url'

    mock_scope = {
            'type': 'websocket',
            'path': '/ws/notification/course--ad10b1d2--1/',
            'query_string': 'utm_source={}&resource_link_id={}'.format(utm_source, resource_link_id).encode('utf-8'),
            'headers': [],
            'subprotocols': [],
    }
    inner_consumer = mut.__call__(scope=mock_scope)

    assert 'hxat_auth' in mock_scope
    assert mock_scope['hxat_auth'] == '403: unknown session-id({})'.format(utm_source)


#@pytest.mark.asyncio
@pytest.mark.django_db
def test_wsauth_unknown_contextid():
###
    # prep to create lti session
    instructor_name = 'audre_lorde'
    instructor_edxid = '{}{}'.format(randint(1000, 65534), randint(1000, 65534))
    course_id = 'hx+FancyCourse+TermCode+Year'
    clean_course_id = re.sub(r'[\W_]', '-', course_id)
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
                'context_id': course_id,
                'context_title': '{}+title'.format(course_id),
                },
            )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(
            target_path,
            data=params,
            )
    utm_source = response.cookies.get('sessionid').value

    # prep to create lti session
    ###

    application = URLRouter([
        re_path(r'^ws/notification/(?P<room_name>[^/]+)/$',
            NotificationConsumer),
        ])
    mut = SessionAuthMiddleware(application)

    unknown_context_id = 'babababab'
    mock_scope = {
            'type': 'websocket',
            'path': '/ws/notification/{}--ad10b1d2--1/'.format(unknown_context_id),
            'query_string': 'utm_source={}&resource_link_id={}'.format(utm_source, resource_link_id).encode('utf-8'),
            'headers': [],
            'subprotocols': [],
    }
    inner_consumer = mut.__call__(scope=mock_scope)

    assert 'hxat_auth' in mock_scope
    assert mock_scope['hxat_auth'] == '403: unknown context-id({})'.format(unknown_context_id)


#@pytest.mark.asyncio
@pytest.mark.django_db
def test_wsauth_ok():
###
    # prep to create lti session
    instructor_name = 'sylvia_plath'
    instructor_edxid = '{}{}'.format(randint(1000, 65534), randint(1000, 65534))
    course_id = 'hx+FancierCourse+TermCode+Year'
    clean_course_id = re.sub(r'[\W_]', '-', course_id)
    target_path = reverse('hx_lti_initializer:launch_lti')
    launch_url = 'http://testserver{}'.format(target_path)
    resource_link_id = 'some_string_to_be_THE_fake_resource_link_id'
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
                'context_id': course_id,
                'context_title': '{}+title'.format(course_id),
                },
            )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(
            target_path,
            data=params,
            )
    utm_source = response.cookies.get('sessionid').value
    # prep to create lti session
    ###

    application = URLRouter([
        re_path(r'^ws/notification/(?P<room_name>[^/]+)/$',
            NotificationConsumer),
        ])
    mut = SessionAuthMiddleware(application)

    mock_scope = {
            'type': 'websocket',
            'path': '/ws/notification/{}--ad10b1d2--1/'.format(clean_course_id),
            'query_string': 'utm_source={}&resource_link_id={}'.format(utm_source, resource_link_id).encode('utf-8'),
            'headers': [],
            'subprotocols': [],
    }
    inner_consumer = mut.__call__(scope=mock_scope)

    assert 'hxat_auth' in mock_scope
    assert mock_scope['hxat_auth'] == 'authenticated'


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_wsconn_ok():
    ###
    # prep to create lti session
    instructor_name = 'sylvia_plath'
    instructor_edxid = '{}{}'.format(randint(1000, 65534), randint(1000, 65534))
    course_id = 'hx+FancierCourse+TermCode+Year'
    clean_course_id = re.sub(r'[\W_]', '-', course_id)
    target_path = reverse('hx_lti_initializer:launch_lti')
    launch_url = 'http://testserver{}'.format(target_path)
    resource_link_id = 'some_string_to_be_THE_fake_resource_link_id'
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
                'context_id': course_id,
                'context_title': '{}+title'.format(course_id),
                },
            )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(
            target_path,
            data=params,
            )
    utm_source = response.cookies.get('sessionid').value
    # prep to create lti session
    ###

    application = SessionAuthMiddleware(URLRouter([
        re_path(r'^ws/notification/(?P<room_name>[^/]+)/$', NotificationConsumer),
        ]))
    path = '/ws/notification/{}--dvorak--1/?utm_source={}&resource_link_id={}'.format(
            clean_course_id, utm_source, resource_link_id)

    communicator = WebsocketCommunicator(application, path)
    connected, subprotocol = await communicator.connect()

    assert connected
    # not sure receive_nothing() is needed
    # it might be good to have some resp from server at application level
    await communicator.receive_nothing()
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_wsconn_denied():
    ###
    # prep to create lti session
    instructor_name = 'sylvia_plath'
    instructor_edxid = '{}{}'.format(randint(1000, 65534), randint(1000, 65534))
    course_id = 'hx+FancierCourse+TermCode+Year'
    clean_course_id = re.sub(r'[\W_]', '-', course_id)
    target_path = reverse('hx_lti_initializer:launch_lti')
    launch_url = 'http://testserver{}'.format(target_path)
    resource_link_id = 'some_string_to_be_THE_fake_resource_link_id'
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
                'context_id': course_id,
                'context_title': '{}+title'.format(course_id),
                },
            )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(
            target_path,
            data=params,
            )
    utm_source = response.cookies.get('sessionid').value
    # prep to create lti session
    ###

    application = SessionAuthMiddleware(URLRouter([
        re_path(r'^ws/notification/(?P<room_name>[^/]+)/$', NotificationConsumer),
        ]))
    path = '/ws/notification/qwerty--dvorak--1/?utm_source={}&resource_link_id={}'.format(
            utm_source, resource_link_id)

    communicator = WebsocketCommunicator(application, path)
    connected, subprotocol = await communicator.connect()

    assert not connected
    await communicator.disconnect()





