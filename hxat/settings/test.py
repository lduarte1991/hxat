import logging

from .base import *

# for harvardx tests
ORGANIZATION = "HARVARDX"
PLATFORM = "edx"

# django secret must not be empty
SECRET_KEY = "SECRET"

# test db is sqlite3
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "hxat-test-sqlite3.db"),
    },
}

logging = LOGGING["loggers"].update(
    {
        "oauthlib.oauth1.rfc5849": {
            "level": "DEBUG",
            "handlers": ["default", "console"],
            "propagate": False,
        },
        "oauthlib.oauth1.rfc5849.request_validator": {
            "level": "DEBUG",
            "handlers": ["default", "console"],
            "propagate": False,
        },
        "oauthlib.oauth1.rfc5849.utils": {
            "level": "DEBUG",
            "handlers": ["default", "console"],
            "propagate": False,
        },
        "oauthlib.oauth1.rfc5849.endpoints": {
            "level": "DEBUG",
            "handlers": ["default", "console"],
            "propagate": False,
        },
        "oauthlib.oauth1.rfc5849.endpoints.base": {
            "level": "DEBUG",
            "handlers": ["default", "console"],
            "propagate": False,
        },
        "oauthlib.oauth1.rfc5849.endpoints.signature_only": {
            "level": "DEBUG",
            "handlers": ["default", "console"],
            "propagate": False,
        },
    }
)

# test lti consumer keys
CONSUMER_KEY = "consumer_key_for_test"
LTI_SECRET = "lti_secret_for_test"
TEST_COURSE = "test_course_from_LTI_SECRET_DICT"
TEST_COURSE_LTI_SECRET = "lti_secret_from_LTI_SECRET_DICT"
LTI_SECRET_DICT = {
    TEST_COURSE: TEST_COURSE_LTI_SECRET,
}

ANNOTATION_DB_URL = "http://default.annotation.db.url.org"
ANNOTATION_DB_API_KEY = "default_annotation_db_api_key"
ANNOTATION_DB_SECRET_TOKEN = "default_annotation_db_secret_token"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

# redefine logging configs to NOT log in files, just console thank you
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s\t%(asctime)s.%(msecs)03dZ\t%(name)s:%(lineno)s\t%(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
        "simple": {
            "format": "%(levelname)s\t%(name)s:%(lineno)s\t%(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "level": "DEBUG",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    "loggers": {
        # Make sure that propagate is False so that the root logger doesn't get involved
        # after an app logger handles a log message.
        "django": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "django.request": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "django.db.backends": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "hx_lti_initializer": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "hx_lti_assignment": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "target_object_database": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "annostore": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "annostore": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "hxat.middleware": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "hxat": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}
