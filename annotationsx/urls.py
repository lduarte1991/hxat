from django.urls import include, path
from django.contrib import admin
from django.views.generic import TemplateView
admin.autodiscover()

# import django_app_lti.urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('lti_init/', include(('hx_lti_initializer.urls', 'hx_lti_initializer.urls'), namespace="hx_lti_initializer")),
    path('annotation_store/', include(('annotation_store.urls', 'annotation_store.urls'), namespace="annotation_store")),
    path('lti_init/launch_lti/assignment/', include(('hx_lti_assignment.urls', 'hx_lti_assignment.urls'), namespace="hx_lti_assignment")),
    path('lti_init/launch_lti/', include(('target_object_database.urls', 'target_object_database.urls'), namespace="target_object_database")),
    path('accounts/profile/', TemplateView.as_view(template_name='index.html')),
    path('500/', TemplateView.as_view(template_name="main/500.html")),
    path('troubleshooting/', TemplateView.as_view(template_name="main/troubleshooting.html")),
    # TODO: Check to see if this works without enabling django_app_lti
    # Include the lti app's urls
    #url(r'^lti/', include((django_app_lti.urls, 'lti'), namespace="lti")),
]
