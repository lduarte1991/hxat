import json
from urllib.parse import quote

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
    path = reverse("annotation_store:api_root_prefix")
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
    "set_ascfg",
    [
        pytest.param(True),
        pytest.param(False),
    ],
)
def test_api_ok(
    set_ascfg,
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
    for op in ["create", "update", "delete"]:
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
        annostore_urls["search"],
        json=search_result,
        status=200,
    )

    path = reverse("annotation_store:api_root_prefix")

    # search request
    # needs resource_link_id to access LTI params
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
    response = client.post(
        "{}/{}?resource_link_id={}".format(path, webann_id, resource_link_id),
        data=webann,
        content_type="application/json",
        HTTP_AUTHORIZATION="token hehehe",
    )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 2
    assert content == webann

    # update request
    path_with_id = "{}/{}?resource_link_id={}".format(path, webann_id, resource_link_id)
    response = client.put(
        path_with_id,
        data=webann,
        content_type="application/json",
        HTTP_AUTHORIZATION="token hihihi",
    )
    assert response.status_code == 200

    content = json.loads(response.content.decode())
    assert len(responses.calls) == 3
    assert content == webann

    # delete request
    response = client.delete(
        path_with_id,
        HTTP_AUTHORIZATION="token hohoho",
    )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 4
    assert content == webann


@responses.activate
@pytest.mark.django_db
def test_api_grade_ok(
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

    path = reverse("annotation_store:api_root_prefix")

    # create request
    response = client.post(
        "{}/{}?resource_link_id={}".format(path, webann_id, resource_link_id),
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
    response = client.get(
        "{}?context_id={}&resource_link_id={}&userid={}".format(
            path, quote(course.course_id), resource_link_id, user.anon_id
        ),
        HTTP_AUTHORIZATION="token hohoho",
    )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 4
    assert content == search_result

    # update request
    path_with_id = "{}/{}?resource_link_id={}".format(path, webann_id, resource_link_id)
    response = client.put(
        path_with_id,
        data=webann,
        content_type="application/json",
        HTTP_AUTHORIZATION="token hehehe",
    )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 5  # does not issue a grade-passback
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
