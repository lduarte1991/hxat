from django import forms
from hx_lti_initializer.models import LTICourse, LTIProfile
from hx_lti_assignment.models import Assignment

class CourseForm(forms.ModelForm):
	
	def __init__(self, *args, **kwargs):
		super(CourseForm, self).__init__(*args, **kwargs)
		self.fields['course_admins'].queryset = self.get_course_admins()

	def get_course_admins(self):
		return LTIProfile.objects.select_related('user').order_by('user__first_name', 'user__last_name', 'user__username')
	
	class Meta:
		model = LTICourse
		fields = ('course_name', 'course_admins', 'course_external_css_default')

