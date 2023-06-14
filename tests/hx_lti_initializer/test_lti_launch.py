#
# run these with pytest:
# $> DJANGO_SETTINGS_MODULE=hxat.settings.test pytest hx_lti_initializer/tests/test_launch.py  -v
#
from random import randint

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from hx_lti_initializer.forms import CourseForm
from hx_lti_initializer.models import LTICourse, LTIProfile, LTIResourceLinkConfig
from lti import ToolConsumer

old_timestamp = "1580487110"


@pytest.mark.django_db
def test_launchLti_session_ok(
    user_profile_factory,
    course_instructor_factory,
    lti_path,
    lti_launch_url,
    lti_launch_params_factory,
):
    # user and course already exists
    course, i = course_instructor_factory()
    user_roles = ["Learner"]
    user = user_profile_factory(roles=user_roles)
    resource_link_id = "some_string_to_be_the_fake_resource_link_id"
    params = lti_launch_params_factory(
        course_id=course.course_id + "xuxu",
        user_name=user.name,
        user_id=user.anon_id,
        user_roles=user_roles,
        resource_link_id=resource_link_id,
        launch_url=lti_launch_url,
    )
    client = Client(enforce_csrf_checks=False)
    response = client.post(lti_path, data=params,)

    # the course does not exist, but it should save a session
    assert response.status_code == 424
    assert "is not supported" in str(response.content, "utf-8")

    # check some info in session
    assert response.cookies.get("sessionid")
    assert client.session is not None
    assert client.session.get("LTI_LAUNCH").get(resource_link_id).get("launch_params")
    launch_params = (
        client.session.get("LTI_LAUNCH").get(resource_link_id).get("launch_params")
    )
    assert launch_params.get("resource_link_id") == resource_link_id
    assert launch_params.get("context_id") == course.course_id + "xuxu"
    assert launch_params.get("lis_person_sourcedid") == user.name
    assert launch_params.get("oauth_consumer_key") == settings.CONSUMER_KEY

    # this will not print if test successful
    for key in launch_params.keys():
        print("************ launch_params: {} = {}".format(key, launch_params.get(key)))

    for key in client.session.keys():
        print("************ SESSION: {} = {}".format(key, client.session.get(key)))

    session_lti = client.session.get("LTI_LAUNCH", None)
    assert session_lti is not None
    for key in session_lti.keys():
        print("************ session LTI: {} = {}".format(key, session_lti.get(key)))

    lti_params = session_lti[resource_link_id]
    assert lti_params is not None
    for key in lti_params.keys():
        print("************ LTI params: {} = {}".format(key, lti_params.get(key)))

    # forces error to print above messages!
    # assert(response.context == 'hey')


@pytest.mark.django_db
def test_launchLti_user_course_created_ok(
    lti_path, lti_launch_url, lti_launch_params_factory,
):
    # user and course don't exist yet
    instructor_name = "audre_lorde"
    instructor_edxid = "{}{}".format(randint(1000, 65534), randint(1000, 65534))
    user_roles = ["Administrator"]
    course_id = "hx+FancyCourse+TermCode+Year"
    resource_link_id = "some_string_to_be_the_FAKE_resource_link_id"

    params = lti_launch_params_factory(
        course_id=course_id,
        user_name=instructor_name,
        user_id=instructor_edxid,
        user_roles=user_roles,
        resource_link_id=resource_link_id,
        launch_url=lti_launch_url,
        course_name="{}+title".format(course_id),
    )

    client = Client(enforce_csrf_checks=False)
    response = client.post(lti_path, data=params,)
    assert response.status_code == 302
    assert response.cookies.get("sessionid")
    expected_url = (
        reverse("hx_lti_initializer:course_admin_hub")
        + f"?resource_link_id={resource_link_id}"
        + f"&utm_source={client.session.session_key}"
    )
    assert response.url == expected_url

    # check user was created
    user = User.objects.get(username=instructor_name)
    assert user is not None
    lti_profile = LTIProfile.objects.get(anon_id=instructor_edxid)
    assert lti_profile is not None
    assert lti_profile.user.username == user.username
    # scope is course
    assert lti_profile.scope == "course:{}".format(course_id)

    # check course was created
    course = LTICourse.get_course_by_id(course_id)
    assert course is not None
    assert len(LTICourse.get_all_courses()) == 1
    assert course.course_admins.all()[0].anon_id == instructor_edxid
    assert course.course_name == "{}+title".format(course_id)


