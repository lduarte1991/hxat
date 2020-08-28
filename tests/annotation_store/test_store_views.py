
import json
import pytest
import responses
import uuid

from django.conf import settings
from django.test import Client
from django.test.client import RequestFactory
from django.urls import reverse

import annotation_store.views as views

from hx_lti_initializer.models import LTIResourceLinkConfig
from hx_lti_initializer.utils import retrieve_token


@responses.activate
@pytest.mark.django_db
def test_api_root_default_ok(
        lti_path,
        lti_launch_url,
        course_user_lti_launch_params,
        assignment_target_factory,
        annotatorjs_annotation_factory,
        catchpy_search_result_shell,
        ):
    '''webannotation api, redirected to the default annotatorjs api.'''

    # 1. create course, assignment, target_object, user
    course, user, launch_params = course_user_lti_launch_params
    assignment_target = assignment_target_factory(course)
    target_object = assignment_target.target_object
    assignment = assignment_target.assignment
    assignment.save()

    # 2. set starting resource
    resource_link_id = launch_params['resource_link_id']
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
    assert response.status_code == 200

    # pluck the jwt token from lti-launch response
    content = response.content.decode()
    assert 'token:' in content
    parts = content.split('token:')
    jwt_token = parts[1].split('"')[1]

    # set responses to assert
    annojs = annotatorjs_annotation_factory(user)
    annojs_id = uuid.uuid4().int
    search_result = catchpy_search_result_shell
    search_result['total'] = 1
    search_result['size'] = 1
    search_result['rows'].append(annojs)

    annotation_store_urls = {}
    for op in ['create', 'search']:
        annotation_store_urls[op] = '{}/{}'.format(
                assignment.annotation_database_url,
                op)
    for op in ['update', 'delete']:
        annotation_store_urls[op] = '{}/{}/{}'.format(
                assignment.annotation_database_url,
                op,
                annojs_id)

    responses.add(
            responses.POST, annotation_store_urls['create'], json=annojs, status=200,
            )
    responses.add(
            responses.POST, annotation_store_urls['update'], json=annojs, status=200,
            )
    responses.add(
            responses.DELETE, annotation_store_urls['delete'], json=annojs, status=200,
            )
    responses.add(
            responses.GET, annotation_store_urls['search'], json=search_result, status=200,
            )

    path = reverse('annotation_store:api_root_prefix')

    # search request
    response = client.get(
            '{}?resource_link_id={}'.format(path, resource_link_id),
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 1
    assert content == search_result

    # create request
    response = client.post(
            '{}/{}?resource_link_id={}'.format(
                path, annojs_id, resource_link_id),
            data=annojs,
            content_type='application/json',
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 2
    assert content == annojs

    # update request
    path_with_id = '{}/{}'.format(path, annojs_id)
    response = client.put(
            path_with_id,
            data=annojs,
            content_type='application/json',
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 3
    assert content == annojs


    # delete request
    response = client.delete(
            path_with_id,
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 4
    assert content == annojs


@pytest.mark.django_db
def test_api_root_default_no_starting_resource(
        lti_path,
        lti_launch_url,
        course_user_lti_launch_params,
        assignment_target_factory,
        annotatorjs_annotation_factory,
        catchpy_search_result_shell,
        ):
    # 1. create course, assignment, target_object, user
    course, user, launch_params = course_user_lti_launch_params
    assignment_target = assignment_target_factory(course)
    target_object = assignment_target.target_object
    assignment = assignment_target.assignment
    assignment.save()

    # 2. set starting resource
    #resource_link_id = launch_params['resource_link_id']
    #resource_config = LTIResourceLinkConfig.objects.create(
    #    resource_link_id=resource_link_id,
    #    assignment_target=assignment_target,
    #)

    # 3. lti launch
    client = Client(enforce_csrf_checks=False)
    response = client.post(
            lti_path,
            data=launch_params,
            )
    assert response.status_code == 200

    # jwt token NOT present lti-launch response
    content = response.content.decode()
    assert 'token:' not in content


@responses.activate
@pytest.mark.django_db
def test_api_root_backend_from_request_ok(
        lti_path,
        lti_launch_url,
        course_user_lti_launch_params,
        assignment_target_factory,
        annotatorjs_annotation_factory,
        catchpy_search_result_shell,
        ):
    '''webannotation api, configured from client search request.'''

    # 1. create course, assignment, target_object, user
    course, user, launch_params = course_user_lti_launch_params
    assignment_target = assignment_target_factory(course)
    target_object = assignment_target.target_object
    assignment = assignment_target.assignment
    #assignment.annotation_database_url = 'http://funky.com'
    #assignment.annotation_database_apikey = 'funky_key'
    #assignment.annotation_database_secret_token = 'funky_secret'
    assignment.save()

    # 2. set starting resource
    resource_link_id = launch_params['resource_link_id']
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
    assert response.status_code == 200

    # pluck the jwt token from lti-launch response
    content = response.content.decode()
    assert 'token:' in content
    parts = content.split('token:')
    jwt_token = parts[1].split('"')[1]

    # set responses to assert
    # TODO: if using webannotation api, should send webannotation format
    annojs = annotatorjs_annotation_factory(user)
    annojs_id = uuid.uuid4().int
    search_result = catchpy_search_result_shell
    search_result['total'] = 1
    search_result['size'] = 1
    search_result['rows'].append(annojs)

    annotation_store_urls = {}
    for op in ['search']:
        annotation_store_urls[op] = '{}'.format(
                assignment.annotation_database_url,
                )
    for op in ['create', 'update', 'delete']:
        annotation_store_urls[op] = '{}/{}'.format(
                assignment.annotation_database_url,
                annojs_id)

    responses.add(
            responses.POST, annotation_store_urls['create'], json=annojs, status=200,
            )
    responses.add(
            responses.PUT, annotation_store_urls['update'], json=annojs, status=200,
            )
    responses.add(
            responses.DELETE, annotation_store_urls['delete'], json=annojs, status=200,
            )
    responses.add(
            responses.GET, annotation_store_urls['search'], json=search_result, status=200,
            )

    path = reverse('annotation_store:api_root_prefix')

    # search request
    response = client.get(
            '{}?version=catchpy&resource_link_id={}'.format(path, resource_link_id),
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 1
    assert content == search_result

    # create request
    response = client.post(
            '{}/{}?version=catchpy&resource_link_id={}'.format(
                path, annojs_id, resource_link_id),
            data=annojs,
            content_type='application/json',
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 2
    assert content == annojs

    # update request
    path_with_id = '{}/{}?version=catchpy&resource_link_id={}'.format(
            path, annojs_id, resource_link_id)
    response = client.put(
            path_with_id,
            data=annojs,
            content_type='application/json',
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200

    content = json.loads(response.content.decode())
    assert len(responses.calls) == 3
    assert content == annojs

    # delete request
    response = client.delete(
            path_with_id,
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 4
    assert content == annojs


@responses.activate
@pytest.mark.django_db
def test_api_root_backend_from_request_store_cfg_from_db_ok(
        lti_path,
        lti_launch_url,
        course_user_lti_launch_params,
        assignment_target_factory,
        annotatorjs_annotation_factory,
        catchpy_search_result_shell,
        ):
    '''webannotation api, configured from client search request.'''

    # 1. create course, assignment, target_object, user
    course, user, launch_params = course_user_lti_launch_params
    assignment_target = assignment_target_factory(course)
    target_object = assignment_target.target_object
    assignment = assignment_target.assignment
    assignment.annotation_database_url = 'http://funky.com'
    assignment.annotation_database_apikey = 'funky_key'
    assignment.annotation_database_secret_token = 'funky_secret'
    assignment.save()

    # 2. set starting resource
    resource_link_id = launch_params['resource_link_id']
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
    assert response.status_code == 200

    # pluck the jwt token from lti-launch response
    content = response.content.decode()
    assert 'token:' in content
    parts = content.split('token:')
    jwt_token = parts[1].split('"')[1]

    # set responses to assert
    # TODO: if using webannotation api, should send webannotation format
    annojs = annotatorjs_annotation_factory(user)
    annojs_id = uuid.uuid4().int
    annojs['collectionId'] = '{}'.format(assignment.assignment_id)  # convert uuid to str
    search_result = catchpy_search_result_shell
    search_result['total'] = 1
    search_result['size'] = 1
    search_result['rows'].append(annojs)

    annotation_store_urls = {}
    for op in ['search']:  # search preserve params request to hxat
        annotation_store_urls[op] = \
            '{}/?version=catchpy&collectionId={}&resource_link_id={}'.format(
                assignment.annotation_database_url,
                assignment.assignment_id,
                resource_link_id,
                )
    for op in ['create', 'update', 'delete']:
        annotation_store_urls[op] = '{}/{}'.format(
                assignment.annotation_database_url,
                annojs_id,
                )

    responses.add(
            responses.POST, annotation_store_urls['create'], json=annojs, status=200,
            )
    responses.add(
            responses.PUT, annotation_store_urls['update'], json=annojs, status=200,
            )
    responses.add(
            responses.DELETE, annotation_store_urls['delete'], json=annojs, status=200,
            )
    responses.add(
            responses.GET, annotation_store_urls['search'], json=search_result, status=200,
            )

    path = reverse('annotation_store:api_root_prefix')

    # create request
    response = client.post(
            '{}/{}?version=catchpy&resource_link_id={}'.format(
                path, annojs_id, resource_link_id),
            data=annojs,
            content_type='application/json',
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 1
    assert content == annojs

    # update request
    path_with_id = '{}/{}?version=catchpy&resource_link_id={}'.format(
            path, annojs_id, resource_link_id)
    response = client.put(
            path_with_id,
            data=annojs,
            content_type='application/json',
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 2
    assert content == annojs

    # delete request
    path_delete = '{}/{}?version=catchpy&collectionId={}&resource_link_id={}'.format(
            path, annojs_id, assignment.assignment_id, resource_link_id)

    response = client.delete(
            path_delete,
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 3
    assert content == annojs

    # search request
    # needs resource_link_id to access LTI params for pass_grade
    response = client.get(
            '{}?version=catchpy&collectionId={}&resource_link_id={}'.format(
                path, assignment.assignment_id, resource_link_id),
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 4
    assert content == search_result


@responses.activate
@pytest.mark.django_db
def test_api_root_webanno_grade_ok(
        lti_path,
        lti_launch_url,
        course_user_lti_launch_params_with_grade,
        assignment_target_factory,
        annotatorjs_annotation_factory,
        catchpy_search_result_shell,
        make_lti_replaceResultResponse,
        ):
    '''webannotation api, configured from client search request.

    sends lis_outcome_service_url, lis_result_sourcedid to signal that lti
    consumer expects a grade
    '''

    # 1. create course, assignment, target_object, user
    course, user, launch_params = course_user_lti_launch_params_with_grade
    assignment_target = assignment_target_factory(course)
    target_object = assignment_target.target_object
    assignment = assignment_target.assignment
    assignment.annotation_database_url = 'http://funky.com'
    assignment.annotation_database_apikey = 'funky_key'
    assignment.annotation_database_secret_token = 'funky_secret'
    assignment.save()

    # get outcome_resource_url
    lis_outcome_service_url = launch_params['lis_outcome_service_url']

    # 2. set starting resource
    resource_link_id = launch_params['resource_link_id']
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
    assert response.status_code == 200

    # pluck the jwt token from lti-launch response
    content = response.content.decode()
    assert 'token:' in content
    parts = content.split('token:')
    jwt_token = parts[1].split('"')[1]

    # set responses to assert
    # TODO: if using webannotation api, should send webannotation format
    annojs = annotatorjs_annotation_factory(user)
    annojs_id = uuid.uuid4().int
    annojs['collectionId'] = '{}'.format(assignment.assignment_id)  # convert uuid to str
    search_result = catchpy_search_result_shell
    search_result['total'] = 1
    search_result['size'] = 1
    search_result['rows'].append(annojs)

    annotation_store_urls = {}
    for op in ['search']:  # search preserve params request to hxat
        annotation_store_urls[op] = \
                '{}/?version=catchpy&collectionId={}&resource_link_id={}&userid={}' \
                .format(
                        assignment.annotation_database_url,
                        assignment.assignment_id,
                        resource_link_id,
                        user.anon_id,
                )
    for op in ['create', 'update', 'delete']:
        annotation_store_urls[op] = '{}/{}'.format(
                assignment.annotation_database_url,
                annojs_id,
                )

    responses.add(
            responses.POST, annotation_store_urls['create'], json=annojs, status=200,
            )
    responses.add(
            responses.PUT, annotation_store_urls['update'], json=annojs, status=200,
            )
    responses.add(
            responses.DELETE, annotation_store_urls['delete'], json=annojs, status=200,
            )
    responses.add(
            responses.GET, annotation_store_urls['search'], json=search_result, status=200,
            )

    replace_result_response = make_lti_replaceResultResponse
    responses.add(
            responses.POST, lis_outcome_service_url,
            body=replace_result_response, content_type='application/xml',
            status=200,
            )

    path = reverse('annotation_store:api_root_prefix')

    # create request
    response = client.post(
            '{}/{}?version=catchpy&resource_link_id={}'.format(
                path, annojs_id, resource_link_id),
            data=annojs,
            content_type='application/json',
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 2
    assert content == annojs

    # update request
    path_with_id = '{}/{}?version=catchpy&resource_link_id={}'.format(
            path, annojs_id, resource_link_id)
    response = client.put(
            path_with_id,
            data=annojs,
            content_type='application/json',
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 3
    assert content == annojs

    # delete request
    path_delete = '{}/{}?version=catchpy&collectionId={}&resource_link_id={}'.format(
            path, annojs_id, assignment.assignment_id, resource_link_id)

    response = client.delete(
            path_delete,
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 4
    assert content == annojs

    # search request
    # needs resource_link_id to access LTI params for pass_grade
    response = client.get(
            '{}?version=catchpy&collectionId={}&resource_link_id={}&userid={}'.format(
                path, assignment.assignment_id, resource_link_id, user.anon_id),
            HTTP_X_ANNOTATOR_AUTH_TOKEN=jwt_token,
            )
    assert response.status_code == 200
    content = json.loads(response.content.decode())
    assert len(responses.calls) == 6
    assert content == search_result






"""
~28feb20 naomi notes:

For the client(hxighlighter or hxat UI) to be able to do perform any
annotations_store operation:
    - the course, assignmnent, and target_object must exist
    - the instructor must have set that target_object as starting resource
      i.e. associate the resource_link_id, provided by lti-consumer, to a
      (course, assign, target_object)
    - jwt token in html response from successful lti-launch: when the
      resource-link-id can be traced to a starting resource, hxat generates a
      jwt for the client to auth with the annotation-store (if annotation_store
      is external). This jwt is generated based on annotation-store creds that
      might be the default from django settings, but can be from the
      assignment. The main motivation of config annotation-store creds in
      assignment db might have come from the original idea of annotation
      federation (where different institutions could share annotations among
      themselvel) and to have test/demo/devo examples in production pointing to
      test/demo/devo annotation-store instances.


The annotations can have 2 formats:
          - annotatorjs
          - webannotation

The annotation_store can be of 2 types:
    X1. local database (atg requirement) -- removed on sha e3c72db
    X  supports annotatorjs only
    2. external api, which has to versions:
          - catch
            supports annotatorjs only
          - webannotation
            supports both annotatorjs and webannotation

    these evolving requirements made config/implementing the annotation store
    somewhat convoluted!


---
1. the only way to have the webannotationBackend configured is when param
   'version' is sent in request from client. Don't know how hxighlighter config
   to use webannotation or annotatorjs happens, but these info looks
   disconnected in hxighlighter and hxat.
   05mar20 naomi: "version" param that comes in the request for annotation_store
   endpoins refer to the format that the client is sending the annotation; so
   the client is asking for webannotation if "version=catchpy", and annotatorjs
   if no version param is present.

2. if client sends version=catchpy, hxat has no way to know if the
   assignment.annotation_store config actually supports webannotation because
   the annotation format (annotatorjs, webannotation) comes from the client --
   hxat has to trust the client

3. annotation-store api-root looks like accepts both annotatorjs and
   webannotation api. Why is it needed? why would client/hxighlighter send a
   annotatorjs request via webannotation api?

4. does hxighlighter knows the resource-link-id outside lti-context? this could
   sent every annotation-store request to identify the backend.
   05mar20 naomi: "resource-link-id" is an id for the lti component instance,
   it doesn't necessarily means that there is a context-id/collection-id
   associated like I was assuming!

5. create and search need to have resource-link-id as parameter because of
   grade-passback (and search for lis_outcome_service_url)

6. what is the behavior for a client that wants to update the collection_id?

7. how much hxat should know about annotation format? reaching out into an
   annotation for info? should this be a conversation between hxighlighter and
   catchpy only?


---------------------
~11may20 naomi notes:
    in debugging signature failure had test_api_root_webanno_grade_ok() changed
    to be always using settings.TEST_COURSE and settings.TEST_COURSE_LTI_SECRET
    (see tests.conftest.course_user_lti_launch_params_with_grade()), instead of
    the default consumer key and secret.
    It's tricky to test that the passback lti call is using proper credentials,
    but since it is copying launch-params from the session (see
    annotation_store.store.WebAnnotationStoreBackend._get_tool_provider()),
    then we are ok.
"""



