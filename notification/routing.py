from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r"^ws/notification/((?P<contextid>[a-zA-Z0-9-.]+)--(?P<collectionid>[a-zA-Z0-9-]+)--(?P<targetid>[0-9]+))+/$",
        consumers.NotificationSyncConsumer.as_asgi()),
]
