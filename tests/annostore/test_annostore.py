import json
from urllib.parse import quote

import annostore.views as annostore_views
import pytest
import responses
from annostore.store import AnnostoreFactory
from django.conf import settings
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import Client, RequestFactory
from django.urls import reverse
from hx_lti_initializer.models import LTIResourceLinkConfig
from hxat.middleware import CookielessSessionMiddleware, MultiLTILaunchMiddleware

other_ascfg = ("http://test.assign.com/assign", "apikey-assign", "secret-assign")
default_ascfg = (
    settings.ANNOTATION_DB_URL,
    settings.ANNOTATION_DB_API_KEY,
    settings.ANNOTATION_DB_SECRET_TOKEN,
)


@responses.activate
@pytest.mark.django_db
@pytest.mark.parametrize(
    "set_ascfg, multi_assign_search",
    [
        pytest.param(True, True),
        pytest.param(True, False),
        pytest.param(False, True),
        pytest.param(False, False),
    ],
)
def test_asconfig(
    set_ascfg,
    multi_assign_search,
    lti_path,
    lti_launch_url,
    course_user_lti_launch_params,
    assignment_target_factory,
    webannotation_annotation_factory,
    catchpy_search_result_shell,
):
    # 1. create course, assignment, target_object, user
    course, user, launch_params = course_user_lti_launch_params
    assignment_target = assignment_target_factory(course)
    target_object = assignment_target.target_object
    assignment = assignment_target.assignment

    if set_ascfg:
        assignment.annotation_database_url = other_ascfg[0]
        assignment.annotation_database_apikey = other_ascfg[1]
        assignment.annotation_database_secret_token = other_ascfg[2]
    assignment.save()

    # 2. set starting resource
    resource_link_id = launch_params["resource_link_id"]
    resource_config = LTIResourceLinkConfig.objects.create(
        resource_link_id=resource_link_id,
        assignment_target=assignment_target,
    )

    # 3. lti launch
    client = Client(enforce_csrf_checks=False)
    response = client.post(
        lti_path,
        data=launch_params,
    )
    assert response.status_code == 302
    assert response.cookies.get("sessionid")
    expected_url = (
        reverse(
            "hx_lti_initializer:access_annotation_target",
            args=[course.course_id, assignment.assignment_id, target_object.pk],
        )
        + f"?resource_link_id={resource_link_id}"
        + f"&utm_source={client.session.session_key}"
    )
    assert response.url == expected_url

    # 4. access target object to be able to create annotations on it
    #    this is required after live-updates implementation!
    #    and to guarantee that all info about an assignment are stashed in session
    response = client.get(expected_url)
    assert (response.status_code) == 200

    # setup search request
    path = reverse("annotation_store:api_root_search")
    params = {
        "context_id": course.course_id,
        "source_id": target_object.id,
        "userid": user.anon_id,
        "utm_source": client.session.session_key,
        "resource_link_id": resource_link_id,
    }
    if not multi_assign_search:
        params["collection_id"] = assignment.assignment_id

    request_factory = RequestFactory()
    search_request = request_factory.get(path, data=params)

    for mware in [  # go through all relevant middleware
        SessionMiddleware,
        CookielessSessionMiddleware,
        AuthenticationMiddleware,
        MultiLTILaunchMiddleware,
    ]:
        m = mware(get_response=lambda request: request)
        m.process_request(search_request)

    annostore = AnnostoreFactory.get_instance(search_request)
    if multi_assign_search:
        assert annostore.asconfig == default_ascfg
    else:
        if set_ascfg:
            assert annostore.asconfig == other_ascfg
        else:
            assert annostore.asconfig == default_ascfg


