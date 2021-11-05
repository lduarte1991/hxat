"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting
"""
import os

import django
import notification.routing
from django.conf.urls import url
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.http import AsgiHandler
from dotenv import load_dotenv

# default settings_module is prod
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hxat.settings.prod")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()
# move below django.setup() due to django exception: django.core.exceptions.ImproperlyConfigured
from notification.middleware import SessionAuthMiddleware
# if dotenv file, load it
dotenv_path = os.environ.get("HXAT_DOTENV_PATH", None)
if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path, override=True)

# application = get_default_application()
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
