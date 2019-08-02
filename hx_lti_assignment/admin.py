from django.contrib import admin
from hx_lti_assignment.models import Assignment, AssignmentTargets


class AssignmentTargetsInline(admin.TabularInline):
    model = AssignmentTargets
    extra = 1


class AssignmentAdmin(admin.ModelAdmin):
    inlines = (AssignmentTargetsInline,)
    list_display = ('assignment_name', 'course', 'is_published', 'use_hxighlighter')
    search_fields = ('assignment_name',)

admin.site.register(Assignment, AssignmentAdmin)