@responses.activate
@pytest.mark.django_db
@pytest.mark.parametrize(
    "set_ascfg, operation",
    [
        pytest.param(True, "create"),
        pytest.param(True, "read"),
        pytest.param(True, "update"),
        pytest.param(True, "delete"),
        pytest.param(True, "search"),
        pytest.param(False, "create"),
        pytest.param(False, "read"),
        pytest.param(False, "update"),
        pytest.param(False, "delete"),
        pytest.param(False, "search"),
    ],
)
def test_api_ok(
    set_ascfg,
    operation,
    lti_path,
    lti_launch_url,
    course_user_lti_launch_params,
    assignment_target_factory,
    webannotation_annotation_factory,
    catchpy_search_result_shell,
):
    # 1. create course, assignment, target_object, user
    course, user, launch_params = course_user_lti_launch_params
    assignment_target = assignment_target_factory(course)
    target_object = assignment_target.target_object
    assignment = assignment_target.assignment

    if set_ascfg:
        assignment.annotation_database_url = other_ascfg[0]
        assignment.annotation_database_apikey = other_ascfg[1]
        assignment.annotation_database_secret_token = other_ascfg[2]
    assignment.save()

    # 2. set starting resource
    resource_link_id = launch_params["resource_link_id"]
    resource_config = LTIResourceLinkConfig.objects.create(
        resource_link_id=resource_link_id,
        assignment_target=assignment_target,
    )

    # 3. lti launch
    client = Client(enforce_csrf_checks=False)
    response = client.post(
        lti_path,
        data=launch_params,
    )
    assert response.status_code == 302
    assert response.cookies.get("sessionid")
    expected_url = (
        reverse(
            "hx_lti_initializer:access_annotation_target",
            args=[course.course_id, assignment.assignment_id, target_object.pk],
        )
        + f"?resource_link_id={resource_link_id}"
        + f"&utm_source={client.session.session_key}"
    )
    assert response.url == expected_url

    # 4. access target object to be able to create annotations on it
    #    this is required after live-updates implementation!
    #    and to guarantee that all info about an assignment are stashed in session
    response = client.get(expected_url)
    assert (response.status_code) == 200

    # set responses to assert
    webann = webannotation_annotation_factory(user)
    webann["platform"]["collection_id"] = str(assignment.assignment_id)
    webann["platform"]["context_id"] = str(course.course_id)
    webann_id = webann["id"]
    search_result = catchpy_search_result_shell
    search_result["total"] = 1
    search_result["size"] = 1
    search_result["rows"].append(webann)

    annostore_urls = {}
    annostore_url = assignment.annotation_database_url

    for op in ["search"]:
        annostore_urls[
            op
        ] = "{}/?context_id={}&collection_id={}&resource_link_id={}".format(
            annostore_url,
            quote(course.course_id),
            quote(str(assignment.assignment_id)),
            resource_link_id,
        )
    for op in ["create", "update", "delete", "read"]:
        annostore_urls[op] = "{}/{}".format(annostore_url, webann_id)

    responses.add(
        responses.POST,
        annostore_urls["create"],
        json=webann,
        status=200,
    )
    responses.add(
        responses.PUT,
        annostore_urls["update"],
        json=webann,
        status=200,
    )
    responses.add(
        responses.DELETE,
        annostore_urls["delete"],
        json=webann,
        status=200,
    )
    responses.add(
        responses.GET,
        annostore_urls["read"],
        json=webann,
        status=200,
    )
    responses.add(
        responses.GET,
        annostore_urls["search"],
        json=search_result,
        status=200,
    )

    path = reverse("annotation_store:api_root_search")
    path_with_id = "{}{}?resource_link_id={}".format(
        reverse("annotation_store:api_root"), webann_id, resource_link_id
    )

    # search request
    # needs resource_link_id to access LTI params
    if operation == "search":
        response = client.get(
            "{}?context_id={}&collection_id={}&resource_link_id={}".format(
                path,
                quote(course.course_id),
                quote(str(assignment.assignment_id)),
                resource_link_id,
            ),
            HTTP_AUTHORIZATION="token hohoho",
        )
        assert response.status_code == 200
        print(response.content)

        content = json.loads(response.content.decode())
        assert len(responses.calls) == 1
        assert content == search_result

    # create request
    elif operation == "create":
        response = client.post(
            "{}/{}?resource_link_id={}".format(path, webann_id, resource_link_id),
            data=webann,
            content_type="application/json",
            HTTP_AUTHORIZATION="token hehehe",
        )
        assert response.status_code == 200
        content = json.loads(response.content.decode())
        assert len(responses.calls) == 1
        assert content == webann

    # update request
    elif operation == "update":
        response = client.put(
            path_with_id,
            data=webann,
            content_type="application/json",
            HTTP_AUTHORIZATION="token hihihi",
        )
        assert response.status_code == 200

        content = json.loads(response.content.decode())
        assert len(responses.calls) == 1
        assert content == webann

    # delete request
    elif operation == "delete":
        response = client.delete(
            path_with_id,
            HTTP_AUTHORIZATION="token hohoho",
        )
        assert response.status_code == 200
        content = json.loads(response.content.decode())
        assert len(responses.calls) == 1
        assert content == webann

    # read request
    elif operation == "read":
        response = client.get(
            path_with_id,
            HTTP_AUTHORIZATION="token huhuhu",
        )
        # read not supported; but fail as a search without context_id
        assert response.status_code == 400
        # don't even call annostore, so counter doesn't move
        assert len(responses.calls) == 0


