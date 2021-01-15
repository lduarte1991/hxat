"""
WSGI config for hxat project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""
try:
    from dotenv import load_dotenv
except:
    pass

import os

from django.core.wsgi import get_wsgi_application

# if dotenv file, load it
dotenv_path = None
if "HXAT_DOTENV_PATH" in os.environ:
    dotenv_path = os.environ["HXAT_DOTENV_PATH"]
elif os.path.exists(os.path.join("hxat", "settings", ".env")):
    dotenv_path = os.path.join("hxat", "settings", ".env")
if dotenv_path:
    load_dotenv(dotenv_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hxat.settings.aws")
application = get_wsgi_application()
