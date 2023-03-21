import json
import logging

from annostore.store import AnnostoreFactory
from django.contrib.auth.decorators import login_required
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import JsonResponse
from django.test import RequestFactory
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from hx_lti_assignment.models import Assignment
from hx_lti_initializer.models import LTICourse
from hxat.middleware import CookielessSessionMiddleware, MultiLTILaunchMiddleware

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

    why we have to have assignment_id in request? see [A] at bottom of file.
    """
    transfer_params = _verify_transfer_params(request, source_assignment_id)
    if "payload" in transfer_params:  # means something went wrong
        return JsonResponse(data=transfer_params, status=transfer_params["status"])

    annostore = AnnostoreFactory.get_instance(request, col_id=source_assignment_id)
    return annostore.transfer(transfer_params)


def _verify_transfer_params(request, source_assignment_id):
    """lots of checks to make sure we are not generating garbage.

    if "payload" present in return dictionary, then there is an error or warning msg.
    return dictionary:
    transfer_data = {
        "userid_map": userid_map,
        "source_context_id": source_context_id,
        "source_collection_id": source_collection_id,
        "target_context_id": target_context_id,
        "target_collection_id": target_collection_id,
        "payload": ["msg1", "msg2", .., "msgN"],
        "status": http_response_status_code,
    }

    """
    user_id = request.LTI["hx_user_id"]
    if not request.LTI["is_staff"]:
        msg = "permission denied; user({}) not admin to transfer annotations".format(
            user_id
        )
        logger.error(msg)
        return {"status": 401, "payload": [msg]}

    source_context_id = request.POST.get("old_course_id")
    try:
        source_course = LTICourse.objects.get(course_id=source_context_id)
    except LTICourse.DoesNotExist:
        # the course might have been deleted?
        msg = "source course({}) for transfer_inst_anno not found".format(
            source_context_id
        )
        logger.error(msg)
        return {"status": 404, "payload": [msg]}

    source_collection_id = request.POST.get("old_assignment_id")
    if source_collection_id != source_assignment_id:
        # sanity check: querystring and post body info must match!
        msg = "conflict from qs and post; expected({}) got ({})".format(
            source_assignment_id, source_collection_id
        )
        logger.error(msg)
        return {"status": 409, "payload": [msg]}
    try:
        source_assignment = Assignment.objects.get(assignment_id=source_collection_id)
    except Assignment.DoesNotExist:
        msg = "source assign({}) for transfer_inst_anno not found".format(
            source_collection_id
        )
        return {"status": 404, "payload": [msg]}
    if source_assignment.course.course_id != source_course.course_id:
        # sanity check: assignment pointing to previous run
        msg = "expected source assignment({}) course to be({}), found({})".format(
            source_assignment.assignment_id,
            source_assignment.course.course_id,
            source_course.course_id,
        )
        logger.error(msg)
        return {"status": 409, "payload": [msg]}

    target_context_id = request.POST.get("new_course_id")
    try:
        target_course = LTICourse.objects.get(course_id=target_context_id)
    except LTICourse.DoesNotExist:
        msg = "target course({}) for transfer_inst_anno not found".format(
            target_context_id
        )
        logger.error(msg)
        return {"status": 404, "payload": [msg]}
    if target_context_id != request.LTI["hx_context_id"]:
        # sanity check: session context_id must be target_context_id
        # guarantee logged admin has write permissions to transfer
        msg = "permission denied; target context_id expected({}) found({})".format(
            request.LTI["hx_context_id"], target_context_id
        )
        logger.error(msg)
        return {"status": 401, "payload": [msg]}

    target_collection_id = request.POST.get("new_assignment_id")
    try:
        target_assignment = Assignment.objects.get(assignment_id=target_collection_id)
    except Assignment.DoesNotExist:
        msg = "target assign({}) for transfer_inst_anno not found".format(
            target_collection_id
        )
        logger.error(msg)
        return {"status": 404, "payload": [msg]}
    if target_assignment.course.course_id != target_course.course_id:
        # sanity check: assignment pointing to previous run
        msg = "expected target assignment({}) course to be({}), found({})".format(
            target_assignment.assignment_id,
            target_assignment.course.course_id,
            target_course.course_id,
        )
        logger.error(msg)
        return {"status": 409, "payload": [msg]}

    if (
        target_assignment.annotation_database_url
        != source_assignment.annotation_database_url
    ):
        # sanity check: both assignments should point to the same annostore
        msg = "expected same annostore found ({}):({}) -> ({}):({})".format(
            source_assignment.assignment_id,
            source_assignment.annotation_database_url,
            target_assignment.assignment_id,
            target_assignment.annotation_database_url,
        )
        logger.error(msg)
        return {"status": 409, "payload": [msg]}

    # gather old admins
    userid_map = {}
    for adm in source_course.course_admins.all():
        userid_map[adm.anon_id] = user_id
    # no admins found; not an error per se
    if len(userid_map) == 0:
        msg = "no annotations to be transferred; no admins in course({})".format(
            source_course.course_id
        )
        logger.warning(msg)
        return {
            "original_total": 0,
            "total_success": 0,
            "total_failure": 0,
            "success": [],
            "failure": [],
            "payload": [msg],
            "status": 200,
        }

    # all checked and ready to go
    transfer_params = {
        "userid_map": userid_map,
        "source_context_id": source_context_id,
        "source_collection_id": source_collection_id,
        "target_context_id": target_context_id,
        "target_collection_id": target_collection_id,
    }
    logger.info(
        (
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
    return transfer_params


"""
20mar23 nmaekawa:
[A] why assignment_id in request url for transfer_instructor_annotation?
REST is hard if you want to overload the meaning of methods... And because we have
annostore configs per assignment.
The way we encapsulate the calls to annostore requires that we specify an annostore
config for every request, and because we define annostore config per assignment, we have
to have access to an assignment every time we want to call annostore.
In the case of annotations transfer, we have a post that it's not just create, nor
update, and this call will usually come from the admin hub, where an assignment is not
yet set in the session. This way, we pass the assignment via url in the path just to
have access to the annostore config.
"""
