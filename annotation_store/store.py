from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from lti.contrib.django import DjangoToolProvider
from hx_lti_assignment.models import Assignment
from hx_lti_initializer.utils import retrieve_token

import channels.layers
from asgiref.sync import async_to_sync

import json
import requests
import logging
import urllib
import re

logger = logging.getLogger(__name__)

CONSUMER_KEY = settings.CONSUMER_KEY
ANNOTATION_DB_URL = settings.ANNOTATION_DB_URL
ANNOTATION_DB_API_KEY = settings.ANNOTATION_DB_API_KEY
ANNOTATION_DB_SECRET_TOKEN = settings.ANNOTATION_DB_SECRET_TOKEN
ANNOTATION_STORE_SETTINGS = getattr(settings, 'ANNOTATION_STORE', {})
ORGANIZATION = getattr(settings, 'ORGANIZATION', None)


class AnnotationStore(object):
    '''
    AnnotationStore implements a storage interface for annotations and is intended to
    abstract the details of the backend that is actually going to be storing the annotations.

    The backend determines where/how annotations are stored. Possible backends include:

    1) catch - The Common Annotation, Tagging, and Citation at Harvard (CATCH) project
               which is a separate, cloud-based instance with its own REST API.
               See also:
                   http://catcha.readthedocs.io/en/latest/
                   https://github.com/annotationsatharvard/catcha

    2) app   - This is an integrated django app that stores annotations in a local database.

    Client code should not instantiate backend classes directly. The choice of backend class is
    determined at runtime based on the django.settings configuration. This should
    include a setting such as:

    ANNOTATION_STORE = {
        "backend": "catch"
    }

    '''
    SETTINGS = dict(ANNOTATION_STORE_SETTINGS)

    def __init__(self, request, backend_instance=None):
        self.request = request
        self.backend = backend_instance
        self.outcome = None
        self.logger = logging.getLogger('{module}.{cls}'.format(module=__name__, cls=self.__class__.__name__))
        assert self.backend is not None

    @classmethod
    def from_settings(cls, request):
        backend_type_setting = cls.SETTINGS.get('backend', 'catchpy')
        backend_types = backend_type_setting.split(',')
        possible_backend_types = {'catch': CatchStoreBackend, 'catchpy': WebAnnotationStoreBackend}
        if request.method == "GET":
            version_requested = request.GET.get('version', None)
        elif request.method == "DELETE":
            qs = urllib.parse.parse_qs(request.META['QUERY_STRING'])
            try:
                version_requested = qs.get('version')[0]
            except (KeyError, IndexError, TypeError) as e:
                version_requested = None
        else:
            body = json.loads(str(request.body, 'utf-8'))
            version_requested = body.get('version', None)
            if version_requested is None:
                version_requested = request.GET.get('version')
            logger.info('WebAnnotation version found %s' % request.GET.get('version'))
        if version_requested is not None:
            try:
                backend_instance = possible_backend_types[version_requested](request)
                return cls(request, backend_instance)
            except Exception as e:
                logger.info(e)
                logger.info('version requested (%s) not in list of possible types' % version_requested)
                raise e
        else:
            return cls(request, possible_backend_types['catch'](request))


    @classmethod
    def update_settings(cls, settings_dict):
        cls.SETTINGS = settings_dict
        return cls

    def root(self, annotation_id=None):
        return self.backend.root(annotation_id)

    def index(self):
        raise NotImplementedError

    def search(self):
        self.logger.info(u"Search: %s" % self.request.GET)
        self._verify_course(self.request.GET.get('contextId', self.request.GET.get('context_id', None)))
        if hasattr(self.backend, 'before_search'):
            self.backend.before_search()
        response = self.backend.search()
        if hasattr(self.backend, 'after_search'):
            # to give participation grades retroactively after instructor
            # forgets to turn it on initially
            is_graded = self.request.LTI.get('is_graded', False)
            if is_graded and self.backend.after_search(response):
                self.lti_grade_passback(score=1)
        return response

    def create(self, annotation_id=None):
        body = json.loads(str(self.request.body, 'utf-8'))
        self.logger.info(u"Create annotation: %s" % body)
        self._verify_course(body.get('contextId', body.get('context_id', None)))
        self._verify_user(body.get('user', body.get('creator', {})).get('id', None))
        if hasattr(self.backend, 'before_create'):
            self.backend.before_create()
        response = self.backend.create(annotation_id)
        return response

    def read(self, annotation_id):
        raise NotImplementedError

    def after_read(self, annotation_id, response):
        pass

    def update(self, annotation_id):
        body = json.loads(str(self.request.body, 'utf-8'))
        self.logger.info(u"Update annotation %s: %s" % (annotation_id, body))
        self._verify_course(body.get('contextId', body.get('platform', {}).get('context_id', None)))
        self._verify_user(body.get('user', body.get('creator', {})).get('id', None))
        if hasattr(self.backend, 'before_update'):
            self.backend.before_update(annotation_id)
        response = self.backend.update(annotation_id)
        self.after_update(annotation_id, response)
        return response

    def after_update(self, annotation_id, response):
        pass

    def delete(self, annotation_id):
        self.logger.info(u"Delete annotation %s" % annotation_id)
        if hasattr(self.backend, 'before_delete'):
            self.backend.before_delete(annotation_id)
        response = self.backend.delete(annotation_id)
        self.after_delete(annotation_id, response)
        return response

    def after_delete(self, annotation_id, response):
        pass

    def _verify_course(self, context_id, raise_exception=True):
        expected = self.request.LTI['hx_context_id']
        result = context_id == expected
        if not result:
            self.logger.warning("Course verification failed. Expected: %s Actual: %s" % (expected, context_id))
        if raise_exception and not result:
            raise PermissionDenied
        return result

    def _verify_user(self, user_id, raise_exception=True):
        expected = self.request.LTI['hx_user_id']
        result = (user_id == expected or self.request.LTI['is_staff'])
        if not result:
            self.logger.warning("User verification failed. Expected: %s Actual: %s" % (expected, user_id))
        if raise_exception and not result:
            raise PermissionDenied
        return result

    def _get_tool_provider(self):
        try:
            lti_secret = settings.LTI_SECRET_DICT[self.request.LTI.get('hx_context_id')]
        except KeyError:
            lti_secret = settings.LTI_SECRET

        if 'launch_params' in self.request.LTI:
            params = self.request.LTI['launch_params']

            # the middleware includes an LTI dict with all lti params for
            # lti_grade_passback() -- an lti request that is not a lti-launch.
            # py-lti only understands lti params that come directly in the POST
            mutable_post = self.request.POST.copy()
            mutable_post.update(params)
            self.request.POST = mutable_post

            return DjangoToolProvider.from_django_request(
                lti_secret, request=self.request)
        return DjangoToolProvider.from_django_request(
            lti_secret, request=self.request)

    def lti_grade_passback(self, score=1.0):
        if score < 0 or score > 1.0 or isinstance(score, str):
            return
        tool_provider = self._get_tool_provider()
        if not tool_provider.is_outcome_service():
            self.logger.debug("LTI consumer does not expect a grade for the current user and assignment")
            return
        self.logger.info("Initiating LTI Grade Passback: score=%s" % score)
        try:
            outcome = tool_provider.post_replace_result(score)
            self.logger.info(vars(outcome))
            if outcome.is_success():
                self.logger.info(u"LTI grade request was successful. Description: %s" % outcome.description)
            else:
                self.logger.error(u"LTI grade request failed. Description: %s" % outcome.description)
            self.outcome = outcome
        except Exception as e:
            self.logger.error("LTI post_replace_result request failed: %s" % str(e))
        return self.outcome


