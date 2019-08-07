"""
Sets the urls which will launch the LTI

This file will allow us to set up the urls by which to launch the LTI tool.
Later on we should be able to differentiate each LTI tool by unrolling the URL
used, e.g. /launch_lti/textannotation, /launch_lti/shared_annotation.
"""
from django.urls import path
from hx_lti_initializer.views import edit_course, launch_lti, course_admin_hub, access_annotation_target, instructor_dashboard_view, instructor_dashboard_student_list_view, delete_assignment, change_starting_resource


urlpatterns = [
    path(
        'course/(<int:id>)/edit/',
        edit_course,
        name="edit_course",
    ),
    path(
        'launch_lti/',
        launch_lti,
        name="launch_lti",
    ),
    path(
        'admin_hub/',
        course_admin_hub,
        name="course_admin_hub",
    ),
    path(
        'admin_hub/<path:course_id>/<slug:assignment_id>/<int:object_id>/preview/',
        access_annotation_target,
        name="access_annotation_target"
    ),
    # using a wildcard for the middle of the url, so lti_init/instructor_dashboard and lti_init/admin_hub/instructor_dashboard will both work
    path('instructor_dashboard_view', instructor_dashboard_view, name='instructor_dashboard_view'),
    path('instructor_dashboard_view/student_list', instructor_dashboard_student_list_view, name='instructor_dashboard_student_list_view'),
    path(
        'delete_assignment/',
        delete_assignment,
        name="delete_assignment",
    ),
    path(
        'admin_hub/<slug:assignment_id>/<int:object_id>/starting_resource/',
        change_starting_resource,
        name="change_starting_resource"
    ),
]
