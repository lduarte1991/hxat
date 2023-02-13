import json

from django.conf import settings
import pytest

from annostore.store import AnnotationStore


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url, apikey, secret, result",
    [
        pytest.param(
            settings.ANNOTATION_DB_URL,
            settings.ANNOTATION_DB_API_KEY,
            settings.ANNOTATION_DB_SECRET_TOKEN,
            ( settings.ANNOTATION_DB_URL,
             settings.ANNOTATION_DB_API_KEY,
             settings.ANNOTATION_DB_SECRET_TOKEN),
        ),
        pytest.param("baba", "biba", "boba", ("baba","biba","boba")),
        pytest.param("xuxu", " ", "      ", None),
        pytest.param("", "", "",
            ( settings.ANNOTATION_DB_URL,
             settings.ANNOTATION_DB_API_KEY,
             settings.ANNOTATION_DB_SECRET_TOKEN),
        ),
    ],
)
def test_annostore_cfg_valid(
    url,
    apikey,
    secret,
    result,
    course_user_lti_launch_params,
    assignment_target_factory,
):
    # 1. create course, assignment, target_object, user
    course, user, launch_params = course_user_lti_launch_params
    assignment_target = assignment_target_factory(course)
    target_object = assignment_target.target_object
    assignment = assignment_target.assignment

    # prep assignment
    assignment.annotation_database_url = url
    assignment.annotation_database_apikey = apikey
    assignment.annotation_database_secret_token = secret
    assignment.save()

    t = AnnotationStore._valid_annostore_config(assignment)
    assert t == result