@pytest.mark.django_db
def test_launchLti_user_scope_canvas_created_ok(
    lti_path, lti_launch_url, lti_launch_params_factory,
):
    # have to set PLATFORM to canvas
    original_platform = settings.PLATFORM
    settings.PLATFORM = "canvas"

    # user and course don't exist yet
    instructor_name = "audre_lorde"
    instructor_edxid = "{}{}".format(randint(1000, 65534), randint(1000, 65534))
    user_roles = ["Administrator"]
    course_id = "hx+FancyCourse+TermCode+Year"
    resource_link_id = "some_string_to_be_the_FAKE_resource_link_id"
    tool_consumer_instance_guid = "canvas"

    params = lti_launch_params_factory(
        course_id=course_id,
        user_name=instructor_name,
        user_id=instructor_edxid,
        user_roles=user_roles,
        resource_link_id=resource_link_id,
        launch_url=lti_launch_url,
        course_name="{}+title".format(course_id),
        tool_consumer_instance_guid=tool_consumer_instance_guid,
    )

    client = Client(enforce_csrf_checks=False)
    response = client.post(lti_path, data=params,)
    assert response.status_code == 302
    assert response.cookies.get("sessionid")
    expected_url = (
        reverse("hx_lti_initializer:course_admin_hub")
        + f"?resource_link_id={resource_link_id}"
        + f"&utm_source={client.session.session_key}"
    )
    assert response.url == expected_url

    # check user was created
    user = User.objects.get(username=instructor_name)
    assert user is not None
    lti_profile = LTIProfile.objects.get(anon_id=instructor_edxid)
    assert lti_profile is not None
    assert lti_profile.user.username == user.username
    # scope is consumer
    assert lti_profile.scope == "consumer:{}".format(tool_consumer_instance_guid)

    # restore platform
    settings.PLATFORM = original_platform


@pytest.mark.django_db
def test_launchLti_user_scope_canvas_no_platform_created_ok(
    lti_path, lti_launch_url, lti_launch_params_factory,
):
    # have to set ORGANIZATION to something else than HARVARDX
    settings.ORGANIZATION = "ATG"

    # user and course don't exist yet
    instructor_name = "audre_lorde"
    instructor_edxid = "{}{}".format(randint(1000, 65534), randint(1000, 65534))
    user_roles = ["Administrator"]
    course_id = "hx+FancyCourse+TermCode+Year"
    resource_link_id = "some_string_to_be_the_FAKE_resource_link_id"

    params = lti_launch_params_factory(
        course_id=course_id,
        user_name=instructor_name,
        user_id=instructor_edxid,
        user_roles=user_roles,
        resource_link_id=resource_link_id,
        launch_url=lti_launch_url,
        course_name="{}+title".format(course_id),
    )

    client = Client(enforce_csrf_checks=False)
    response = client.post(lti_path, data=params,)
    assert response.status_code == 302
    assert response.cookies.get("sessionid")
    expected_url = (
        reverse("hx_lti_initializer:course_admin_hub")
        + f"?resource_link_id={resource_link_id}"
        + f"&utm_source={client.session.session_key}"
    )
    assert response.url == expected_url

    # check user was created
    user = User.objects.get(username=instructor_name)
    assert user is not None
    lti_profile = LTIProfile.objects.get(anon_id=instructor_edxid)
    assert lti_profile is not None
    assert lti_profile.user.username == user.username
    # scope is course
    assert lti_profile.scope == "course:{}".format(course_id)

    # check course was created
    course = LTICourse.get_course_by_id(course_id)
    assert course is not None
    assert len(LTICourse.get_all_courses()) == 1
    assert course.course_admins.all()[0].anon_id == instructor_edxid
    assert course.course_name == "{}+title".format(course_id)


