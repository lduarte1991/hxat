import copy
import json
import logging
import mock

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory

from store import StoreBackend, AnnotationStore

logger = logging.getLogger(__name__)

TEST_SESSION_NOT_STAFF = {
    'hx_context_id': '2a8b2d3fa55b7866a9',
    'hx_collection_id': '123',
    'hx_object_id': '7',
    'hx_user_id': 'cfc663eb08c91046',
    'is_staff': False,
    'is_graded': False,
}
TEST_SESSION_IS_STAFF = dict(TEST_SESSION_NOT_STAFF)
TEST_SESSION_IS_STAFF['is_staff'] = True

def object_params_from_session(session):
    return {
        'contextId': session['hx_context_id'],
        'collectionId': session['hx_collection_id'],
        'uri': session['hx_object_id'],
        'user': {"id": session['hx_user_id']},
    }

def search_params_from_session(session):
    return {'contextId': session['hx_context_id']}

def create_request(method='get', **kwargs):
    session = kwargs.pop('session', TEST_SESSION_NOT_STAFF)
    params = kwargs.pop('params', {})
    body = kwargs.pop('data', {})
    url = kwargs.pop('url', '/foo')
    request_factory = RequestFactory()
    if method == 'get':
        request = request_factory.get(url, data=params, content_type='application/json')
    elif method == 'post':
        request = request_factory.post(url, data=json.dumps(body), content_type='application/json')
    elif method == 'put':
        request = request_factory.put(url, data=json.dumps(body), content_type='application/json')
    elif method == 'delete':
        request = request_factory.delete(url, data=json.dumps(body), content_type='application/json')
    else:
        raise Exception("invalid method: %s" % method)
    request.session = session
    return request


class DummyStoreBackend(StoreBackend):
    BACKEND_NAME = 'dummy'

    def _action(self, *args, **kwargs):
        return HttpResponse()

    search = _action
    root = _action
    create = _action
    read = _action
    update = _action
    delete = _action


