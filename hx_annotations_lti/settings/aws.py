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
from .secure import SECURE_SETTINGS
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

#TODO: False for aws, true for local
# SECURITY WARNING: don't run with debug turned on in production!
LTI_DEBUG = True
DEBUG = True
TEMPLATE_DEBUG = True

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECURE_SETTINGS.get('secret_key')

# TODO: find out if this is supposed to be ['*']
ALLOWED_HOSTS = []


# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    #'django_jenkins',
    'bootstrap3',
    'ims_lti_py',
    'hx_lti_initializer',
    'hx_lti_todapi',
    'hx_lti_assignment',
    'django_auth_lti',
    'django_app_lti',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_auth_lti.middleware_patched.MultiLTILaunchAuthMiddleware'
)

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django_auth_lti.backends.LTIAuthBackend',  
)

# Add LTI configuration settings (for django-app-lti)
LTI_SETUP = {
    "TOOL_TITLE": "HX Annotations",
    "TOOL_DESCRIPTION": "Tool for annotating texts ported from HarvardX",

    ##this is where we're getting trouble
    "LAUNCH_URL": "hx_lti_initializer:launch_lti", #"lti_init/launch_lti"

    "LAUNCH_REDIRECT_URL": "hx_lti_initializer:launch_lti",
    "INITIALIZE_MODELS": False, # Options: False|resource_only|resource_and_course|resource_and_course_users


    "EXTENSION_PARAMETERS": {
        "canvas.instructure.com": {
            "privacy_level": "public",
            "course_navigation": {
                "enabled": "true",
                "default": "enabled",
                "text": "Annotations (localhost)", 
            }
        }
    }
}

# Add LTI oauth credentials (for django-auth-lti)
LTI_OAUTH_CREDENTIALS = {
    "123key":"secret",
}

ROOT_URLCONF = 'hx_annotations_lti.urls'

WSGI_APPLICATION = 'hx_annotations_lti.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': SECURE_SETTINGS.get('db_default_name', 'dce_course_info'),
            #'postgres' is in the TLT aws wiki, but won't this give access to all databases?
        'USER': SECURE_SETTINGS.get('db_default_user', 'postgres'),
        'PASSWORD': SECURE_SETTINGS.get('db_default_password'),
        'HOST': SECURE_SETTINGS.get('db_default_host', '127.0.0.1'),
        'PORT': SECURE_SETTINGS.get('db_default_port', 5432),
} }

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
STATICFILES_DIRS = (
    os.path.normpath(os.path.join(os.path.dirname(BASE_DIR), 'hx_lti_initializer/static/')),
)

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
    'django_jenkins.tasks.run_csslint',
)

# note that consumer key will be visible via the request
CONSUMER_KEY = SECURE_SETTINGS.get('consumer_key')

# the secret token will be encoded in the request.
# Only places visible are here and the secret given to the LTI consumer,
# in other words, keep it hidden!
LTI_SECRET = SECURE_SETTINGS.get('lti_secret')

# needs context_id, collection_id, and object_id to open correct item in tool
LTI_COURSE_ID = 'context_id'
LTI_COLLECTION_ID = 'custom_collection_id'
LTI_OBJECT_ID = 'custom_object_id'

# collects roles as user needs to be an admin in order to create a profile
LTI_ROLES = 'roles'

# should be changed depending on platform roles, these are set up for edX
ADMIN_ROLES = ['urn:lti:instrole:ims/lis/Administrator', 'urn:lti:role:ims/lis/Instructor', 'urn:lti:role:ims/lis/TeachingAssistant']
STUDENT_ROLES = ['Learner']

# settings for Annotation Server
DB_API_KEY = SECURE_SETTINGS.get('db_api_key')