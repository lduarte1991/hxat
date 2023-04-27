import pytest
from hx_lti_assignment.models import AssignmentTargets
from hx_lti_initializer.models import LTICourse


@pytest.mark.parametrize("status_code", [404, 500])
@pytest.mark.django_db
def test_AssignmentTargets_get_canvas_id_for_mirador_manifest_not_found(
    user_profile_factory, assignment_target_factory, requests_mock, status_code
):
    """
    Checks that if the mirador manifest returns an HTTP error response, then
    the canvas ID will be returned as None.
    """
    manifest_url = "http://localhost:8000/non-existent/manifest.json"
    instructor = user_profile_factory(roles=["Instructor"])
    course_object = LTICourse.create_course("test_course_id", instructor)
    assignment_target = assignment_target_factory(
        course_object,
        target_type="ig",
        target_content=manifest_url,
        target_external_options="ImageView,,false,,,",
    )

    requests_mock.get(manifest_url, status_code=status_code, text="")
    canvas_id = assignment_target.get_canvas_id_for_mirador()
    assert requests_mock.called
    assert canvas_id is None


@pytest.mark.django_db
def test_AssignmentTargets_get_canvas_id_for_mirador_manifest_returns_canvas_id_in_options(
    user_profile_factory, assignment_target_factory, requests_mock
):
    """
    Checks that if a canvas ID is explicitly set in the target options, it is returned immediately
    without querying the manifest.
    """
    manifest_url = "http://localhost:8000/valid/manifest.json"
    expected_canvas_id = "3123"
    instructor = user_profile_factory(roles=["Instructor"])
    course_object = LTICourse.create_course("test_course_id", instructor)
    assignment_target = assignment_target_factory(
        course_object,
        target_type="ig",
        target_content=manifest_url,
        target_external_options=f"ImageView,{expected_canvas_id},false,,,",
    )

    requests_mock.get(manifest_url, status_code=200, text="")
    actual_canvas_id = assignment_target.get_canvas_id_for_mirador()
    assert not requests_mock.called
    assert actual_canvas_id == expected_canvas_id


@pytest.mark.django_db
@pytest.mark.parametrize(
    "initial_options, new_options_list, expected_options",
    [
        pytest.param("ImageView,,true", [], ",,false,false,false,false"),
        pytest.param(
            "ImageView,,true",
            ["ImageView", "xuxu"],
            "ImageView,xuxu,false,false,false,false",
        ),
        pytest.param(",,true", ["", "xuxu"], ",xuxu,false,false,false,false"),
        pytest.param(
            ",,true,,,", ["", "", "true", "true", "", "true"], ",,true,true,false,true"
        ),
        pytest.param(
            "UnsupportedView,blah,true,,,",
            ["", "", "true", "true", "", "true"],
            ",,true,true,false,true",
        ),
    ],
)
def test_save_target_external_options_list(
    initial_options,
    new_options_list,
    expected_options,
    user_profile_factory,
    assignment_target_factory,
):
    manifest_url = "http://localhost:8000/non-existent/manifest.json"
    instructor = user_profile_factory(roles=["Instructor"])
    course_object = LTICourse.create_course("test_course_id", instructor)
    assignment_target = assignment_target_factory(
        course_object,
        target_type="ig",
        target_content=manifest_url,
        target_external_options=initial_options,
    )
    assignment_target.save_target_external_options_list(new_options_list)
    at = AssignmentTargets.objects.get(pk=assignment_target.id)
    assert at.target_external_options == expected_options
