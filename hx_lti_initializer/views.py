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

#from hx_lti_todapi.models       import TargetObject
from target_object_database.models import TargetObject
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
from django.template.defaulttags    import register

import sys
import json
import requests
import logging

logging.basicConfig()

def create_user(request, anon_id):
    '''
        Creates a backend (annotation) user for a given unique ID
        TODO: The Student's Name should not be the primary key in the DB,
        it should be the userID. All backend logic goes through that (unique) key,
        and all frontend shows the 'username' attribute.
    '''
    debug_printer('DEBUG - LTI Profile not found. New User to be created.')

    # gather the necessary data from the LTI initialization request
    # What if there are two people named 'John Doe'?? (or Test Student)
    # what if their name is longer than the db field? (30 char)
    # Caution: this username shows up in the 'choose course admins' field.
    lti_username = request.LTI.get('lis_person_name_full')

    roles = request.LTI.get('roles')
    # checks to see if email and username were not passed in
    # cannot create a user without them
    if not lti_username:
        debug_printer('DEBUG - Email and/or user_id not found in post.')
        error_view(request, "Incorrect authentication was provided for user creation")
        #raise PermissionDenied()

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

    #user, lti_profile = create_new_user(lti_username, anon_id, roles, anon_id)
    #return user, lti_profile

    # TODO: make primary key userID, not username. 'Test Student' can't join more than one course.
    try:
        user = User.objects.create_user(lti_username, anon_id)
    except:
        debug_printer('DEBUG - There was already a student named %s, creating a second one.' % lti_username)
        #raise PermissionDenied() 
        # Not elegant, but this will save the tool from failing hard for duplicate names,
        # until we can figure out how to make names not the primary key
        user = User.objects.create_user(lti_username + " 2", anon_id)
        # this will still fail if there are three people with the same name in a course though...
    
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
    
#@login_required
@require_POST
@csrf_exempt
def launch_lti(request):
    '''
        This view handles the original request to launch the tool.
        It authenticates the user, 
    '''
    
    try:
        consumer_key_requested = request.POST['oauth_consumer_key']
    except:
        return error_view(request, 'No authentication details were provided for the new user')

    if consumer_key_requested != settings.CONSUMER_KEY:
        return error_view(request, 'Incorrect authentication details provided for the new user')

    request.session['oauth_consumer_key'] = consumer_key_requested

    roles = request.LTI.get('roles')
    request.session['roles'] = roles

    #user_id = request.LTI.get('user_id')
    #username = request.LTI.get('lis_person_name_full'),
    #course = request.LTI.get('resource_link_id')

    #print("User ID: " + request.LTI['user_id'])

    request.session['LTI'] = request.LTI

    if set(roles).intersection(settings.ADMIN_ROLES):
        return instructor_view(request)
    elif set(roles).intersection(settings.STUDENT_ROLES):
        return student_view(request)
    else:
        # default to student view for now.
        return student_view(request)
        #return error_view(request, 'The user is neither student nor teacher')


def student_view(request):
    '''
        Shows the student index - an accordion of all assignments and their objects
    '''

    #TODO: check how secure we are
    #consumer_key_requested = request.session['oauth_consumer_key']

    try:
        consumer_key_requested = request.session['oauth_consumer_key']
    except:
        return error_view(request, 'No authentication details were provided for the student view')

    if consumer_key_requested != settings.CONSUMER_KEY:
        return error_view(request, 'Incorrect authentication details provided for the student view')

    try:
        LTI = request.session['LTI']
    except:
        return error_view(request, "Something went wrong with the student's Canvas launch")

    # MARK - It seems that a lot depends on this formatting. It may be a good idea to abstract it.
    user_id = LTI.get('user_id')
    anon_id = '%s:%s' % (consumer_key_requested, user_id)

    try:
        course = LTI.get('resource_link_id')
        debug_printer('DEBUG - Course was found %s' % course)
        course_object = LTICourse.get_course_by_id(course)
    except:
        return error_view(request, "It appears you're trying to access a course that doesn't exist")

    try:
        # try to get the profile via the anon id
        lti_profile = LTIProfile.objects.get(anon_id=anon_id)
        debug_printer('DEBUG - Student already had an lti_profile')
    except LTIProfile.DoesNotExist:
        # if there's no user, create one for the student. Right now the user variable is unused.
        user, lti_profile = create_user(request, anon_id)

    # get only the active course and its files
    active_course = LTICourse.get_course_by_id(course)
    files_in_courses = TOD_Implementation.get_dict_of_files_from_courses(lti_profile, [active_course])


    context = {
        'user': lti_profile.user,
        'user_name': LTI.get('lis_person_name_full'),
        'email': lti_profile.user.email,
        'user_id': lti_profile.user.get_username(),
        'roles': lti_profile.roles,
        'course': active_course,
        'files': files_in_courses
    }

    return render(request, 'hx_lti_initializer/student_index.html', context)


