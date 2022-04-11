"""
Django settings for hx_lti_tools project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

import logging

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from ast import literal_eval

from django.contrib import messages

try:
    from .secure import SECURE_SETTINGS
except Exception as e:
    SECURE_SETTINGS = dict()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", SECURE_SETTINGS.get("django_secret_key", "")
)

# SECURITY WARNING: don't run with debug turned on in production!

# disambiguation when reading from env: env vars always strings so if
# DEBUG=False, it's still evaluated as boolean True. Some ways to read a
# boolean from a string source in this related thread:
#   https://stackoverflow.com/questions/21732123/convert-true-false-value-read-from-file-to-boolean
debug = os.environ.get("DEBUG", None)
if debug is None:
    DEBUG = SECURE_SETTINGS.get("debug", False)
else:
    DEBUG = debug.lower() == "true"

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
other_hosts = os.environ.get("ALLOWED_HOSTS", None)
if other_hosts is None:  # no envvar, secure.py already has a list object
    allowed_hosts_other = SECURE_SETTINGS.get("allowed_hosts", [])
else:  # space as separator if envvar
    allowed_hosts_other = other_hosts.split()

if allowed_hosts_other:
    ALLOWED_HOSTS.extend(allowed_hosts_other)


# Application definition
INSTALLED_APPS = (
    "channels",
    "notification",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "rest_framework",
    "django_extensions",
    "bootstrap3",
    "crispy_forms",
    "hx_lti_initializer",
    "annotation_store",
    "hx_lti_assignment",
    "target_object_database",
)

MIDDLEWARE = (
    "log_request_id.middleware.RequestIDMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "hxat.middleware.CookielessSessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "hxat.middleware.ContentSecurityPolicyMiddleware",
    "hxat.middleware.MultiLTILaunchMiddleware",
    #'hxat.middleware.SessionMiddleware',
    "hxat.middleware.ExceptionLoggingMiddleware",
)

ROOT_URLCONF = "hxat.urls"

WSGI_APPLICATION = "hxat.wsgi.application"

DATABASES = {
    "default": {
        # django.db.backends.postgresql_psycopg2 module is deprecated in favor of django.db.backends.postgresq
        # https://docs.djangoproject.com/en/3.0/releases/2.0/#id1
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get(
            "HXAT_DB_NAME", SECURE_SETTINGS.get("db_default_name", "annotationsx")
        ),
        "USER": os.environ.get(
            "HXAT_DB_USER", SECURE_SETTINGS.get("db_default_user", "annotationsx")
        ),
        "PASSWORD": os.environ.get(
            "HXAT_DB_PASSWORD", SECURE_SETTINGS.get("db_default_password")
        ),
        "HOST": os.environ.get(
            "HXAT_DB_HOST", SECURE_SETTINGS.get("db_default_host", "localhost")
        ),
        "PORT": os.environ.get(
            "HXAT_DB_PORT", SECURE_SETTINGS.get("db_default_port", "5432")
        ),
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.environ.get("HXAT_STATIC_ROOT", os.path.join(BASE_DIR, "http_static/"))

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "hxat.context_processors.resource_link_id_processor",
                "hxat.context_processors.utm_source_processor",
            ],
            "debug": True,
        },
    }
]

MESSAGE_TAGS = {
    messages.SUCCESS: "success success",
    messages.WARNING: "warning warning",
    messages.ERROR: "danger error",
}

# Jenkins configuration
PROJECT_APPS = (
    "hx_lti_initializer",
    "hx_lti_assignment",
    "target_object_database",
)
JENKINS_TASKS = (
    "django_jenkins.tasks.run_pep8",
    "django_jenkins.tasks.run_pylint",
)

CRISPY_TEMPLATE_PACK = "bootstrap3"

_DEFAULT_LOG_LEVEL = os.environ.get(
    "LOG_LEVEL",
    SECURE_SETTINGS.get("log_level", SECURE_SETTINGS.get("django_log_level", "DEBUG")),
)
_LOG_QUERIES = os.environ.get("LOG_QUERIES", SECURE_SETTINGS.get("log_queries", False))
_LOG_ROOT = os.environ.get("LOG_ROOT", SECURE_SETTINGS.get("log_root", ""))
_LOG_FILENAME = os.environ.get(
    "LOG_FILENAME", SECURE_SETTINGS.get("log_filename", "app.log")
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_id": {
            "()": "log_request_id.filters.RequestIDFilter",
        },
    },
    "formatters": {
        "verbose": {
            "format": "[%(request_id)s]:%(levelname)s\t%(asctime)s.%(msecs)03dZ\t%(name)s:%(lineno)s\t%(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
        "simple": {"format": "[%(request_id)s]:%(levelname)s\t%(name)s:%(lineno)s\t%(message)s",},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_id"],
            "formatter": "simple",
            "level": "DEBUG",
            "stream": "ext://sys.stdout",
        },
        "default": {
            "class": "logging.handlers.WatchedFileHandler",
            "level": _DEFAULT_LOG_LEVEL,
            "filename": os.path.join(_LOG_ROOT, _LOG_FILENAME),
            "filters": ["request_id"],
            "formatter": "verbose",
        },
    },
    # This is the default logger for any apps or libraries that use the logger
    # package, but are not represented in the `loggers` dict below.  A level
    # must be set and handlers defined.  Setting this logger is equivalent to
    # setting an empty string logger in the loggers dict below, but the separation
    # here is a bit more explicit.  See link for more details:
    # https://docs.python.org/2.7/library/logging.config.html#dictionary-schema-details
    "root": {"level": logging.INFO, "handlers": ["default", "console"],},
    "loggers": {
        # Add app-specific loggers below.
        # Make sure that propagate is False so that the root logger doesn't get involved
        # after an app logger handles a log message.
        "django": {
            "level": "ERROR",
            "handlers": ["default", "console"],
            "propagate": False,
        },
        "django.request": {
            "level": "ERROR",
            "handlers": ["default", "console"],
            "propagate": False,
        },
        "django.db.backends": {
            "level": "DEBUG" if _LOG_QUERIES else "ERROR",
            "handlers": ["default", "console"],
            "propagate": False,
        },
        "hx_lti_initializer": {
            "level": _DEFAULT_LOG_LEVEL,
            "handlers": ["default", "console"],
            "propagate": False,
        },
        "hx_lti_assignment": {
            "level": _DEFAULT_LOG_LEVEL,
            "handlers": ["default", "console"],
            "propagate": False,
        },
        "target_object_database": {
            "level": _DEFAULT_LOG_LEVEL,
            "handlers": ["default", "console"],
            "propagate": False,
        },
        "annotation_store": {
            "level": _DEFAULT_LOG_LEVEL,
            "handlers": ["default", "console"],
            "propagate": False,
        },
        "hxat.middleware": {
            "level": _DEFAULT_LOG_LEVEL,
            "handlers": ["default", "console"],
            "propagate": False,
        },
        "hxat.lti_validators": {
            "level": _DEFAULT_LOG_LEVEL,
            "handlers": ["default", "console"],
            "propagate": False,
        },
        "notification": {
            "level": _DEFAULT_LOG_LEVEL,
            "handlers": ["default", "console"],
            "propagate": False,
        },
        "image_store.backends": {
            "level": _DEFAULT_LOG_LEVEL,
            "handlers": ["default", "console"],
            "propagate": False,
        },
    },
}

ADMIN_GROUP_ID = "__admin__"
LTI_COURSE_ID = "context_id"
LTI_COLLECTION_ID = "custom_collection_id"
LTI_OBJECT_ID = "custom_object_id"
LTI_ROLES = "roles"
LTI_DEBUG = os.environ.get("DEBUG", SECURE_SETTINGS.get("debug", False))
ADMIN_ROLES = literal_eval(
    os.environ.get(
        "ADMIN_ROLES", str(SECURE_SETTINGS.get("ADMIN_ROLES", {"Administrator"}))
    )
)
LTI_UNIQUE_RESOURCE_ID = "resource_link_id"
CONTENT_SECURITY_POLICY_DOMAIN = os.environ.get(
    "CONTENT_SECURITY_POLICY_DOMAIN",
    SECURE_SETTINGS.get("content_security_policy_domain", None),
)

SERVER_NAME = os.environ.get("SERVER_NAME", SECURE_SETTINGS.get("SERVER_NAME", ""))
ORGANIZATION = os.environ.get("ORGANIZATION", SECURE_SETTINGS.get("ORGANIZATION", ""))

LTI_TOOL_CONFIGURATION = {
    "title": "AnnotationsX",
    "description": "Tool for annotating text, image, and video",
    "launch_url": "hx_lti_initializer:launch_lti",
    "course_navigation_enabled": True,
    "new_tab": True,
    "embed_enabled": True,
    "embed_url": "hx_lti_initializer:embed_lti",
    "embed_icon_url": "img/HxAT-16x16.png",
}

CONSUMER_KEY = os.environ.get("CONSUMER_KEY", SECURE_SETTINGS.get("CONSUMER_KEY", ""))
LTI_SECRET = os.environ.get(
    "LTI_SECRET", SECURE_SETTINGS.get("LTI_SECRET", "")
)  # ignored if using django_auth_lti
LTI_SECRET_DICT = literal_eval(
    os.environ.get("LTI_SECRET_DICT", str(SECURE_SETTINGS.get("LTI_SECRET_DICT", {})))
)

SITE_ID = 1

ANNOTATION_MANUAL_URL = os.environ.get(
    "MANUAL_URL", SECURE_SETTINGS.get("annotation_manual_url", None)
)
ANNOTATION_MANUAL_TARGET = os.environ.get(
    "MANUAL_TARGET", SECURE_SETTINGS.get("annotation_manual_target", None)
)
ANNOTATION_DB_URL = os.environ.get(
    "ANNOTATION_DB_URL", SECURE_SETTINGS.get("annotation_database_url", "")
)
ANNOTATION_DB_API_KEY = os.environ.get(
    "ANNOTATION_DB_KEY", SECURE_SETTINGS.get("annotation_db_api_key", "")
)
ANNOTATION_DB_SECRET_TOKEN = os.environ.get(
    "ANNOTATION_DB_SECRET", SECURE_SETTINGS.get("annotation_db_secret_token")
)
ANNOTATION_PAGINATION_LIMIT_DEFAULT = os.environ.get(
    "ANNOTATION_LIMIT_DEFAULT",
    SECURE_SETTINGS.get("annotation_pagination_limit_default", 20),
)
ANNOTATION_TRANSCRIPT_LINK_DEFAULT = os.environ.get(
    "ANNOTATION_TRANSCRIPT_DEFAULT",
    SECURE_SETTINGS.get("annotation_transcript_link_default", None),
)
ANNOTATION_HTTPS_ONLY = literal_eval(
    os.environ.get("HTTPS_ONLY", str(SECURE_SETTINGS.get("https_only", False)))
)
ANNOTATION_LOGGER_URL = os.environ.get(
    "ANNOTATION_LOGGER_URL", SECURE_SETTINGS.get("annotation_logger_url", "")
)
ANNOTATION_STORE = os.environ.get(
    "ANNOTATION_STORE", SECURE_SETTINGS.get("annotation_store", {})
)
ACCESSIBILITY = literal_eval(
    os.environ.get("ACCESSIBILITY", str(SECURE_SETTINGS.get("accessibility", True)))
)
IMAGE_STORE_BACKEND = os.environ.get(
    "IMAGE_STORE_BACKEND", str(SECURE_SETTINGS.get("image_store_backend", ""))
)
IMAGE_STORE_BACKEND_CONFIG = os.environ.get(
    "IMAGE_STORE_BACKEND_CONFIG", SECURE_SETTINGS.get("image_store_backend_config", "")
)

# https://docs.djangoproject.com/en/3.2/releases/3.1/#django-contrib-sessions
# due to chrome 80.X, see https://www.chromium.org/updates/same-site
SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SAMESITE = "None"

if ANNOTATION_HTTPS_ONLY:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Instead of using the default JSON serializer, we need to modify it slightly so that
# session dicts stored in JSON are de-serialized with their order preserved. This functionality
# is used in particular by the MultiLTILaunchMiddleware.
SESSION_SERIALIZER = "hxat.serializers.JsonOrderedDictSerializer"

# Organization-specific configuration
# Try to minimize this as much as possible in favor of configuration
if ORGANIZATION == "ATG":
    pass
elif ORGANIZATION == "HARVARDX":
    pass

# channels for notification
ASGI_APPLICATION = "hxat.routing.application"
REDIS_HOST = os.environ.get(
    "REDIS_HOST", SECURE_SETTINGS.get("redis_host", "localhost")
)
REDIS_PORT = os.environ.get("REDIS_PORT", SECURE_SETTINGS.get("redis_port", "6379"))
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [(REDIS_HOST, REDIS_PORT)],},
    }
}
HXAT_NOTIFY_ERRORLOG = os.environ.get("HXAT_NOTIFY_ERRORLOG", "false").lower() == "true"

# time-to-live for ws auth
WS_JWT_TTL = os.environ.get("WS_JWT_TTL", 300)

# https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# log request-id
LOG_REQUEST_ID_HEADER = "HTTP_X_REQUEST_ID"
NO_REQUEST_ID = "none"

