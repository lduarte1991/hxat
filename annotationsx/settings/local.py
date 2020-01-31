from .base import *

ORGANIZATION = 'HARVARDX'

# django secret must not be empty
SECRET_KEY = 'SECRET'

# local db is sqlite3
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'hxat-test-sqlite3.db'),
    },
}

# test lti consumer keys
CONSUMER_KEY='stark'
LTI_SECRET='winter is coming'
TEST_COURSE='coursex'
TEST_COURSE_LTI_SECRET='coursex_secret'
LTI_SECRET_DICT = {
        TEST_COURSE: TEST_COURSE_LTI_SECRET,
        }

