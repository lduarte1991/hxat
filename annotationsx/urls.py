from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView
admin.autodiscover()
urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'annotationsx.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^lti_init/', include('hx_lti_initializer.urls', namespace="hx_lti_initializer")),
    url(r'^lti_init/launch_lti/assignment/', include('hx_lti_assignment.urls', namespace="hx_lti_assignment")),
    url(r'^lti_init/launch_lti/', include('target_object_database.urls', namespace="target_object_database")),
    url(r'^accounts/profile/', TemplateView.as_view(template_name='index.html')) 
)
