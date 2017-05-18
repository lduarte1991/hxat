from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from target_object_database.models import TargetObject
from hx_lti_initializer.models import LTICourse 
from hx_lti_assignment.models import Assignment
from hx_lti_initializer.utils import retrieve_token
from hx_lti_initializer import annotation_database
from store import AnnotationStore

import json
import requests
import urllib
import logging

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def api_root(request):
    return AnnotationStore.from_settings(request).root()

@require_http_methods(["GET"])
def search(request):
    return AnnotationStore.from_settings(request).search()

@csrf_exempt
@require_http_methods(["POST"])
def create(request):
    return AnnotationStore.from_settings(request).create()

@csrf_exempt
@require_http_methods(["PUT"])
def update(request, annotation_id):
    return AnnotationStore.from_settings(request).update(annotation_id)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete(request, annotation_id):
    return AnnotationStore.from_settings(request).delete(annotation_id)

@login_required
def transfer(request, instructor_only):
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
            logger.info("annotation user_id: %s" % ann['user']['id'])
            if ann['user']['id'] in old_admins:
                try:
                    if new_admins[ann['user']['name']]:
                        ann['user']['id'] = new_admins[ann['user']['name']]
                except:
                    ann['user']['id'] = user_id
            response2 = requests.post(create_database_url, headers=headers, data=json.dumps(ann))

    #logger.debug("%s" % str(request.POST.getlist('assignment_inst[]')))
    data = dict()
    return HttpResponse(json.dumps(data), content_type='application/json')
