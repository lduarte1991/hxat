import pytest

from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory
from django.urls import reverse
from hxat.middleware import LTILaunchSession, MultiLTILaunchMiddleware


@pytest.mark.django_db
def test_MultiLTILaunchMiddleware_is_basic_lti_launch(
    lti_path,
    lti_launch_url,
    lti_launch_params_factory
):

    resource_link_id = "resource_link_id_1234567"
    params = lti_launch_params_factory(
        course_id="fake_context_id",
        user_name="fake_user_name",
        user_id="fake_user_id",
        user_roles=["Instructor", "Administrator"],
        resource_link_id=resource_link_id,
        launch_url=lti_launch_url,
    )

    request_factory = RequestFactory()
    request = request_factory.post(lti_path, data=params)
    request.session = SessionStore()

    middleware = MultiLTILaunchMiddleware(get_response=lambda request: None)
    try:
        middleware.process_request(request)
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")

    assert request.session.modified is True
    assert hasattr(request, "LTI")
    assert isinstance(request.LTI, LTILaunchSession)
    assert request.LTI.resource_link_id == resource_link_id


@pytest.mark.django_db
def test_MultiLTILaunchMiddleware_is_lti_content_item_message(
    embed_lti_path,
    embed_lti_launch_url,
    lti_content_item_request_factory
):

    params = lti_content_item_request_factory(
        course_id="fake_context_id",
        user_name="fake_user_name",
        user_id="fake_user_id",
        user_roles=["Instructor", "Administrator"],
        launch_url=embed_lti_launch_url,
    )

    request_factory = RequestFactory()
    request = request_factory.post(embed_lti_path, data=params)
    request.session = SessionStore()

    middleware = MultiLTILaunchMiddleware(get_response=lambda request: None)
    try:
        middleware.process_request(request)
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")

    assert not hasattr(request, "LTI")