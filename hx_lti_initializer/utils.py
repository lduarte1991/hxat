"""
These functions will be used for the initializer module, but may also be
helpful elsewhere.
"""
import django.shortcuts
from urlparse import urlparse
from abstract_base_classes.target_object_database_api import *
from models import *
from django.conf import settings
from django.core.urlresolvers import reverse
from ims_lti_py.tool_provider import DjangoToolProvider
import base64
import sys
import time
import datetime
import jwt
import requests
import urllib
import re
import logging

# import Sample Target Object Model
from hx_lti_assignment.models import Assignment
from target_object_database.models import TargetObject

logger = logging.getLogger(__name__)

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


def fetch_annotations_by_course(context_id, token):
    '''
    Fetches the annotations of a given course from the CATCH database
    '''
    # build request
    headers = {
        "x-annotator-auth-token": token,
        "Content-Type":"application/json"
    }
    limit = -1 #TODO: How do we want to handle this?
    encoded_context_id = urllib.quote_plus(context_id)
    request_url = "%s/search?contextId=%s&limit=%s" % (settings.ANNOTATION_DB_URL, encoded_context_id, limit)

    debug_printer("DEBUG - fetch_annotations_by_course(): url: %s" % request_url)

    # make request
    request_start_time = time.clock()
    r = requests.get(request_url, headers=headers)
    request_end_time = time.clock()
    request_elapsed_time = request_end_time - request_start_time

    debug_printer("DEBUG - fetch_annotations_by_course(): annotation database response code: %s" % r.status_code)
    debug_printer("DEBUG - fetch_annotations_by_course(): request time elapsed: %s seconds" % (request_elapsed_time))

    try:
        # this gets the whole request, including such things as 'count'
        # however, that also means that the annotations come in as an object called 'rows,'
        # where each row represents an annotation object.
        # if more convenient, we could cut the top level and just return flat annotations.
        annotations = r.json()
        
    except:
        # If there are no annotations, the database should return a dictionary with empty rows,
        # but in the event of another exception such as an authentication error, fail
        # gracefully by manually passing in that empty response
        annotations = {'rows':[]}

    return annotations

def get_distinct_users_from_annotations(annotations, sort_key=None):
    '''
    Given a set of annotation objects returned by the CATCH database,
    this function returns a list of distinct user objects.
    '''
    rows = annotations['rows']
    annotations_by_user = {}
    for r in rows:
        user_id = r['user']['id']
        if user_id not in annotations_by_user:
            annotations_by_user[user_id] = r['user']
    if sort_key is None:
        sort_key = lambda user: user['id']
    users = list(sorted(annotations_by_user.values(), key=sort_key))
    return users

def get_distinct_assignment_objects(annotations):
    '''
    Given a set of annotation objects returned by the CATCH database,
    this function returns a list of distinct course assignment objects identified
    by the tuple: (context_id, assignment_id, object_id)
    '''
    rows = annotations['rows']
    assignment_set = set()
    for r in rows:
        context_id = r['contextId']
        assignment_id = r['collectionId']
        object_id = str(r['uri'])
        assignment_tuple = (context_id, assignment_id, object_id)
        assignment_set.add(assignment_tuple)
    assignment_objects = list(sorted(assignment_set))
    return assignment_objects

def get_annotations_for_user_id(annotations, user_id):
    '''
    Given a set of annotation objects returned by the CATCH database
    and an user ID, this functino returns all of the annotations
    for that user.
    '''
    rows = annotations['rows']
    return [r for r in rows if r['user']['id'] == user_id]

def get_annotations_keyed_by_user_id(annotations):
    '''
    Given a set of annotation objects returned by the CATCH database,
    this function returns a dictionary that maps user IDs to annotation objects.
    '''
    rows = annotations['rows']
    annotations_by_user = {}
    for r in rows:
        user_id = r['user']['id']
        annotations_by_user.setdefault(user_id, []).append(r)
    return annotations_by_user

def get_annotations_keyed_by_annotation_id(annotations):
    '''
    Given a set of annotation objects returned by the CATCH database,
    this function returns a dictionary that maps annotation IDs to
    annotation objects.
    
    The intended usage is for when you have an annotation that is a
    reply to another annotation, and you want to lookup the parent
    annotation by its ID.
    '''
    rows = annotations['rows']
    return dict([(r['id'], r) for r in rows])


