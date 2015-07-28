from django import forms
from hx_lti_initializer.models import LTICourse
from hx_lti_assignment.models import Assignment

class CourseForm(forms.ModelForm):

	class Meta:
		model = LTICourse
		fields = ('course_name', 'course_admins', 'course_external_css_default')

