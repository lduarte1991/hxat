from django.conf.urls import patterns, url

from testapp import views

urlpatterns = patterns('',
    url(r'^launch_lti/$', 'testapp.views.launch_lti', name="launch_lti"),
)
