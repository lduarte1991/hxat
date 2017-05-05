from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F, Q
from ims_lti_py.tool_provider import DjangoToolProvider
from hx_lti_assignment.models import Assignment
from hx_lti_initializer.utils import (debug_printer, retrieve_token)

from utils import (update_read_permissions, ADMIN_GROUP_ID)
from models import Annotation, AnnotationTags, UserStats

import json
import requests
import datetime

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
    def __init__(self, request):
        self.request = request
        self.gather_statistics = ANNOTATION_STORE_SETTINGS.get('gather_statistics', False)
        self.backend_type = ANNOTATION_STORE_SETTINGS.get('backend', 'catch')
        self.backend = self._get_backend_instance(request, self.backend_type)

    def _get_backend_types(self):
        return {
            'app': AppStoreBackend,
            'catch': CatchStoreBackend,
        }

    def _get_backend_instance(self, request, backend_type):
        backend_types = self._get_backend_types()
        if backend_type not in backend_types:
            raise Exception('Invalid backend type: %s. Must be one of: %s' % (', '.join(backend_types.keys())))
        return backend_types[backend_type](request)

    def root(self):
        return self.backend.root()

    def index(self):
        raise NotImplementedError

    def search(self):
        self._verify_course(self.request.GET.get('contextId', None))
        if hasattr(self.backend, 'before_search'):
            self.backend.before_search()
        return self.backend.search()

    def create(self):
        body = json.loads(self.request.body)
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

    def update(self, annotation_id):
        body = json.loads(self.request.body)
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

    def _lti_grade_passback(self, is_graded=False, status_code=None, result_score=1):
        debug_printer("LTI Grade Passback: is_graded=%s status_code=%s" % (is_graded, status_code))
        if not (is_graded and status_code == 200):
            return
        try:
            consumer_key = settings.CONSUMER_KEY
            secret = settings.LTI_SECRET
            params = self.request.session['lti_params']
            tool_provider = DjangoToolProvider(consumer_key, secret, params)
            outcome = tool_provider.post_replace_result(result_score)
            debug_printer(u"LTI grade request was {successful}. Description is {description}".format(
                successful="successful" if outcome.is_success() else "unsuccessful", description=outcome.description
            ))
        except Exception as e:
            debug_printer("Error submitting grade outcome after annotation created: %s" % str(e))

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
    def __init__(self, request):
        self.request = request

    def _get_assignment(self, assignment_id):
        debug_printer("assignment_id: %s" % assignment_id)
        return get_object_or_404(Assignment, assignment_id=assignment_id)

    def _get_request_body(self):
        body = json.loads(self.request.body)
        if settings.ORGANIZATION == "ATG":
            update_read_permissions(body)
        return body

class CatchStoreBackend(StoreBackend):
    def __init__(self, request):
        super(CatchStoreBackend, self).__init__(request)
        self.headers = {
            'x-annotator-auth-token': request.META.get('HTTP_X_ANNOTATOR_AUTH_TOKEN', '!!MISSING!!'),
            'content-type': 'application/json',
        }

    def _get_database_url(self, assignment, path='/'):
        base_url = str(assignment.annotation_database_url).strip()
        return '{base_url}{path}'.format(base_url=base_url, path=path)

    def root(self):
        data = dict(name="CatchStore")
        return HttpResponse(json.dumps(data), content_type='application/json')

    def before_search(self):
        # Override the auth token for ATG when the user is a course administrator,
        # so they can query against private annotations that have granted permission to the admin group.
        # Note: this only works if private annotations included the "__admin__" group ID in the "read" permissions
        # for the annotation.
        is_staff = self.request.session['is_staff']
        if settings.ORGANIZATION == "ATG" and is_staff:
            assignment = self._get_assignment(self.request.GET.get('collectionId', None))
            self.headers['x-annotator-auth-token'] = retrieve_token(
                ADMIN_GROUP_ID,
                assignment.annotation_database_apikey,
                assignment.annotation_database_secret_token
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
    def __init__(self, request):
        super(AppStoreBackend, self).__init__(request)
        self.date_format = '%Y-%m-%dT%H:%M:%S %Z'

    def root(self):
        data = dict(name="AppStore")
        return HttpResponse(json.dumps(data), content_type='application/json')

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

        limit = -1
        if 'limit' in self.request.GET and self.request.GET['limit'].isdigit():
            limit = int(self.request.GET['limit'])

        offset = 0
        if 'offset' in self.request.GET and self.request.GET['offset'].isdigit():
            offset = int(self.request.GET['offset'])

        queryset = Annotation.objects.filter(*filter_conds, **filters)
        total = queryset.count()
        if limit < 0:
            queryset = queryset[offset:]
        else:
            queryset = queryset[offset:limit]

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