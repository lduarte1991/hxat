import pytest

from channels.routing import URLRouter
from channels.testing import HttpCommunicator
from channels.testing import WebsocketCommunicator

from django.urls import re_path

from notification.consumers import NotificationConsumer
from notification.middleware import SessionAuthMiddleware


@pytest.mark.asyncio
async def test_wsconn_ok():
    application = URLRouter([
        re_path(r'^ws/notification/(?P<room_name>[^/]+)/$', NotificationConsumer),
        ])
    path = '/ws/notification/course--ad10b1d2--1/?utm_source=3333333'

    communicator = WebsocketCommunicator(application, path)
    connected, subprotocol = await communicator.connect()

    assert connected
    # not sure receive_nothing() is needed
    # it might be good to have some resp from server at application level
    await communicator.receive_nothing()
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_wsconn_auth_ok():
    application = SessionAuthMiddleware(
            URLRouter([
                re_path(
                    r'^ws/notification/(?P<room_name>[^/]+)/$',
                    NotificationConsumer
                ),
            ])
            )
    path = '/ws/notification/course--ad10b1d2--1/?utm_source=3333333&resource_link_id=haha'

    communicator = WebsocketCommunicator(application, path)
    connected, subprotocol = await communicator.connect()

    assert connected
    # not sure receive_nothing() is needed
    # it might be good to have some resp from server at application level
    await communicator.receive_nothing()
    await communicator.disconnect()



    assert(subprotocol == 'juju')
