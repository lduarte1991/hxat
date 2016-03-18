"""
Admin set up for the LTI Initializer

The initializer needs to set up a profile. This is the one thing consistent
throughout the LTI. Even courses is only related via the target objects.
"""

from django.contrib import admin
from hx_lti_initializer.models import LTIProfile, LTICourse


class LTIProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'scope', 'anon_id', 'name', 'roles')
    ordering = ('user', 'scope', 'anon_id', 'name', 'roles')


class LTICourseAdmin(admin.ModelAdmin):
    fields = [
        'course_id',
        'course_name',
        'course_admins',
        'course_external_css_default',
        'course_users',
    ]
    readonly_fields = ['course_id']

    def course_id(self, instance):  # pragma: no cover
        return str(self.course_id)

admin.site.register(LTIProfile, LTIProfileAdmin)
admin.site.register(LTICourse, LTICourseAdmin)
