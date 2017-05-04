from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from ims_lti_py.tool_provider import DjangoToolProvider

from target_object_database.models import TargetObject
from hx_lti_initializer.models import LTICourse 
from hx_lti_assignment.models import Assignment
from hx_lti_initializer.utils import (debug_printer, retrieve_token)
from hx_lti_initializer import annotation_database

import json
import requests
from urlparse import urlparse
import urllib2
import urllib

import logging
logging.basicConfig()

def api_root(request):
    return HttpResponse("OK")

def search(request):
    '''
    This view is intended to be called by the annotation dashboard when searching
    the CATCH database for annotations.

    It's essentially a proxy for annotatorJS requests, with a permission check to
    make sure the user is authorized to search the given course and collection.

    Required GET parameters:
     - collectionId: this is the assignment model
     - contextId: this is the course identifier as defined by LTI (the "course context")

    The optional GET parameters include those specified by the CATCH database as
    search fields.
    '''
    session_collection_id = request.session['hx_collection_id']
    session_context_id = request.session['hx_context_id']
    session_is_staff = request.session['is_staff']

    request_collection_id = request.GET.get('collectionId', None)
    request_context_id = request.GET.get('contextId', None)

    # verifies the query against session so they can't get unauthorized items
    if (session_collection_id != request_collection_id or
            session_context_id != request_context_id):
        return HttpResponse("You are not authorized to search for annotations")

    assignment = get_object_or_404(Assignment, assignment_id=request_collection_id)

    url_values = request.GET.urlencode()
    database_url = str(assignment.annotation_database_url).strip() + '/search?'
    headers = {
        'x-annotator-auth-token': request.META['HTTP_X_ANNOTATOR_AUTH_TOKEN'],
        'content-type': 'application/json',
    }

    # Override the auth token for ATG when the user is a course administrator,
    # so they can query against private annotations that have granted permission to the admin group.
    if settings.ORGANIZATION == "ATG" and session_is_staff:
        headers['x-annotator-auth-token'] = retrieve_token(
            annotation_database.ADMIN_GROUP_ID,
            assignment.annotation_database_apikey,
            assignment.annotation_database_secret_token
        )

    response = requests.post(database_url, headers=headers, params=url_values)
    return HttpResponse(response.content, status=response.status_code, content_type='application/json')


@csrf_exempt
def create(request):
    session_collection_id = request.session['hx_collection_id']
    session_object_id = str(request.session['hx_object_id'])
    session_context_id = request.session['hx_context_id']
    session_user_id = request.session['hx_user_id']
    session_is_staff = request.session['is_staff']

    json_body = json.loads(request.body)

    request_collection_id = json_body['collectionId']
    request_object_id = str(json_body['uri'])
    request_context_id = json_body['contextId']
    request_user_id = json_body['user']['id']

    if settings.ORGANIZATION == "ATG":
        annotation_database.update_read_permissions(json_body)

    debug_printer("%s: %s" % (session_user_id, request_user_id))
    debug_printer("%s: %s" % (session_collection_id, request_collection_id))
    debug_printer("%s: %s" % (session_object_id, request_object_id))
    debug_printer("%s: %s" % (session_context_id, request_context_id))

    # verifies the query against session so they can't get unauthorized items
    if (session_collection_id != request_collection_id or
            session_context_id != request_context_id or
            (session_user_id != request_user_id and not session_is_staff)):
        return HttpResponse("You are not authorized to create an annotation.")

    assignment = get_object_or_404(
        Assignment,
        assignment_id=session_collection_id
    )

    database_url = str(assignment.annotation_database_url).strip() + '/create'
    headers = {
        'x-annotator-auth-token': request.META['HTTP_X_ANNOTATOR_AUTH_TOKEN'],
        'content-type': 'application/json',
    }
    response = requests.post(
        database_url,
        data=json.dumps(json_body),
        headers=headers
    )

    try:
        if request.session['is_graded'] and response.status_code == 200:
            consumer_key = settings.CONSUMER_KEY
            secret = settings.LTI_SECRET
            params = request.session['lti_params']
            tool_provider = DjangoToolProvider(consumer_key, secret, params)
            outcome = tool_provider.post_replace_result(1)
            debug_printer(u"LTI grade request was {successful}. Description is {description}".format(
                successful="successful" if outcome.is_success() else "unsuccessful", description=outcome.description
            ))
    except:
        debug_printer("is_graded was not found in the session")

    return HttpResponse(response.content, status=response.status_code, content_type='application/json')


@csrf_exempt
def delete(request, annotation_id):
    session_user_id = request.session['hx_user_id']
    session_collection_id = request.session['hx_collection_id']
    session_is_staff = request.session['is_staff']
    try:
        json_body = json.loads(request.body)
        request_user_id = json_body['user']['id']

        debug_printer("%s: %s" % (session_user_id, request_user_id))

        # verifies queries against session so they can't get unauthorized items
        if (session_user_id != request_user_id and not session_is_staff):
            return HttpResponse("You are not allowed to create an annotation.")
    except:
        debug_printer("Probably a Mirador instance")
    assignment = get_object_or_404(
        Assignment,
        assignment_id=session_collection_id
    )

    database_url = str(assignment.annotation_database_url).strip() +\
        '/delete/' + str(annotation_id)
    headers = {
        'x-annotator-auth-token': request.META['HTTP_X_ANNOTATOR_AUTH_TOKEN'],
        'content-type': 'application/json',
    }
    response = requests.delete(database_url, headers=headers)

    return HttpResponse(response)


