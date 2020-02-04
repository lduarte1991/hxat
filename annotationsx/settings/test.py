from .base import *

# for harvardx tests
ORGANIZATION = 'HARVARDX'

# django secret must not be empty
SECRET_KEY = 'SECRET'

# test db is sqlite3
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'hxat-test-sqlite3.db'),
    },
}

# test lti consumer keys
CONSUMER_KEY = 'consumer_key_for_test'
LTI_SECRET = 'lti_secret_for_test'
TEST_COURSE = 'test_course'
TEST_COURSE_LTI_SECRET = 'lti_secret_for_test_course'
LTI_SECRET_DICT = {
        TEST_COURSE: TEST_COURSE_LTI_SECRET,
        }

