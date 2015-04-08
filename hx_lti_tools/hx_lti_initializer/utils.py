from django.conf import settings
from abstract_base_classes.target_object_database_api import *
from models import *
import base64
import sys

# import Sample Target Object Model
from hx_lti_todapi.models import TargetObject

def get_lti_value(key, tool_provider):
    """ 
    Searches for the given key in the tool_provider. If not found returns None 
    """
    
    lti_value = None
    
    try:
        lti_value = getattr(tool_provider,key)
    except AttributeError:
        print "Attribute: %s not found in LTI tool_provider" % key

    return lti_value

def debug_printer(debug_text):
    """
    Prints text passed in to stderr (Terminal on Mac) for debugging purposes.
    """
    if settings.LTI_DEBUG:
        print >> sys.stderr, debug_text + '\r'
