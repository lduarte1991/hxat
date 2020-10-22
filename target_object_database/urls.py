from django.conf.urls import url
from target_object_database import views
from target_object_database.views import (
    create_new_source,
    edit_source,
    newSource,
    open_target_object,
)

urlpatterns = [
    url(
        r'^source/(?P<collection_id>[^/]*)/(?P<target_obj_id>\d+)/',
        open_target_object,
        name="open_target_object"
    ),
    url(
        r'^source/create_new_source/$',
        create_new_source,
        name="create_new_source"
    ),
    url(
        r'^source/(?P<id>\d+)/edit/$',
        edit_source,
        name="edit_source"
    ),
    url(
        r'^source/get/(?P<object_id>\d+)',
        views.SourceView.as_view(),
        name="source_list"
    ),
    url(
        r'^source/add/target_object/?$',
        newSource,
        name="popUpNewSource"
    ),
]
