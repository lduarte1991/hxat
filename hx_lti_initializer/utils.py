"""
These functions will be used for the initializer module, but may also be
helpful elsewhere.
"""
import django.shortcuts
from urlparse import urlparse
from abstract_base_classes.target_object_database_api import *
from models import *
from django.conf import settings
from ims_lti_py.tool_provider import DjangoToolProvider
import base64
import sys
import datetime
import jwt

# import Sample Target Object Model
from target_object_database.models import TargetObject

# If we were to restructure (not recommended because then we can't reconcile with HX),
# these first 4 functions would be in utils.py
def validate_request(req):
    """
    Validates the request in order to permit or deny access to the LTI tool.
    """
    # print out the request to the terminal window if in debug mode
    # this item is set in the settings, in the __init__.py file
    if settings.LTI_DEBUG:
        for item in sorted(req.POST.dict()):
            debug_printer('DEBUG - %s: %s \r' % (item, req.POST[item]))

    # verifies that request contains the information needed
    if 'oauth_consumer_key' not in req.POST:
        debug_printer('DEBUG - Consumer Key was not present in request.')
        raise PermissionDenied()
    if 'user_id' not in req.POST:
        debug_printer('DEBUG - Anonymous ID was not present in request.')
        raise PermissionDenied()
    if ('lis_person_sourcedid' not in req.POST and
            'lis_person_name_full' not in req.POST):
        debug_printer('DEBUG - Username or Name was not present in request.')
        raise PermissionDenied()


def initialize_lti_tool_provider(req):
    """
    Starts the provider given the consumer_key and secret.
    """
    consumer_key = settings.CONSUMER_KEY
    secret = settings.LTI_SECRET

    # use the function from ims_lti_py app to verify and initialize tool
    provider = DjangoToolProvider(consumer_key, secret, req.POST)

    # NOTE: before validating the request, temporarily remove the
    # QUERY_STRING to work around an issue with how Canvas signs requests
    # that contain GET parameters. Before Canvas launches the tool, it duplicates the GET
    # parameters as POST parameters, and signs the POST parameters (*not* the GET parameters).
    # However, the oauth2 library that validates the request generates
    # the oauth signature based on the combination of POST+GET parameters together,
    # resulting in a signature mismatch. By removing the QUERY_STRING before
    # validating the request, the library will generate the signature based only on
    # the POST parameters like Canvas.
    qs = req.META.pop('QUERY_STRING', '')

    # now validate the tool via the valid_request function
    # this means that request was well formed but invalid
    if provider.valid_request(req) == False:
        debug_printer("DEBUG - LTI Exception: Not a valid request.")
        raise PermissionDenied()
    else:
        debug_printer('DEBUG - LTI Tool Provider was valid.')

    req.META['QUERY_STRING'] = qs  # restore the query string

    return provider


def create_new_user(username, user_id, roles):
    # now create the user and LTIProfile with the above information
    # Max 30 length for person's name, do we want to change this? It's valid for HX but not ATG/FAS
    try:
        user = User.objects.create_user(username, user_id)
    except IntegrityError:
        # TODO: modify db to make student name not the primary key
        # a temporary workaround for key integrity errors, until we can make the username not the primary key.
        return create_new_user(username + " ", user_id, roles)
    user.set_unusable_password()
    user.is_superuser = False
    user.is_staff = False

    for admin_role in settings.ADMIN_ROLES:
        for user_role in roles:
            if admin_role.lower() == user_role.lower():
                user.is_superuser = True
                user.is_staff = True
    user.save()
    debug_printer('DEBUG - User was just created')

    # pull the profile automatically created once the user was above
    lti_profile = LTIProfile.objects.get(user=user)

    lti_profile.anon_id = user_id
    lti_profile.roles = (",").join(roles)
    lti_profile.save()

    return user, lti_profile


def save_session(request, **kwargs):
    session_key_for = {
        "user_id": ["hx_user_id", None],
        "user_name": ["hx_user_name", None],
        "context_id": ["hx_context_id", None],
        "course_id": ["hx_lti_course_id", None],
        "course_name": ["course_name", None],
        "collection_id": ["hx_collection_id", None],
        "object_id": ["hx_object_id", None],
        "roles": ["hx_roles", []],
        "is_staff": ["is_staff", False],
        "is_instructor": ["is_instructor", False],
    }
    
    for k in kwargs:
        if k not in session_key_for:
            raise Exception("invalid keyword argument: %s" % k)

    for k, v in kwargs.iteritems():
        session_key, session_key_default = session_key_for[k]
        request.session[session_key] = kwargs.get(k, session_key_default)
        debug_printer("DEBUG - save_session: (%s, %s) => (%s, %s)" % (k, v, session_key, kwargs.get(k, session_key_default)))

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
        print >> sys.stderr, debug_text


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
