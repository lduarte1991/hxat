import copy
import json
import logging
import mock

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory

from annotation_store.store import StoreBackend, AnnotationStore

logger = logging.getLogger(__name__)

launch_params = {
    'context_id': '2a8b2d3fa55b7866a9',
    'resource_link_id': '2a8b2d3fa51ea413d19e480fb6c2eb085b7866a9',
    'consumer_key': '123key',
    'consumer_secret': 'secret',
    'lis_result_sourcedid': '10357-39-176095-241388-bb66bc4607aab98c2b5ad0f946939611bc77a80b',
    'lis_outcome_service_url': 'https://canvas.harvard.edu/api/lti/v1/tools/10357/grade_passback',
    'user_id': 'cfc663eb08c91046',
}

TEST_SESSION_NOT_STAFF = {
    'hx_context_id': launch_params.get('context_id', 'cfc663eb08c91046'),
    'hx_user_id': launch_params.get('user_id', 'cfc663eb08c91046'),
    'hx_collection_id': '123',
    'hx_object_id': '7',
    'is_staff': False,
    'launch_params': launch_params,
}

TEST_SESSION_IS_STAFF = dict(TEST_SESSION_NOT_STAFF)
TEST_SESSION_IS_STAFF['is_staff'] = True
del TEST_SESSION_IS_STAFF['launch_params']


def object_params_from_session(session):
    return {
        'contextId': session['hx_context_id'],
        'collectionId': session['hx_collection_id'],
        'uri': session['hx_object_id'],
        'user': {"id": session['hx_user_id']},
        'media': 'text',
    }


def search_params_from_session(session):
    return {'contextId': session['hx_context_id']}


def create_request(method='get', **kwargs):
    resource_link_id = kwargs.pop(
        'resource_link_id', '2a8b2d3fa51ea413d19e480fb6c2eb085b7866a9'
    )
    session = {'LTI_LAUNCH': {}}
    session['LTI_LAUNCH'][resource_link_id] = kwargs.pop('session')
    params = kwargs.pop('params', {})
    body = kwargs.pop('data', {})
    url = kwargs.pop('url', '/foo')
    request_factory = RequestFactory()
    if method == 'get':
        request = request_factory.get(url, data=params, content_type='application/json')
    elif method == 'post':
        request = request_factory.post(
            url, data=json.dumps(body), content_type='application/json'
        )
    elif method == 'put':
        request = request_factory.put(
            url, data=json.dumps(body), content_type='application/json'
        )
    elif method == 'delete':
        request = request_factory.delete(
            url, data=json.dumps(body), content_type='application/json'
        )
    else:
        raise Exception('invalid method: %s' % method)
    request.session = session
    setattr(request, 'LTI', session.get('LTI_LAUNCH', {}).get(resource_link_id))
    return request


class StoreBackendTest(TestCase):
    def setUp(self):
        self.not_staff_session = dict(TEST_SESSION_NOT_STAFF)
        self.request_factory = RequestFactory()

    def test_modify_permissions(self):
        session = self.not_staff_session
        anno = object_params_from_session(session)

        tests = [
            {
                'parent': '0',
                'permissions': {'read': [], 'admin': [], 'update': [], 'delete': []},
            },
            {
                'parent': '0',
                'permissions': {
                    'read': [anno['user']['id']],
                    'admin': [anno['user']['id']],
                    'update': [anno['user']['id']],
                    'delete': [anno['user']['id']],
                },
            },
            {
                'parent': '12345',
                'permissions': {
                    'read': [anno['user']['id']],
                    'admin': [anno['user']['id']],
                    'update': [anno['user']['id']],
                    'delete': [anno['user']['id']],
                },
            },
        ]
        request = create_request(method='post', session=session)
        backend = StoreBackend(request)
        backend.ADMIN_GROUP_ENABLED = True
        for test in tests:
            anno_test = copy.deepcopy(anno)
            anno_test.update(
                {
                    'permissions': test['permissions'],
                    'parent': test['parent'],
                }
            )
            before_perms = copy.deepcopy(anno_test['permissions'])
            result = backend._modify_permissions(anno_test)
            if len(before_perms['read']) == 0:
                self.assertEqual(0, len(result['permissions']['read']))
            else:
                if test['parent'] == '0':
                    self.assertTrue(
                        anno_test['user']['id'] in result['permissions']['read']
                    )
                    self.assertTrue(
                        backend.ADMIN_GROUP_ID in result['permissions']['read']
                    )
                else:
                    self.assertEqual(0, len(result['permissions']['read']))
