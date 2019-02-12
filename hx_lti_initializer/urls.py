"""
Sets the urls which will launch the LTI

This file will allow us to set up the urls by which to launch the LTI tool.
Later on we should be able to differentiate each LTI tool by unrolling the URL
used, e.g. /launch_lti/textannotation, /launch_lti/shared_annotation.
"""
from django.conf.urls import url
from hx_lti_initializer.views import edit_course, launch_lti, course_admin_hub, access_annotation_target, instructor_dashboard_view, instructor_dashboard_student_list_view, delete_assignment, change_starting_resource


urlpatterns = [
    url(
        r'^course/(?P<id>[0-9]+)/edit/$',
        edit_course,
        name="edit_course",
    ),
    url(
        r'^launch_lti/$',
        launch_lti,
        name="launch_lti",
    ),
    url(
        r'^admin_hub/$',
        course_admin_hub,
        name="course_admin_hub",
    ),
    url(
        r'\w/admin_hub/(?P<course_id>[0-9a-z:+-_]+)/(?P<assignment_id>[0-9a-z\-]+)/(?P<object_id>[0-9]+)/preview/$',
        access_annotation_target,
        name="access_annotation_target"
    ),
    # using a wildcard for the middle of the url, so lti_init/instructor_dashboard and lti_init/admin_hub/instructor_dashboard will both work
    url(r'\w/instructor_dashboard_view$', instructor_dashboard_view, name='instructor_dashboard_view'),
    url(r'\w/instructor_dashboard_view/student_list$', instructor_dashboard_student_list_view, name='instructor_dashboard_student_list_view'),
    url(
        r'^delete_assignment/$',
        delete_assignment,
        name="delete_assignment",
    ),
    url(
        r'\w/admin_hub/(?P<assignment_id>[0-9a-z\-]+)/(?P<object_id>[0-9]+)/starting_resource/$',
        change_starting_resource,
        name="change_starting_resource"
    ),
]
