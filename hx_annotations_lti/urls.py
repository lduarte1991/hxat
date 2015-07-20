from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
import django_app_lti.urls

admin.autodiscover()
urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'hx_annotations_lti.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^lti_init/', include('annotationsx.urls', namespace="annotationsx")),
    url(r'^lti_init/launch_lti/annotation/', include('hx_lti_todapi.urls', namespace="hx_lti_todapi")),
    url(r'^accounts/profile/', TemplateView.as_view(template_name='index.html')),
    url(r'^lti/', include(django_app_lti.urls, namespace="lti"))
)

urlpatterns += staticfiles_urlpatterns()