class AnnotationStoreTest(TestCase):
    def setUp(self):
        AnnotationStore.update_settings({})
        self.not_staff_session = dict(TEST_SESSION_NOT_STAFF)
        self.staff_session = dict(TEST_SESSION_IS_STAFF)
        self.request_factory = RequestFactory()

    def test_from_settings(self):
        request = self.request_factory.get('/foo')
        test_settings = [
            {'backend': 'catch', 'gather_statistics': True},
            {'backend': 'app',   'gather_statistics': False},
        ]
        for settings in test_settings:
            store = AnnotationStore.update_settings(settings).from_settings(request=request)
            self.assertEqual(settings['gather_statistics'], store.gather_statistics)
            self.assertEqual(settings['backend'], store.backend.BACKEND_NAME)

    def test_from_settings_defaults(self):
        request = self.request_factory.get('/foo')
        store = AnnotationStore.update_settings({}).from_settings(request=request)
        self.assertEqual(False, store.gather_statistics)
        self.assertEqual('catch', store.backend.BACKEND_NAME)

    def test_from_settings_invalid(self):
        request = self.request_factory.get('/foo')
        AnnotationStore.update_settings({'backend': 'invalid_backend_name'})
        with self.assertRaises(AssertionError):
            store = AnnotationStore.from_settings(request=request)

    def test_search(self):
        session = self.not_staff_session
        params = search_params_from_session(session)
        request = create_request(method="get", session=session, params=params)
        store = AnnotationStore(request, backend_instance=DummyStoreBackend(request))
        response = store.search()
        self.assertIsInstance(response, HttpResponse, 'Search should return an HttpResponse')

    def test_create(self):
        session = self.not_staff_session
        data = object_params_from_session(session)
        request = create_request(method="post", session=session, data=data)
        store = AnnotationStore(request, backend_instance=DummyStoreBackend(request))
        response = store.create()
        self.assertIsInstance(response, HttpResponse, 'Create should return an HttpResponse')

    def test_permission_denied(self):
        def invalidator(key, corruptor='_INVALID_'):
            def invalidate(data):
                d = copy.deepcopy(data)
                if key == 'user.id':
                    d['user']['id'] = d['user']['id'] + corruptor
                else:
                    d[key] = d[key] + corruptor
                return d
            return invalidate

        tests = [
            {"method": "get",    "action": "search", "invalidate": invalidator('contextId')},
            {"method": "post",   "action": "create", "invalidate": invalidator('user.id')},
            {"method": "post",   "action": "create", "invalidate": invalidator('contextId')},
            {"method": "post",   "action": "create", "invalidate": invalidator('collectionId')},
            {"method": "post",   "action": "create", "invalidate": invalidator('uri')},
            {"method": "put",    "action": "update", "annotation_id": 123, "invalidate": invalidator('user.id')},
            {"method": "put",    "action": "update", "annotation_id": 123, "invalidate": invalidator('contextId')},
            {"method": "put",    "action": "update", "annotation_id": 123, "invalidate": invalidator('collectionId')},
            {"method": "put",    "action": "update", "annotation_id": 123, "invalidate": invalidator('uri')},
            {"method": "delete", "action": "delete", "annotation_id": 123, "invalidate": invalidator('user.id')},
            {"method": "delete", "action": "delete", "annotation_id": 123, "invalidate": invalidator('contextId')},
            {"method": "delete", "action": "delete", "annotation_id": 123, "invalidate": invalidator('collectionId')},
            {"method": "delete", "action": "delete", "annotation_id": 123, "invalidate": invalidator('uri')},
        ]

        for test in tests:
            session = self.not_staff_session
            data = object_params_from_session(session)
            invalid_data = test['invalidate'](data)
            request = create_request(method=test['method'], session=session, data=invalid_data)
            store = AnnotationStore(request, backend_instance=DummyStoreBackend(request))
            with self.assertRaises(PermissionDenied):
                action = getattr(store, test['action'])
                response = action() if test.get('annotation_id', None) is None else action(test['annotation_id'])

    def test_lti_passback_triggered_after_create(self):
        session = self.not_staff_session
        data = object_params_from_session(session)
        request = create_request(method="post", session=session, data=data)
        store = AnnotationStore(request, backend_instance=DummyStoreBackend(request))
        store._lti_grade_passback = mock.Mock(return_value=True)
        response = store.create()
        store._lti_grade_passback.assert_called()

class StoreBackendTest(TestCase):
    def setUp(self):
        self.not_staff_session = dict(TEST_SESSION_NOT_STAFF)
        self.request_factory = RequestFactory()

    def test_modify_permissions(self):
        session = self.not_staff_session
        anno = object_params_from_session(session)

        tests = [
            {
                "parent": "0",
                "permissions": {
                    "read": [],
                    "admin": [],
                    "update": [],
                    "delete": []
                },
            },
            {
                "parent": "0",
                "permissions": {
                    "read": [anno['user']['id']],
                    "admin": [anno['user']['id']],
                    "update": [anno['user']['id']],
                    "delete": [anno['user']['id']],
                }
            },
            {
                "parent": "12345",
                "permissions": {
                    "read": [anno['user']['id']],
                    "admin": [anno['user']['id']],
                    "update": [anno['user']['id']],
                    "delete": [anno['user']['id']],
                }
            },
        ]
        request = create_request(method="post", session=session)
        backend = StoreBackend(request)
        backend.ADMIN_GROUP_ENABLED = True
        for test in tests:
            anno_test = copy.deepcopy(anno)
            anno_test.update({
                "permissions": test["permissions"],
                "parent": test["parent"],
            })
            before_perms = copy.deepcopy(anno_test['permissions'])
            result = backend._modify_permissions(anno_test)
            if len(before_perms['read']) == 0:
                self.assertEqual(0, len(result['permissions']['read']))
            else:
                if test['parent'] == '0':
                    self.assertTrue(anno_test['user']['id'] in result['permissions']['read'])
                    self.assertTrue(backend.ADMIN_GROUP_ID in result['permissions']['read'])
                else:
                    self.assertEqual(0, len(result['permissions']['read']))


