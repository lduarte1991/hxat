
import json
import pytest
import pytest_asyncio
import re

from asgiref.sync import sync_to_async
from django import db
from django.conf import settings
from django.test import Client
from django.urls import reverse
from channels.layers import get_channel_layer
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from channels.testing import WebsocketCommunicator
from lti import ToolConsumer

from hx_lti_initializer.models import LTIResourceLinkConfig
from notification.middleware import NotificationMiddlewareStack
from notification.routing import websocket_urlpatterns


@pytest_asyncio.fixture(loop_scope="session", scope="function")
def ltilaunch_setup(random_assignment_target):
    course = random_assignment_target["course"]
    assignment = random_assignment_target["assignment"]
    target_object = random_assignment_target["target_object"]
    assignment_target = random_assignment_target["assignment_target"]
    instructor = random_assignment_target["profile"]

    course_id = course.course_id
    resource_link_id = "FakeResourceLinkIDStartingResource"
    target_path = "/lti_init/launch_lti/"
    launch_url = "http://testserver{}".format(target_path)

    lti_resource_link_config = LTIResourceLinkConfig.objects.create(
        resource_link_id=resource_link_id, assignment_target=assignment_target,
    )

    consumer = ToolConsumer(
        consumer_key=settings.CONSUMER_KEY,
        consumer_secret=settings.LTI_SECRET,
        launch_url=launch_url,
        params={
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": resource_link_id,
            "lis_person_sourcedid": instructor.name,
            "lis_outcome_service_url": "fake_url",
            "user_id": instructor.anon_id,
            "roles": ["Instructor"],
            "context_id": course_id,
            "context_title": "{}-title".format(course_id),
        },
    )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(target_path, data=params,)
    assert response.status_code == 302
    expected_url = (
        reverse(
            "hx_lti_initializer:access_annotation_target",
            args=[course_id, assignment.assignment_id, target_object.pk],
        )
        + f"?resource_link_id={resource_link_id}"
        + f"&utm_source={client.session.session_key}"
    )
    assert response.url == expected_url
    assert client.session.get("LTI_LAUNCH", None)
    assert response.cookies.get(settings.SESSION_COOKIE_NAME, None)

    response = client.get(expected_url)
    assert response.status_code == 200

    return {
        "course": course,
        "assignment": assignment,
        "target_object": target_object,
        "assignment_target": assignment_target,
        "instructor": instructor,
        "resource_link_id": resource_link_id,
        "multi_launch": client.session.get("LTI_LAUNCH"),
        "session_id": client.session._session_key,
        "session": client.session,
        "cookies": response.cookies.get(settings.SESSION_COOKIE_NAME),
    }


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_wsconn_ok(ltilaunch_setup, webannotation_annotation_factory):

    application = ProtocolTypeRouter({
        "websocket": OriginValidator(
            NotificationMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            ),
            ["*"],
        ),
    })

    pat = re.compile("[^a-zA-Z0-9-.]")
    launch = ltilaunch_setup["multi_launch"].get(ltilaunch_setup["resource_link_id"])
    room_name = "{}--{}--{}".format(
        pat.sub("-", launch["hx_context_id"]),
        pat.sub("-", launch["hx_collection_id"]),
        launch["hx_object_id"],
    )
    settings.ALLOWED_HOSTS = ["*"]  # revert to original value!

    communicator = WebsocketCommunicator(
        application,
        "/ws/notification/{}/?resource_link_id={}".format(
            room_name, ltilaunch_setup["resource_link_id"],
        ),
        headers=[
            (
                b"cookie",
                bytes("{}={}".format(
                    settings.SESSION_COOKIE_NAME, ltilaunch_setup["session_id"]
                ), "utf-8")
            ),
        ],
    )
    connected, _ = await communicator.connect()
    assert connected

    webann = webannotation_annotation_factory(ltilaunch_setup["instructor"])
    channel_layer = get_channel_layer()  # ws notification
    await channel_layer.group_send(
        room_name,
        {
            "type": "annotation_notification",
            "message": json.dumps(webann),
            "action": "annotation_created",
        },
    )

    response = await communicator.receive_json_from()

    assert response["type"] == "annotation_created"
    msg = json.loads(response["message"])
    # we can send annotation from a different context/collection/object !!!!
    assert msg["platform"]["context_id"] == webann["platform"]["context_id"]
    assert msg["platform"]["collection_id"] == webann["platform"]["collection_id"]

    await communicator.disconnect()
