import notification.routing
from channels.routing import ProtocolTypeRouter, URLRouter
from notification.middleware import SessionAuthMiddleware
from channels.http import AsgiHandler

ASGI_APPLICATION = "hxat.routing.application"

django_asgi_app = AsgiHandler()

application = ProtocolTypeRouter(
    {
        # Explicitly set 'http' key using Django's ASGI application.
        "https": django_asgi_app,
        "websocket": SessionAuthMiddleware(
            URLRouter(notification.routing.websocket_urlpatterns)
        ),
    }
)
