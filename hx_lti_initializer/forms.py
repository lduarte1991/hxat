from django import forms
from django.db.models import Q
from hx_lti_assignment.models import Assignment
from hx_lti_initializer.models import LTICourse, LTIProfile


class CourseForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self._user_scope = kwargs.pop('user_scope', None)
        super(CourseForm, self).__init__(*args, **kwargs)
        self.fields['course_admins'].queryset = self.get_course_admins()

    def get_course_admins(self):
        queryset = LTIProfile.objects.all()
        if self._user_scope:
            queryset = queryset.filter(Q(scope=self._user_scope)|Q(scope__isnull=True))
        return queryset.select_related('user').order_by('name', 'user__username')

    class Meta:
        model = LTICourse
        fields = (
            'course_name',
            'course_admins',
            'course_external_css_default'
        )
