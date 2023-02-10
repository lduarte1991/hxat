import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import JsonResponse
from django.test import RequestFactory
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from annotation_store.store import AnnotationStoreFactory
from hxat.middleware import CookielessSessionMiddleware, MultiLTILaunchMiddleware

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "POST", "PUT", "DELETE"])
def api_root(request, annotation_id=None):
    annostore = AnnotationStoreFactory.get_instance(request)
    return annostore.dispatcher(annotation_id)


@require_http_methods("GET")
def grade_me(request):
    """explicit request to send participation grades back to LMS"""
    # have to fake a search request to pass to AnnotationStore
    path = reverse("annotation_store:api_root_prefix")
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

    annostore = AnnotationStoreFactory.get_instance(search_request)
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
