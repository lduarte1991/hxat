from channels.routing import ProtocolTypeRouter
from channels.routing import URLRouter

import notification.routing
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

