from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F, Q
from ims_lti_py.tool_provider import DjangoToolProvider
from hx_lti_assignment.models import Assignment
from hx_lti_initializer.utils import retrieve_token

from models import Annotation, AnnotationTags, UserStats

import json
import requests
import datetime
import logging

logger = logging.getLogger(__name__)

CONSUMER_KEY, LTI_SECRET = settings.CONSUMER_KEY, settings.LTI_SECRET
ANNOTATION_STORE_SETTINGS = getattr(settings, 'ANNOTATION_STORE', {})


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
        "gather_statistics": False,
    }

    '''
    SETTINGS = dict(ANNOTATION_STORE_SETTINGS)

    def __init__(self, request, backend_instance=None, gather_statistics=False):
        self.request = request
        self.backend = backend_instance
        self.gather_statistics = gather_statistics
        self.grade_passback_outcome = None
        assert self.backend is not None
        assert isinstance(self.gather_statistics, bool)
        logger.info("Initialized %s with backend=%s gather_statistics=%s" % (self.__class__.__name__, self.backend.__class__.__name__, self.gather_statistics))

    @classmethod
    def from_settings(cls, request):
        gather_statistics = cls.SETTINGS.get('gather_statistics', False)
        backend_type = cls.SETTINGS.get('backend', 'catch')
        backend_types = {'app': AppStoreBackend, 'catch': CatchStoreBackend}
        assert backend_type in backend_types
        backend_instance = backend_types[backend_type](request)
        return cls(request, backend_instance=backend_instance, gather_statistics=gather_statistics)

    @classmethod
    def update_settings(cls, settings_dict):
        cls.SETTINGS = settings_dict
        return cls

    def root(self):
        return self.backend.root()

    def index(self):
        raise NotImplementedError

    def search(self):
        logger.debug(u"Search: %s" % self.request.GET)
        self._verify_course(self.request.GET.get('contextId', None))
        if hasattr(self.backend, 'before_search'):
            self.backend.before_search()
        return self.backend.search()

    def create(self):
        body = json.loads(self.request.body)
        logger.debug(u"Create: %s" % body)
        self._verify_course(body.get('contextId', None))
        self._verify_assignment(body.get('collectionId', None))
        self._verify_object(body.get('uri', None))
        self._verify_user(body.get('user', {}).get('id', None))
        if hasattr(self.backend, 'before_create'):
            self.backend.before_create()
        response = self.backend.create()
        self.after_create(response)
        return response

    def after_create(self, response):
        is_graded = self.request.session.get('is_graded', False)
        self._lti_grade_passback(is_graded=is_graded, status_code=response.status_code, result_score=1)
        self._update_stats('create', response)

    def read(self, annotation_id):
        raise NotImplementedError

    def after_read(self, response):
        self._update_stats('read', response)

    def update(self, annotation_id):
        body = json.loads(self.request.body)
        logger.debug(u"Update %s: %s" % (annotation_id, body))
        self._verify_course(body.get('contextId', None))
        self._verify_assignment(body.get('collectionId', None))
        self._verify_object(body.get('uri', None))
        self._verify_user(body.get('user', {}).get('id', None))
        if hasattr(self.backend, 'before_update'):
            self.backend.before_update(annotation_id)
        response = self.backend.update(annotation_id)
        self.after_update(response)
        return response

    def after_update(self, response):
        self._update_stats('update', response)

    def delete(self, annotation_id):
        body = json.loads(self.request.body)
        logger.debug(u"Delete %s: %s" % (annotation_id, body))
        self._verify_course(body.get('contextId', None))
        self._verify_assignment(body.get('collectionId', None))
        self._verify_object(body.get('uri', None))
        self._verify_user(body.get('user', {}).get('id', None))
        if hasattr(self.backend, 'before_delete'):
            self.backend.before_delete(annotation_id)
        response = self.backend.delete(annotation_id)
        self.after_delete(response)
        return response

    def after_delete(self, response):
        self._update_stats('delete', response)

    def _verify_course(self, context_id, raise_exception=True):
        result = (context_id == self.request.session['hx_context_id'])
        if raise_exception and not result:
            raise PermissionDenied
        return result

    def _verify_assignment(self, assignment_id, raise_exception=True):
        result = (assignment_id == self.request.session['hx_collection_id'])
        if raise_exception and not result:
            raise PermissionDenied
        return result

    def _verify_object(self, object_id, raise_exception=True):
        result = (str(object_id) == str(self.request.session['hx_object_id']))
        if raise_exception and not result:
            raise PermissionDenied
        return result

    def _verify_user(self, user_id, raise_exception=True):
        result = (user_id == self.request.session['hx_user_id'] or self.request.session['is_staff'])
        if raise_exception and not result:
            raise PermissionDenied
        return result

    def _get_tool_provider(self):
        params = self.request.session['lti_params']
        tool_provider = DjangoToolProvider(CONSUMER_KEY, LTI_SECRET, params)
        return tool_provider

    def _lti_grade_passback(self, is_graded=False, status_code=None, result_score=1):
        logger.debug("LTI Grade Passback: is_graded=%s status_code=%s result_score=%s" % (is_graded, status_code, result_score))
        if not (is_graded and status_code == 200):
            return
        try:
            outcome = self._get_tool_provider().post_replace_result(result_score)
            self.grade_passback_outcome = outcome
            msg = {
                "status":      "successful" if outcome.is_success() else "unsuccessful",
                "description": outcome.description,
            }
            logger.debug(u"LTI grade request was {status}. Description is {description}".format(**msg))
        except Exception as e:
            logger.error("Error submitting grade outcome after annotation created: %s" % str(e))
        return self.grade_passback_outcome

    def _update_stats(self, action, response):
        if not self.gather_statistics:
            return
        if action not in ('create', 'update', 'delete'):
            return

        body = json.loads(response.content)
        attrs = {
            'context_id':body['contextId'],
            'collection_id': body['collectionId'],
            'uri': body['uri'],
            'user_id': body['user']['id'],
            'user_name': body['user']['name'],
        }
        qs = list(UserStats.objects.filter(**attrs))
        if len(qs) == 0:
            userstats = UserStats.objects.create(**attrs)
        else:
            userstats = qs[0]

        if body['media'] == 'comment':
            if action == 'create':
                userstats.total_comments = F('total_comments') + 1
            elif action == 'delete':
                userstats.total_comments = F('total_comments') - 1
        else:
            if action == 'create':
                userstats.total_annotations = F('total_annotations') + 1
            elif action == 'delete':
                userstats.total_annotations = F('total_annotations') - 1

        userstats.save()

###########################################################
# Backend Classes


class StoreBackend(object):
    BACKEND_NAME = None
    ADMIN_GROUP_ID = '__admin__'
    ADMIN_GROUP_ENABLED = True if settings.ORGANIZATION == 'ATG' else False

    def __init__(self, request):
        self.request = request

    def root(self):
        return HttpResponse(json.dumps(dict(name=self.BACKEND_NAME)), content_type='application/json')

    def search(self):
        raise NotImplementedError

    def create(self):
        raise NotImplementedError

    def read(self, annotation_id):
        raise NotImplementedError

    def update(self, annotation_id):
        raise NotImplementedError

    def delete(self, annotation_id):
        raise NotImplementedError

    def _get_assignment(self, assignment_id):
        return get_object_or_404(Assignment, assignment_id=assignment_id)

    def _get_request_body(self):
        body = json.loads(self.request.body)
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
        logger.debug("_modify_permissions() before: %s" % str(permissions))

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

        logger.debug("_modify_permissions() after: %s" % str(permissions))

        data['permissions'] = permissions
        return data

class CatchStoreBackend(StoreBackend):
    BACKEND_NAME = 'catch'

    def __init__(self, request):
        super(CatchStoreBackend, self).__init__(request)
        self.headers = {
            'x-annotator-auth-token': request.META.get('HTTP_X_ANNOTATOR_AUTH_TOKEN', '!!MISSING!!'),
            'content-type': 'application/json',
        }

    def _get_database_url(self, assignment, path='/'):
        base_url = str(assignment.annotation_database_url).strip()
        return '{base_url}{path}'.format(base_url=base_url, path=path)

    def _retrieve_annotator_token(self, user_id, assignment):
        return retrieve_token(user_id, assignment.annotation_database_apikey, assignment.annotation_database_secret_token)

    def before_search(self):
        # Override the auth token when the user is a course administrator, so they can query annotations
        # that have set their read permissions to private (i.e. read: self-only).
        # Note: this only works if the "__admin__" group ID was added to the annotation read permissions
        # prior to saving it, otherwise this will have no effect.
        if self.ADMIN_GROUP_ENABLED and self.request.session['is_staff']:
            assignment = self._get_assignment(self.request.GET.get('collectionId', None))
            self.headers['x-annotator-auth-token'] = self._retrieve_annotator_token(
                assignment=assignment,
                user_id=self.ADMIN_GROUP_ID
            )

    def search(self):
        assignment = self._get_assignment(self.request.GET.get('collectionId', None))
        params = self.request.GET.urlencode()
        database_url = self._get_database_url(assignment, '/search')
        response = requests.get(database_url, headers=self.headers, params=params)
        return HttpResponse(response.content, status=response.status_code, content_type='application/json')

    def create(self):
        body = self._get_request_body()
        assignment = self._get_assignment(body.get('collectionId', None))
        database_url = self._get_database_url(assignment, '/create')
        response = requests.post(database_url, data=json.dumps(body), headers=self.headers)
        return HttpResponse(response.content, status=response.status_code, content_type='application/json')

    def update(self, annotation_id):
        body = self._get_request_body()
        assignment = self._get_assignment(body.get('collectionId', None))
        database_url = self._get_database_url(assignment, '/update/%s' % annotation_id)
        response = requests.post(database_url, data=json.dumps(body), headers=self.headers)
        return HttpResponse(response.content, status=response.status_code, content_type='application/json')

    def delete(self, annotation_id):
        assignment = self._get_assignment(self.request.session['hx_collection_id'])
        database_url = self._get_database_url(assignment, '/delete/%s' % annotation_id)
        response = requests.delete(database_url, headers=self.headers)
        return HttpResponse(response)



class AppStoreBackend(StoreBackend):
    BACKEND_NAME = 'app'

    def __init__(self, request):
        super(AppStoreBackend, self).__init__(request)
        self.date_format = '%Y-%m-%dT%H:%M:%S %Z'
        self.max_limit = 1000

    def read(self, annotation_id):
        anno = get_object_or_404(Annotation, pk=annotation_id)
        result = self._serialize_annotation(anno)
        return HttpResponse(json.dumps(result), status=200, content_type='application/json')

    def search(self):
        user_id = self.request.session['hx_user_id']
        is_staff = self.request.session['is_staff']

        query_map = {
            'contextId':            'context_id',
            'collectionId':         'collection_id',
            'uri':                  'uri',
            'media':                'media',
            'userid':               'user_id',
            'username':             'user_name__icontains',
            'parentid':             'parent_id',
            'text':                 'text__icontains',
            'quote':                'quote__icontains',
            'tag':                  'tags__name__iexact',
            'dateCreatedOnOrAfter': 'created_at__gte',
            'dateCreatedOnOrBefore':'created_at__lte',
        }

        # Setup filters based on the search query
        filters = {}
        for param, filter_key in query_map.iteritems():
            if param not in self.request.GET or self.request.GET[param] == '':
                continue
            value = self.request.GET[param]
            if param.startswith('date'):
                filters[filter_key] = datetime.datetime.strptime(str(value), self.date_format)
            else:
                filters[filter_key] = value

        filter_conds = []
        if not is_staff:
            filter_conds.append(Q(is_private=False) | (Q(is_private=True) & Q(user_id=user_id)))

        # Create the queryset with the filters applied and get a count of the total size
        queryset = Annotation.objects.filter(*filter_conds, **filters)
        total = queryset.count()

        # Examine the user's requested limit and offset and check constraints
        limit = -1
        if 'limit' in self.request.GET and self.request.GET['limit'].isdigit():
            requested_limit = int(self.request.GET['limit'])
            limit = requested_limit if requested_limit <= self.max_limit else self.max_limit
        else:
            limit = self.max_limit

        offset = 0
        if 'offset' in self.request.GET and self.request.GET['offset'].isdigit():
            requested_offset = int(self.request.GET['offset'])
            offset = requested_offset if requested_offset < total else total

        # Slice the queryset and return the selected rows
        start, end = (offset, offset + limit if offset + limit < total else total)
        if limit < 0:
            queryset = queryset[start:]
        else:
            queryset = queryset[start:end]

        rows = [self._serialize_annotation(anno) for anno in queryset]
        result = {
            'total': total,
            'limit': limit,
            'offset': offset,
            'size': len(rows),
            'rows': rows,
        }

        return HttpResponse(json.dumps(result), status=200, content_type='application/json')

    def create(self):
        anno = self._create_or_update(anno=None)
        result = self._serialize_annotation(anno)
        return HttpResponse(json.dumps(result), status=200, content_type='application/json')

    def update(self, annotation_id):
        anno = self._create_or_update(anno=Annotation.objects.get(pk=annotation_id))
        result = self._serialize_annotation(anno)
        return HttpResponse(json.dumps(result), status=200, content_type='application/json')

    @transaction.atomic
    def delete(self, annotation_id):
        anno = Annotation.objects.get(pk=annotation_id)
        anno.is_deleted = True
        anno.save()

        if anno.parent_id:
            parent_anno = Annotation.objects.get(pk=anno.parent_id)
            parent_anno.total_comments = F('total_comments') - 1
            parent_anno.save()

        result = self._serialize_annotation(anno)
        return HttpResponse(json.dumps(result), status=200, content_type='application/json')

    @transaction.atomic
    def _create_or_update(self, anno=None):
        create = anno is None
        if create:
            anno = Annotation()

        body = self._get_request_body()
        anno.context_id = body['contextId']
        anno.collection_id = body['collectionId']
        anno.uri = body['uri']
        anno.media = body['media']
        anno.user_id = body['user']['id']
        anno.user_name = body['user']['name']
        anno.is_private = False if len(body.get('permissions', {}).get('read', [])) == 0 else True
        anno.text = body.get('text', '')
        anno.quote = body.get('quote', '')
        anno.json = json.dumps(body)

        if 'parent' in body and body['parent'] != '0':
            anno.parent_id = int(body['parent'])
        anno.save()

        if create and anno.parent_id:
            parent_anno = Annotation.objects.get(pk=int(body['parent']))
            parent_anno.total_comments = F('total_comments') + 1
            parent_anno.save()

        if not create:
            anno.tags.clear()
        for tag_name in body.get('tags', []):
            tag_object, created = AnnotationTags.objects.get_or_create(name=tag_name.strip())
            anno.tags.add(tag_object)

        return anno

    def _serialize_annotation(self, anno):
        data = json.loads(anno.json)
        data.update({
            "id": anno.pk,
            "deleted": anno.is_deleted,
            "created": anno.created_at.strftime(self.date_format),
            "updated": anno.updated_at.strftime(self.date_format),
        })
        if anno.parent_id is None:
            data['totalComments'] = anno.total_comments
        return data
