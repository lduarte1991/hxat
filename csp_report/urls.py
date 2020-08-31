from django.conf.urls import url
from . import views

urlpatterns = [
    url( r'^report$', views.csp_report, name='csp_report'),
]