@pytest.mark.django_db
def test_launchLti_user_course_ok_no_context_title(
    lti_path, lti_launch_url, lti_launch_params_factory,
):
    # user and course don't exist yet
    instructor_name = "sylvia_plath"
    instructor_edxid = "{}{}".format(randint(1000, 65534), randint(1000, 65534))
    user_roles = ["Administrator"]
    course_id = "hx+FANcyCourse+TermCode+Year"
    resource_link_id = "some_string_to_BE_THE_fake_resource_link_id"

    params = lti_launch_params_factory(
        course_id=course_id,
        user_name=instructor_name,
        user_id=instructor_edxid,
        user_roles=user_roles,
        resource_link_id=resource_link_id,
        launch_url=lti_launch_url,
        # 04feb20 naomi: context_title has to do with edx studio not
        # sending user_id in launch params to create course user.
        # course_name='{}+title'.format(course_id),
    )

    client = Client(enforce_csrf_checks=False)
    response = client.post(lti_path, data=params,)
    assert response.status_code == 302
    assert response.cookies.get("sessionid")
    expected_url = (
        reverse("hx_lti_initializer:course_admin_hub")
        + f"?resource_link_id={resource_link_id}"
        + f"&utm_source={client.session.session_key}"
    )
    assert response.url == expected_url

    # check user was created
    user = User.objects.get(username=instructor_name)
    assert user is not None
    lti_profile = LTIProfile.objects.get(anon_id=instructor_edxid)
    assert lti_profile is not None
    assert lti_profile.user.username == user.username

    # check course was created
    course = LTICourse.get_course_by_id(course_id)
    assert course is not None
    assert len(LTICourse.get_all_courses()) == 1
    assert course.course_admins.all()[0].anon_id == instructor_edxid
    assert course.course_name.startswith("changeme-")


@pytest.mark.django_db
def test_launchLti_expired_timestamp(
    lti_path, lti_launch_url, lti_launch_params_factory,
):
    # user and course don't exist yet
    instructor_name = "sylvia_plath"
    instructor_edxid = "{}{}".format(randint(1000, 65534), randint(1000, 65534))
    user_roles = ["Administrator"]
    course_id = "hx+fancyCOURSE+TermCode+Year"
    resource_link_id = "some_STRING_to_be_the_fake_resource_link_id"

    params = lti_launch_params_factory(
        course_id=course_id,
        user_name=instructor_name,
        user_id=instructor_edxid,
        user_roles=user_roles,
        resource_link_id=resource_link_id,
        launch_url=lti_launch_url,
    )
    # replace for old timestamp
    params["oauth_timestamp"] = old_timestamp

    client = Client(enforce_csrf_checks=False)
    response = client.post(lti_path, data=params,)
    assert response.status_code == 403

    # check user was NOT created
    with pytest.raises(User.DoesNotExist) as e:
        user = User.objects.get(username=instructor_name)
    assert "does not exist" in str(e.value)

    # check course was created
    with pytest.raises(LTICourse.DoesNotExist) as e:
        course = LTICourse.get_course_by_id(course_id)
    assert "does not exist" in str(e.value)


@pytest.mark.django_db
def test_launchLti_unknown_consumer(
    lti_path, lti_launch_url, course_user_lti_launch_params
):
    course, user, launch_params = course_user_lti_launch_params

    # replace consumer
    launch_params["oauth_consumer_key"] = "unknown_consumer"
    client = Client(enforce_csrf_checks=False)
    response = client.post(lti_path, data=launch_params,)
    assert response.status_code == 403


@pytest.mark.django_db
def test_launchLti_missing_context_id(
    lti_path, lti_launch_url, course_user_lti_launch_params
):
    course, user, launch_params = course_user_lti_launch_params

    # delete context_id
    del launch_params["context_id"]
    client = Client(enforce_csrf_checks=False)
    response = client.post(lti_path, data=launch_params,)
    assert response.status_code == 403


@pytest.mark.django_db
def test_launchLti_missing_required_param(
    lti_path, lti_launch_url, course_instructor_factory,
):
    course, user = course_instructor_factory()
    consumer = ToolConsumer(
        consumer_key=settings.CONSUMER_KEY,
        consumer_secret=settings.LTI_SECRET,
        launch_url=lti_launch_url,
        params={
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": "FakeResourceLinkID",
            # for hxat lis_person_sourcedid is required!
            #'lis_person_sourcedid': user.name,
            "lis_outcome_service_url": "fake_url",
            "user_id": user.anon_id,
            "roles": ["Instructor"],
            "context_id": course.course_id,
        },
    )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(lti_path, data=params,)
    assert response.status_code == 424


