from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^annotation/(?P<collection_id>[^/]*)/(?P<target_obj_id>\d+)/', 'target_object_database.views.open_target_object', name="open_target_object"),
)
