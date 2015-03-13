from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^(?P<target_obj_id>\d+)/', 'hx_lti_todapi.views.open_target_object', name="open_target_object"),
)
