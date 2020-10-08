import html
import logging

from media_management_sdk import Client
from media_management_sdk.exceptions import ApiError

logger = logging.getLogger(__name__)


def get_backend_class(class_name):
    ''' Returns backend class. '''
    if class_name in globals():
        return globals()[class_name]
    return None


class ImageStoreBackendException(Exception):
    pass


class ImageStoreBackend(object):
    '''
    Image storage backend.
    '''
    def __init__(self, config=None, lti_params=None):
        ''' Initialize backend with config and LTI parameters as required. '''
        pass

    def store(self, uploaded_files, title):
        ''' Returns URL to a IIIF manifest containing the images. '''
        pass


class IMMImageStoreBackend(ImageStoreBackend):
    '''
    Collaborates with the Image Media Manager (IMM) service to store images
    and generate IIIF manifests.

    See also: https://github.com/harvard-atg/media_management_api

    Notes:
    - IMM requires client credentials (client key and secret) to authenticate and obtain a
      temporary access token for the logged-in user.
    - Requires LTI context_id and tool_consumer_instance_guid to identify the course library.
    - Additional LTI attributes are provided when creating a new course library.
    - A manifest can be obtained for a collection with images.
    '''
    def __init__(self, config=None, lti_params=None):
        super().__init__(config, lti_params)

        # client for API
        try:
            self.client = Client(
                client_id=config['client_id'],
                client_secret=config['client_secret'],
                base_url=config['base_url'],
            )
        except KeyError as e:
            raise ImageStoreBackendException("Misconfigured: %s" % str(e))

        # course-specific parameters
        try:
            # required
            self.user_id = lti_params['lis_person_sourcedid']
            self.course_attrs = {
                "lti_context_id": lti_params['context_id'],
                "lti_tool_consumer_instance_guid": lti_params['tool_consumer_instance_guid'],
                "lti_context_title": lti_params['context_title'],
                "lti_context_label": lti_params['context_label'],
                "title": html.unescape(lti_params['context_title']),
            }
            # optional (if provided)
            if lti_params.get('lis_course_offering_sourcedid'):
                self.course_attrs["sis_course_id"] = lti_params['lis_course_offering_sourcedid']
            if lti_params.get('custom_canvas_course_id'):
                self.course_attrs['canvas_course_id'] = int(lti_params['custom_canvas_course_id'])
        except (KeyError, ValueError) as e:
            raise ImageStoreBackendException("Missing or invalid LTI params: %s" % str(e))

    def store(self, uploaded_files, title):
        ''' Returns URL to a IIIF manifest containing the images. '''
        if not uploaded_files or len(uploaded_files) == 0:
            return None

        manifest_url = None
        try:
            # authenticate and ensure course space exists
            self.client.authenticate(user_id=self.user_id)
            course = self.client.find_or_create_course(**self.course_attrs)
            logger.info("User %s loaded course: %s" % (self.user_id, course))

            # upload image to the course space
            course_images = self.client.api.upload_images(
                course_id=course['id'],
                upload_files=[(f.name, f.file, f.content_type) for f in uploaded_files],
                title=title,
            )
            logger.info("User %s uploaded images: %s" % (self.user_id, course_images))

            # create a collection and add images to it
            collection = self.client.api.create_collection(
                course_id=course['id'],
                title=title,
                description='',
            )
            self.client.api.update_collection(
                collection_id=collection['id'],
                course_id=course['id'],
                course_image_ids=[image['id'] for image in course_images],
                title=title,
            )

            # get IIIF manifest URL for collection
            collection = self.client.api.get_collection(collection_id=collection['id'])
            manifest_url = collection.get('iiif_manifest', {}).get('url')
            logger.info("User %s obtained manifest for collection: %s" % (self.user_id, collection))

        except ApiError as e:
            logger.exception("Failed to upload and store image: %s" % str(e))
            raise ImageStoreBackendException("Failed to upload and store image")
        except Exception as e:
            logger.exception("Image store exception: %s" % str(e))
            raise e

        return manifest_url
