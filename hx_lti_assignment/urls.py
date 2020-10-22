from django.conf.urls import url
from hx_lti_assignment.views import (
    assignments_from_course,
    create_new_assignment,
    delete_assignment,
    edit_assignment,
    import_assignment,
    moving_assignment,
)

urlpatterns = [
    url(
        r'^create_new/$',
        create_new_assignment,
        name="create_new_assignment",
    ),
    url(
        r'^(?P<id>[0-9]+)/edit/',
        edit_assignment,
        name="edit_assignment",
    ),
    url(
        r'^(?P<id>[0-9]+)/delete/',
        delete_assignment,
        name="delete_assignment",
    ),
    url(
        r'^import_assignment/$',
        import_assignment,
        name="import_assignment",
    ),
    url(
        r'^(?P<course_id>[0-9]+)/get_assignments',
        assignments_from_course,
        name="assignments_from_course",
    ),
    url(
        r'^(?P<old_course_id>[0-9]+)/(?P<new_course_id>[0-9]+)/(?P<assignment_id>[0-9]+)/import',
        moving_assignment,
        name="moving_assignment",
    )
]
