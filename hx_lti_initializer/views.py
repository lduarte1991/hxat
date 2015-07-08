"""
This will launch the LTI Annotation tool.

This is basically the controller part of the app. It will set up the tool provider, create/retrive the user and pass along any other information that will be rendered to the access/init screen to the user. 
"""

from ims_lti_py.tool_provider import DjangoToolProvider
from django.http import HttpResponseRedirect
from django.template import RequestContext

from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render_to_response, render
from django.contrib.auth import login
from django.conf import settings
from django.contrib import messages

from hx_lti_todapi.models import TargetObject
from hx_lti_assignment.models import Assignment
from hx_lti_initializer.models import LTIProfile, LTICourse
from abstract_base_classes.target_object_database_api import TOD_Implementation

from models import *
from utils import *
import sys
import json

def validate_request(req):
    """
    Validates the request in order to permit or deny access to the LTI tool.
    """
    # print out the request to the terminal window if in debug mode
    # this item is set in the settings, in the __init__.py file
    if settings.LTI_DEBUG:
        for item in req.POST:
            debug_printer('DEBUG - %s: %s \r' % (item, req.POST[item]))
    
    # verifies that request contains the information needed
    if 'oauth_consumer_key' not in req.POST:
        debug_printer('DEBUG - Consumer Key was not present in request.')
        raise PermissionDenied()
    if 'user_id' not in req.POST:
        debug_printer('DEBUG - Anonymous ID was not present in request.')
        raise PermissionDenied()
    if 'lis_person_name_full' not in req.POST:
        debug_printer('DEBUG - User full name was not present in request.')
        raise PermissionDenied()

def initialize_lti_tool_provider(req):
    """
    """
    # get the consumer key and secret from settings (__init__.py file)
    # will be used to compare against request to validate the tool init
    consumer_key = settings.CONSUMER_KEY
    secret = settings.LTI_SECRET
    
    # use the function from ims_lti_py app to verify and initialize tool
    provider = DjangoToolProvider(consumer_key, secret, req.POST)
    
    # now validate the tool via the valid_request function
    try:
        # this means that request was well formed but invalid
        if provider.valid_request(req) == False:
            debug_printer("DEBUG - LTI Exception: Not a valid request.")
            raise PermissionDenied()
        else:
            debug_printer('DEBUG - LTI Tool Provider was valid.')
    except:
        raise PermissionDenied()
    return provider

def create_new_user(username, user_id, roles, anon_id):
    # now create the user and LTIProfile with the above information
    user = User.objects.create_user(username, user_id)
    user.set_unusable_password()
    user.is_superuser = False
    user.is_staff = False

    for admin_role in settings.ADMIN_ROLES:
        for user_role in roles:
                if admin_role.lower() == user_role.lower():
                    user.is_superuser = True
                    user.is_staff = True
    user.save()
    debug_printer('DEBUG - User was just created')
    
    # pull the profile automatically created once the user was above
    lti_profile = LTIProfile.objects.get(user=user)
    
    lti_profile.anon_id = anon_id
    lti_profile.roles = (",").join(roles)
    lti_profile.save()
    
    return user, lti_profile

