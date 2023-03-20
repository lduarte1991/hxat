import json
import logging

from annostore.store import AnnostoreFactory
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import JsonResponse
from django.test import RequestFactory
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from hxat.middleware import CookielessSessionMiddleware, MultiLTILaunchMiddleware
from hx_lti_initializer.models import LTICourse
from hx_lti_assignment.models import Assignment

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "POST", "PUT", "DELETE"])
def api_root(request, annotation_id=None):
    annostore = AnnostoreFactory.get_instance(request)
    return annostore.dispatcher(annotation_id)


@require_http_methods("GET")
def grade_me(request):
    """explicit request to send participation grades back to LMS"""
    # have to fake a search request to pass to Annostore
    path = reverse("annotation_store:api_root_search")
    params = {
        "collection_id": request.LTI["hx_collection_id"],
        "context_id": request.LTI["hx_context_id"],
        "source_id": request.LTI["hx_object_id"],
        "userid": request.LTI["hx_user_id"],
        "utm_source": request.GET.get("utm_source", ""),
        "resource_link_id": request.GET.get("resource_link_id", ""),
    }
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
    response = api_root(search_request)  # this already do grade_passback!!!
    request_sent = False

    if response.status_code == 200:
        logger.info("Grade me search successful({})".format(response))
        annotations = json.loads(response.content)
        if annotations["total"] > 0:
            logger.info(
                "check grade back({}):({}):({}):({}):total({})".format(
                    request.LTI["hx_user_id"],
                    request.LTI["hx_context_id"],
                    request.LTI["hx_collection_id"],
                    request.LTI["hx_object_id"],
                    annotations["total"],
                )
            )
            annostore.lti_grade_passback()
            request_sent = True
    return JsonResponse(
        data={"grade_request_sent": request_sent},
    )

@require_http_methods("POST")
@login_required
def transfer_instructor_annotations(request, source_assignment_id):
    """copies instructor annotations from source assignment to target assignment.

    updates the context_id, collection_id, and sets the creator as the current logged in
    user (since current user has to be admin of the target course/assignment)
    does a lot of checks to catch reruns pointing to previous assignments!

    why we have to have assignment_id in request? explain.

    """
    user_id = request.LTI["hx_user_id"]

    source_context_id = request.POST.get("old_course_id")
    try:
        source_course = LTICourse.objects.get(course_id=source_context_id)
    except LTICourse.DoesNotExist:
        # it might be that the course was deleted!
        msg = "source course({}) for transfer_inst_anno not found".format(source_context_id)
        logger.error(msg)
        return JsonResponse(data={"status": 404, "payload": [msg]}, status=404)

    source_collection_id = request.POST.get("old_assignment_id")
    if source_collection_id != source_assignment_id:
       msg = "conflict from qs and post; expected({}) got ({})".format(
            source_assignment_id, source_collection_id
        )
       logger.error(msg)
       return JsonResponse(data={"status": 409, "payload": [msg]}, status=409)
    try:
        source_assignment = Assignment.objects.get(assignment_id=source_collection_id)
    except Assignment.DoesNotExist:
        msg = "source assign({}) for transfer_inst_anno not found".format(source_collection_id)
        return JsonResponse(data={"status": 404, "payload": [msg]}, status=404)
    if source_assignment.course.course_id != source_course.course_id:
        msg = "expected source assignment({}) course to be({}), found({})".format(
            source_assignment.assignment_id,
            source_assignment.course.course_id,
            source_course.course_id,
        )
        logger.error(msg)
        return JsonResponse(data={"status": 409, "payload": [msg]}, status=409)

    target_context_id = request.POST.get("new_course_id")
    try:
        target_course = LTICourse.objects.get(course_id=target_context_id)
    except LTICourse.DoesNotExist:
        msg = "target course({}) for transfer_inst_anno not found".format(target_context_id)
        logger.error(msg)
        return JsonResponse(data={"status": 404, "payload": [msg]}, status=404)
    # sanity check: session context_id must be target_context_id
    # guarantee logged admin has write permissions to transfer
    if target_context_id != request.LTI["hx_context_id"]:
        msg = "permission denied; target context_id expected({}) found({})".format(
            request.LTI["hx_context_id"], target_context_id
        )
        logger.error(msg)
        return JsonResponse(data={"status": 401, "payload": [msg]}, status=401)

    target_collection_id = request.POST.get("new_assignment_id")
    try:
        target_assignment = Assignment.objects.get(assignment_id=target_collection_id)
    except Assignment.DoesNotExist:
        msg = "target assign({}) for transfer_inst_anno not found".format(
            target_collection_id
        )
        logger.error(msg)
        return JsonResponse(data={"status": 404, "payload": [msg]}, status=404)
    if target_assignment.course.course_id != target_course.course_id:
        msg = "expected target assignment({}) course to be({}), found({})".format(
            target_assignment.assignment_id,
            target_assignment.course.course_id,
            target_course.course_id,
        )
        logger.error(msg)
        return JsonResponse(data={"status": 409, "payload": [msg]}, status=409)

    # sanity check: both assignments should point to the same annostore
    if target_assignment.annotation_database_url != source_assignment.annotation_database_url:
        msg = "expected same annostore found ({}):({}) -> ({}):({})".format(
            source_assigment.assignment_id,
            source_assignment.annotation_database_url,
            target_assigment.assignment_id,
            target_assignment.annotation_database_url,
        )
        logger.error(msg)
        return JsonResponse(data={"status": 409, "payload": [msg]}, status=409)

    # gather old admins
    userid_map = {}
    for adm in source_course.course_admins.all():
        userid_map[adm.anon_id] = user_id
    # no admins found; not an error per se
    if len(userid_map) == 0:
        msg = "no annotations to be transferred; no admins in course({})".format(
            source_course.course_id
        )
        logger.warn(msg)
        return JsonResponse(
            data={
                "original_total": 0, "total_success": 0, "total_failure": 0,
                "success": [], "failure": [],
                "payload": [msg], "status": 200,
            },
            status=200,
        )

    # all checked and ready to go
    transfer_data = {
        "userid_map": userid_map,
        "source_context_id": source_context_id,
        "source_collection_id": source_collection_id,
        "target_context_id": target_context_id,
        "target_collection_id": target_collection_id,
    }
    logger.info((
        "request to transfer annotation from source_course({}) to target_course({}) "
        "source_assign({}) to target_assign({}), by user({}), to annostore({})."
        ).format(
            source_context_id,
            target_context_id,
            source_collection_id,
            target_collection_id,
            user_id,
            source_assignment.annotation_database_url,
        )
    )
    annostore = AnnostoreFactory.get_instance(request)
    return annostore.dispatcher(annotation_id)


def transfer_deprecated(request, instructor_only="1"):
    user_id = request.LTI['hx_user_id']

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
        if response.status_code == 200:
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


"""
"""
