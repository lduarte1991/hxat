#   testapp/views.py
#
#   This will launch the LTI Annotation tool

from ims_lti_py.tool_provider import DjangoToolProvider
from django.http import HttpResponseRedirect

from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from models import *
from utils import *
import sys

@csrf_exempt
def launch_lti(request):
    """
    Receives a request from consumer and authenticates user (or create it)
    """

    # print out log if LTI_DEBUG=True in settings
    if settings.LTI_DEBUG:
        for item in request.POST:
            print >> sys.stderr, ('%s: %s \r' % (item, request.POST[item]))
    
    if 'oauth_consumer_key' not in request.POST:
        raise PermissionDenied()
        
    consumer_key = settings.CONSUMER_KEY
    secret = settings.LTI_SECRET
    tool_provider = DjangoToolProvider(consumer_key, secret, request.POST)
    
    try: # attempt to validate request, if fails raises 403 Forbidden
        if tool_provider.valid_request(request) == False:
            raise PermissionDenied()
    except:
        print "LTI Exception: Not a valid request."
        raise PermissionDenied()
    
    return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
