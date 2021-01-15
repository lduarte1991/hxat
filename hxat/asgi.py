"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting
"""
import os

import django
from channels.routing import get_default_application
from dotenv import load_dotenv

# default settings_module is prod
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hxat.settings.prod")

# if dotenv file, load it
dotenv_path = os.environ.get("HXAT_DOTENV_PATH", None)
if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path, override=True)

django.setup()
application = get_default_application()