###########################################################
# Backend Classes


class StoreBackend(object):
    BACKEND_NAME = None
    ADMIN_GROUP_ID = '__admin__'
    ADMIN_GROUP_ENABLED = True if ORGANIZATION == 'ATG' else False

    def __init__(self, request):
        self.request = request
        self.logger = logging.getLogger('{module}.{cls}'.format(module=__name__, cls=self.__class__.__name__))

    def root(self, annotation_id=None):
        return HttpResponse(json.dumps(dict(name=self.BACKEND_NAME)), content_type='application/json')

    def search(self):
        raise NotImplementedError

    def create(self, annotation_id):
        raise NotImplementedError

    def read(self, annotation_id):
        raise NotImplementedError

    def update(self, annotation_id):
        raise NotImplementedError

    def delete(self, annotation_id):
        raise NotImplementedError

    def _get_assignment(self, assignment_id):
        try:
            return get_object_or_404(Assignment, assignment_id=assignment_id)
        except Exception as e:
            self.logger.error("Error loading assignment object: %s" % assignment_id)
            raise e

    def _get_request_body(self):
        body = json.loads(str(self.request.body, 'utf-8'))
        if self.ADMIN_GROUP_ENABLED:
            return self._modify_permissions(body)
        return body

    def _modify_permissions(self, data):
        '''
        Given an annotation data object, update the "read" permissions so that
        course admins can view private annotations.

        Instead of adding the specific user IDs of course admins, a group identifier is used
        so that the IDs aren't hard-coded, which would require updating if the list of admins
        changes in the tool. It's expected that when the tool searchs the annotation database on
        behalf of a course admin, it will use the admin group identifier.

        Possible read permissions:
           - permissions.read = []                        # world-readable (public)
           - permissions.read = [user_id]                 # private (user only)
           - permissions.read = [user_id, ADMIN_GROUP_ID] # semi-private (user + admins only)

        '''
        permissions = {"read": [], "admin": [], "update": [], "delete": []}
        permissions.update(data.get('permissions', {}))
        self.logger.debug("_modify_permissions() before: %s" % str(permissions))

        # No change required when the annotation is world-readable
        if len(permissions['read']) == 0:
            return data

        has_parent = ('parent' in data and data['parent'] != '' and data['parent'] != '0')
        if has_parent:
            # Ensure that when a reply is created, it remains visible to the author of the parent
            # annotation, even if the reply has unchecked "Allow anyone to view this annotation" in
            # the annotator editor. Ideally, the annotator UI field should either be removed from the
            # annotator editor for replies, or work as expected. That is, when checked, only the annotation
            # author, reply author, and thread participants have read permission.
            permissions['read'] = []
        else:
            # Ensure that the annotation author's user_id is present in the read permissions.
            # This might not be the case if an admin changes a public annotation to private,
            # since annotator will set the admin's user_id, and not the author's user_id.
            if data['user']['id'] not in permissions['read']:
                permissions['read'].insert(0, data['user']['id'])

            # Ensure the annotation is readable by course admins.
            if self.ADMIN_GROUP_ID not in permissions['read']:
                permissions['read'].append(self.ADMIN_GROUP_ID)

        self.logger.debug("_modify_permissions() after: %s" % str(permissions))

        data['permissions'] = permissions
        return data

