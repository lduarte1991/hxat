"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from dotenv import load_dotenv

# default settings_module is prod
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hxat.settings.prod")

# if dotenv file, load it
dotenv_path = os.environ.get("HXAT_DOTENV_PATH", None)
# defaults to standard path for .env file if dotenv cant be found from environment variable
if not dotenv_path:
    if os.path.exists(os.path.join("hxat", "settings", ".env")):
        dotenv_path = os.path.join("hxat", "settings", ".env")
if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path, override=True)

# initialize django asgi application early to ensure the AppRegistry
# is populated before importing code that may import ORM models
django_asgi_app = get_asgi_application()


from notification.routing import websocket_urlpatterns  # noqa

application = ProtocolTypeRouter(
    {
        # django's asgi apps to handle traditional http requests
        "http": django_asgi_app,
        # websocket notification app
        "websocket": AllowedHostsOriginValidator(
            URLRouter(websocket_urlpatterns),
        ),
    }
)
