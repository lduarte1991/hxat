from django.conf import settings
from abstract_base_classes.target_object_database_api import *
from firebase_token_generator import create_token
from models import *
import base64
import sys
import datetime

# import Sample Target Object Model
from hx_lti_todapi.models import TargetObject


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
            print "Attribute: %s not found in LTI tool_provider" % key

    return lti_value


def debug_printer(debug_text):
    """
    Prints text passed in to stderr (Terminal on Mac) for debugging purposes.
    """
    if settings.LTI_DEBUG:
        print >> sys.stderr, debug_text + '\r'

def retrieve_token(userid, secret):
    '''
    Return a token for the backend of annotations.
    It uses the course id to retrieve a variable that contains the secret
    token found in inheritance.py. It also contains information of when
    the token was issued. This will be stored with the user along with
    the id for identification purposes in the backend.
    '''
    apikey = settings.DB_API_KEY
    secret = apikey
    # the following five lines of code allows you to include the defaulttimezone in the iso format
    # for more information: http://stackoverflow.com/questions/3401428/how-to-get-an-isoformat-datetime-string-including-the-default-timezone

    dtnow = datetime.datetime.now()
    dtutcnow = datetime.datetime.utcnow()
    delta = dtnow - dtutcnow
    newhour, newmin = divmod((delta.days * 24 * 60 * 60 + delta.seconds + 30) // 60, 60)
    newtime = "%s%+02d:%02d" % (dtnow.isoformat(), newhour, newmin)

    # uses the issued time (UTC plus timezone), the consumer key and the user's email to maintain a
    # federated system in the annotation backend server

    custom_data = {"issuedAt": newtime, "consumerKey": apikey, "uid": userid, "ttl": 172800}
    newtoken = create_token(secret, custom_data)
    return newtoken