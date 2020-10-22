import re

from crispy_forms.bootstrap import Tab, TabHolder
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Fieldset, Hidden, Layout
from django import forms
from django.forms.models import inlineformset_factory, modelformset_factory
from django.utils.html import strip_tags
from hx_lti_assignment.models import Assignment, AssignmentTargets


class AssignmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AssignmentForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            TabHolder(
                Tab(
                    "Assignment Information",
                    "assignment_name",
                    Field("course", css_class="selectpicker", data_live_search="true"),
                ),
                Tab(
                    "Database Settings",
                    "annotation_database_url",
                    "annotation_database_apikey",
                    "annotation_database_secret_token",
                ),
                Tab(
                    "Annotation Table Settings",
                    "include_instructor_tab",
                    "include_mynotes_tab",
                    "include_public_tab",
                    HTML(
                        "<p><em>Note:</em> Turning off all three will turn on Zen mode where only the object is shown. Annotations cannot be made.</p>"
                    ),
                    Field("default_tab", css_class="selectpicker"),
                    "pagination_limit",
                ),
                Tab(
                    "Annotator Settings",
                    Fieldset(
                        "Colored Highlights", "allow_highlights", "highlights_options",
                    ),
                    Fieldset("Turn Settings On/Off", "allow_touch", "allow_flags",),
                ),
            )
        )

    def clean_annotation_database_url(self):
        # noqa from http://stackoverflow.com/questions/6883049/regex-to-find-urls-in-string-in-python
        url = self.cleaned_data["annotation_database_url"]
        urls = re.findall(
            "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            url,
        )  # noqa

        if len(urls) == 0:
            raise forms.ValidationError("Did not type in a URL for the db!")

        return url

    class Meta:
        model = Assignment
        exclude = []


class AssignmentTargetsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AssignmentTargetsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div("target_object", "order", "target_external_css"),
        )

    def clean_target_instructions(self):
        """
        When instructions are just an empty paragraph or line break, set to the empty string
        which is used to determine whether or not to display instructions to students.
        """
        target_instructions = self.cleaned_data["target_instructions"]
        if strip_tags(target_instructions).strip() == "":
            return ""
        return target_instructions

    class Meta:
        model = AssignmentTargets
        fields = [
            "target_object",
            "order",
            "target_external_css",
        ]


# Note: extra=0 kwargs is necessary otherwise the formset will be padded with 3 empty widgets that do not
# have valid model instances
AssignmentTargetsFormSet = inlineformset_factory(
    Assignment, AssignmentTargets, exclude=[], can_delete=True, extra=0
)  # noqa


class NoFormTagCrispyFormMixin(object):
    @property
    def helper(self):
        if not hasattr(self, "_helper"):
            self._helper = FormHelper()
            self._helper.form_tag = False
        return self._helper


class DeleteAssignmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DeleteAssignmentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Assignment
        fields = []
