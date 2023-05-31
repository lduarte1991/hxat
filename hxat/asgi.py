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
# defaults to standard path for .env file if dotenv cant be found from environment variable
if not dotenv_path:
    if os.path.exists(os.path.join('hxat', 'settings', '.env')):
        dotenv_path = os.path.join('hxat', 'settings', '.env')
if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path, override=True)

django.setup()
application = get_default_application()