def instructor_view(request):
    '''
        TODO: explanation
    '''

    #TODO: fail on 'not instructor in roles'
    
    #TODO: 403 on fail consumer key
    # we need to check how secure we are...
    consumer_key_requested = request.session['oauth_consumer_key']

    try:
        LTI = request.session['LTI']
    except:
        return error_view(request, "Something went wrong with the instructor's Canvas launch")
    
    user_id = LTI.get('user_id')
    anon_id = '%s:%s' % (consumer_key_requested, user_id)
    request.session['anon_id'] = anon_id

    course = LTI.get('resource_link_id')

    try:
        # try to get the profile via the anon id
        lti_profile = LTIProfile.objects.get(anon_id=anon_id)
    except LTIProfile.DoesNotExist:
        user, lti_profile = create_user(request, anon_id)
        print("You're Rolled - no lti_profile")

    try:
        debug_printer('DEBUG - Course was found %s' % course)
        course_object = LTICourse.get_course_by_id(course)
    except LTICourse.DoesNotExist:
        # this should only happen if an instructor is trying to access the
        # tool from a different course
        debug_printer('DEBUG - Course %s was NOT found. Will be created.' %course)
        message_error = "Sorry, the course you are trying to reach does not exist."
        messages.error(request, message_error)

        #TODO: try/catch on the 'roles' lookup?
        if set(request.session['roles']).intersection(settings.ADMIN_ROLES):
            # if the user is an administrator, the missing course is created
            # otherwise, it will just display an error message
            message_error = "Because you are an instructor, a course has been created for you, edit it below to add a proper name."
            messages.warning(request, message_error)
            course_object = LTICourse.create_course(course, lti_profile)
        else:
            debug_printer('DEBUG - ERROR: Non-administrative user attempted to create course')
            course_object = []
            #course_object = LTICourse.create_course(course, lti_profile)
    
    active_course = LTICourse.get_course_by_id(course)
    files_in_courses = TOD_Implementation.get_dict_of_files_from_courses(lti_profile, [active_course])
    

    context = {
        'user': lti_profile.user,
        'email': lti_profile.user.email,
        'is_instructor': True,
        'roles': lti_profile.roles,
        'courses': [active_course],
        'files': files_in_courses,
    }
    
    print(context)


    return render(request, 'hx_lti_initializer/testpage2.html', context)

# @csrf_exempt
# def annotation_view(request):
#     '''
#         TODO: explanation
#     '''

#     # Get object_id and collection_id from POST
#     # id of the target source
#     object_id = request.GET.get('requested_object')
#     # id of the assignment the annotation object belongs to
#     collection_id = request.GET.get('requested_assignment')

#     # Check if object and collection id exist
#     if object_id is None or collection_id is None:
#         raise Http404("Assignment does not exist.")

#     # Get target object 
#     try:
#         assignment = Assignment.objects.get(assignment_id=collection_id)
#         targ_obj = TargetObject.objects.get(pk=object_id)
#     except Assignment.DoesNotExist or TargetObject.DoesNotExist:
#         raise PermissionDenied()

#     try:
#         LTI = request.session['LTI']
#     except:
#         return error_view(request, "Something went wrong with the student's Canvas launch")

#     # Filter for LTIProfile with Instructor role
#     # TODO: Current invariant assumes that we have only one Instructor. 
#     instructor_profile = LTIProfile.objects.filter(roles='Instructor')[:1].get()
#     # Get instructor's user_id
#     instructor_id = instructor_profile.get_id()

#     context = {
#         'user_id': LTI.get('user_id'),
#         'username': LTI.get('lis_person_name_full'),
#         'roles': LTI.get('roles'),
#         'collection': collection_id,
#         'course': LTI.get('resource_link_id'),
#         'object': object_id,
#         'target_object': targ_obj,
#         'token': retrieve_token(LTI.get('user_id'), assignment.annotation_database_secret_token),
#         'assignment': assignment,
#         'instructor_id': instructor_id
#     }

#     # Check whether the target object is a video or image
#     if (targ_obj.target_type == 'vd'):
#         srcurl = targ_obj.target_content
#         if 'youtu' in srcurl:
#             typeSource = 'video/youtube'
#         else:
#             disassembled = urlparse(srcurl)
#             file_ext = splitext(basename(disassembled.path))[1]
#             typeSource = 'video/' + file_ext.replace('.', '')
#         context.update({'typeSource': typeSource})
#     elif (targ_obj.target_type == 'ig'):
#         context.update({'osd_json': targ_obj.target_content})

#     return render(request, '%s/detail.html' % targ_obj.target_type, context)


# def dashboard_view(request):
#     '''
#         The instructor Dashboard
#     '''
    
#     #TODO: 'fail on not instructor in roles'
    
#     try:
#         LTI = request.session['LTI']
#     except:
#         return error_view(request, "Something went wrong with the dashboard view")
    
