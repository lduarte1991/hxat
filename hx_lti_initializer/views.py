"""
This will launch the LTI Annotation tool.

This is basically the controller part of the app. It will set up the tool provider, create/retrive the user and pass along any other information that will be rendered to the access/init screen to the user. 
"""

from django.http                import HttpResponseRedirect, HttpResponse, Http404
from django.template            import RequestContext

from django.core.exceptions     import PermissionDenied
from django.shortcuts           import get_object_or_404, render_to_response, render
from django.contrib.auth        import login
from django.conf                import settings
from django.contrib             import messages

from hx_lti_todapi.models       import TargetObject
from hx_lti_assignment.models   import Assignment
from hx_lti_initializer.models  import LTIProfile, LTICourse
from django.views.decorators.csrf import csrf_exempt
from abstract_base_classes.target_object_database_api import TOD_Implementation
from models import *
from utils import *
from os.path import basename, splitext
from urlparse import urlparse

from django.views.decorators.http   import require_POST
from django.contrib.auth.decorators import login_required



import sys
import json
import requests
import logging

logging.basicConfig()

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
def launch_lti_old(request):
    """
    Gets a request from an LTI consumer.
    Passes along information to render a welcome screen to the user.
    """
    # collect anonymous_id and consumer key in order to fetch LTIProfile
    # if it exists, we initialize the tool otherwise, we create a new user
    #print str(request.LTI) + 'LTI session...................................................'

    consumer_key_requested = request.POST['oauth_consumer_key']
    user_id = request.LTI.get('user_id')
    anon_id = '%s:%s' % (consumer_key_requested, user_id)
    debug_printer('DEBUG - Found anonymous ID in request: %s' % anon_id)
    
    course = request.LTI.get('resource_link_id')
    collection_id = request.LTI.get('custom_collection_id')
    object_id = request.LTI.get('custom_object_id')
    
    debug_printer('DEBUG - Found course being accessed: %s' % course)
    debug_printer('DEBUG - Found assignment being accessed: %s' % collection_id)
    debug_printer('DEBUG - Found object being accessed: %s' % object_id)
    
    roles = request.LTI.get('roles')

    if set(roles).intersection(settings.STUDENT_ROLES):

        #fails here: no object or ID I guess?
        try:
            print collection_id
            #print(Assignment.objects.get(assignment_id = collection_id) )
            assignment = Assignment.objects.get(assignment_id=collection_id)
            targ_obj = TargetObject.objects.get(pk=object_id)
        except Assignment.DoesNotExist or TargetObject.DoesNotExist:
            raise PermissionDenied()

        original = {
            'user_id': user_id,
            'username': request.LTI.get('lis_person_name_full'),
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

        request.session['Authenticated'] = True
        return render(request, '%s/detail.html' % targ_obj.target_type, original)
    
    try:
        # try to get the profile via the anon id
        lti_profile = LTIProfile.objects.get(anon_id=anon_id)
        debug_printer('DEBUG - LTI Profile was found via anonymous id.')
    
    except LTIProfile.DoesNotExist:
        debug_printer('DEBUG - LTI Profile not found. New User to be created.')
        
        # gather the necessary data from the LTI initialization request
        lti_username = request.LTI.get('lis_person_name_full')
        
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
        else:
            debug_printer('DEBUG - ERROR: Non-administrative user attempted to create course')
            #course_object = LTICourse.create_course(course, lti_profile)

    
    # get all the courses the user is a part of
    courses_for_user = LTICourse.get_courses_of_user(lti_profile, course_object)
    
    # then gets all the files associated with the courses 
    files_in_courses = TOD_Implementation.get_dict_of_files_from_courses(lti_profile, courses_for_user)
    
    # logs the user in
    lti_profile.user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, lti_profile.user)

    request.session['Authenticated'] = True

    # then renders the page using the template
    return render(request, 'hx_lti_initializer/testpage2.html', {'user': lti_profile.user, 'email': lti_profile.user.email, 'user_id': lti_profile.user.get_username(), 'roles': lti_profile.roles, 'courses': courses_for_user, 'files': files_in_courses})

