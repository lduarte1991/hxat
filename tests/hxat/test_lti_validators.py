from django.conf import settings
from django.test import RequestFactory
from django.urls import reverse
from hxat.lti_validators import LTIRequestValidator
from lti import ToolConsumer
from lti.contrib.django import DjangoToolProvider


def test_lti_validation_from_ltidict_ok():
    target_path = reverse("hx_lti_initializer:launch_lti")
    launch_url = "http://testserver{}".format(target_path)
    resource_link_id = "some_string_to_be_the_fake_resource_link_id"
    consumer = ToolConsumer(
        consumer_key=settings.CONSUMER_KEY,
        consumer_secret=settings.TEST_COURSE_LTI_SECRET,
        launch_url=launch_url,
        params={
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": resource_link_id,
            "lis_person_sourcedid": "instructor_1",
            "lis_outcome_service_url": "fake_url",
            "user_id": "instructor_1-anon",
            "roles": ["Instructor", "Administrator"],
            "context_id": settings.TEST_COURSE,
        },
    )
    params = consumer.generate_launch_data()
    for key in params:
        print("****** LTI[{}]: {}".format(key, params[key]))

    factory = RequestFactory()
    request = factory.post(target_path, data=params)

    validator = LTIRequestValidator()
    tool_provider = DjangoToolProvider.from_django_request(request=request)
    request_is_valid = tool_provider.is_valid_request(validator)

    assert request_is_valid


def test_lti_validation_default_key_ok():
    target_path = "/some_path"
    launch_url = "http://testserver{}".format(target_path)
    resource_link_id = "some_string_to_be_the_fake_resource_link_id"
    consumer = ToolConsumer(
        consumer_key=settings.CONSUMER_KEY,
        consumer_secret=settings.LTI_SECRET,
        launch_url=launch_url,
        params={
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": resource_link_id,
            "lis_person_sourcedid": "instructor_1",
            "lis_outcome_service_url": "fake_url",
            "user_id": "instructor_1-anon",
            "roles": ["Instructor", "Administrator"],
            "context_id": "fake_course",
        },
    )
    params = consumer.generate_launch_data()
    for key in params:
        print("****** LTI[{}]: {}".format(key, params[key]))

    factory = RequestFactory()
    request = factory.post(target_path, data=params)

    validator = LTIRequestValidator()
    tool_provider = DjangoToolProvider.from_django_request(request=request)
    request_is_valid = tool_provider.is_valid_request(validator)

    assert request_is_valid


def test_lti_validation_default_key_unknown_consumer_fail():
    target_path = "/some_path"
    launch_url = "http://testserver{}".format(target_path)
    resource_link_id = "some_string_to_be_the_fake_resource_link_id"
    consumer = ToolConsumer(
        consumer_key="unknown_consumer_key",
        consumer_secret=settings.LTI_SECRET,
        launch_url=launch_url,
        params={
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": resource_link_id,
            "lis_person_sourcedid": "instructor_1",
            "lis_outcome_service_url": "fake_url",
            "user_id": "instructor_1-anon",
            "roles": ["Instructor", "Administrator"],
            "context_id": "fake_course",
        },
    )
    params = consumer.generate_launch_data()
    for key in params:
        print("****** LTI[{}]: {}".format(key, params[key]))

    factory = RequestFactory()
    request = factory.post(target_path, data=params)

    validator = LTIRequestValidator()
    tool_provider = DjangoToolProvider.from_django_request(request=request)
    request_is_valid = tool_provider.is_valid_request(validator)

    assert not request_is_valid


def test_lti_validation_ltidict_unknown_consumer_fail():
    target_path = "/some_path"
    launch_url = "http://testserver{}".format(target_path)
    resource_link_id = "some_string_to_be_the_fake_resource_link_id"
    consumer = ToolConsumer(
        consumer_key="unknown_consumer_key",
        consumer_secret=settings.TEST_COURSE_LTI_SECRET,
        launch_url=launch_url,
        params={
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": resource_link_id,
            "lis_person_sourcedid": "instructor_1",
            "lis_outcome_service_url": "fake_url",
            "user_id": "instructor_1-anon",
            "roles": ["Instructor", "Administrator"],
            "context_id": settings.TEST_COURSE,
        },
    )
    params = consumer.generate_launch_data()
    for key in params:
        print("****** LTI[{}]: {}".format(key, params[key]))

    factory = RequestFactory()
    request = factory.post(target_path, data=params)

    validator = LTIRequestValidator()
    tool_provider = DjangoToolProvider.from_django_request(request=request)
    request_is_valid = tool_provider.is_valid_request(validator)

    assert not request_is_valid


def test_lti_validation_ltidict_wrong_secret():
    target_path = "/some_path"
    launch_url = "http://testserver{}".format(target_path)
    resource_link_id = "some_string_to_be_the_fake_resource_link_id"
    consumer = ToolConsumer(
        consumer_key=settings.CONSUMER_KEY,
        consumer_secret=settings.TEST_COURSE_LTI_SECRET,
        launch_url=launch_url,
        params={
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": resource_link_id,
            "lis_person_sourcedid": "instructor_1",
            "lis_outcome_service_url": "fake_url",
            "user_id": "instructor_1-anon",
            "roles": ["Instructor", "Administrator"],
            "context_id": "wrong_course",
        },
    )
    params = consumer.generate_launch_data()
    for key in params:
        print("****** LTI[{}]: {}".format(key, params[key]))

    factory = RequestFactory()
    request = factory.post(target_path, data=params)

    validator = LTIRequestValidator()
    tool_provider = DjangoToolProvider.from_django_request(request=request)
    request_is_valid = tool_provider.is_valid_request(validator)

    assert not request_is_valid
