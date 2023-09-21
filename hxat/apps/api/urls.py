from django.urls import path
from hxat.apps.api import views
from rest_framework.urlpatterns import format_suffix_patterns

app_name = "api"
urlpatterns = [
    path(
        "v1/course/<course_id>/",
        views.LTICourseDetail.as_view(),
        name="lticourse-detail",
    ),
]

urlpatterns = format_suffix_patterns(urlpatterns)
