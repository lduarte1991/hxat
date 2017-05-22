"""
Django settings for hx_lti_tools project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import logging
from django.contrib import messages
from secure import SECURE_SETTINGS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

SECRET_KEY = SECURE_SETTINGS['django_secret_key']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = SECURE_SETTINGS.get('debug', True)

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = SECURE_SETTINGS.get('allowed_hosts', [])

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_extensions',
    'django_jenkins',
    'bootstrap3',
    'crispy_forms',
    'ims_lti_py',
    'hx_lti_initializer',
    'annotation_store',
    'hx_lti_assignment',
    'target_object_database',
    'django_app_lti',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'annotationsx.middleware.XFrameOptionsMiddleware',
    'annotationsx.middleware.CookielessSessionMiddleware',
    'annotationsx.middleware.MultiLTILaunchMiddleware',
    #'annotationsx.middleware.SessionMiddleware',
)

ROOT_URLCONF = 'annotationsx.urls'

WSGI_APPLICATION = 'annotationsx.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': SECURE_SETTINGS.get('db_default_name', 'annotationsx'),
        'USER': SECURE_SETTINGS.get('db_default_user', 'annotationsx'),
        'PASSWORD': SECURE_SETTINGS.get('db_default_password'),
        'HOST': SECURE_SETTINGS.get('db_default_host', 'localhost'),
        'PORT': SECURE_SETTINGS.get('db_default_port', '5432'),
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'http_static/')

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "annotationsx.context_processors.resource_link_id_processor",
    "annotationsx.context_processors.utm_source_processor",
)

MESSAGE_TAGS = {
            messages.SUCCESS: 'success success',
            messages.WARNING: 'warning warning',
            messages.ERROR: 'danger error'
}

# Jenkins configuration
PROJECT_APPS = (
    'hx_lti_initializer',
    'hx_lti_assignment',
    'target_object_database',
)
JENKINS_TASKS = (
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pylint',
)

CRISPY_TEMPLATE_PACK = "bootstrap3"

_DEFAULT_LOG_LEVEL = SECURE_SETTINGS.get('log_level', SECURE_SETTINGS.get('django_log_level', 'DEBUG'))
_LOG_QUERIES = SECURE_SETTINGS.get('log_queries', False)
_LOG_ROOT = SECURE_SETTINGS.get('log_root', '')
_LOG_FILENAME = SECURE_SETTINGS.get('log_filename', 'app.log')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s\t%(asctime)s.%(msecs)03dZ\t%(name)s:%(lineno)s\t%(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s\t%(name)s:%(lineno)s\t%(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'DEBUG',
        },
        'default': {
            'class': 'logging.handlers.WatchedFileHandler',
            'level': _DEFAULT_LOG_LEVEL,
            'formatter': 'verbose',
            'filename': os.path.join(_LOG_ROOT, _LOG_FILENAME),
        },
    },
    # This is the default logger for any apps or libraries that use the logger
    # package, but are not represented in the `loggers` dict below.  A level
    # must be set and handlers defined.  Setting this logger is equivalent to
    # setting an empty string logger in the loggers dict below, but the separation
    # here is a bit more explicit.  See link for more details:
    # https://docs.python.org/2.7/library/logging.config.html#dictionary-schema-details
    'root': {
        'level': logging.WARNING,
        'handlers': ['default', 'console'],
    },
    'loggers': {
        # Add app-specific loggers below.
        # Make sure that propagate is False so that the root logger doesn't get involved
        # after an app logger handles a log message.
        'django.db.backends': {
            'level': 'DEBUG' if _LOG_QUERIES else 'ERROR',
            'handlers': ['default', 'console'],
            'propagate': False,
        },
        'hx_lti_initializer': {
            'level': _DEFAULT_LOG_LEVEL,
            'handlers': ['default', 'console'],
            'propagate': False,
        },
        'hx_lti_assignment': {
            'level': _DEFAULT_LOG_LEVEL,
            'handlers': ['default', 'console'],
            'propagate': False,
        },
        'target_object_database': {
            'level': _DEFAULT_LOG_LEVEL,
            'handlers': ['default', 'console'],
            'propagate': False,
        },
        'annotation_store': {
            'level': _DEFAULT_LOG_LEVEL,
            'handlers': ['default', 'console'],
            'propagate': False,
        },
        'annotationsx.middleware': {
            'level': _DEFAULT_LOG_LEVEL,
            'handlers': ['default', 'console'],
            'propagate': False,
        },
    },
}

LTI_COURSE_ID = "context_id"
LTI_COLLECTION_ID = "custom_collection_id"
LTI_OBJECT_ID = "custom_object_id"
LTI_ROLES = "roles"
LTI_DEBUG = SECURE_SETTINGS.get('debug', False)
ADMIN_ROLES = SECURE_SETTINGS.get('ADMIN_ROLES', {'Administrator'})
LTI_UNIQUE_RESOURCE_ID = 'resource_link_id'
X_FRAME_ALLOWED_SITES = SECURE_SETTINGS.get('X_FRAME_ALLOWED_SITES')
SERVER_NAME = SECURE_SETTINGS.get('SERVER_NAME')
ORGANIZATION = SECURE_SETTINGS.get('ORGANIZATION')

LTI_SETUP = {
    "TOOL_TITLE": "AnnotationsX",
    "TOOL_DESCRIPTION": "Tool for annotating texts ported from HarvardX",

    "LAUNCH_URL": "hx_lti_initializer:launch_lti",  #"lti_init/launch_lti"
    "LAUNCH_REDIRECT_URL": "hx_lti_initializer:launch_lti",
    "INITIALIZE_MODELS": False,  # Options: False|resource_only|resource_and_course|resource_and_course_users

    "EXTENSION_PARAMETERS": {
        "canvas.instructure.com": {
            "privacy_level": "public",
            "course_navigation": {
                "enabled": "true",
                "default": "enabled",
                "text": "AnnotationsX",
            }
        }
    }
}

CONSUMER_KEY = SECURE_SETTINGS['CONSUMER_KEY']
LTI_SECRET = SECURE_SETTINGS['LTI_SECRET'] # ignored if using django_auth_lti

ANNOTATION_MANUAL_URL = SECURE_SETTINGS.get("annotation_manual_url", None)
ANNOTATION_MANUAL_TARGET = SECURE_SETTINGS.get("annotation_manual_target", None)
ANNOTATION_DB_URL = SECURE_SETTINGS.get("annotation_database_url")
ANNOTATION_DB_API_KEY = SECURE_SETTINGS.get("annotation_db_api_key")
ANNOTATION_DB_SECRET_TOKEN = SECURE_SETTINGS.get("annotation_db_secret_token")
ANNOTATION_PAGINATION_LIMIT_DEFAULT = SECURE_SETTINGS.get("annotation_pagination_limit_default", 20)
ANNOTATION_TRANSCRIPT_LINK_DEFAULT = SECURE_SETTINGS.get("annotation_transcript_link_default", None)
ANNOTATION_HTTPS_ONLY = SECURE_SETTINGS.get("https_only", False)
ANNOTATION_LOGGER_URL = SECURE_SETTINGS.get("annotation_logger_url", "")
ANNOTATION_STORE = SECURE_SETTINGS.get("annotation_store", {})

if ANNOTATION_HTTPS_ONLY:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Organization-specific configuration
# Try to minimize this as much as possible in favor of configuration
if ORGANIZATION == "ATG":
    pass
elif ORGANIZATION == "HARVARDX":
    pass
