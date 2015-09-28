from django.contrib import admin
from hx_lti_assignment.models import Assignment, AssignmentTargets


class AssignmentTargetsInline(admin.TabularInline):
    model = AssignmentTargets
    extra = 1


class AssignmentAdmin(admin.ModelAdmin):
    inlines = (AssignmentTargetsInline,)

admin.site.register(Assignment, AssignmentAdmin)
