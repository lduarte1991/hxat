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

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#                      Target Object Database API (TODAPI)                    #
#   This section contains the functions that would need to change should the  #
#   Target Object Database need to change. Adding boolean variables for       #
#   settings would be more ideal than erasing.                                #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Simple_django_tod_api(TODAPI_LTI):
    def get_own_targets_from_course(user_requesting, course_id):
        """
        This function should return a list of Target Objects (following the model created in hx_annotations/hx_lti_todapi) from the course given.
        """
        course_for_user = LTICourse.objects.filter(course_id=course_id)
        response = TargetObject.objects.filter(target_courses=course_for_user)
        return response

    def get_own_targets_as_user(user_requesting):
        """
        This function should return all the files 
        """
        courses_for_user = LTICourse.objects.filter(course_users=User_requesting.id)
        files_in_courses = []
        for course_item in courses_for_user:
            files_found = TargetObject.objects.filter(target_courses=course_item)
            files_in_courses += list(files_found)
        return files_in_courses