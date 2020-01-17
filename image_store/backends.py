import requests
import json
import html
import logging

logger = logging.getLogger(__name__)

class ImageStoreBackendException(Exception):
    pass

class ImageStoreBackend:
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
      temporary access token for subsequent requests.
    - Requires LTI context_id and tool_consumer_instance_guid to identify the course library.
    - Additional LTI context/course attributes are provided when creating a new course library.
    - A collection is associated with a manifest, so as soon as a collection is created, a manifest
      URL can be obtained and it will be generated on the fly.
    '''
    def __init__(self, config=None, lti_params=None):
        super().__init__(config, lti_params)

        # configuration for API
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.base_url = config['base_url']
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # course-specific parameters
        self.user_id = lti_params['lis_person_sourcedid']
        self.course_attrs = {
            "lti_context_id": lti_params['context_id'],
            "lti_tool_consumer_instance_guid": lti_params['tool_consumer_instance_guid'],
            "lti_tool_consumer_instance_name": lti_params['tool_consumer_instance_name'],
            "lti_context_title": lti_params['context_title'],
            "lti_context_label": lti_params['context_label'],
            "title": html.unescape(lti_params['context_title']),
            "sis_course_id": lti_params['lis_course_offering_sourcedid'],
            "canvas_course_id": lti_params['custom_canvas_course_id'],
        }

    def store(self, uploaded_files, title):
        ''' Returns URL to a IIIF manifest containing the images. '''
        manifest_url = None
        try:
            # authenticate 
            access_token = self._authenticate()
            self.headers['Authorization'] = 'Token {access_token}'.format(access_token=access_token)

            # create course space if not exists for storing images
            course = self._find_or_create_course()

            # upload image to the course space
            course_images = self._upload_images(course['id'], uploaded_files)
            course_image_ids = [image['id'] for image in course_images]
            
            # create a collection and add images to it
            collection = self._create_collection(course['id'], title)
            self._add_to_collection(collection['id'], course_image_ids)
            
            # get IIIF manifest URL for collection
            collection = self._get_collection(collection['id'])
            manifest_url = collection.get('iiif_manifest', {}).get('url')

        except ImageStoreBackendException as e:
            logger.exception("Image store backend error: %s" % str(e))
            raise e

        return manifest_url

    def _authenticate(self):
        ''' 
        Authenticates with API using client credentials (key/secret).
        Obtains temporary access token for subsequent API requests.
        '''
        url = "%s/auth/obtain-token" % self.base_url
        post_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "user_id": self.user_id,
        }
        r = requests.post(url, headers=self.headers, data=json.dumps(post_data))
        logger.debug("API POST {url} data:{post_data} status:{status_code} text:{text}".format(url=url, post_data=post_data, status_code=r.status_code, text=r.text))
        
        access_token = None
        if r.status_code == 200:
            data = r.json()
            access_token = data.get('access_token', None)
            if not access_token:
                raise ImageStoreBackendException("Authenticated successfully, but access token absent from response")
        else: 
            raise ImageStoreBackendException("Authentication failed: {status_code}".format(status_code=r.status_code))
        return access_token
    
    def _find_or_create_course(self):
        '''
        Find associated course space for images using Canvas/LTI identifiers.
        If no course space exists, create one.
        '''
        url = "%s/courses" % self.base_url
        search_params = {
            "lti_context_id": self.course_attrs["lti_context_id"],
            "lti_tool_consumer_instance_guid": self.course_attrs["lti_tool_consumer_instance_guid"]
        }
        r = requests.get(url, headers=self.headers, params=search_params)
        logger.debug("API GET {url} params:{params} status:{status_code} text:{text}".format(url=url, params=search_params, status_code=r.status_code, text=r.text))

        course = None
        if r.status_code == 200:
            courses = r.json()
            if len(courses) == 0:
                course = self._create_course()
            else:
                course = courses[0]
        elif r.status_code == 404:
            course = self._create_course()
        else:
            raise ImageStoreBackendException("Find course error: {status_code}".format(status_code=r.status_code))
        return course

    def _create_course(self):
        '''
        Create a new course space for images.
        '''
        url = "%s/courses" % self.base_url
        post_data = self.course_attrs
        r = requests.post(url, headers=self.headers, data=json.dumps(post_data))
        logger.debug("API POST {url} data:{data} status:{status_code} text:{text}".format(url=url, data=post_data, status_code=r.status_code, text=r.text))

        if r.status_code not in (200, 201):
            raise ImageStoreBackendException("Create course error: {status_code}".format(status_code=r.status_code))
        return r.json()

    def _upload_images(self, course_id, uploaded_files):
        '''
        Upload images to course space.
        '''
        url = "%s/courses/%s/images" % (self.base_url, course_id)
        post_files = []
        for uploaded_file in uploaded_files:
            file_tuple = (uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)
            post_files.append(('file', file_tuple)) # the field name must be "files" 

        post_headers = {'Authorization': self.headers['Authorization']}
        r = requests.post(url, headers=post_headers, data={'title':'Untitled'}, files=post_files)
        logger.debug("API POST {url} status:{status_code} text:{text}".format(url=url, status_code=r.status_code, text=r.text))

        if r.status_code not in (200, 201):
            raise ImageStoreBackendException("Upload image error: {status_code}".format(status_code=r.status_code))
        return r.json()

    def _create_collection(self, course_id, title="Untitled Collection", description="Image Annotation"):
        '''
        Create a new collection.
        '''
        url = "%s/courses/%s/collections" % (self.base_url, course_id)
        post_data = {"title": title, "description": description}
        r = requests.post(url, headers=self.headers, data=json.dumps(post_data))
        logger.debug("API POST {url} data:{data} status:{status_code} text:{text}".format(url=url, data=post_data, status_code=r.status_code, text=r.text))

        if r.status_code not in (200, 201):
            raise ImageStoreBackendException("Create collection error: {status_code}".format(status_code=r.status_code))
        return r.json()

    def _get_collection(self, collection_id):
        '''
        Retrieve collection details.
        '''
        url = "%s/collections/%s" % (self.base_url, collection_id)
        r = requests.get(url, headers=self.headers)
        logger.debug("API GET {url} status:{status_code} text:{text}".format(url=url, status_code=r.status_code, text=r.text))

        if r.status_code == 200:
            collection = r.json()
        elif r.status_code == 404:
            collection = False
        else:
            raise ImageStoreBackendException("Get collection error: {status_code}".format(status_code=r.status_code))
        return collection

    def _add_to_collection(self, collection_id, image_ids):
        '''
        Add images from course space to a specific collection so that we can obtain a IIIF manifest.
        '''
        url = "%s/collections/%s/images" % (self.base_url, collection_id)
        post_data = [dict(course_image_id=image_id) for image_id in image_ids]
        r = requests.post(url, headers=self.headers, data=json.dumps(post_data))
        logger.debug("API POST {url} data:{data} status:{status_code} text:{text}".format(url=url, data=post_data, status_code=r.status_code, text=r.text))

        if r.status_code not in (200, 201):
            raise ImageStoreBackendException("Add images to collection error: {status_code}".format(status_code=r.status_code))
        return r.json()
    