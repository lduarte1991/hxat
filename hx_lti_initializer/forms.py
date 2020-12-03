import oauthlib.common
import oauthlib.oauth1
from django import forms
from django.conf import settings
from django.db.models import Q
from hx_lti_initializer.models import LTICourse, LTIProfile


class CourseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self._user_scope = kwargs.pop("user_scope", None)
        super(CourseForm, self).__init__(*args, **kwargs)
        self.fields["course_admins"].queryset = self.get_course_admins()

    def get_course_admins(self):
        queryset = LTIProfile.objects.all()
        if self._user_scope:
            queryset = queryset.filter(
                Q(scope=self._user_scope) | Q(scope__isnull=True)
            )
        return queryset.select_related("user").order_by("name", "user__username")

    class Meta:
        model = LTICourse
        fields = ("course_name", "course_admins", "course_external_css_default")


class EmbedLtiSelectionForm(forms.Form):
    '''
    This form is intended to be used as part of the LTI content item embed workflow
    to present a selection interface to the user.

    Note: Attempted to use django-crispy-forms for layout, but the crispy template
        for RadioSelect does not render subgroups of choices.
    '''

    def __init__(self, *args, **kwargs):
        course_instance = kwargs.pop('course_instance')
        content_item_return_url = kwargs.pop('content_item_return_url')
        super().__init__(*args, **kwargs)

        self.fields['content_item_return_url'] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=content_item_return_url,
        )

        choices = self._get_choices(course_instance)
        self.fields['content_item'] = forms.ChoiceField(
            widget=forms.RadioSelect(attrs={'class':'content_item'}),
            choices=choices,
            initial=self._get_initial_choice(choices),
            required=True,
        )

    def _get_choices(self, course_instance):
        choices = []
        for assignment in course_instance.get_published_assignments():
            group_name = assignment.assignment_name
            group_choices = []
            for target in assignment.assignment_objects.all():
                value = f"{assignment.assignment_id}/{target.pk}"
                label = target.target_title
                group_choices.append((value, label))
            choices.append((group_name, group_choices))
        return choices

    def _get_initial_choice(self, choices):
        if len(choices) == 0:
            return None
        group_name, group_choices = choices[0]
        return group_choices[0][0]


class EmbedLtiResponseForm(forms.Form):
    '''
    This form is intended to be used as part of the LTI content item embed workflow
    to return a response back to the tool consumer. Mostly it encapsulates the oauth
    signing process.
    '''

    lti_message_type = forms.CharField(widget=forms.HiddenInput())
    lti_version = forms.CharField(widget=forms.HiddenInput())
    content_items = forms.CharField(widget=forms.HiddenInput())  # Note: this should probably be a JSONField, but requires Django 3.1
    oauth_version = forms.CharField(widget=forms.HiddenInput())
    oauth_nonce = forms.CharField(widget=forms.HiddenInput())
    oauth_timestamp = forms.CharField(widget=forms.HiddenInput())
    oauth_consumer_key = forms.CharField(widget=forms.HiddenInput())
    oauth_callback = forms.CharField(widget=forms.HiddenInput())
    oauth_signature_method = forms.CharField(widget=forms.HiddenInput())
    oauth_signature = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_oauth_signature(self, http_method="POST", url=None):
        body = dict(self.data)  # shallow copy
        headers = {}
        request = oauthlib.common.Request(url, http_method, body, headers)

        # generate the oauth params and update the form data
        client = oauthlib.oauth1.Client(settings.CONSUMER_KEY, client_secret=settings.LTI_SECRET)
        oauth_params = client.get_oauth_params(request)
        oauth_signature =  client.get_oauth_signature(request)
        oauth_params.append(('oauth_signature', oauth_signature))
        oauth_params.append(('oauth_callback', 'about:blank'))
        self.data.update(oauth_params)