@csrf_exempt
def update(request, annotation_id):
    session_collection_id = request.session['hx_collection_id']
    session_object_id = str(request.session['hx_object_id'])
    session_context_id = request.session['hx_context_id']
    session_user_id = request.session['hx_user_id']
    session_is_staff = request.session['is_staff']

    json_body = json.loads(request.body)
    if settings.ORGANIZATION == "ATG":
        annotation_database.update_read_permissions(json_body)

    request_collection_id = json_body['collectionId']
    request_object_id = str(json_body['uri'])
    request_context_id = json_body['contextId']
    request_user_id = json_body['user']['id']

    debug_printer("%s %s %s" % (session_user_id, session_user_id != request_user_id, request_user_id))  # noqa
    debug_printer("%s %s %s" % (session_collection_id, session_collection_id != request_collection_id, request_collection_id))  # noqa
    debug_printer("%s %s %s" % (session_object_id, session_object_id != request_object_id, request_object_id))  # noqa
    debug_printer("%s %s %s" % (session_context_id, session_context_id != request_context_id, request_context_id))  # noqa

    # verifies query against session so they can't get more than they should
    if (session_collection_id != request_collection_id or
            session_context_id != request_context_id or
            (session_user_id != request_user_id and not session_is_staff)):
    # TODO: ADD MORE CHECKS HERE, TOOK OUT OBJECT AND CONTEXT BECAUSE OF IMG ANNOTATIONS
    # Give admins universal edit privileges
    # verifies the data queried against session so they can't get more than they should
    # if (session_collection_id != request_collection_id
    #     or session_object_id != request_object_id
    #     or session_context_id != request_context_id
    #     or (session_user_id != request_user_id and session_user_id not in admin_ids)):
        return HttpResponse("You are not authorized to create an annotation.")

    assignment = get_object_or_404(
        Assignment,
        assignment_id=session_collection_id
    )

    database_url = str(assignment.annotation_database_url).strip() + \
        '/update/' + str(annotation_id)
    headers = {
        'x-annotator-auth-token': request.META['HTTP_X_ANNOTATOR_AUTH_TOKEN'],
        'content-type': 'application/json',
    }
    response = requests.post(
        database_url,
        data=json.dumps(json_body),
        headers=headers
    )

    return HttpResponse(response.content, status=response.status_code, content_type='application/json')


@login_required
def transfer(request, instructor_only):
    session_is_staff = request.session['is_staff']
    user_id = request.session['hx_user_id']

    old_assignment_id = request.POST.get('old_assignment_id')
    new_assignment_id = request.POST.get('new_assignment_id')
    old_course_id = request.POST.get('old_course_id')
    new_course_id = request.POST.get('new_course_id')
    old_course = LTICourse.objects.get(course_id=old_course_id)
    new_course = LTICourse.objects.get(course_id=new_course_id)
    old_admins = []
    new_admins = dict()
    for ads in old_course.course_admins.all():
        old_admins.append(ads.anon_id)
    for ads in new_course.course_admins.all():
        new_admins[ads.name] = ads.anon_id

    assignment = Assignment.objects.get(assignment_id=old_assignment_id)
    object_ids = request.POST.getlist('object_ids[]')
    token = retrieve_token(
            user_id,
            assignment.annotation_database_apikey,
            assignment.annotation_database_secret_token
    )

    types = {
        "ig": "image",
        "tx": "text",
        "vd": "video"
    }
    responses = []
    for pk in object_ids:
        obj = TargetObject.objects.get(pk=pk)
        uri = pk
        target_type = types[obj.target_type]
        if target_type == "image":
            result = requests.get(obj.target_content)
            uri = json.loads(result.text)["sequences"][0]["canvases"][0]["@id"]
        search_database_url = str(assignment.annotation_database_url).strip() + '/search?'
        create_database_url = str(assignment.annotation_database_url).strip() + '/create'
        headers = {
            'x-annotator-auth-token': token,
            'content-type': 'application/json',
        }

        params = {
            'uri': uri,
            'contextId': old_course_id,
            'collectionId': old_assignment_id,
            'media': target_type,
            'limit': -1,
        }

        if str(instructor_only) == "1":
            params.update({'userid': old_admins})
        url_values = urllib.urlencode(params, True)
        response = requests.get(search_database_url, headers=headers, params=url_values)
        annotations = json.loads(response.text)
        for ann in annotations['rows']:
            ann['contextId'] = unicode(new_course_id)
            ann['collectionId'] = unicode(new_assignment_id)
            ann['id'] = None
            debug_printer("%s" % ann['user']['id'])
            if ann['user']['id'] in old_admins:
                try:
                    if new_admins[ann['user']['name']]:
                        ann['user']['id'] = new_admins[ann['user']['name']]
                except:
                    ann['user']['id'] = user_id
            response2 = requests.post(create_database_url, headers=headers, data=json.dumps(ann))

    #debug_printer("%s" % str(request.POST.getlist('assignment_inst[]')))
    data = dict()
    return HttpResponse(json.dumps(data), content_type='application/json')
