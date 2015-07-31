"""
These functions will be used for the initializer module, but may also be helpful
elsewhere. 
"""
from django.conf import settings
import django.shortcuts
from urlparse import urlparse
from abstract_base_classes.target_object_database_api import *
from firebase_token_generator import create_token
from models import *
import base64
import sys
import datetime
from django.conf import settings

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

def render(request, template, context):
    #TODO: set this back to false.
    x_frame_allowed = True
    # print request.META
    parsed_uri = urlparse(request.META.get('HTTP_REFERER'))
    domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
    debug_printer('DEBUG - Domain: %s \r' % domain)
    for item in settings.X_FRAME_ALLOWED_SITES:
        if domain.endswith(item):
            x_frame_allowed = True
            break
    response = django.shortcuts.render(request, template, context)
    if not x_frame_allowed:
        response['X-Frame-Options'] = "DENY"
    else :
        response['X-Frame-Options'] = "ALLOW FROM " + domain
    return response
