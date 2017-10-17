"""
These functions will be used for the initializer module, but may also be
helpful elsewhere.
"""
import django.shortcuts
from urlparse import urlparse
from django.core.exceptions import PermissionDenied
from django.db import transaction
from abstract_base_classes.target_object_database_api import *
from models import *
from django.conf import settings
from django.core.urlresolvers import reverse
from ims_lti_py.tool_provider import DjangoToolProvider
from os.path import splitext, basename
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


@transaction.atomic
def create_new_user(anon_id=None, username=None, display_name=None, roles=None, scope=None):
    logger.debug('create_new_user: anon_id=%s, username=%s, display_name=%s, roles=%s' % (anon_id, username, display_name, roles))
    if anon_id is None or display_name is None or roles is None:
        raise Exception("create_new_user missing required parameters: anon_id, display_name, roles")

    lti_profile = LTIProfile(anon_id=anon_id)
    lti_profile.name = display_name
    lti_profile.roles = ",".join(roles)
    lti_profile.scope = scope
    lti_profile.save()

    if not username:
        username = 'profile:{id}'.format(id=lti_profile.id)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User.objects.create_user(username)
        user.is_superuser = False
        user.is_staff = set(roles) & set(settings.ADMIN_ROLES)
        user.set_unusable_password()
        user.save()
    except User.MultipleObjectsReturned:
        user = User.objects.filter(username=username).order_by('id')[0]
    
    lti_profile.user = user
    lti_profile.save(update_fields=['user'])
    
    logger.debug('create_new_user: LTIProfile.%s associated with User.%s' % (lti_profile.id, user.id))
    return user, lti_profile

def save_session(request, **kwargs):
    session_map = {
        "user_id": ["hx_user_id", None],
        "user_name": ["hx_user_name", None],
        "user_scope": ["hx_user_scope", None],
        "context_id": ["hx_context_id", None],
        "course_id": ["hx_lti_course_id", None],
        "course_name": ["course_name", None],
        "collection_id": ["hx_collection_id", None],
        "object_id": ["hx_object_id", None],
        "object_uri": ["hx_object_uri", None],
        "roles": ["hx_roles", []],
        "is_staff": ["is_staff", False],
        "is_instructor": ["is_instructor", False],
        "is_graded": ['is_graded', False],
        "lti_params": ['lti_params', None],
        "resource_link_id": ['resource_link_id', None]
    }

    for k in kwargs:
        assert k in session_map, 'save_session kwarg=%s is not valid!' % k

    resource_link_id = request.LTI['resource_link_id']

    for kwarg in kwargs:
        session_key, default_value = session_map[kwarg]
        session_value = kwargs.get(kwarg, default_value)
        logger.debug("save_session: %s=%s" % (session_key, session_value))
        request.session['LTI_LAUNCH'][resource_link_id][session_key] = session_value
        request.session.modified = True

def get_session_value(request, key, default_value=None):
    resource_link_id = request.LTI['resource_link_id']
    value = request.session['LTI_LAUNCH'][resource_link_id].get(key, default_value)
    logger.debug("get_session_value: %s=%s" % (key, value))
    return value

def get_lti_value(key, request):
    """Returns the LTI parameter from the request otherwise None."""
    value = request.LTI.get('lti_params', {}).get(key, None)
    logger.debug("get_lti_value: %s=%s" % (key, value))
    return value

def debug_printer(debug_text):
    """Logs debug information to the logging system"""
    if settings.LTI_DEBUG:
        logger.debug(str(debug_text))

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

def get_admin_ids(context_id):
    """
        Returns a set of the user ids of all users with an admin role
    """
    course_object = LTICourse.get_course_by_id(context_id)
    admins = course_object.course_admins.all()
    admin_ids = [admin.get_id() for admin in admins]

    return admin_ids

class simple_utc(datetime.tzinfo):
    def tzname(self):
        return "UTC"

    def utcoffset(self, dt):
        return datetime.timedelta(0)

def get_annotation_db_credentials_by_course(context_id):
    '''
    Returns the distinct set of annotation database credentials (url, api key, secret token)
    for a given course.

    The credentials are stored on a per-assignment basis, and a course will have many assignments.
    The expected use case is that *one* credential (url, api key, secret token) will be
    used across all assignments in a course, but it's possible that might not be the case.

    Returns:

    [
        {
            'annotation_database_url': 'http://catch-database.localhost/catch/annotator',
            'annotation_database_apikey': 'Tpt7HaodxVDNQljaMjLz',
            'annotation_database_secret_token': u'GWoXMgXkprYL4ZtkELyq',
        },
        {
            'annotation_database_url': 'https://catch-database.localhost/catch/annotator',
            'annotation_database_apikey': '069fK9KTLHugO7uxjfwN',
            'annotation_database_secret_token': 'Xbi791aSsF4AVWjMhQnl',
        }
    ]
    '''
    fields = ['annotation_database_url', 'annotation_database_apikey', 'annotation_database_secret_token']
    values = Assignment.objects.filter(course__course_id=context_id).values(*fields).distinct(*fields).order_by(*fields)
    
    # The list of database entries might not be unique (despite the *select distinct*) if any of
    # the URLs contain whitespace. The code below accounts for that possibility.
    k, values_by_url = ('annotation_database_url', {})
    for row in values:
        row[k] = row[k].strip()
        if row[k] and row[k] not in values_by_url:
            values_by_url[row[k]] = row

    return values_by_url.values()

