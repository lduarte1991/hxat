from django.urls import re_path
from target_object_database import views
from target_object_database.views import (
    create_new_source,
    edit_source,
    newSource,
    open_target_object,
)

urlpatterns = [
    re_path(
        r"^source/(?P<collection_id>[^/]*)/(?P<target_obj_id>\d+)/",
        open_target_object,
        name="open_target_object",
    ),
    re_path(r"^source/create_new_source/$", create_new_source, name="create_new_source"),
    re_path(r"^source/(?P<id>\d+)/edit/$", edit_source, name="edit_source"),
    re_path(
        r"^source/get/(?P<object_id>\d+)",
        views.SourceView.as_view(),
        name="source_list",
    ),
    re_path(r"^source/add/target_object/?$", newSource, name="popUpNewSource"),
]
