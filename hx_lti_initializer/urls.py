"""
Sets the urls which will launch the LTI

This file will allow us to set up the urls by which to launch the LTI tool.
Later on we should be able to differentiate each LTI tool by unrolling the URL
used, e.g. /launch_lti/textannotation, /launch_lti/shared_annotation.
"""
from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^launch_lti/$', 'hx_lti_initializer.views.launch_lti', name="launch_lti"),
    # TODO: Change this to a more sensible URL
    url(r'^launch_lti/annotation_view$', 'hx_lti_initializer.views.annotation_view', name="annotation_view"),
)