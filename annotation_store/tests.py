from django.test.client import RequestFactory
from django.test import TestCase
from django.http import HttpResponse
import json

from store import StoreBackend, AnnotationStore

DEFAULT_SESSION_DATA = {
    'hx_context_id': '2a8b2d3fa55b7866a9',
    'hx_collection_id': '123',
    'hx_object_id': '7',
    'hx_user_id': 'cfc663eb08c91046',
    'is_staff': False,
    'is_graded': False,
}


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

def make_request(method='get', **kwargs):
    session = kwargs.pop('session', DEFAULT_SESSION_DATA)
    params = kwargs.pop('params', {})
    body = json.dumps(kwargs.pop('body', {}))
    url = kwargs.pop('url', '/foo')
    request_factory = RequestFactory()
    if method == 'get':
        request = request_factory.get(url, data=params)
    elif method == 'post':
        request = request_factory.post(url, data=body)
    elif method == 'put':
        request = request_factory.put(url, data=body)
    elif method == 'delete':
        request = request_factory.delete(url, data=body)
    else:
        raise Exception("invalid method: %s" % method)
    request.session = session
    return request

class AnnotationStoreTest(TestCase):
    def setUp(self):
        AnnotationStore.update_settings({})
        self.default_session = dict(DEFAULT_SESSION_DATA)
        self.request_factory = RequestFactory()

    def _create_request_GET(self, **kwargs):
        session = kwargs.pop('session', self.default_session)
        return make_request(method='get', session=session, **kwargs)

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
        session = self.default_session
        request = self._create_request_GET(session=session, params={
            'contextId': session['hx_context_id'],
        })
        backend_instance = DummyStoreBackend(request)
        store = AnnotationStore(request, backend_instance=backend_instance)
        response = store.search()
        self.assertIsInstance(response, HttpResponse, 'Search should return an HttpResponse')

class StoreBackendTest(TestCase):
    def setUp(self):
        self.default_session = dict(DEFAULT_SESSION_DATA)
        self.request_factory = RequestFactory()
