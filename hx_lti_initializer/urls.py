"""
Sets the urls which will launch the LTI

This file will allow us to set up the urls by which to launch the LTI tool.
Later on we should be able to differentiate each LTI tool by unrolling the URL
used, e.g. /launch_lti/textannotation, /launch_lti/shared_annotation.
"""
from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(
        r'^course/(?P<id>[0-9]+)/edit/$',
        'hx_lti_initializer.views.edit_course',
        name="edit_course",
    ),
    url(
        r'^launch_lti/$',
        'hx_lti_initializer.views.launch_lti',
        name="launch_lti",
    ),
    url(
        r'^annotation_api/search$',
        'hx_lti_initializer.views.annotation_database_search',
        name="annotation_database_search",
    ),
    url(
        r'^annotation_api/create$',
        'hx_lti_initializer.views.annotation_database_create',
        name="annotation_database_create",
    ),
    url(
        r'^annotation_api/delete/(?P<annotation_id>[0-9]+)$',
        'hx_lti_initializer.views.annotation_database_delete',
        name="annotation_database_delete",
    ),
    url(
        r'^annotation_api/update/(?P<annotation_id>[0-9]+)$',
        'hx_lti_initializer.views.annotation_database_update',
        name="annotation_database_update",
    ),
    url(
        r'^admin_hub/$',
        'hx_lti_initializer.views.course_admin_hub',
        name="course_admin_hub",
    ),
    url(
        # TODO: Make URL routing more elegant as opposed to having /admin_hub/admin_hub
        #r'\w/admin_hub/(?P<course_id>[0-9a-z]+)/(?P<assignment_id>[0-9a-z\-]+)/(?P<object_id>[0-9]+)/preview/$',
        r'\w/admin_hub/(?P<course_id>[0-9a-z:+-_]+)/(?P<assignment_id>[0-9a-z\-]+)/(?P<object_id>[0-9]+)/preview/$',
        'hx_lti_initializer.views.access_annotation_target',
        name="access_annotation_target"
    ),
    
    # using a wildcard for the middle of the url, so lti_init/instructor_dashboard and lti_init/admin_hub/instructor_dashboard will both work
    url(r'\w/instructor_dashboard_view$', 'hx_lti_initializer.views.instructor_dashboard_view', name='instructor_dashboard_view'),

    url(
        r'^delete_assignment/$',
        'hx_lti_initializer.views.delete_assignment',
        name="delete_assignment",
    ),
)
