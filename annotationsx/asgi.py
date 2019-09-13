"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting
"""
from dotenv import load_dotenv
import os
from channels.routing import get_default_application
import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "annotationsx.settings.prod")

# if dotenv file, load it
dotenv_path = os.environ.get(
    'HXAT_DOTENV_PATH', 'annotationsx.settings.prod')
if dotenv_path:
    load_dotenv(dotenv_path)

django.setup()
application = get_default_application()
