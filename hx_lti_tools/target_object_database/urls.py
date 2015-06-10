from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^source/(?P<collection_id>[^/]*)/(?P<target_obj_id>\d+)/', 'target_object_database.views.open_target_object', name="open_target_object"),
    url(r'^source/create_new_source/$', 'target_object_database.views.create_new_source', name="create_new_source"),
    url(r'^source/(?P<id>\d+)/edit/$', 'target_object_database.views.edit_source', name="edit_source"),
)
