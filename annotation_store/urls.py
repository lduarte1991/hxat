from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^api$", views.api_root, name="api_root_prefix"),
    re_path(r"^api/(?P<annotation_id>[A-Za-z0-9-]+|)?$", views.api_root, name="api_root"),
    re_path(r"^api/search$", views.search, name="api_search"),
    re_path(r"^api/create$", views.create, name="api_create"),
    re_path(r"^api/delete/(?P<annotation_id>[0-9]+|)$", views.delete, name="api_delete"),
    re_path(r"^api/destroy/(?P<annotation_id>[0-9]+|)$", views.delete, name="api_delete"),
    re_path(r"^api/update/(?P<annotation_id>[0-9]+)$", views.update, name="api_update"),
    re_path(
        r"^api/transfer_annotations/(?P<instructor_only>[0-1])?$",
        views.transfer,
        name="api_transfer_annotations",
    ),
    re_path(r"^api/grade/me", views.grade_me, name="api_grade_me"),
]