def fetch_annotations_by_course(context_id, user_id):
    '''
    Fetches annotations for all assignments in a course as given by the LTI context ID.
    
    This function accounts for the fact that annotation database credentials are stored
    on a per-assignment level, so if course assignments have different annotation database
    settings, they will be included in the results. In general, it's expected that a
    course will have one annotation database setting used across assignments (URL, API KEY, SECRET),
    but it's possible that this assumption could change by the simple fact that the settings
    are saved on assignment models, and not on course models.
    
    Returns: [{"rows": [], "totalCount": 0 }]
    '''
    annotation_db_credentials = get_annotation_db_credentials_by_course(context_id)

    results = {'rows': [], 'totalCount': 0}
    for credential in annotation_db_credentials:
        db_url = credential['annotation_database_url'].strip()
        db_apikey = credential['annotation_database_apikey']
        db_secret = credential['annotation_database_secret_token']
        annotator_auth_token = retrieve_token(user_id, db_apikey, db_secret)
        logger.debug("Fetching annotations with context_id=%s database_url=%s" % (context_id, db_url))
        data = _fetch_annotations_by_course(context_id, db_url, annotator_auth_token)
        #logger.debug("Annotations fetched: %s" % data)
        if 'rows' in data:
            results['rows'] += data['rows']
        if 'totalCount' in data:
            results['totalCount'] += int(data['totalCount'])

    return results

def _fetch_annotations_by_course(context_id, annotation_db_url, annotator_auth_token, **kwargs):
    '''
    Fetches the annotations of a given course from the CATCH database
    '''
    # build request
    headers = {
        "x-annotator-auth-token": annotator_auth_token,
        "Content-Type":"application/json"
    }
    limit = kwargs.get('limit', -1) # Note: -1 means get everything there is
    encoded_context_id = urllib.quote_plus(context_id)
    request_url = "%s/search?contextId=%s&limit=%s" % (annotation_db_url, encoded_context_id, limit)

    logger.debug("fetch_annotations_by_course(): url: %s" % request_url)

    # make request
    request_start_time = time.clock()
    r = requests.get(request_url, headers=headers)
    request_end_time = time.clock()
    request_elapsed_time = request_end_time - request_start_time

    logger.debug("fetch_annotations_by_course(): annotation database response code: %s" % r.status_code)
    logger.debug("fetch_annotations_by_course(): request time elapsed: %s seconds" % (request_elapsed_time))

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
        annotations = {'rows':[], 'totalCount': 0}

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
        self.target_objects_by_content = {
            x.get('target_content', '').strip(): x
            for x in self.target_objects_list
            if x['target_type'] == 'ig'
        }
        self.preview_url_cache = {}

    def get_annotations_by_id(self):
        return get_annotations_keyed_by_annotation_id(self.annotations)

    def get_distinct_users(self):
        sort_key = lambda user: user.get('name', '').strip().lower()
        return get_distinct_users_from_annotations(self.annotations, sort_key)

    def get_assignments_dict(self, ):
        return dict(Assignment.objects.values_list('assignment_id', 'assignment_name'))

    def get_target_objects_list(self):
        return TargetObject.objects.values('id', 'target_title', 'target_content', 'target_type')

    def get_annotations_by_user(self):
        annotations_by_user = get_annotations_keyed_by_user_id(self.annotations)
        users = []
        for user in self.distinct_users:
            user_id = user['id']
            user_name = user['name']
            annotations = []
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
            trimmed_object_id = object_id[0:object_id.find('/canvas/')] # only use regex if absolutely necessary
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
        media_type = annotation.get('media', None)
        object_id = annotation['uri']
        target_id = self.get_target_id(media_type, object_id)
        if target_id in self.target_objects_by_id:
            return self.target_objects_by_id[target_id]['target_title']
        return ''

    def get_target_preview_url(self, annotation):
        annotation_id = annotation['id']
        media_type = annotation.get('media', None)
        context_id = annotation['contextId']
        collection_id = annotation['collectionId']
        url_format = "%s?focus_on_id=%s"
        preview_url = ''

        if media_type == 'image':
            target_id = self.get_target_id(media_type, annotation['uri'])
        else:
            target_id = annotation['uri']

        if target_id:
            url_cache_key = "%s%s%s" % (context_id, collection_id, target_id)
            if url_cache_key in self.preview_url_cache:
                preview_url = self.preview_url_cache[url_cache_key]
            else:
                preview_url = reverse('hx_lti_initializer:access_annotation_target', kwargs={
                    "course_id": context_id,
                    "assignment_id": collection_id,
                    "object_id": target_id,
                })
                self.preview_url_cache[url_cache_key] = preview_url

        if preview_url:
            preview_url = url_format % (preview_url, annotation_id)

        return preview_url
    
    def assignment_object_exists(self, annotation):
        media_type = annotation.get('media', None)
        collection_id = annotation['collectionId']
        object_id = annotation['uri']
        target_id = self.get_target_id(media_type, object_id)
        return (collection_id in self.assignment_name_of) and target_id

    def get_annotation_parent_value(self, annotation, attr):
        parent_value = None
        if 'parent' in annotation and annotation['parent']:
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
