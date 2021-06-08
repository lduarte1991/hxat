import pytest

from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory
from django.urls import reverse
from hxat.middleware import LTILaunchSession, MultiLTILaunchMiddleware


@pytest.mark.django_db
def test_MultiLTILaunchMiddleware_is_basic_lti_launch(lti_launch_params_factory):
    target_path = reverse("hx_lti_initializer:launch_lti")
    launch_url = "http://testserver{}".format(target_path)

    resource_link_id = "resource_link_id_1234567"
    params = lti_launch_params_factory(
        lti_message_type="basic-lti-launch-request",
        course_id="fake_context_id",
        user_name="fake_user_name",
        user_id="fake_user_id",
        user_roles=["Instructor", "Administrator"],
        resource_link_id=resource_link_id,
        launch_url=launch_url,
    )

    request_factory = RequestFactory()
    request = request_factory.post(target_path, data=params)
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
def test_MultiLTILaunchMiddleware_is_lti_content_item_message(lti_launch_params_factory):
    target_path = reverse("hx_lti_initializer:launch_lti")
    launch_url = "http://testserver{}".format(target_path)

    resource_link_id = "resource_link_id_1234567"
    params = lti_launch_params_factory(
        lti_message_type="ContentItemSelectionRequest",
        course_id="fake_context_id",
        user_name="fake_user_name",
        user_id="fake_user_id",
        user_roles=["Instructor", "Administrator"],
        resource_link_id=resource_link_id,
        launch_url=launch_url,
    )

    request_factory = RequestFactory()
    request = request_factory.post(target_path, data=params)
    request.session = SessionStore()

    middleware = MultiLTILaunchMiddleware(get_response=lambda request: None)
    try:
        middleware.process_request(request)
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")

    assert not hasattr(request, "LTI")