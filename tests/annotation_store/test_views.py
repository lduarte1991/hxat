
import json
import pytest
import responses

from django.conf import settings
from django.test import Client
from django.test.client import RequestFactory
from django.urls import reverse


import annotation_store.views as views

from hx_lti_initializer.models import LTIResourceLinkConfig
from hx_lti_initializer.utils import retrieve_token


@responses.activate
@pytest.mark.django_db
def test_api_root_default(
        lti_path,
        lti_launch_url,
        course_user_lti_launch_params,
        assignment_target_factory,
        annotatorjs_annotation_factory,
        catchpy_search_result_shell,
        ):

    course, user, launch_params = course_user_lti_launch_params
    assignment_target = assignment_target_factory(course)
    target_object = assignment_target.target_object
    assignment = assignment_target.assignment
    #assignment.annotation_database_url = 'http://funky.com'
    #assignment.annotation_database_apikey = 'funky_key'
    #assignment.annotation_database_secret_token = 'funky_secret'
    assignment.save()

    # resource config from hx_lti_initializer.change_starting_resource
    # when instructor set the starting target for assignment
    resource_link_id = launch_params['resource_link_id']
    resource_config = LTIResourceLinkConfig(
            resource_link_id=resource_link_id,
            collection_id=assignment.assignment_id,
            object_id=target_object.id,
            )
    resource_config.save()

    # lti launch
    client = Client(enforce_csrf_checks=False)
    response = client.post(
            lti_path,
            data=launch_params,
            )
    assert response.status_code == 200

    # pluck the jwt token from lti-launch response
    content = response.content.decode()
    assert 'token' in content
    parts = content.split('token:')
    jwt_token = parts[1].split('"')[1]

    # set responses to assert
    annotation_store_request_url = '{}/search?resource_link_id={}'.format(
            assignment.annotation_database_url,
            resource_link_id)
    annojs = annotatorjs_annotation_factory(user)
    result = catchpy_search_result_shell
    result['total'] = 1
    result['size'] = 1
    result['rows'].append(annojs)
    responses.add(
            responses.GET,
            annotation_store_request_url,
            json=result,
            status=200,
            )

    path = reverse('annotation_store:api_root_prefix')
    response = client.get(
            '{}?resource_link_id={}'.format(path, resource_link_id),
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    content = json.loads(response.content.decode())

    assert response.status_code == 200

    assert len(responses.calls) == 1
    assert content == result
    #assert response is None



@pytest.mark.skip
@pytest.mark.django_db
def test_api_root_old(
        lti_path,
        lti_launch_url,
        course_user_lti_launch_params,
        assignment_target_factory,
        ):
    # to get the annotation db jwt in place, a bunch of things need to happen:
    # 1. successfull lti launch
    # 2. existing assignment and target object
    # 3. a resource_link_id association with collection_id, target_object_id
    #    which is recorded when instructor sets the starting target for assign
    # 4. jwt when starting target is set for assign (redirect from lti_launch)

    # 1. lti launch
    course, user, launch_params = course_user_lti_launch_params
    client = Client(enforce_csrf_checks=False)
    response = client.post(
            lti_path,
            data=launch_params,
            )
    assert(response.status_code == 200)

    # 2. existing assignment and target object
    assignment_target = assignment_target_factory(course)
    # default is hardcoded as 'catch' == 'annotatorjs'
    # and requires the backend-config to be in the assignment
    assignment = assignment_target.assignment
    target_object = assignment_target.target_object
    #assignment.annotation_database_url = 'http://funky.com'
    #assignment.annotation_database_apikey = 'funky_key'
    #assignment.annotation_database_secret_token = 'funky_secret'
    assignment.save()

    # 3. resource config from hx_lti_initializer.change_starting_resource
    resource_link_id = launch_params['resource_link_id']
    resource_config = LTIResourceLinkConfig(
            resource_link_id=resource_link_id,
            collection_id=assignment.assignment_id,
            object_id=target_object.id,
            )
    resource_config.save()

    # 4. jwt generated in hx_lti_initializer.access_annotation_target
    jwt_token = retrieve_token(
            user.anon_id,
            assignment.annotation_database_apikey,
            assignment.annotation_database_secret_token
        ),

    path = reverse('annotation_store:api_root_prefix')
    annotation_store_request_url = '{}?resource_link_id={}'.format(
            assignment.annotation_database_url,
            resource_link_id)
    responses.add(
            responses.GET,
            annotation_store_request_url,
            json={'error': 'not found'},
            status=200,
            )
    response = client.get(
            '{}?resource_link_id={}'.format(path, resource_link_id),
            X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200
    assert len(responses.calls) == 1
    assert response is None











