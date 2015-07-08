from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
admin.autodiscover()
urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'hx_lti_tools.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^lti_init/', include('hx_lti_initializer.urls', namespace="hx_lti_intializer")),
    url(r'^lti_init/launch_lti/annotation/', include('hx_lti_todapi.urls', namespace="hx_lti_todapi")),
    url(r'^accounts/profile/', TemplateView.as_view(template_name='index.html')) 
)

urlpatterns += staticfiles_urlpatterns()