@pytest.mark.django_db
def test_launchLti_from_LTIdict_ok(
    lti_path, lti_launch_url, course_instructor_factory,
):
    course, user = course_instructor_factory()
    course.course_id = settings.TEST_COURSE  # force context_id
    resource_link_id = "FakeResourceLinkID"
    consumer = ToolConsumer(
        consumer_key=settings.CONSUMER_KEY,
        consumer_secret=settings.TEST_COURSE_LTI_SECRET,
        launch_url=lti_launch_url,
        params={
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": resource_link_id,
            "lis_person_sourcedid": user.name,
            "lis_outcome_service_url": "fake_url",
            "user_id": user.anon_id,
            "roles": ["Instructor"],
            "context_id": course.course_id,
        },
    )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(lti_path, data=params,)
    assert response.status_code == 302
    expected_url = (
        reverse("hx_lti_initializer:course_admin_hub")
        + f"?resource_link_id={resource_link_id}"
        + f"&utm_source={client.session.session_key}"
    )
    assert response.url == expected_url


@pytest.mark.django_db
def test_launchLti_from_LTIdict_unknown_consumer(
    lti_path, lti_launch_url, course_instructor_factory,
):
    course, user = course_instructor_factory()
    course.course_id = settings.TEST_COURSE  # force context_id
    consumer = ToolConsumer(
        consumer_key="unknown_consumer",
        consumer_secret=settings.TEST_COURSE_LTI_SECRET,
        launch_url=lti_launch_url,
        params={
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": "FakeResourceLinkID",
            "lis_person_sourcedid": user.name,
            "lis_outcome_service_url": "fake_url",
            "user_id": user.anon_id,
            "roles": ["Instructor"],
            "context_id": course.course_id,
        },
    )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(lti_path, data=params,)
    assert response.status_code == 403


@pytest.mark.django_db
def test_launchLti_from_LTIdict_wrong_secret(
    lti_path, lti_launch_url, course_instructor_factory,
):
    course, user = course_instructor_factory()
    consumer = ToolConsumer(
        consumer_key=settings.CONSUMER_KEY,
        consumer_secret=settings.TEST_COURSE_LTI_SECRET,
        launch_url=lti_launch_url,
        params={
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": "FakeResourceLinkID",
            "lis_person_sourcedid": user.name,
            "lis_outcome_service_url": "fake_url",
            "user_id": user.anon_id,
            "roles": ["Instructor"],
            "context_id": course.course_id,
        },
    )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(lti_path, data=params,)
    assert response.status_code == 403


#
# TODO: not able to force a query string using django.test.Client
# debug messages in oauthlib/oauth1/rfc5849/signature.py:verify_hmac_sha1()
# prints request.uri with clear query strings...
#
@pytest.mark.skip
@pytest.mark.django_db
def test_launchLti_with_query_string(random_course_instructor):
    instructor = random_course_instructor["profile"]
    course = random_course_instructor["course"]
    target_path = "/lti_init/launch_lti/"
    launch_url = "http://testserver{}?extra_param=blah&more_args=bloft".format(
        target_path
    )
    print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm launch_url: {}".format(launch_url))
    consumer = ToolConsumer(
        consumer_key=settings.CONSUMER_KEY,
        consumer_secret=settings.LTI_SECRET,
        launch_url=launch_url,
        params={
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": "FakeResourceLinkID",
            "lis_person_sourcedid": instructor.name,
            "lis_outcome_service_url": "fake_url",
            "user_id": instructor.anon_id,
            "roles": ["Instructor"],
            "context_id": course.course_id,
        },
    )
    params = consumer.generate_launch_data()
    print("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm lti params: {}".format(params))

    client = Client(enforce_csrf_checks=False)
    response = client.post(target_path, data=params,)

    print(
        "mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm response content: {}".format(
            response.content
        )
    )
    assert response.status_code == 403
    assert response.content == "hey"


