from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
admin.autodiscover()

import django_app_lti.urls

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^lti_init/', include('hx_lti_initializer.urls', namespace="hx_lti_initializer")),
    url(r'^annotation_store/', include('annotation_store.urls', namespace="annotation_store")),
    url(r'^lti_init/launch_lti/assignment/', include('hx_lti_assignment.urls', namespace="hx_lti_assignment")),
    url(r'^lti_init/launch_lti/', include('target_object_database.urls', namespace="target_object_database")),
    url(r'^accounts/profile/', TemplateView.as_view(template_name='index.html')),
    url(r'^500/', TemplateView.as_view(template_name="main/500.html")),
    url(r'^troubleshooting/', TemplateView.as_view(template_name="main/troubleshooting.html")),
    # TODO: Check to see if this works without enabling django_app_lti
    # Include the lti app's urls
    url(r'^lti/', include(django_app_lti.urls, namespace="lti")),
]
