import html
import logging
import unittest
from unittest.mock import Mock, patch, call

import media_management_sdk
from image_store import backends

ImageStoreBackend = backends.ImageStoreBackend
ImageStoreBackendException = backends.ImageStoreBackendException
IMMImageStoreBackend = backends.IMMImageStoreBackend


class TestImageStoreBackend(unittest.TestCase):
    def test_backend_has_required_methods(self):
        backend = ImageStoreBackend()
        self.assertTrue(hasattr(backend, "store"))


class TestIMMImageStoreBackend(unittest.TestCase):
    def setUp(self):
        self.config = {
            "base_url": "http://media-management-api.localhost/api",
            "client_id": "my-client-id",
            "client_secret": "my-secret",
        }
        self.user_id = "a1b2c3d4"
        self.lti_params = {
            "tool_consumer_instance_guid": "7db438071375c02373713c12c73869ff2f470b68.harvard.instructure.com",
            "tool_consumer_instance_name": "Harvard University",
            "context_id": "9a8b2d3fa51ef413d19e480fb6c2ab091b7866a9",
            "context_label": "demo-foo",
            "context_title": "Foo&#39;s Demo Course",
            "lis_course_offering_sourcedid": "demo-foo",
            "lis_person_sourcedid": self.user_id,
            "custom_canvas_course_id": "11223344",
        }
        logging.disable(logging.CRITICAL)  # only show CRITICAL log events during test

    def tearDown(self):
        logging.disable(logging.NOTSET)  # restores logging

    def test_constructor(self):
        backend = IMMImageStoreBackend(self.config, self.lti_params)

        # check configuration
        self.assertEqual(self.config["base_url"], backend.client.base_url)
        self.assertEqual(self.config["client_id"], backend.client.client_id)
        self.assertEqual(self.config["client_secret"], backend.client.client_secret)

        # check lti params
        self.assertEqual(self.lti_params["lis_person_sourcedid"], backend.user_id)
        self.assertTrue(hasattr(backend, "course_attrs"))
        self.assertEqual(
            self.lti_params["tool_consumer_instance_guid"],
            backend.course_attrs["lti_tool_consumer_instance_guid"],
        )
        self.assertEqual(
            self.lti_params["context_id"], backend.course_attrs["lti_context_id"]
        )
        self.assertEqual(
            self.lti_params["context_label"], backend.course_attrs["lti_context_label"]
        )
        self.assertEqual(
            self.lti_params["context_title"], backend.course_attrs["lti_context_title"]
        )
        self.assertEqual(
            self.lti_params["lis_course_offering_sourcedid"],
            backend.course_attrs["sis_course_id"],
        )
        self.assertEqual(
            int(self.lti_params["custom_canvas_course_id"]),
            int(backend.course_attrs["canvas_course_id"]),
        )

    def test_constructor_missing_required_config(self):
        with self.assertRaises(ImageStoreBackendException):
            config = {}
            lti_params = self.lti_params
            backend = IMMImageStoreBackend(config, lti_params)

    def test_constructor_missing_required_lti_params(self):
        with self.assertRaises(ImageStoreBackendException):
            config = self.config
            lti_params = {"context_id": "foocontext123"}
            backend = IMMImageStoreBackend(config, lti_params)

    def test_store_called_with_no_uploaded_files(self):
        backend = IMMImageStoreBackend(self.config, self.lti_params)
        manifest_url = backend.store(uploaded_files=[], title=None)
        self.assertEqual(manifest_url, None)

    def test_store_raises_exception_if_auth_fails(self):
        mock_client = Mock(
            authenticate=Mock(side_effect=media_management_sdk.exceptions.ApiError)
        )
        with self.assertRaises(ImageStoreBackendException):
            backend = IMMImageStoreBackend(self.config, self.lti_params)
            backend.client = mock_client
            backend.store(uploaded_files=[Mock(name="testfile.jpg")], title=None)

    def test_store_returns_manifest_url(self):
        course_response = {"id": 999}
        images_response = [{"id": 111}]
        collection_response = {
            "id": 222,
            "iiif_manifest": {"url": "http://localhost:8000/api/iiif/manifest/222"},
        }
        title = "Untitled Test"

        mock_file = Mock(name="testfile.jpg", file=None, content_type="image/jpeg",)
        mock_api = Mock(
            upload_images=Mock(return_value=images_response),
            create_collection=Mock(return_value=collection_response),
            get_collection=Mock(return_value=collection_response),
        )
        mock_client = Mock(
            api=mock_api,
            find_or_create_course=Mock(return_value=course_response),
            authenticate=Mock(),
        )

        backend = IMMImageStoreBackend(self.config, self.lti_params)
        backend.client = mock_client
        manifest_url = backend.store(uploaded_files=[mock_file], title=title)

        self.assertEqual(manifest_url, collection_response["iiif_manifest"]["url"])

        mock_client.authenticate.assert_has_calls([
            call(user_id=self.user_id),
            call(user_id=self.user_id, course_id=course_response["id"], course_permission="write")
        ])
        mock_client.find_or_create_course.assert_called_with(
            lti_context_id=self.lti_params["context_id"],
            lti_tool_consumer_instance_guid=self.lti_params[
                "tool_consumer_instance_guid"
            ],
            lti_context_title=self.lti_params["context_title"],
            lti_context_label=self.lti_params["context_label"],
            title=html.unescape(self.lti_params["context_title"]),
            canvas_course_id=int(self.lti_params["custom_canvas_course_id"]),
            sis_course_id=self.lti_params["lis_course_offering_sourcedid"],
        )
        mock_client.api.upload_images.assert_called_with(
            course_id=course_response["id"],
            upload_files=[(mock_file.name, mock_file.file, mock_file.content_type)],
            title=title,
        )
        mock_client.api.create_collection.assert_called_with(
            course_id=course_response["id"], title=title, description="",
        )
        mock_client.api.update_collection.assert_called_with(
            collection_id=collection_response["id"],
            course_id=course_response["id"],
            course_image_ids=[image["id"] for image in images_response],
            title=title,
        )
        mock_client.api.get_collection.assert_called_with(
            collection_id=collection_response["id"],
        )