class DashboardAnnotations(object):
    '''
    This class is used to transform annotations retrieved from the CATCH DB into
    a data structure that can be rendered on the instructor dashboard.
    
    The intended use case is to take a set of course annotations, group them by user,
    and then augment them with additional information that is useful on the dashboard.
    That includes things like the Assignment and TargetObject names associated with the
    annotations, etc.
    
    Example usage:
    
        user_annotations = DashboardAnnotations(course_annotations).get_annotations_by_user()
    
    Notes:

    This class is designed to minimize database hits by loading data up front.
    The assumption is that the number of assignments and target objects in the tool
    is going to be small compared to the number of annotations, so the memory use
    should be negligible.
    '''

    def __init__(self, annotations):
        self.annotations = annotations
        self.annotation_by_id = self.get_annotations_by_id()
        self.distinct_users = self.get_distinct_users()
        self.assignment_name_of = self.get_assignments_dict()
        self.target_objects_list = self.get_target_objects_list()
        self.target_objects_by_id = {x['id']: x for x in self.target_objects_list}
        self.target_objects_by_content = {x.get('target_content', '').strip(): x for x in self.target_objects_list}

    def get_annotations_by_id(self):
        return get_annotations_keyed_by_annotation_id(self.annotations)

    def get_distinct_users(self):
        sort_key = lambda user: user.get('name', '').strip().lower()
        return get_distinct_users_from_annotations(self.annotations, sort_key)

    def get_assignments_dict(self, ):
        return dict(Assignment.objects.values_list('assignment_id', 'assignment_name'))

    def get_target_objects_list(self):
        return TargetObject.objects.values('id', 'target_title', 'target_content')

    def get_annotations_by_user(self):
        annotations_by_user = get_annotations_keyed_by_user_id(self.annotations)
        users = []
        for user in self.distinct_users:
            user_id = user['id']
            user_name = user['name']
            annotations = []
            total_annotations = 0
            total_comments = 0
            for annotation in annotations_by_user[user_id]:
                if self.assignment_object_exists(annotation):
                    annotations.append({
                        'data': annotation,
                        'assignment_name': self.get_assignment_name(annotation),
                        'target_preview_url': self.get_target_preview_url(annotation),
                        'target_object_name': self.get_target_object_name(annotation),
                        'parent_text': self.get_annotation_parent_value(annotation, 'text'),
                    })
            if len(annotations) > 0:
                users.append({
                    'id': user_id,
                    'name': user_name,
                    'annotations': annotations,
                    'total_annotations': len(annotations),
                })
        return users

    def get_target_id(self, media_type, object_id):
        target_id = ''
        if media_type == 'image':
            trimmed_object_id = re.sub(r'/canvas/.*$', '', object_id)
            if trimmed_object_id in self.target_objects_by_content:
                target_id = self.target_objects_by_content[trimmed_object_id]['id']
        else:
            if object_id in self.target_objects_by_id:
                target_id = object_id
        return target_id
    
    def get_assignment_name(self, annotation):
        collection_id = annotation['collectionId']
        if collection_id in self.assignment_name_of:
            return self.assignment_name_of[collection_id]
        return ''
    
    def get_target_object_name(self, annotation):
        media_type = annotation['media']
        object_id = annotation['uri']
        target_id = self.get_target_id(media_type, object_id)
        if target_id in self.target_objects_by_id:
            return self.target_objects_by_id[target_id]['target_title']
        return ''

    def get_target_preview_url(self, annotation):
        annotation_id = annotation['id']
        media_type = annotation['media']
        context_id = annotation['contextId']
        collection_id = annotation['collectionId']
        url_format = "%s?focus_id=%s"
        preview_url = ''
        
        if media_type == 'image':
            target_id = self.get_target_id(media_type, annotation['uri'])
            if target_id:
                preview_url = url_format % (reverse('hx_lti_initializer:access_annotation_target', kwargs={
                    "course_id": context_id,
                    "assignment_id": collection_id,
                    "object_id": target_id,
                }), annotation_id)
        else:
            preview_url = url_format % (reverse('hx_lti_initializer:access_annotation_target', kwargs={
                "course_id": context_id,
                "assignment_id": collection_id,
                "object_id": annotation['uri'],
            }), annotation_id)
        
        
        return preview_url
    
    def assignment_object_exists(self, annotation):
        media_type = annotation['media']
        collection_id = annotation['collectionId']
        object_id = annotation['uri']
        target_id = self.get_target_id(media_type, object_id)
        return (collection_id in self.assignment_name_of) and target_id

    def get_annotation_parent_value(self, annotation, attr):
        parent_value = None
        if annotation['parent']:
            parent_id = annotation['parent']
            parent_annotation = self.get_annotation_by_id(parent_id)
            if parent_annotation is not None and attr in parent_annotation:
                parent_value = parent_annotation[attr]
        return parent_value

    def get_annotation_by_id(self, annotation_id):
        annotation_id = int(annotation_id)
        if annotation_id in self.annotation_by_id:
            return self.annotation_by_id[annotation_id]
        return None