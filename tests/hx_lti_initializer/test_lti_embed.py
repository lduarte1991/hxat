import pytest
from django.test import Client


@pytest.mark.django_db
def test_embed_lti_permissions_learner_denied(
    user_profile_factory,
    course_instructor_factory,
    embed_lti_path,
    embed_lti_launch_url,
    lti_content_item_request_factory
):
    user_roles = ["Learner"]
    user = user_profile_factory(roles=user_roles)
    course_object, i = course_instructor_factory()
    params = lti_content_item_request_factory(
        course_id=course_object.course_id,
        user_name=user.name,
        user_id=user.anon_id,
        user_roles=user_roles,
        launch_url=embed_lti_launch_url,
    )

    client = Client(enforce_csrf_checks=False)
    response = client.post(embed_lti_path, data=params)
    assert response.status_code == 403
    assert "You must be a course admin to insert content items" in response.content.decode()


@pytest.mark.django_db
def test_embed_lti_permissions_instructor_ok(
    user_profile_factory,
    course_instructor_factory,
    embed_lti_path,
    embed_lti_launch_url,
    lti_content_item_request_factory
):
    user_roles = ["Instructor"]
    user = user_profile_factory(roles=user_roles)
    course_object, i = course_instructor_factory()
    params = lti_content_item_request_factory(
        course_id=course_object.course_id,
        user_name=user.name,
        user_id=user.anon_id,
        user_roles=user_roles,
        launch_url=embed_lti_launch_url,
    )

    client = Client(enforce_csrf_checks=False)
    response = client.post(embed_lti_path, data=params)
    assert response.status_code == 200
    assert 'No annotation content items available to add.' in response.content.decode()


@pytest.mark.django_db
def test_embed_lti_with_content_items(
    user_profile_factory,
    course_instructor_factory,
    embed_lti_path,
    embed_lti_launch_url,
    lti_content_item_request_factory,
    assignment_target_factory
):
    user_roles = ["Instructor"]
    user = user_profile_factory(roles=user_roles)
    course_object, i = course_instructor_factory()
    assignment_target = assignment_target_factory(course_object)
    content_item_identifier = f"{assignment_target.assignment.assignment_id}/{assignment_target.target_object.pk}"

    params = lti_content_item_request_factory(
        course_id=course_object.course_id,
        user_name=user.name,
        user_id=user.anon_id,
        user_roles=user_roles,
        launch_url=embed_lti_launch_url,
    )

    client = Client(enforce_csrf_checks=False)
    response = client.post(embed_lti_path, data=params)
    assert response.status_code == 200

    # Expecting the HTML selection UI to include a submit button and the assignment object(s)
    response_content = response.content.decode()
    assert 'Insert this annotation content' in response_content
    assert content_item_identifier in response_content