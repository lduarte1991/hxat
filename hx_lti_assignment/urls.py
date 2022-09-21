from django.urls import re_path
from hx_lti_assignment.views import (
    assignments_from_course,
    create_new_assignment,
    delete_assignment,
    edit_assignment,
    import_assignment,
    moving_assignment,
)

urlpatterns = [
    re_path(r"^create_new/$", create_new_assignment, name="create_new_assignment",),
    re_path(r"^(?P<id>[0-9]+)/edit/", edit_assignment, name="edit_assignment",),
    re_path(r"^(?P<id>[0-9]+)/delete/", delete_assignment, name="delete_assignment",),
    re_path(r"^import_assignment/$", import_assignment, name="import_assignment",),
    re_path(
        r"^(?P<course_id>[0-9]+)/get_assignments",
        assignments_from_course,
        name="assignments_from_course",
    ),
    re_path(
        r"^(?P<old_course_id>[0-9]+)/(?P<new_course_id>[0-9]+)/(?P<assignment_id>[0-9]+)/import",
        moving_assignment,
        name="moving_assignment",
    ),
]