@login_required
@require_POST
@csrf_exempt
def launch_lti(request):

    #TODO: Authentication code?

    roles = request.LTI.get('roles')
    user_id = request.LTI.get('user_id')
    username = request.LTI.get('lis_person_name_full'),
    course = request.LTI.get('resource_link_id')


    request.session['LTI'] = request.LTI

    #TODO: Make this work for people with multiple roles
    #if set(roles).intersection(settings.STUDENT_ROLES):
    if roles == ['Learner']:
        context = {}
        #return(render(request, 'hx_lti_initializer/student_index.html', context))

        return student_view(request)
    #elif set(roles).intersection(settings.ADMIN_ROLES):
    elif roles == ['Instructor']:
        context = {}
        #return(render(request, 'hx_lti_initializer/instructor_index.html', context))
        #return(render(request, 'hx_lti_initializer/testpage2.html', context))
        return instructor_view(request)
    else:
        #TODO: What kind of failure functionality do we want? Redirect to fail page?
        return HttpResponse('FAIL')


def student_view(request):
    consumer_key_requested = request.POST['oauth_consumer_key']
    user_id = request.LTI.get('user_id')
    anon_id = '%s:%s' % (consumer_key_requested, user_id)
    course = request.LTI.get('resource_link_id')

    try:
        debug_printer('DEBUG - Course was found %s' % course)
        course_object = LTICourse.get_course_by_id(course)
    except:
        #TODO: correct functionality
        print("You're buggered - no course_object")

    try:
        # try to get the profile via the anon id
        lti_profile = LTIProfile.objects.get(anon_id=anon_id)
    except:
        #TODO: make them an account
        print("You're Rolled - no lti_profile")


    courses_for_user = LTICourse.get_courses_of_user(lti_profile, course_object)
    files_in_courses = TOD_Implementation.get_dict_of_files_from_courses(lti_profile, courses_for_user)


    context = {
        'user': lti_profile.user,
        'email': lti_profile.user.email,
        'user_id': lti_profile.user.get_username(),
        'roles': lti_profile.roles,
        'courses': courses_for_user,
        'files': files_in_courses
    }

    return render(request, 'hx_lti_initializer/student_index.html', context)

def instructor_view(request):

    consumer_key_requested = request.POST['oauth_consumer_key']
    user_id = request.LTI.get('user_id')
    anon_id = '%s:%s' % (consumer_key_requested, user_id)
    course = request.LTI.get('resource_link_id')

    try:
        debug_printer('DEBUG - Course was found %s' % course)
        course_object = LTICourse.get_course_by_id(course)
    except:
        #TODO: correct functionality
        print("You're buggered - no course_object")

    try:
        # try to get the profile via the anon id
        lti_profile = LTIProfile.objects.get(anon_id=anon_id)
    except:
        #TODO: make them an account
        print("You're Rolled - no lti_profile")


    courses_for_user = LTICourse.get_courses_of_user(lti_profile, course_object)
    files_in_courses = TOD_Implementation.get_dict_of_files_from_courses(lti_profile, courses_for_user)


    context = {
        'user': lti_profile.user,
        'email': lti_profile.user.email,
        'user_id': lti_profile.user.get_username(),
        'roles': lti_profile.roles,
        'courses': courses_for_user,
        'files': files_in_courses
    }

    return render(request, 'hx_lti_initializer/instructor_index.html', context)

@csrf_exempt
def annotation_view(request):
    # Get object_id and collection_id from POST
    # id of the target source
    object_id = request.POST.get('requested_object')
    # id of the assignment the annotation object belongs to
    collection_id = request.POST.get('requested_assignment')

    # Check if object and collection id exist
    if object_id is None or collection_id is None:
        raise Http404("Assignment does not exist.")

    # Get target object 
    try:
        assignment = Assignment.objects.get(assignment_id=collection_id)
        targ_obj = TargetObject.objects.get(pk=object_id)
    except Assignment.DoesNotExist or TargetObject.DoesNotExist:
        raise PermissionDenied()

    LTI = request.session['LTI']

    context = {
        'user_id': LTI.get('user_id'),
        'username': LTI.get('lis_person_name_full'),
        'roles': LTI.get('roles'),
        'collection': collection_id,
        'course': LTI.get('resource_link_id'),
        'object': object_id,
        'target_object': targ_obj,
        'token': retrieve_token(LTI.get('user_id'), assignment.annotation_database_secret_token),
        'assignment': assignment,
    }

    # Check whether the target object is a video or image
    if (targ_obj.target_type == 'vd'):
        srcurl = targ_obj.target_content
        if 'youtu' in srcurl:
            typeSource = 'video/youtube'
        else:
            disassembled = urlparse(srcurl)
            file_ext = splitext(basename(disassembled.path))[1]
            typeSource = 'video/' + file_ext.replace('.', '')
        context.update({'typeSource': typeSource})
    elif (targ_obj.target_type == 'ig'):
        context.update({'osd_json': targ_obj.target_content})

    return render(request, '%s/detail.html' % targ_obj.target_type, context)
