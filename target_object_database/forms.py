from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import URLValidator
from django.forms import ValidationError
from target_object_database.models import TargetObject

import image_store.backends

class SourceForm(forms.ModelForm):
    target_content = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(SourceForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(SourceForm, self).clean()
        target_type = self.cleaned_data.get('target_type')
        target_content = self.cleaned_data.get('target_content')

        if target_type in ('tx', 'vd'):
            if not target_content:
                self.add_error('target_content', 'This field is required.')
        elif target_type == 'ig':
            if settings.IMAGE_STORE_BACKEND:
                if not self.files and not target_content:
                    self.add_error(None, 'Please choose an image to upload OR provide a source manifest URL.')
                elif not self.files and target_content:
                    self.validate_manifest_url(target_content)
                    self.validate_manifest_unique(target_content)
            else:
                if target_content:
                    self.validate_manifest_url(target_content)
                    self.validate_manifest_unique(target_content)
                else:
                    self.add_error('target_content', 'This field is required.')

    def validate_manifest_url(self, target_content):
        try:
            validate_https_url = URLValidator(schemes=['https'])
            validate_https_url(target_content)
        except ValidationError as e:
            self.add_error('target_content', 'Not a valid manifest URL. Make sure it\'s only one URL and that it begins with "https".')

    def validate_manifest_unique(self, target_content):
        found = None
        try:
            found = TargetObject.objects.filter(target_content__icontains=target_content)[0]
        except:
            pass
        if found and found.pk != self.instance.pk:
            msg = "The image manifest must be unique. It is already provided by source '%s' (ID:%s)." % (found.target_title, found.pk)
            self.add_error('target_content', msg)

    def save(self):
        if settings.IMAGE_STORE_BACKEND and self.files:
            try:
                self.instance.target_content = handle_file_upload(self.data, self.files, self.request.LTI['launch_params'])
            except ValidationError as e:
                self.add_error(None, e.message)
                raise e
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
        ValidationError
    '''
    title = "Annotation: %s" % data.get('target_title', 'Untitled Target Object')
    # it is a MultiValueDict, and a list of values can be returned with getlist
    list_of_files = files.getlist('target_file')

    try:
        cls = image_store.backends.get_backend_class(settings.IMAGE_STORE_BACKEND)
        image_backend = cls(config=settings.IMAGE_STORE_BACKEND_CONFIG, lti_params=lti_params)
        manifest_url = image_backend.store([file for file in list_of_files], title) # Intentionally passed as a list() instead of MultiValueDict
    except image_store.backends.ImageStoreBackendException as e:
        raise ValidationError("Error uploading image. Details: %s" % e)

    if not manifest_url:
        raise ValidationError("Failed to get manifest after uploading image (manifest required for annotation).")

    return manifest_url
