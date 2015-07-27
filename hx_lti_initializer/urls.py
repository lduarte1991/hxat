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
        r'^admin_hub/$',
        'hx_lti_initializer.views.course_admin_hub',
        name="course_admin_hub",
    ),
    url(
        r'^admin_hub/(?P<course_id>[0-9a-z]+)/(?P<assignment_id>[0-9a-z\-]+)/(?P<object_id>[0-9]+)/preview/$',
        'hx_lti_initializer.views.access_annotation_target',
        name="access_annotation_target"
    ),
)