@responses.activate
@pytest.mark.django_db
@pytest.mark.parametrize(
    "operation",
    [
        pytest.param("create"),
        pytest.param("update"),
        pytest.param("search"),
    ],
)
def test_api_grade_ok(
    operation,
    lti_path,
    lti_launch_url,
    course_user_lti_launch_params_with_grade,
    assignment_target_factory,
    webannotation_annotation_factory,
    catchpy_search_result_shell,
    make_lti_replaceResultResponse,
):
    """
    sends lis_outcome_service_url, lis_result_sourcedid to signal that lti
    consumer expects a grade
    """

    # 1. create course, assignment, target_object, user
    course, user, launch_params = course_user_lti_launch_params_with_grade
    assignment_target = assignment_target_factory(course)
    target_object = assignment_target.target_object
    assignment = assignment_target.assignment
    # get outcome_resource_url
    lis_outcome_service_url = launch_params["lis_outcome_service_url"]

    # 2. set starting resource
    resource_link_id = launch_params["resource_link_id"]
    resource_config = LTIResourceLinkConfig.objects.create(
        resource_link_id=resource_link_id,
        assignment_target=assignment_target,
    )

    print("---------------- resource_config({})".format(resource_config))

    # 3. lti launch
    client = Client(enforce_csrf_checks=False)
    response = client.post(
        lti_path,
        data=launch_params,
    )
    assert response.status_code == 302
    assert response.cookies.get("sessionid")
    expected_url = (
        reverse(
            "hx_lti_initializer:access_annotation_target",
            args=[course.course_id, assignment.assignment_id, target_object.pk],
        )
        + f"?resource_link_id={resource_link_id}"
        + f"&utm_source={client.session.session_key}"
    )
    assert response.url == expected_url

    # 4. access target object to be able to create annotations on it
    #    this is required after live-updates implementation!
    #    and to guarantee that all info about an assignment are stashed in session
    response = client.get(expected_url)
    assert (response.status_code) == 200

    # set responses to assert
    webann = webannotation_annotation_factory(user)
    webann["platform"]["collection_id"] = str(assignment.assignment_id)
    webann["platform"]["context_id"] = str(course.course_id)
    webann_id = webann["id"]
    search_result = catchpy_search_result_shell
    search_result["total"] = 1
    search_result["size"] = 1
    search_result["rows"].append(webann)

    annotation_store_urls = {}
    for op in ["search"]:  # search preserve params request to hxat
        annotation_store_urls[
            op
        ] = "{}/?context_id={}&resource_link_id={}&userid={}".format(
            assignment.annotation_database_url,
            quote(course.course_id),
            resource_link_id,
            user.anon_id,
        )
    for op in ["create", "update", "delete"]:
        annotation_store_urls[op] = "{}/{}".format(
            assignment.annotation_database_url,
            webann_id,
        )

    responses.add(
        responses.POST,
        annotation_store_urls["create"],
        json=webann,
        status=200,
    )
    responses.add(
        responses.PUT,
        annotation_store_urls["update"],
        json=webann,
        status=200,
    )
    responses.add(
        responses.DELETE,
        annotation_store_urls["delete"],
        json=webann,
        status=200,
    )
    responses.add(
        responses.GET,
        annotation_store_urls["search"],
        json=search_result,
        status=200,
    )

    replace_result_response = make_lti_replaceResultResponse
    responses.add(
        responses.POST,
        lis_outcome_service_url,
        body=replace_result_response,
        content_type="application/xml",
        status=200,
    )

    path = reverse("annotation_store:api_root_search")
    path_with_id = "{}{}?resource_link_id={}".format(
        reverse("annotation_store:api_root"), webann_id, resource_link_id
    )

    # create request
    if operation == "create":
        response = client.post(
            path_with_id,
            data=webann,
            content_type="application/json",
            HTTP_AUTHORIZATION="token hahaha",
        )
        assert response.status_code == 200
        content = json.loads(response.content.decode())
        assert len(responses.calls) == 2
        assert content == webann

    # search request
    # needs resource_link_id to access LTI params for pass_grade
    elif operation == "search":
        response = client.get(
            "{}?context_id={}&resource_link_id={}&userid={}".format(
                path, quote(course.course_id), resource_link_id, user.anon_id
            ),
            HTTP_AUTHORIZATION="token hohoho",
        )
        assert response.status_code == 200
        content = json.loads(response.content.decode())
        assert len(responses.calls) == 2
        assert content == search_result

    # update request
    elif operation == "update":
        response = client.put(
            path_with_id,
            data=webann,
            content_type="application/json",
            HTTP_AUTHORIZATION="token hehehe",
        )
        assert response.status_code == 200
        content = json.loads(response.content.decode())
        assert len(responses.calls) == 1  # does not issue a grade-passback
        assert content == webann