@pytest.mark.skip
@pytest.mark.django_db
def test_launchLti(random_course_instructor):
    instructor = random_course_instructor["profile"]
    course = random_course_instructor["course"]
    target_path = "/lti_init/launch_lti/"
    launch_url = "http://testserver{}".format(target_path)
    consumer = ToolConsumer(
        consumer_key=settings.CONSUMER_KEY,
        consumer_secret=settings.LTI_SECRET,
        launch_url=launch_url,
        params={
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": "FakeResourceLinkID",
            "lis_person_sourcedid": instructor.name,
            "lis_outcome_service_url": "fake_url",
            "user_id": instructor.anon_id,
            "roles": ["Instructor"],
            "context_id": course.course_id,
        },
    )
    params = consumer.generate_launch_data()
    # req = consumer.generate_launch_request()

    client = Client(enforce_csrf_checks=False)
    response = client.post(target_path, data=params,)

    assert response.status_code == 403
    assert response.content == "hey"


@pytest.mark.django_db
def test_launchLti_starting_resource(random_assignment_target):
    course = random_assignment_target["course"]
    assignment = random_assignment_target["assignment"]
    target_object = random_assignment_target["target_object"]
    assignment_target = random_assignment_target["assignment_target"]
    instructor = random_assignment_target["profile"]

    course_id = course.course_id
    resource_link_id = "FakeResourceLinkIDStartingResource"
    target_path = "/lti_init/launch_lti/"
    launch_url = "http://testserver{}".format(target_path)

    lti_resource_link_config = LTIResourceLinkConfig.objects.create(
        resource_link_id=resource_link_id, assignment_target=assignment_target,
    )

    consumer = ToolConsumer(
        consumer_key=settings.CONSUMER_KEY,
        consumer_secret=settings.LTI_SECRET,
        launch_url=launch_url,
        params={
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "resource_link_id": resource_link_id,
            "lis_person_sourcedid": instructor.name,
            "lis_outcome_service_url": "fake_url",
            "user_id": instructor.anon_id,
            "roles": ["Instructor"],
            "context_id": course_id,
            "context_title": "{}-title".format(course_id),
        },
    )
    params = consumer.generate_launch_data()

    client = Client(enforce_csrf_checks=False)
    response = client.post(target_path, data=params,)
    assert response.status_code == 302
    expected_url = (
        reverse(
            "hx_lti_initializer:access_annotation_target",
            args=[course_id, assignment.assignment_id, target_object.pk],
        )
        + f"?resource_link_id={resource_link_id}"
        + f"&utm_source={client.session.session_key}"
    )
    assert response.url == expected_url


class LTIInitializerCourseFormTests(TestCase):
    def setUp(self):
        # Create users
        users = []
        profiles = []
        names = (
            "Sally Singer",
            "Bob Brown",
            "Jimmy Kim",
            "Jimmy Jam",
        )  # intentionally unordered
        for name in names:
            first, last = name.split(" ")
            username = name.replace(" ", "").lower()
            user = User(
                username=username,
                first_name=first,
                last_name=last,
                email="%s@localhost" % username,
            )
            user.save()
            users.append(user)
            profiles.append(LTIProfile.objects.create(user=user))

        # Create course with admins
        course = LTICourse(course_id=1)
        course.save()
        for profile in profiles:
            course.add_admin(profile)

        # Add instance reference to course and form
        self.course_admins = profiles
        self.course = course
        self.course_form = CourseForm(instance=course)

    def tearDown(self):
        LTIProfile.objects.filter(pk__in=[p.pk for p in self.course_admins]).delete()
        self.course.delete()

    def test_course_form_admins(self):
        queryset = self.course_form.get_course_admins().all()

        expected_names = sorted(
            [
                (profile.user.first_name, profile.user.last_name)
                for profile in self.course_admins
            ],
            key=lambda user: user[0] + user[1],
        )
        # actual_names = sorted([(profile.user.first_name, profile.user.last_name) for profile in queryset], key=lambda user: user[0] + user[1])
        actual_names = [
            (profile.user.first_name, profile.user.last_name) for profile in queryset
        ]

        self.assertEqual(len(expected_names), len(actual_names))
        self.assertEqual(expected_names, actual_names)
