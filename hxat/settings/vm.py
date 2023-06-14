import json

from .base import *

ORGANIZATION = "HARVARDX"

# django secret must not be empty
SECRET_KEY = "SECRET"

# local db is sqlite3
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "hxat2",
        "USER": "hxat",
        "PASSWORD": "hxat",
        "HOST": "dbserver.vm",
        "PORT": "5432",
    }
}

# test lti consumer keys
#CONSUMER_KEY = "stark"
#LTI_SECRET = "winter is coming"
CONSUMER_KEY = "default_consumer_key"
LTI_SECRET = "default_lti_secret"
TEST_COURSE = "coursex"
TEST_COURSE_LTI_SECRET = "coursex_secret"

# course-v1:HarvardX+SW12.4x+2015
# course-v1:HarvardX+HxAT101+2015_T4
