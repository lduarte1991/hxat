import unittest
import json
import html
from unittest.mock import Mock, patch

from . import backends 

ImageStoreBackend = backends.ImageStoreBackend
IMMImageStoreBackend = backends.IMMImageStoreBackend

class TestImageStoreBackend(unittest.TestCase):
    def test_backend_has_required_methods(self):
        backend = ImageStoreBackend()
        self.assertTrue(hasattr(backend, 'store'))


class TestIMMImageStoreBackend(unittest.TestCase):
    def setUp(self):
        self.config = {
            'base_url': 'http://media-management-api.localhost/api', 
            'client_id': 'my-client-id', 
            'client_secret': 'my-secret', 
        }
        self.user_id = 'aaaabbbb'
        self.lti_params = {
            'tool_consumer_instance_guid': '7db438071375c02373713c12c73869ff2f470b68.harvard.instructure.com', 
            'tool_consumer_instance_name': 'Harvard University',
            'context_id': '9a8b2d3fa51ef413d19e480fb6c2ab091b7866a9',
            'context_label': 'demo-foo',
            'context_title': 'Foo&#39;s Demo Course',
            'lis_course_offering_sourcedid': 'demo-foo', 
            'lis_person_sourcedid': self.user_id, 
            'custom_canvas_course_id': '11223344',
        }

    def test_constructor(self):
        backend = IMMImageStoreBackend(self.config, self.lti_params)

        # check configuration
        self.assertEqual(self.config['base_url'], backend.base_url)
        self.assertEqual(self.config['client_id'], backend.client_id)
        self.assertEqual(self.config['client_secret'], backend.client_secret)

        # check lti params
        self.assertEqual(self.lti_params['lis_person_sourcedid'], backend.user_id)
        self.assertTrue(hasattr(backend, 'course_attrs'))
        self.assertEqual(self.lti_params['tool_consumer_instance_guid'], backend.course_attrs['lti_tool_consumer_instance_guid'])
        self.assertEqual(self.lti_params['tool_consumer_instance_name'], backend.course_attrs['lti_tool_consumer_instance_name'])
        self.assertEqual(self.lti_params['context_id'], backend.course_attrs['lti_context_id'])
        self.assertEqual(self.lti_params['context_label'], backend.course_attrs['lti_context_label'])
        self.assertEqual(self.lti_params['context_title'], backend.course_attrs['lti_context_title'])
        self.assertEqual(self.lti_params['lis_course_offering_sourcedid'], backend.course_attrs['sis_course_id'])
        self.assertEqual(self.lti_params['custom_canvas_course_id'], backend.course_attrs['canvas_course_id'])

        # check initial headers
        self.assertTrue(hasattr(backend, 'headers'))
        expected_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.assertEqual(expected_headers, backend.headers)

    @patch('image_store.backends.requests.post')
    def test_authenticate(self, mock_post):
        request_url = "%s/auth/obtain-token" % self.config['base_url']
        request_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        request_data = {
            "client_id": self.config['client_id'],
            "client_secret": self.config['client_secret'],
            "user_id": self.user_id,
        }
        response_data = {
            "course_id": None,
            "user_id": self.user_id,
            "access_token": 'ABC-123423asdfascxwQRW-AAAA',
            "expires": "2030-01-03 15:35:49",
            "course_permission": None
        }
        mock_post.return_value = Mock(ok=True, status_code=200)
        mock_post.return_value.json.return_value = response_data
        
        backend = IMMImageStoreBackend(self.config, self.lti_params)
        actual_access_token = backend._authenticate()

        mock_post.assert_called_with(request_url, headers=request_headers, data=json.dumps(request_data))
        self.assertEqual(response_data["access_token"], actual_access_token)
        
    @patch('image_store.backends.requests.post')
    def test_create_course(self, mock_post):
        request_url = "%s/courses" % self.config['base_url']
        request_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Token Fake123",
        }
        request_data = {
            "lti_context_id": self.lti_params['context_id'],
            "lti_tool_consumer_instance_guid": self.lti_params['tool_consumer_instance_guid'],
            "lti_tool_consumer_instance_name": self.lti_params['tool_consumer_instance_name'],
            "lti_context_title": self.lti_params['context_title'],
            "lti_context_label": self.lti_params['context_label'],
            "title": html.unescape(self.lti_params['context_title']),
            "sis_course_id": self.lti_params['lis_course_offering_sourcedid'],
            "canvas_course_id": self.lti_params['custom_canvas_course_id'],
        }
        response_data = {
            "id": 101,
            "created": "2020-01-16T20:34:42.887005Z",
            "updated": "2020-01-16T20:34:42.887032Z",
        }
        response_data.update(request_data)

        mock_post.return_value = Mock(ok=True, status_code=201)
        mock_post.return_value.json.return_value = response_data

        backend = IMMImageStoreBackend(self.config, self.lti_params)
        backend.headers = request_headers
        actual_data = backend._create_course()

        mock_post.assert_called_with(request_url, headers=request_headers, data=json.dumps(request_data))
        self.assertEqual(response_data, actual_data)

    @patch('image_store.backends.requests.post')
    def test_create_collection(self, mock_post):
        course_id = 123
        title = "Image Annotation"
        request_url = "%s/courses/%s/collections" % (self.config['base_url'], course_id)
        request_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Token Fake123",
        }
        request_data = {
            "title": title,
            "description": "Image Annotation"
        }
        response_data = {
            "id": 901,
            "created": "2020-01-16T20:34:42.887005Z",
            "updated": "2020-01-16T20:34:42.887005Z",
            "title": request_data['title'],
            "description": request_data['description'],
            "course_id": course_id,
            "course_image_ids": [],
            "iiif_manifest": {
                "source": "images",
                "canvas_id": "",
                "url": "%s/iiif/manifest/641" % self.config['base_url']
            },
        }

        mock_post.return_value = Mock(ok=True, status_code=201)
        mock_post.return_value.json.return_value = response_data

        backend = IMMImageStoreBackend(self.config, self.lti_params)
        backend.headers = request_headers
        actual_data = backend._create_collection(course_id, title)

        mock_post.assert_called_with(request_url, headers=request_headers, data=json.dumps(request_data))
        self.assertEqual(response_data, actual_data)

    @patch('image_store.backends.requests.get')
    def test_get_collection(self, mock_get):
        collection_id = 555
        request_url = "%s/collections/%s" % (self.config['base_url'], collection_id)
        request_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Token Fake123",
        }
        response_data = {
            "id": collection_id,
            "created": "2020-01-16T20:34:42.887005Z",
            "updated": "2020-01-16T20:34:42.887005Z",
            "title": "Test Collection",
            "description": "",
            "course_id": 123,
            "course_image_ids": [],
            "iiif_manifest": {
                "source": "images",
                "canvas_id": "",
                "url": "%s/iiif/manifest/%s" % (self.config['base_url'], collection_id)
            },
        }

        mock_get.return_value = Mock(ok=True, status_code=200)
        mock_get.return_value.json.return_value = response_data

        backend = IMMImageStoreBackend(self.config, self.lti_params)
        backend.headers = request_headers
        actual_data = backend._get_collection(collection_id)

        mock_get.assert_called_with(request_url, headers=request_headers)
        self.assertEqual(response_data, actual_data)

    @patch('image_store.backends.requests.post')
    def test_add_to_collection(self, mock_post):
        collection_id = 555
        image_ids = [100,101,102]
        request_url = "%s/collections/%s/images" % (self.config['base_url'], collection_id)
        request_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Token Fake123",
        }
        request_data = [dict(course_image_id=image_id) for image_id in image_ids]
        response_data = [{
            "id": idx,
            "collection_id": collection_id,
            "course_image_id": image_id,
            } for idx, image_id in enumerate(image_ids)]
        mock_post.return_value = Mock(ok=True, status_code=201)
        mock_post.return_value.json.return_value = response_data

        backend = IMMImageStoreBackend(self.config, self.lti_params)
        backend.headers = request_headers
        actual_data = backend._add_to_collection(collection_id, image_ids)

        mock_post.assert_called_with(request_url, headers=request_headers, data=json.dumps(request_data))
        self.assertEqual(response_data, actual_data)