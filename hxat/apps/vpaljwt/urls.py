from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from hxat.apps.vpaljwt import views

app_name = "vpaljwt"
urlpatterns = [
    path("v1/endpoints/", views.AllowedEndpoints.as_view(), name="allowedendpoints"),
]

urlpatterns = format_suffix_patterns(urlpatterns)
