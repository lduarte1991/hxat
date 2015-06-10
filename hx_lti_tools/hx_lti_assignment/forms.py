from django import forms
from hx_lti_assignment.models import Assignment

class AssignmentForm(forms.ModelForm):

    class Meta:
		model = Assignment
		fields = ('assignment_name', 'assignment_objects', 'annotation_database_url', 'annotation_database_apikey', 'annotation_database_secret_token', 'allow_highlights', 'include_instructor_tab', 'highlights_options', 'allow_touch', 'pagination_limit', 'allow_flags', 'default_tab', 'course')