#     #anon_id = request.session['anon_id']

#     course_id = LTI.get('resource_link_id') #returns the unicode course hash
#     course_object = LTICourse.objects.get(course_id=course_id)

#     #YES!! this works.
#     assignments = Assignment.objects.filter(course=course_object)

#     # user_profiles = course_object.course_users.all()
#     user_profiles = LTIProfile.objects.filter(roles='Learner') 
    
#     # TODO: role safety - might have more than one role

#     student_objects = {}
#     #student_object will look like:
#     #  {'8132098129034871': {'student_name': 'Test Student', 'student_annotations': {....} }}

#     # LOGIC:
#     # 1: get the correct course
#     # 2: get the students in that course
#     # 3: get those students' annotations
#     # 4: display those annotations that are for the correct course (TODO)
    
#     #TODO: this should be based on object, not assignment existence
    
#     for profile in list(user_profiles):
#         print str(profile)
#         user_id = profile.get_id() #returns the value, which is the ID
#         for assignment in assignments:
#             token = retrieve_token(LTI.get(user_id), assignment.annotation_database_secret_token) 
#             student_objects[user_id] = {
#                 'student_name': str(profile), #the model is set up to return the name of the user on a utf call
#                 'annotations': filter_by_course(fetch_user_annotations(user_id, token), course_id)
#                     #as long as this only returns the annotations for a particular assignment, it should work fine
#             }
#             # print student_objects
#     context = {
#         'student_objects': student_objects,
#     }
    
#     return render(request, 'hx_lti_initializer/dashboard_view.html', context)


# def fetch_user_annotations (id, token):
#     '''
#         Fetches the annotations of a given user from the CATCH database
#     '''
    
#     # token = 'eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJpYXQiOiAxNDM3NzY5NTE5LCAiZCI6IHsiaXNzdWVkQXQiOiAiMjAxNS0wNy0yNFQyMDoyNToxOS44OTIwNzYrMDowMCIsICJjb25zdW1lcktleSI6ICI1YWFhNjBmNi1iYTNhLTRjNjAtOTUzYi1hYjk2YzJkMjA2MjQiLCAidWlkIjogIjNlOWZkMjAwNjY1YmY0ZDBiNGJhOWJkZDE3MDg0NWUyZmRmMWFiMjAiLCAidHRsIjogMTcyODAwfSwgInYiOiAwfQ.lvVa1lui9jBZROISfQzadjzIQzZopsRuD9uJoGQ5scM'
#     headers = {"x-annotator-auth-token": token, "Content-Type":"application/json"}
#     # TODO: secure.py
#     baseurl = "http://ec2-52-26-240-251.us-west-2.compute.amazonaws.com:8080/catch/annotator/"
#     requesturl = baseurl + "search?userid=" + id
 
#     # Make request
#     r = requests.get(requesturl, headers=headers)

#     return r.json()
    
# def filter_by_course (annotations, context_id):
#     ''' Given a decoded response from the CATCH database, filters out the annotations for the current course
#         based on context_id'''
#     for row in annotations['rows']:
#         # Check if context_id is contained within the URI
#         if context_id not in row['uri']:
#             annotations['rows'].remove(row)
#     #print(annotations)
#     return annotations

def index_view(request):
    '''
        Routes the user to his/her correct index view
    '''

    #TODO: TESTING - what if the user has many roles?

    # Can i do .contains()?
    if set(request.session['roles']).intersection(settings.ADMIN_ROLES):
        return instructor_view(request)
    elif set(request.session['roles']).intersection(settings.STUDENT_ROLES):
        return student_view(request)
    else:
        #TODO: 403 redirect?
        return HttpResponse("You're Rolled: Not a student or admin")
        
def route_uri(request):
    uri = request.GET.get('uri')
    object_id, context_id, collection_id = split_uri(uri)
    
    # Modifying the GET dictionary is usually not allowed.
    # if anyone has strong moral objections to the below code, I guess
    # we could add a couple parameters/refactor/finagle annotation view
    # so that 
    request.GET = request.GET.copy()
    request.GET['requested_object'] = object_id
    request.GET['requested_assignment'] = collection_id
    
    return annotation_view(request)

def split_uri(uri):
    '''Currently the uri consists of the object_id, context_id and collection_id separated by underscores.
    This function returns a tuple of these parts for separate access.
    This will break if the uri configuration changes.'''
    
    [object_id, context_id, collection_id] = uri.split('_')
    
    return (object_id, context_id, collection_id)
    

def error_view(request, message):
    '''
    Implements graceful and user-friendly (also debugger-friendly) error displays
    If used properly, we can use this to have better bug reproducibility down the line.
    While we won't dump any sensitive information, we can at least describe what went wrong
    uniquely and get an indication from the user which part of our code failed.
    '''
    
    context = {
        'message': message
    }
    
    return render(request, 'hx_lti_initializer/error_page.html', context)

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
