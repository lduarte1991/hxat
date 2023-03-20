from django.urls import re_path

from . import views

urlpatterns = [
    re_path(
        r"^api/(?P<annotation_id>[A-Za-z0-9-]+|)?$", views.api_root, name="api_root"
    ),
    re_path(r"^api$", views.api_root, name="api_root_search"),
    re_path(r"^api/grade/me", views.grade_me, name="api_grade_me"),
    re_path(r"^api/transfer_annotations/(?P<source_assignment_id>[A-Za-z0-9-]+)?$",
        views.transfer_instructor_annotations,
        name="api_transfer_annotations",
    ),
]
