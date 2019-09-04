from django.conf.urls import url
from . import views

urlpatterns = [
    url( r'^api$', views.api_root, name="api_root_prefix"),
    url( r'^api/(?P<annotation_id>[A-Za-z0-9-]+|)?$', views.api_root, name="api_root"),
    url( r'^api/search$',views.search,name="api_search"),
    url( r'^api/create$', views.create, name="api_create"),
    url( r'^api/delete/(?P<annotation_id>[0-9]+|)$', views.delete, name="api_delete"),
    url( r'^api/destroy/(?P<annotation_id>[0-9]+|)$', views.delete, name="api_delete"),
    url( r'^api/update/(?P<annotation_id>[0-9]+)$', views.update, name="api_update"),
    url( r'^api/transfer_annotations/(?P<instructor_only>[0-1])?$', views.transfer, name="api_transfer_annotations"),
]
