"""
Sets the urls which will launch the LTI

This file will allow us to set up the urls by which to launch the LTI tool.
Later on we should be able to differentiate each LTI tool by unrolling the URL
used, e.g. /launch_lti/textannotation, /launch_lti/shared_annotation.
"""
from django.conf.urls import patterns, url

#None of these urls are seen by the user, because the whole tool operates within an iFrame.
urlpatterns = patterns(
    '',
    url(r'^launch_lti/$', 'annotationsx.views.launch_lti', name="launch_lti"),
    url(r'^launch_lti/annotation_view$', 'annotationsx.views.annotation_view', name="annotation_view"),
    url(r'^launch_lti/index_view$', 'annotationsx.views.index_view', name='index_view'),
    url(r'launch_lti/dashboard_view$', 'annotationsx.views.dashboard_view', name='dashboard_view')
)