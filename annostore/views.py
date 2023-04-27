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

@login_required
def transfer(request, instructor_only="1"):
    user_id = request.LTI["hx_user_id"]

    old_assignment_id = request.POST.get("old_assignment_id")
    new_assignment_id = request.POST.get("new_assignment_id")
    old_course_id = request.POST.get("old_course_id")
    new_course_id = request.POST.get("new_course_id")
    logger.debug((
        "request to transfer annotation from old_course({}) to new_course({}) "
        "old_assign({}) to new_assign({}), by user({}). Failing SILENTLY!"
        ).format(
            old_course_id,
            new_course_id,
            old_assignment_id,
            new_assignment_id,
            user_id,
        )
    )
    return HttpResponse(json.dumps({}), content_type="application/json")