@csrf_exempt
def launch_lti(request):
    """
    Gets a request from an LTI consumer.
    Passes along information to render a welcome screen to the user.
    """
    
    validate_request(request)
    tool_provider = initialize_lti_tool_provider(request)
    
    # collect anonymous_id and consumer key in order to fetch LTIProfile
    # if it exists, we initialize the tool otherwise, we create a new user
    consumer_key_requested = request.POST['oauth_consumer_key']
    user_id = get_lti_value('user_id', tool_provider)
    anon_id = '%s:%s' % (consumer_key_requested, user_id)
    debug_printer('DEBUG - Found anonymous ID in request: %s' % anon_id)
    
    course = get_lti_value(settings.LTI_COURSE_ID, tool_provider)
    collection_id = get_lti_value(settings.LTI_COLLECTION_ID, tool_provider)
    object_id = get_lti_value(settings.LTI_OBJECT_ID, tool_provider)
    
    debug_printer('DEBUG - Found course being accessed: %s' % course)
    debug_printer('DEBUG - Found assignment being accessed: %s' % collection_id)
    debug_printer('DEBUG - Found object being accessed: %s' % object_id)
    
    roles = get_lti_value(settings.LTI_ROLES, tool_provider)

    if set(roles).intersection(settings.STUDENT_ROLES):
        try:
            assignment = Assignment.objects.get(assignment_id=collection_id)
            targ_obj = TargetObject.objects.get(pk=object_id)
        except Assignment.DoesNotExist or TargetObject.DoesNotExist:
            raise PermissionDenied()

        original = {
            'user_id': user_id,
            'username': get_lti_value('lis_person_name_full', tool_provider),
            'roles': roles,
            'collection': collection_id,
            'course': course,
            'object': object_id,
            'target_object': targ_obj,
            'token': retrieve_token(user_id, assignment.annotation_database_secret_token),
            'assignment': assignment,
        }

        if (targ_obj.target_type == 'vd'):
            srcurl = targ_obj.target_content
            if 'youtu' in srcurl:
                typeSource = 'video/youtube'
            else:
                disassembled = urlparse(srcurl)
                file_ext = splitext(basename(disassembled.path))[1]
                typeSource = 'video/' + file_ext.replace('.', '')
            original.update({'typeSource': typeSource})
        elif (targ_obj.target_type == 'ig'):
            original.update({'osd_json': targ_obj.target_content})

        return render(request, '%s/detail.html' % targ_obj.target_type, original)
    
    try:
        # try to get the profile via the anon id
        lti_profile = LTIProfile.objects.get(anon_id=anon_id)
        debug_printer('DEBUG - LTI Profile was found via anonymous id.')
    
    except LTIProfile.DoesNotExist:
        debug_printer('DEBUG - LTI Profile not found. New User to be created.')
        
        # gather the necessary data from the LTI initialization request
        lti_username = get_lti_value('lis_person_name_full', tool_provider)
        
        # checks to see if email and username were not passed in
        # cannot create a user without them
        if not lti_username:
            debug_printer('DEBUG - Email and/or user_id not found in post.')
            raise PermissionDenied()
        
        # checks to see if roles were passed in. Defaults to student role.
        all_user_roles = []
        
        if not roles:
            debug_printer('DEBUG - ALL_ROLES is set but user was not passed in any roles via the request. Defaults to student.')
            all_user_roles += settings.STUDENT_ROLES
        
        else:
            # makes sure that roles is a list and not just a string
            if not isinstance(roles, list):
                roles = [roles]
            all_user_roles += roles
        
        debug_printer('DEBUG - User had an acceptable role: %s' % all_user_roles)
        
        user, lti_profile = create_new_user(lti_username, anon_id, roles, anon_id)
    
    # now it's time to deal with the course_id it does not associate
    # with users as they can flow in and out in a MOOC
    try:
        debug_printer('DEBUG - Course was found %s' % course)
        course_object = LTICourse.get_course_by_id(course)
    
    except LTICourse.DoesNotExist:
        # this should only happen if an instructor is trying to access the 
        # tool from a different course
        debug_printer('DEBUG - Course %s was NOT found. Will be created.' %course)
        message_error = "Sorry, the course you are trying to reach does not exist."
        messages.error(request, message_error)
        if set(roles).intersection(settings.ADMIN_ROLES):
            # if the user is an administrator, the missing course is created
            # otherwise, it will just display an error message
            message_error = "Because you are an instructor, a course has been created for you, edit it below to add a proper name."
            messages.warning(request, message_error)
            course_object = LTICourse.create_course(course, lti_profile)
    
    # get all the courses the user is a part of
    courses_for_user = LTICourse.get_courses_of_user(lti_profile, course_object)
    
    # then gets all the files associated with the courses 
    files_in_courses = TOD_Implementation.get_dict_of_files_from_courses(lti_profile, courses_for_user)
    
    # logs the user in
    lti_profile.user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, lti_profile.user)
    
    # then renders the page using the template
    return render(request, 'hx_lti_initializer/testpage2.html', {'user': lti_profile.user, 'email': lti_profile.user.email, 'user_id': lti_profile.user.get_username(), 'roles': lti_profile.roles, 'courses': courses_for_user, 'files': files_in_courses})
