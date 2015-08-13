"""
Django settings for hx_lti_tools project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from django.contrib import messages
from secure import SECURE_SETTINGS
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECURE_SETTINGS['django_secret_key']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


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
    'hx_lti_assignment',
    'target_object_database',
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
    #'django_auth_lti.middleware.LTIAuthMiddleware',
    #'django_auth_lti.middleware_patched.MultiLTILaunchAuthMiddleware'
)

ROOT_URLCONF = 'annotationsx.urls'

WSGI_APPLICATION = 'annotationsx.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

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

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'http_static/')

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

MESSAGE_TAGS = {
            messages.SUCCESS: 'success success',
            messages.WARNING: 'warning warning',
            messages.ERROR: 'danger error'
}

PROJECT_APPS = (
    'hx_lti_initializer',
)

JENKINS_TASKS = (
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pylint',
)

CRISPY_TEMPLATE_PACK = "bootstrap3"

LTI_COURSE_ID = "context_id"
LTI_COLLECTION_ID = "custom_collection_id"
LTI_OBJECT_ID = "custom_object_id"
LTI_ROLES = "roles"
LTI_DEBUG = SECURE_SETTINGS.get('debug', False)
LTI_SECRET = SECURE_SETTINGS['LTI_SECRET'] # ignored if using django_auth_lti
CONSUMER_URL = SECURE_SETTINGS.get('CONSUMER_URL', '') 
CONSUMER_KEY = SECURE_SETTINGS['CONSUMER_KEY'] 
ADMIN_ROLES = SECURE_SETTINGS.get('ADMIN_ROLES', {'Administrator'}) 
X_FRAME_ALLOWED_SITES = SECURE_SETTINGS.get('X_FRAME_ALLOWED_SITES', {'harvard.edu'})
X_FRAME_ALLOWED_SITES_MAP = SECURE_SETTINGS.get('X_FRAME_ALLOWED_SITES_MAP', {'harvard.edu':'harvardx.harvard.edu'})

# Add to authentication backends (for django-auth-lti)
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django_auth_lti.backends.LTIAuthBackend',
)

LTI_SETUP = {
    "TOOL_TITLE": "AnnotationsX",
    "TOOL_DESCRIPTION": "Tool for annotating texts ported from HarvardX",

    "LAUNCH_URL": "hx_lti_initializer:launch_lti", #"lti_init/launch_lti"
    "LAUNCH_REDIRECT_URL": "hx_lti_initializer:launch_lti",
    "INITIALIZE_MODELS": False, # Options: False|resource_only|resource_and_course|resource_and_course_users

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

# Add LTI oauth credentials (for django-auth-lti)
# hard fail (keyerror) if not present
LTI_OAUTH_CREDENTIALS = SECURE_SETTINGS['lti_oauth_credentials']

ANNOTATION_DB_URL = SECURE_SETTINGS.get("annotation_database_url")
ANNOTATION_DB_API_KEY = SECURE_SETTINGS.get("annotation_db_api_key")
ANNOTATION_DB_SECRET_TOKEN = SECURE_SETTINGS.get("annotation_db_secret_token")


CSRF_COOKIE_SECURE = SECURE_SETTINGS.get("https_only", True)
SESSION_COOKIE_SECURE = SECURE_SETTINGS.get("https_only", True)
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# AWS SSL settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