class CatchStoreBackend(StoreBackend):
    BACKEND_NAME = 'catch'

    def __init__(self, request):
        super(CatchStoreBackend, self).__init__(request)
        self.logger = logging.getLogger('{module}.{cls}'.format(module=__name__, cls=self.__class__.__name__))
        self.headers = {
            'x-annotator-auth-token': request.META.get('HTTP_X_ANNOTATOR_AUTH_TOKEN', '!!MISSING!!'),
            'content-type': 'application/json',
        }
        self.timeout = 5.0 # most actions should complete within this amount of time, other than search perhaps

    def root(self, annotation_id):
        self.logger.info(u"MethodType: %s" % self.request.method)
        if self.request.method == "GET":
            self.before_search()
            response = self.search()
            is_graded = self.request.LTI['launch_params'].get('lis_outcome_service_url', None) is not None
            if is_graded and self.after_search(response):
                self.lti_grade_passback(score=1)
                self.logger.info("Grade sent back for user %s" % self.request.LTI['hx_user_id'])
            return response
        elif self.request.method == "POST":
            return self.create(annotation_id)
        elif self.request.method == "PUT":
            return self.update(annotation_id)
        elif self.request.method == "DELETE":
            return self.delete(annotation_id)
        return self.BACKEND_NAME

    def _get_database_url(self, path='/'):
        try:
            if self.request.method == "GET":
                assignment_id = self.request.GET.get('collectionId', self.request.GET.get('collection_id', None))
            else:
                body = self._get_request_body()
                assignment_id = body.get('collectionId', body.get('collection_id', None))
            if assignment_id:
                assignment = self._get_assignment(assignment_id)
                base_url = assignment.annotation_database_url
            else:
                base_url = str(ANNOTATION_DB_URL).strip()
        except:
            self.logger.info("Default annotation_database_url used as assignment could not be found.")
            base_url = str(ANNOTATION_DB_URL).strip()
        return '{base_url}{path}'.format(base_url=base_url, path=path)

    def _retrieve_annotator_token(self, user_id):
        return retrieve_token(user_id, ANNOTATION_DB_API_KEY, ANNOTATION_DB_SECRET_TOKEN)

    def _response_timeout(self):
        return HttpResponse(json.dumps({"error": "request timeout"}), status=500, content_type='application/json')

    def before_search(self):
        # Override the auth token when the user is a course administrator, so they can query annotations
        # that have set their read permissions to private (i.e. read: self-only).
        # Note: this only works if the "__admin__" group ID was added to the annotation read permissions
        # prior to saving it, otherwise this will have no effect.
        if self.ADMIN_GROUP_ENABLED and self.request.LTI['is_staff']:
            self.logger.info('updating auth token for admin')
            self.headers['x-annotator-auth-token'] = self._retrieve_annotator_token(user_id=self.ADMIN_GROUP_ID)

    def search(self):
        timeout = 10.0
        params = self.request.GET.urlencode()
        database_url = self._get_database_url('/search')
        self.logger.info('search request: url=%s headers=%s params=%s timeout=%s' % (database_url, self.headers, params, timeout))
        try:
            response = requests.get(database_url, headers=self.headers, params=params, timeout=timeout)
        except requests.exceptions.Timeout as e:
            self.logger.error("requested timed out!")
            return self._response_timeout()
        self.logger.info('search response status_code=%s content_length=%s' % (response.status_code, response.headers.get('content-length', 0)))
        return HttpResponse(response.content, status=response.status_code, content_type='application/json')

    def after_search(self, response):
        retrieved_self = self.request.LTI['launch_params'].get('user_id', '*') == self.request.GET.get('userid', '')
        return retrieved_self and int(json.loads(response.content)['total'] > 0)

    def create(self, annotation_id):
        body = self._get_request_body()
        database_url = self._get_database_url('/create')
        data = json.dumps(body)
        self.logger.info('create request: url=%s headers=%s data=%s' % (database_url, self.headers, data))
        try:
            response = requests.post(database_url, data=data, headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                is_graded = self.request.LTI['launch_params'].get('lis_outcome_service_url', False)
                self.logger.debug('************** passgrade url({})'.format(is_graded))
                if is_graded:
                    self.lti_grade_passback(score=1)
                    self.logger.info("Grade sent back for user %s" % self.request.LTI['hx_user_id'])
        except requests.exceptions.Timeout as e:
            self.logger.error("requested timed out!")
            return self._response_timeout()
        self.logger.info('create response status_code=%s' % response.status_code)
        return HttpResponse(response.content, status=response.status_code, content_type='application/json')

    def update(self, annotation_id):
        body = self._get_request_body()
        database_url = self._get_database_url('/update/%s' % annotation_id)
        data = json.dumps(body)
        self.logger.info('update request: url=%s headers=%s data=%s' % (database_url, self.headers, data))
        try:
            response = requests.post(database_url, data=data, headers=self.headers, timeout=self.timeout)
        except requests.exceptions.Timeout as e:
            self.logger.error("requested timed out!")
            return self._response_timeout()
        self.logger.info('update response status_code=%s' % response.status_code)
        return HttpResponse(response.content, status=response.status_code, content_type='application/json')

    def delete(self, annotation_id):
        database_url = self._get_database_url('/delete/%s' % annotation_id)
        self.logger.info('delete request: url=%s headers=%s' % (database_url, self.headers))
        try:
            response = requests.delete(database_url, headers=self.headers, timeout=self.timeout)
        except requests.exceptions.Timeout as e:
            self.logger.error("requested timed out!")
            return self._response_timeout()
        self.logger.info('delete response status_code=%s' % response.status_code)
        return HttpResponse(response)

    def _get_tool_provider(self):
        try:
            lti_secret = settings.LTI_SECRET_DICT[self.request.LTI.get('hx_context_id')]
        except KeyError:
            lti_secret = settings.LTI_SECRET

        if 'launch_params' in self.request.LTI:
            params = self.request.LTI['launch_params']

            # the middleware includes an LTI dict with all lti params for
            # lti_grade_passback() -- an lti request that is not a lti-launch.
            # py-lti only understands lti params that come directly in the POST
            mutable_post = self.request.POST.copy()
            mutable_post.update(params)
            self.request.POST = mutable_post

            return DjangoToolProvider.from_django_request(
                lti_secret, request=self.request)
        return DjangoToolProvider.from_django_request(
            lti_secret, request=self.request)

    def lti_grade_passback(self, score=1.0):
        if score < 0 or score > 1.0 or isinstance(score, str):
            return
        tool_provider = self._get_tool_provider()
        if not tool_provider.is_outcome_service():
            self.logger.debug("LTI consumer does not expect a grade for the current user and assignment")
            return
        self.logger.info("Initiating LTI Grade Passback: score=%s" % score)
        try:
            outcome = tool_provider.post_replace_result(score)
            self.logger.info(vars(outcome))
            if outcome.is_success():
                self.logger.info(u"LTI grade request was successful. Description: %s" % outcome.description)
            else:
                self.logger.error(u"LTI grade request failed. Description: %s" % outcome.description)
            self.outcome = outcome
        except Exception as e:
            self.logger.error("LTI post_replace_result request failed: %s" % str(e))


class WebAnnotationStoreBackend(StoreBackend):
    BACKEND_NAME = 'catchpy'

    def __init__(self, request):
        super(WebAnnotationStoreBackend, self).__init__(request)
        self.logger = logging.getLogger('{module}.{cls}'.format(module=__name__, cls=self.__class__.__name__))
        self.headers = {
            'x-annotator-auth-token': request.META.get('HTTP_X_ANNOTATOR_AUTH_TOKEN', '!!MISSING!!'),
            'content-type': 'application/json',
        }
        self.timeout = 5.0 # most actions should complete within this amount of time, other than search perhaps

    def root(self, annotation_id):
        self.logger.info(u"MethodType: %s" % self.request.method)
        self.channel_layer = channels.layers.get_channel_layer()
        if self.request.method == "GET":
            self.before_search()
            response = self.search()
            is_graded = self.request.LTI['launch_params'].get('lis_outcome_service_url', False)

            if is_graded and self.after_search(response):
                self.lti_grade_passback(score=1)
            return response
        elif self.request.method == "POST":
            return self.create(annotation_id)
        elif self.request.method == "PUT":
            return self.update(annotation_id)
        elif self.request.method == "DELETE":
            return self.delete(annotation_id)
        return self.BACKEND_NAME

    def _get_database_url(self, path='/'):
        try:
            if self.request.method == "GET":
                assignment_id = self.request.GET.get('collectionId', self.request.GET.get('collection_id', None))
            elif self.request.method == "DELETE":
                qs = urllib.parse.parse_qs(self.request.META['QUERY_STRING'])
                try:
                    assignment_id = qs.get('collectionId')[0]
                except (KeyError, IndexError) as e:
                    assignment_id = None

            else:
                body = self._get_request_body()
                # 02mar20 naomi: pulling collection_id from wrong place,
                # this is a webannotation so body['platform']['collection_id']
                # related to https://github.com/lduarte1991/hxat/issues/116
                # 03mar20 naomi: if client tries to update the collection_id?
                # what is the supposed behavior for hxat?
                assignment_id = body.get('collectionId', body.get('collection_id', None))
                #assignment_id = body['platform']['collection_id']
            if assignment_id:
                assignment = self._get_assignment(assignment_id)
                base_url = assignment.annotation_database_url
            else:
                # 02mar20 naomi: if collection_id not present it is probably a
                # search throughout course. In this case, search should iterate
                # over all assignments and issue a search per assignment since,
                # potentially, each assignment can be in a different store with
                # different credentials. _get_database_url() maybe returns a
                # map of (collection_id, database_url) pairs and its clients
                # have to deal with that. (see bottom of file item1)
                base_url = str(ANNOTATION_DB_URL).strip()
        except Exception as e:
            base_url = str(ANNOTATION_DB_URL).strip()
            self.logger.info("unknown assignment, fallback to ({}): {}".format(base_url, e))
        return '{base_url}{path}'.format(base_url=base_url, path=path)

    def _retrieve_annotator_token(self, user_id):
        return retrieve_token(user_id, ANNOTATION_DB_API_KEY, ANNOTATION_DB_SECRET_TOKEN)

    def _response_timeout(self):
        return HttpResponse(json.dumps({"error": "request timeout"}), status=500, content_type='application/json')

    def before_search(self):
        # Override the auth token when the user is a course administrator, so they can query annotations
        # that have set their read permissions to private (i.e. read: self-only).
        # Note: this only works if the "__admin__" group ID was added to the annotation read permissions
        # prior to saving it, otherwise this will have no effect.
        if self.ADMIN_GROUP_ENABLED and self.request.LTI['is_staff']:
            self.logger.info('updating auth token for admin')
            self.headers['x-annotator-auth-token'] = self._retrieve_annotator_token(user_id=self.ADMIN_GROUP_ID)

    def search(self):
        timeout = 10.0
        params = self.request.GET.urlencode()
        database_url = self._get_database_url('/')
        self.logger.info('search request: url=%s headers=%s params=%s timeout=%s' % (database_url, self.headers, params, timeout))
        try:
            response = requests.get(database_url, headers=self.headers, params=params, timeout=timeout)
        except requests.exceptions.Timeout as e:
            self.logger.error("requested timed out!")
            return self._response_timeout()
        self.logger.info('search response status_code=%s content_length=%s' % (response.status_code, response.headers.get('content-length', 0)))
        return HttpResponse(response.content, status=response.status_code, content_type='application/json')

    def after_search(self, response):
        # 06mar20 naomi: below code assumes that the search restricted within
        # an assignment (collection_id, context_id present in search params)
        # --- it doesn't check within the search result, but in the query params...
        retrieved_self = self.request.LTI['launch_params'].get('user_id', '*') in self.request.GET.getlist('userid[]', self.request.GET.getlist('userid', []))
        return retrieved_self and int(json.loads(response.content)['total']) > 0

    def create(self, annotation_id):
        body = self._get_request_body()
        database_url = self._get_database_url('/%s' % annotation_id)
        data = json.dumps(body)
        self.logger.info('create request: url=%s headers=%s data=%s' % (database_url, self.headers, data))
        try:
            response = requests.post(database_url, data=data, headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                is_graded = self.request.LTI['launch_params'].get('lis_outcome_service_url', False)
                if is_graded:
                    self.lti_grade_passback(score=1)
        except requests.exceptions.Timeout as e:
            self.logger.error("requested timed out!")
            return self._response_timeout()
        self.logger.info('create response status_code=%s' % response.status_code)
        if response.status_code == 200:
            cleaned_annotation = json.loads(response.content)
            self.send_annotation_notification('annotation_created', cleaned_annotation)
        return HttpResponse(response.content, status=response.status_code, content_type='application/json')

    def update(self, annotation_id):
        body = self._get_request_body()
        database_url = self._get_database_url('/%s' % annotation_id)
        data = json.dumps(body)
        self.logger.info('update request: url=%s headers=%s data=%s' % (database_url, self.headers, data))
        try:
            response = requests.put(database_url, data=data, headers=self.headers, timeout=self.timeout)
        except requests.exceptions.Timeout as e:
            self.logger.error("requested timed out!")
            return self._response_timeout()
        self.logger.info('update response status_code=%s' % response.status_code)
        if response.status_code == 200:
            cleaned_annotation = json.loads(response.content)
            self.send_annotation_notification('annotation_updated', cleaned_annotation)
        return HttpResponse(response.content, status=response.status_code, content_type='application/json')

    def delete(self, annotation_id):
        database_url = self._get_database_url('/%s' % annotation_id)
        self.logger.info('delete request: url=%s headers=%s' % (database_url, self.headers))
        try:
            response = requests.delete(database_url, headers=self.headers, timeout=self.timeout)
        except requests.exceptions.Timeout as e:
            self.logger.error("requested timed out!")
            return self._response_timeout()
        self.logger.info('delete response status_code=%s' % response.status_code)
        if response.status_code == 200:
            cleaned_annotation = json.loads(response.content)
            self.send_annotation_notification('annotation_deleted', cleaned_annotation)
        return HttpResponse(response)


    def _get_tool_provider(self):
        try:
            lti_secret = settings.LTI_SECRET_DICT[self.request.LTI.get('hx_context_id')]
        except KeyError:
            lti_secret = settings.LTI_SECRET

        if 'launch_params' in self.request.LTI:
            params = self.request.LTI['launch_params']

            # the middleware includes an LTI dict with all lti params for
            # lti_grade_passback() -- an lti request that is not a lti-launch.
            # py-lti only understands lti params that come directly in the POST
            mutable_post = self.request.POST.copy()
            mutable_post.update(params)
            self.request.POST = mutable_post

            return DjangoToolProvider.from_django_request(
                lti_secret, request=self.request)

        return DjangoToolProvider.from_django_request(
            lti_secret, request=self.request)


    def lti_grade_passback(self, score=1.0):
        if score < 0 or score > 1.0 or isinstance(score, str):
            return

        tool_provider = self._get_tool_provider()
        if not tool_provider.is_outcome_service():
            self.logger.debug("LTI consumer does not expect a grade for the current user and assignment")
            return
        self.logger.info("Initiating LTI Grade Passback: score=%s" % score)
        try:
            outcome = tool_provider.post_replace_result(score)
            self.logger.info(vars(outcome))
            if outcome.is_success():
                self.logger.info(u"LTI grade request was successful. Description: %s" % outcome.description)
            else:
                self.logger.error(u"LTI grade request failed. Description: %s" % outcome.description)
            self.outcome = outcome
        except Exception as e:
            self.logger.error("LTI post_replace_result request failed: %s" % str(e))


    def send_annotation_notification(self, message_type, annotation):
        # target_source_id from session guarantees it's a sequential integer id from
        # hxat db; image annotations have the uri as target_source_id in `platform`
        pat = re.compile('[^a-zA-Z0-9-.]')
        context_id = pat.sub('-', self.request.LTI["hx_context_id"])
        collection_id = pat.sub('-', self.request.LTI["hx_collection_id"])
        target_source_id = self.request.LTI["hx_object_id"]

        group = '{}--{}--{}'.format(re.sub('[^a-zA-Z0-9-.]', '-', context_id), collection_id, target_source_id)
        self.logger.info("###################### action({}) group({}) id({})".format(
            message_type, group, annotation.get('id', 'unknown_id')))
        try:
            async_to_sync(self.channel_layer.group_send)(group, {
                'type': 'annotation_notification',
                'message': annotation,
                'action': message_type,
            })
        except Exception as e:
            # while transitioning to websockets, it might be that a redis backend is not
            # available and notifications are not really being used; to avoid clogging
            # logs, just printing error; to print the error stack set env var
            # "HXAT_NOTIFY_ERRORLOG=true"
            msg = "###################### action({}) group({}) id({}): {}".format(
                    message_type, group, annotation.get('id', 'unknown_id'), e)
            self.logger.error(msg, exc_info=settings.HXAT_NOTIFY_ERRORLOG)

"""
05mar20 naomi: (item1) right now the assumption is that, at least at course
level, all assignments use the same backend config (same url and credentials).
This is tacit and not enforced in code, we are blindly trusting in the random
goodness of users hearts. This requirement allows developers to create
assignemnts with lti components pointing to other lti providers than prod and
do debugging and tests.

"""
