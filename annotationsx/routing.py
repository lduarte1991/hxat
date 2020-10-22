import notification.routing
from channels.routing import ProtocolTypeRouter, URLRouter
from notification.middleware import SessionAuthMiddleware

ASGI_APPLICATION = 'annotationsx.routing.application'

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': SessionAuthMiddleware(
        URLRouter(
            notification.routing.websocket_urlpatterns
        )
    ),
})

