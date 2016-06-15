from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(
        r'^create_new/$',
        'hx_lti_assignment.views.create_new_assignment',
        name="create_new_assignment",
    ),
    url(
        r'^(?P<id>[0-9]+)/edit/',
        'hx_lti_assignment.views.edit_assignment',
        name="edit_assignment",
    ),
    url(
        r'^(?P<id>[0-9]+)/delete/',
        'hx_lti_assignment.views.delete_assignment',
        name="delete_assignment",
    ),
)
