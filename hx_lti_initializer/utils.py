"""
These functions will be used for the initializer module, but may also be
helpful elsewhere.
"""
import django.shortcuts
from urlparse import urlparse
from abstract_base_classes.target_object_database_api import *
from models import *
from django.conf import settings
import base64
import sys
import datetime
import jwt

# import Sample Target Object Model
from target_object_database.models import TargetObject


def get_lti_value(key, tool_provider):
    """
    Searches for the given key in the tool_provider. If not found returns None
    """

    lti_value = None
    if "custom" in key:
        lti_value = tool_provider.custom_params[key]
    else:
        try:
            lti_value = getattr(tool_provider, key)
        except AttributeError:
            debug_printer("%s not found in LTI tool_provider" % key)
            return None

    return lti_value


def debug_printer(debug_text):
    """
    Prints text passed in to stderr (Terminal on Mac) for debugging purposes.
    """
    if settings.LTI_DEBUG:
        print >> sys.stderr, str(debug_text) + '\r'


def retrieve_token(userid, apikey, secret):
    '''
    Return a token for the backend of annotations.
    It uses the course id to retrieve a variable that contains the secret
    token found in inheritance.py. It also contains information of when
    the token was issued. This will be stored with the user along with
    the id for identification purposes in the backend.
    '''
    apikey = apikey
    secret = secret
    # the following five lines of code allows you to include the
    # defaulttimezone in the iso format
    # noqa for more information: http://stackoverflow.com/questions/3401428/how-to-get-an-isoformat-datetime-string-including-the-default-timezone

    def _now():
        return datetime.datetime.utcnow().replace(tzinfo=simple_utc()).replace(microsecond=0).isoformat()  # noqa

    token = jwt.encode({
      'consumerKey': apikey,
      'userId': userid,
      'issuedAt': _now(),
      'ttl': 86400
    }, secret)

    return token


class simple_utc(datetime.tzinfo):
    def tzname(self):
        return "UTC"

    def utcoffset(self, dt):
        return datetime.timedelta(0)
