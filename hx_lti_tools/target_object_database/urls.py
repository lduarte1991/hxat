from django.conf.urls import patterns, url
from target_object_database import views

urlpatterns = patterns('',
    url(r'^source/(?P<collection_id>[^/]*)/(?P<target_obj_id>\d+)/', 'target_object_database.views.open_target_object', name="open_target_object"),
    url(r'^source/create_new_source/$', 'target_object_database.views.create_new_source', name="create_new_source"),
    url(r'^source/(?P<id>\d+)/edit/$', 'target_object_database.views.edit_source', name="edit_source"),
    url(r'^source/get/(?P<object_id>\d+)', views.SourceView.as_view(), name="source_list"),
    url(r'^source/add/target_object/?$', 'target_object_database.views.newSource', name="popUpNewSource"),
)