@responses.activate
@pytest.mark.django_db
def test_api_grade_me(
    lti_path,
    lti_launch_url,
    course_user_lti_launch_params_with_grade,
    assignment_target_factory,
    webannotation_annotation_factory,
    catchpy_search_result_shell,
    make_lti_replaceResultResponse,
):
    """
    sends lis_outcome_service_url, lis_result_sourcedid to signal that lti
    consumer expects a grade
    """
    # 1. create course, assignment, target_object, user
    course, user, launch_params = course_user_lti_launch_params_with_grade
    assignment_target = assignment_target_factory(course)
    target_object = assignment_target.target_object
    assignment = assignment_target.assignment
    # get outcome_resource_url
    lis_outcome_service_url = launch_params["lis_outcome_service_url"]

    # 2. set starting resource
    resource_link_id = launch_params["resource_link_id"]
    resource_config = LTIResourceLinkConfig.objects.create(
        resource_link_id=resource_link_id,
        assignment_target=assignment_target,
    )

    # 3. lti launch
    client = Client(enforce_csrf_checks=False)
    response = client.post(
        lti_path,
        data=launch_params,
    )
    assert response.status_code == 302
    assert response.cookies.get("sessionid")
    expected_url = (
        reverse(
            "hx_lti_initializer:access_annotation_target",
            args=[course.course_id, assignment.assignment_id, target_object.pk],
        )
        + f"?resource_link_id={resource_link_id}"
        + f"&utm_source={client.session.session_key}"
    )
    assert response.url == expected_url

    # 4. access target object to be able to create annotations on it
    #    this is required after live-updates implementation!
    #    and to guarantee that all info about an assignment are stashed in session
    response = client.get(expected_url)
    assert (response.status_code) == 200

    # set responses to assert
    webann = webannotation_annotation_factory(user)
    webann["creator"]["id"] = user.anon_id
    webann["platform"]["collection_id"] = str(assignment.assignment_id)
    webann["platform"]["context_id"] = str(course.course_id)
    webann_id = webann["id"]
    search_result = catchpy_search_result_shell
    search_result["total"] = 1
    search_result["size"] = 1
    search_result["rows"].append(webann)

    annotation_store_urls = {}
    for op in ["search"]:  # search preserve params request to hxat
        annotation_store_urls[
            op
        ] = "{}/?collection_id={}&context_id={}&source_id={}&userid={}&utm_source={}&resource_link_id={}".format(
            assignment.annotation_database_url,
            assignment.assignment_id,
            quote(course.course_id),
            target_object.pk,
            user.anon_id,
            client.session.session_key,
            resource_link_id,
        )
    responses.add(
        responses.GET,
        annotation_store_urls["search"],
        json=search_result,
        status=200,
    )

    replace_result_response = make_lti_replaceResultResponse
    responses.add(
        responses.POST,
        lis_outcome_service_url,
        body=replace_result_response,
        content_type="application/xml",
        status=200,
    )

    path = reverse("annotation_store:api_grade_me")

    # needs resource_link_id to access LTI params for pass_grade
    response = client.get(
        "{}?resource_link_id={}&utm_source={}".format(
            path, resource_link_id, client.session.session_key
        )
    )
    assert response.status_code == 200
    assert len(responses.calls) == 3  # 2 grade_passback, 1 search
    resp_content = json.loads(response.content)
    assert resp_content["grade_request_sent"] is True


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status_code, msg_pattern",
    [
        pytest.param(200, None),
        pytest.param(200, "no annotations to be transferred"),
        pytest.param(401, "not admin to transfer"),
        pytest.param(401, "target context_id expected"),
        pytest.param(409, "conflict from qs"),
        pytest.param(409, "expected source assignment"),
        pytest.param(409, "expected same annostore"),
    ],
)
def test_verify_transfer_params(
    status_code,
    msg_pattern,
    lti_path,
    lti_launch_url,
    course_user_lti_launch_params_factory,
    assignment_target_factory,
):
    # to restore settings
    restore_platform = None

    # 1. create course, assignment, target_object, user
    (
        source_course,
        source_user,
        source_launch_params,
    ) = course_user_lti_launch_params_factory()
    source_assignment_target = assignment_target_factory(source_course)
    source_target_object = source_assignment_target.target_object
    source_assignment = source_assignment_target.assignment
    second_source_assignment_target = assignment_target_factory(source_course)
    second_source_assignment = second_source_assignment_target.assignment

    if 401 == status_code and "not admin to transfer" == msg_pattern:
        # canvas allow learners to access index/dashboard
        restore_platform = settings.PLATFORM
        settings.PLATFORM = "canvas"
        is_staff = False
    else:
        is_staff = True
    (
        target_course,
        target_user,
        target_launch_params,
    ) = course_user_lti_launch_params_factory(is_staff=is_staff)
    target_assignment_target = assignment_target_factory(target_course)
    target_target_object = target_assignment_target.target_object
    target_assignment = target_assignment_target.assignment
    if 409 == status_code and "expected same annostore" == msg_pattern:
        target_assignment.annotation_store_url = other_ascfg[0]

    # 3. lti launch
    client = Client(enforce_csrf_checks=False)
    response = client.post(
        lti_path,
        data=target_launch_params,
    )
    assert response.status_code == 302
    assert response.cookies.get("sessionid")
    # hub admin because no starting target object
    expected_url = (
        reverse("hx_lti_initializer:course_admin_hub")
        + f"?resource_link_id={target_launch_params['resource_link_id']}"
        + f"&utm_source={client.session.session_key}"
    )
    assert response.url == expected_url

    # params for conflict errors
    if (409 == status_code) and (
        "conflict from qs" == msg_pattern or "expected source assignment" == msg_pattern
    ):
        old_assignment_id = str(second_source_assignment.assignment_id)
    else:
        old_assignment_id = str(source_assignment.assignment_id)
    # params for permission errors
    if (401 == status_code) and "target context_id expected" == msg_pattern:
        new_course_id = source_course.course_id
    else:
        new_course_id = target_course.course_id
    params = {
        "old_course_id": source_course.course_id,
        "new_course_id": new_course_id,
        "old_assignment_id": old_assignment_id,
        "new_assignment_id": str(target_assignment.assignment_id),
    }

    if 200 == status_code and "no annotations to be transferred" == msg_pattern:
        # delete admins from source course to force nothing to be transferred
        source_course.course_admins.all().delete()

    # transfer request
    path = reverse(
        "annotation_store:api_transfer_annotations",
        args=[
            str(source_assignment.assignment_id)
            if 409 == status_code and "conflict from qs" == msg_pattern
            else old_assignment_id
        ],
    ) + "?resource_link_id={}&utm_source={}".format(
        target_launch_params["resource_link_id"], client.session.session_key
    )

    request_factory = RequestFactory()
    transfer_request = request_factory.post(path, data=params)

    for mware in [  # go through all relevant middleware
        SessionMiddleware,
        CookielessSessionMiddleware,
        AuthenticationMiddleware,
        MultiLTILaunchMiddleware,
    ]:
        m = mware(get_response=lambda request: request)
        m.process_request(transfer_request)

    """
    annostore = AnnostoreFactory.get_instance(
        transfer_request, col_id=old_assignment_id
    )
    assert annostore.asconfig == default_ascfg
    """

    verified_params = annostore_views._verify_transfer_params(
        transfer_request, old_assignment_id
    )

    print("****************************** verified_params({})".format(verified_params))
    if verified_params.get("status", None):
        assert verified_params["status"] == status_code
        assert msg_pattern in verified_params["payload"][0]
    else:
        assert verified_params["source_context_id"] == source_course.course_id
        assert verified_params["source_collection_id"] == str(old_assignment_id)
        assert verified_params["target_context_id"] == target_course.course_id
        assert verified_params["target_collection_id"] == str(
            target_assignment.assignment_id
        )
        assert len(verified_params["userid_map"]) == 1
        assert (
            verified_params["userid_map"][source_course.course_admins.all()[0].anon_id]
            == target_course.course_admins.all()[0].anon_id
        )

    # cleanup
    if restore_platform:
        settings.PLATFORM = restore_platform
