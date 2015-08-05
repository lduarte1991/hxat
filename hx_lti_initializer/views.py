"""
This will launch the LTI Annotation tool.

This is basically the controller part of the app. It will set up the tool provider, create/retrive the user and pass along any other information that will be rendered to the access/init screen to the user. 
"""

from ims_lti_py.tool_provider import DjangoToolProvider
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext

from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import login
from django.contrib import messages

from target_object_database.models import TargetObject
from hx_lti_initializer.models import LTIProfile, LTICourse
from hx_lti_assignment.models import Assignment
from hx_lti_initializer.forms import CourseForm
from django.conf import settings
from abstract_base_classes.target_object_database_api import TOD_Implementation

from models import *
from utils import *
from urlparse import urlparse
import json
import sys

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
    if 'lis_person_sourcedid' not in req.POST and 'lis_person_name_full' not in req.POST:
        debug_printer('DEBUG - Username or Name was not present in request.')
        raise PermissionDenied()

def initialize_lti_tool_provider(req):
    """
    Starts the provider given the consumer_key and secret.
    """
    # get the consumer key and secret from settings (__init__.py file)
    # will be used to compare against request to validate the tool init
    consumer_key = settings.CONSUMER_KEY
    secret = settings.LTI_SECRET
    
    # use the function from ims_lti_py app to verify and initialize tool
    provider = DjangoToolProvider(consumer_key, secret, req.POST)
    
    # now validate the tool via the valid_request function
    # this means that request was well formed but invalid
    if provider.valid_request(req) == False:
        debug_printer("DEBUG - LTI Exception: Not a valid request.")
        raise PermissionDenied()
    else:
        debug_printer('DEBUG - LTI Tool Provider was valid.')
    return provider

def create_new_user(username, user_id, roles):
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
    
    lti_profile.anon_id = user_id
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
    debug_printer('DEBUG - Found anonymous ID in request: %s' % user_id)
    
    course = get_lti_value(settings.LTI_COURSE_ID, tool_provider)
    debug_printer('DEBUG - Found course being accessed: %s' % course)

    roles = get_lti_value(settings.LTI_ROLES, tool_provider)

    if "Student" in roles or "Learner" in roles:
        collection_id = get_lti_value(settings.LTI_COLLECTION_ID, tool_provider)
        object_id = get_lti_value(settings.LTI_OBJECT_ID, tool_provider)
        debug_printer('DEBUG - Found assignment being accessed: %s' % collection_id)
        debug_printer('DEBUG - Found object being accessed: %s' % object_id)

        user_name = get_lti_value('lis_person_name_full', tool_provider)
        if user_name == None:
            # gather the necessary data from the LTI initialization request
            user_name = get_lti_value('lis_person_sourcedid', tool_provider)

        try:
            assignment = Assignment.objects.get(assignment_id=collection_id)
            targ_obj = TargetObject.objects.get(pk=object_id)
        except Assignment.DoesNotExist or TargetObject.DoesNotExist:
            raise PermissionDenied()

        original = {
            'user_id': user_id,
            'username': user_name,
            'is_instructor': request.user and request.user.is_authenticated(),
            'collection': collection_id,
            'course': course,
            'object': object_id,
            'target_object': targ_obj,
            'token': retrieve_token(user_id, assignment.annotation_database_apikey, assignment.annotation_database_secret_token),
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
        lti_profile = LTIProfile.objects.get(anon_id=user_id)
        debug_printer('DEBUG - LTI Profile was found via anonymous id.')
    
    except LTIProfile.DoesNotExist:
        debug_printer('DEBUG - LTI Profile not found. New User to be created.')
        
        lti_username = get_lti_value('lis_person_name_full', tool_provider)
        if lti_username == None:
            # gather the necessary data from the LTI initialization request
            lti_username = get_lti_value('lis_person_sourcedid', tool_provider)
        
        # checks to see if email and username were not passed in
        # cannot create a user without them
        if not lti_username:
            debug_printer('DEBUG - user_id not found in post.')
            raise PermissionDenied()
        
        # checks to see if roles were passed in. Defaults to student role.
        all_user_roles = []
        
        if not roles:
            debug_printer('DEBUG - ALL_ROLES is set but user was not passed in any roles via the request. Defaults to student.')
            all_user_roles += "Student"
        
        else:
            # makes sure that roles is a list and not just a string
            if not isinstance(roles, list):
                roles = [roles]
            all_user_roles += roles
        
        debug_printer('DEBUG - User had an acceptable role: %s' % all_user_roles)
        
        user, lti_profile = create_new_user(lti_username, user_id, roles)
    
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
        if 'Administrator' in roles or 'Instructor' in roles:
            # if the user is an administrator, the missing course is created
            # otherwise, it will just display an error message
            message_error = "Because you are an instructor, a course has been created for you, edit it below to add a proper name."
            messages.warning(request, message_error)
            course_object = LTICourse.create_course(course, lti_profile)
    
    # logs the user in
    lti_profile.user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, lti_profile.user)
    
    return redirect('hx_lti_initializer:course_admin_hub')


@login_required
def edit_course(request, id):
    course = get_object_or_404(LTICourse, pk=id)
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            course.save()

            messages.success(request, 'Course was successfully edited!')
            return redirect('hx_lti_initializer:course_admin_hub')
        else:
            raise PermissionDenied()
    else: 
        form = CourseForm(instance=course)
    return render(
        request,
        'hx_lti_initializer/edit_course.html', 
        {
            'form': form,
            'user': request.user,
        }
    )



@login_required
def course_admin_hub(request):
    """
    """
    lti_profile = LTIProfile.objects.get(user=request.user)
    courses_for_user = LTICourse.objects.filter(course_admins=lti_profile.id)
    files_in_courses = TOD_Implementation.get_dict_of_files_from_courses(lti_profile, courses_for_user)
    debug = files_in_courses
    return render(
        request,
        'hx_lti_initializer/testpage2.html',
        {
            'user': request.user,
            'email': request.user.email,
            'is_instructor': request.user and request.user.is_authenticated(),
            'roles': lti_profile.roles,
            'courses': courses_for_user,
            'files': files_in_courses,
            'debug': debug,
        }
    )

def access_annotation_target(request, course_id, assignment_id, object_id, user_id=None, user_name=None, roles=None):
    """
    """
    if user_id is None:
        user_name = request.user.get_username()
        user_id = request.user.email
        lti_profile = LTIProfile.objects.get(anon_id=user_id)
        roles = lti_profile.roles
    try:
        assignment = Assignment.objects.get(assignment_id=assignment_id)
        targ_obj = TargetObject.objects.get(pk=object_id)
    except Assignment.DoesNotExist or TargetObject.DoesNotExist:
        raise PermissionDenied()    

    original = {
        'user_id': user_id,
        'username': user_name,
        'is_instructor': request.user and request.user.is_authenticated(),
        'collection': assignment_id,
        'course': course_id,
        'object': object_id,
        'target_object': targ_obj,
        'token': retrieve_token(user_id, assignment.annotation_database_apikey, assignment.annotation_database_secret_token),
        'assignment': assignment,
    }
    if not assignment.object_before(object_id) is None:
        original['prev_object'] = assignment.object_before(object_id)

    if not assignment.object_after(object_id) is None:
        original['next_object'] = assignment.object_after(object_id)

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
