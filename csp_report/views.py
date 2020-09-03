
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from http import HTTPStatus

import json
import logging


logger = logging.getLogger(__name__)

@require_http_methods(["POST"])
@csrf_exempt
def csp_report(request):
    if request.body:
        try:
            # make sure it's json
            data = json.loads(request.body.decode('utf-8'))
        except Exception as e:
            # ignore errors
            pass
        else:
            # save in log
            logger.warning('CSP_REPORT: {}'.format(json.dumps(data, sort_keys=True)))

    return JsonResponse(status=HTTPStatus.NO_CONTENT, data={})


