from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.forms import ValidationError
from target_object_database.models import TargetObject
from hx_lti_initializer.utils import debug_printer

import image_store.backends

class SourceForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(SourceForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(SourceForm, self).clean()
        data = self.cleaned_data.get('target_content')
        targ_type = self.cleaned_data.get('target_type')

        possible_to = None
        try:
            possible_to = TargetObject.objects.filter(target_content__icontains=data)[0]
        except:
            pass
        if possible_to is not None and possible_to.target_type == "ig":
            msg = "The image manifest already exists and is named %s (url: %s)" % (possible_to, possible_to.target_content)
            self.add_error('target_content', msg)

    def save(self):
        if self.files and settings.IMAGE_STORE_BACKEND:
            try:
                manifest_url = handle_file_upload(self.data, self.files, self.request.LTI['launch_params'])
            except ValidationError as e:
                self.add_error(None, str(e))
                raise e
            self.instance.target_content = manifest_url

        return super(SourceForm, self).save()

    class Meta:
        model = TargetObject
        fields = (
            'target_title',
            'target_author',
            'target_content',
            'target_citation',
            'target_creator',
            'target_courses',
            'target_type'
        )


def handle_file_upload(data, files, lti_params):
    '''
    Parameters:
        data(dict): the request.POST dict-like object
        files(dict): the request.FILES dict-like object
        lti_params(dict): should be the initial LTI launch params stored in th session
    
    Returns:
        str: the manifest URL
    
    Raises:
        ValidationError: Error saving the image
    '''
    image_backend_class = getattr(image_store.backends, settings.IMAGE_STORE_BACKEND)
    image_backend = image_backend_class(settings.IMAGE_STORE_BACKEND_CONFIG, lti_params)
    
    title = data.get('target_title', 'Untitled Target Object')
    if 'target_file' not in files:
        raise ValidationError("Error saving image. Missing 'target_file' field.")
    uploaded_file = files['target_file']
    
    try:
        manifest_url = image_backend.store([uploaded_file], title)
    except image_store.backends.ImageStoreBackendException as e:
        raise ValidationError("Error saving image. Details: %s" % e)

    if not manifest_url:
        raise ValidationError("Failed to get manifest after saving image (manifest required for annotation).")

    return manifest_url