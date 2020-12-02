"""
Admin set up for the LTI Initializer

The initializer needs to set up a profile. This is the one thing consistent
throughout the LTI. Even courses is only related via the target objects.
"""

from django.contrib import admin
from django.contrib.sessions.models import Session
from hx_lti_initializer.models import LTICourse, LTICourseAdmin, LTIProfile, LTIResourceLinkConfig


class LTIProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "scope", "anon_id", "name", "roles")
    search_fields = ("user__username", "anon_id", "name")
    ordering = ("user", "scope", "anon_id", "name", "roles")


class LTICourseListAdmin(admin.ModelAdmin):
    list_display = (
        "course_name",
        "course_id",
    )
    search_fields = ("course_name",)
    fields = [
        "course_id",
        "course_name",
        "course_admins",
        "course_external_css_default",
        "course_users",
    ]
    readonly_fields = ["course_id"]

    def course_id(self, instance):  # pragma: no cover
        return str(self.course_id)


class LTIResourceLinkConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "assignment_target", "resource_link_id")
    search_fields = ("resource_link_id",)


class SessionAdmin(admin.ModelAdmin):
    def _session_data(self, obj):
        return obj.get_decoded()

    list_display = ["session_key", "_session_data", "expire_date"]


class LTIPendingAdmin(admin.ModelAdmin):
    list_display = ("admin_unique_identifier", "new_admin_course_id")


admin.site.register(Session, SessionAdmin)
admin.site.register(LTIProfile, LTIProfileAdmin)
admin.site.register(LTICourse, LTICourseListAdmin)
admin.site.register(LTIResourceLinkConfig, LTIResourceLinkConfigAdmin)
admin.site.register(LTICourseAdmin, LTIPendingAdmin)
