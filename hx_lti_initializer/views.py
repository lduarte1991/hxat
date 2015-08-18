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
from django.http import Http404
from django.contrib.auth import login
from django.contrib import messages
from django.contrib import messages
from django.db import IntegrityError

from target_object_database.models import TargetObject
from hx_lti_initializer.models import LTIProfile, LTICourse
from hx_lti_assignment.models import Assignment
from hx_lti_initializer.forms import CourseForm
from django.conf import settings
from abstract_base_classes.target_object_database_api import TOD_Implementation

from models import *
from utils import *
from urlparse import urlparse
import urllib2
import urllib
import json
import sys
import requests

import logging
logging.basicConfig()

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
    #consumer_key = settings.CONSUMER_KEY
    #secret = settings.LTI_SECRET

    # both of these will give key errors if there is no key or it's the wrong key, respectively.
    consumer_key = req.POST['oauth_consumer_key']
    secret = settings.LTI_OAUTH_CREDENTIALS[consumer_key]
    
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
    # Max 30 length for person's name, do we want to change this? It's valid for HX but not ATG/FAS
    try:
        user = User.objects.create_user(username, user_id)
    except IntegrityError:
        # TODO: modify db to make student name not the primary key
        # a temporary workaround for key integrity errors, until we can make the username not the primary key.
        return create_new_user(username + " ", user_id, roles)
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

def save_session(request, user_id, collection_id, object_id, context_id, roles):
    if user_id is not None:
        request.session["hx_user_id"] = user_id
    if collection_id is not None:
        request.session["hx_collection_id"] = collection_id
    if object_id is not None:
        request.session["hx_object_id"] = object_id
    if context_id is not None:
        request.session["hx_context_id"] = context_id
    if roles is not None:
        request.session["hx_roles"] = roles

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
    request.session['is_instructor'] = False
    
    # Set creator name, to be used later as default in addition of source material
    request.session['creator_default'] = get_lti_value('lis_person_name_full', tool_provider)
    
    # Check whether user is a admin, instructor or teaching assistant
    # TODO: What roles do we actually want here?
    debug_printer("DEBUG - user logging in with roles: " + str(roles))
    if set(roles) & set(settings.ADMIN_ROLES):# or "Teaching Assistant" in roles:
    # Set flag in session to later direct user to the appropriate version of the index
        request.session['is_instructor'] = True

    # if "Student" in roles or "Learner" in roles:
    #     collection_id = get_lti_value(settings.LTI_COLLECTION_ID, tool_provider)
    #     object_id = get_lti_value(settings.LTI_OBJECT_ID, tool_provider)
    #     debug_printer('DEBUG - Found assignment being accessed: %s' % collection_id)
    #     debug_printer('DEBUG - Found object being accessed: %s' % object_id)

    #     user_name = get_lti_value('lis_person_name_full', tool_provider)
    #     if user_name == None:
    #         # gather the necessary data from the LTI initialization request
    #         user_name = get_lti_value('lis_person_sourcedid', tool_provider)

    #     try:
    #         assignment = Assignment.objects.get(assignment_id=collection_id)
    #         targ_obj = TargetObject.objects.get(pk=object_id)
    #     except Assignment.DoesNotExist or TargetObject.DoesNotExist:
    #         raise PermissionDenied()
    #     original = {
    #         'user_id': user_id,
    #         'username': user_name,
    #         'is_instructor': request.user and request.user.is_authenticated(),
    #         'collection': collection_id,
    #         'course': course,
    #         'object': object_id,
    #         'target_object': targ_obj,
    #         'token': retrieve_token(user_id, assignment.annotation_database_apikey, assignment.annotation_database_secret_token),
    #         'assignment': assignment,
    #     }

    #     if (targ_obj.target_type == 'vd'):
    #         srcurl = targ_obj.target_content
    #         if 'youtu' in srcurl:
    #             typeSource = 'video/youtube'
    #         else:
    #             disassembled = urlparse(srcurl)
    #             file_ext = splitext(basename(disassembled.path))[1]
    #             typeSource = 'video/' + file_ext.replace('.', '')
    #         original.update({'typeSource': typeSource})
    #     elif (targ_obj.target_type == 'ig'):
    #         original.update({'osd_json': targ_obj.target_content})
        
        collection_id = get_lti_value(settings.LTI_COLLECTION_ID, tool_provider)
        object_id = get_lti_value(settings.LTI_OBJECT_ID, tool_provider)
        save_session(request, user_id, collection_id, object_id, course, roles)
    '''
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
    '''
    #     return render(request, '%s/detail.html' % targ_obj.target_type, original)
    
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
        # Add user to course_users if not already there
        course_object.add_user(lti_profile)
        # Store course name in session
        request.session['course_name'] = course_object.course_name
    
    except LTICourse.DoesNotExist:
        # this should only happen if an instructor is trying to access the 
        # tool from a different course
        debug_printer('DEBUG - Course %s was NOT found. Will be created.' %course)
        message_error = "Sorry, the course you are trying to reach does not exist."
        messages.error(request, message_error)
        if set(roles) & set(settings.ADMIN_ROLES):
            # if the user is an administrator, the missing course is created
            # otherwise, it will just display an error message
            message_error = "Because you are an instructor, a course has been created for you, edit it below to add a proper name."
            messages.warning(request, message_error)
            course_object = LTICourse.create_course(course, lti_profile)
            # Set default course name to context title
            course_object.course_name = get_lti_value('context_title', tool_provider)
            course_object.save()
            # Store course name in session
            request.session['course_name'] = course_object.course_name

    
    # logs the user in
    lti_profile.user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, lti_profile.user)
    
    # Save id of current course in the session
    request.session['active_course'] = course
    save_session(request, user_id, "", "", "", roles)
    return course_admin_hub(request)
    #return redirect('hx_lti_initializer:course_admin_hub')


@login_required
def edit_course(request, id):
    course = get_object_or_404(LTICourse, pk=id)
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            course.save()
            
            request.session['course_name'] = course.course_name
            messages.success(request, 'Course was successfully edited!')
            return redirect('hx_lti_initializer:course_admin_hub')
        else:
            print("Rolled )))")
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
    #print "Course Admin Session: " + str(request.session.session_key)

    lti_profile = LTIProfile.objects.get(user=request.user)
    active_course = LTICourse.objects.filter(course_id=request.session['active_course'])
    files_in_courses = TOD_Implementation.get_dict_of_files_from_courses(lti_profile, list(active_course))

    try:
        is_instructor = request.session['is_instructor']
    except:
        is_instructor = False

    debug = files_in_courses
    return render(
        request,
        'hx_lti_initializer/testpage2.html',
        {
            'user': request.user,
            'email': request.user.email,
            'is_instructor': request.user and request.user.is_authenticated() and is_instructor,
            'roles': lti_profile.roles,
            'courses': list(active_course),
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
        
    try:
        is_instructor = request.session['is_instructor']
    except:
        is_instructor = False

    save_session(request, None, assignment_id, object_id, course_id, None)
    for item in request.session.keys():
        debug_printer('DEBUG SESSION - %s: %s \r' % (item, request.session[item]))
    original = {
        'user_id': user_id,
        'username': user_name,
        'is_instructor': request.user and request.user.is_authenticated() and is_instructor,
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

def instructor_dashboard_view(request):
    '''
        TODO
    '''
    lti_profile = LTIProfile.objects.get(user=request.user)
    active_course_id = request.session['active_course']
    active_course_object = LTICourse.objects.filter(course_id=active_course_id)
    # Gets object as opposed to queryset
    course = LTICourse.objects.get(course_id=active_course_id)
    assignments = Assignment.objects.filter(course=active_course_object)
    user_id = request.user.email #for some reason
    user_profiles = course.course_users.all()
    student_objects = []
    token = retrieve_token(user_id, settings.ANNOTATION_DB_API_KEY, settings.ANNOTATION_DB_SECRET_TOKEN)
    annotations_for_course = fetch_annotations(active_course_id, token)

    # get only the annotations for a specific user
    def filter_annotations(annotations, id):
        user_annotations = []
        for anno in annotations['rows']:
            a = anno['user']['id']
            if id == a:
                user_annotations.append(anno)
        return user_annotations

    for profile in user_profiles:
        student_objects.append({
            'student_name': profile,  #the model is set up to return the name of the user on a utf call
            'student_id': profile.get_id(),
            'annotations': filter_annotations(annotations_for_course, profile.get_id())
        })
    
    # Pass alphabetically sorted version of student_objects
    context = {
        'student_objects': sorted(student_objects, lambda x,y:cmp(str(x['student_name']).lower(), str(y['student_name']).lower())),
    }
    
    return render(request, 'hx_lti_initializer/dashboard_view.html', context)

 
def fetch_annotations (course_id, token):
    '''
        Fetches the annotations of a given course from the CATCH database
    '''
    
    headers = {"x-annotator-auth-token": token, "Content-Type":"application/json"}
    baseurl = settings.ANNOTATION_DB_URL + "/"
    requesturl = baseurl + "search?contextId=" + course_id
    
    # Make request
    r = requests.get(requesturl, headers=headers)
    debug_printer("DEBUG - Database Response: " + str(r))
    return r.json()
   
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
    
    return HttpResponse(message)
   # return render(request, 'hx_lti_initializer/error_page.html', context)


def delete_assignment(request):
    try:
        collection_id = request.POST['assignment_id']
        assignment = Assignment.objects.get(assignment_id=collection_id)
        assignment.delete()
        debug_printer("DEBUG - Assignment Deleted: " + unicode(assignment))
    except:
        return error_view(request, "Something went wrong with assignment deletion")
    
    return redirect('hx_lti_initializer:course_admin_hub')
    
######################
##
##  Annotation Database Methods
##
##  Creates a wall between the Annotation tool (mostly JS) and the backend
##  database, making it harder to spoof a request.
##
######################

def annotation_database_search(request):
    session_collection_id = request.session['hx_collection_id']
    session_object_id = request.session['hx_object_id']
    session_context_id = request.session['hx_context_id']

    request_collection_id = request.GET['collectionId']
    request_object_id = request.GET['uri']
    request_context_id = request.GET['contextId']

    # verifies the data queried against session so they can't get more than they should
    if (session_collection_id != request_collection_id
        or session_object_id != request_object_id
        or session_context_id != request_context_id):
        return HttpResponse("You are not authorized to search for annotations")

    collection_id = request.GET['collectionId']
    assignment = get_object_or_404(Assignment, assignment_id=collection_id)

    data = request.GET
    url_values = urllib.urlencode(data)
    debug_printer("URL Values: %s" % url_values)
    database_url = str(assignment.annotation_database_url).strip() + '/search?' + url_values 
    headers = {'x-annotator-auth-token': request.META['HTTP_X_ANNOTATOR_AUTH_TOKEN']}

    response = requests.post(database_url, headers=headers)

    return HttpResponse(response)

@csrf_exempt
def annotation_database_create(request):
    session_collection_id = request.session['hx_collection_id']
    session_object_id = str(request.session['hx_object_id'])
    session_context_id = request.session['hx_context_id']
    session_user_id = request.session['hx_user_id']

    json_body = json.loads(request.body)

    request_collection_id = json_body['collectionId']
    request_object_id = str(json_body['uri'])
    request_context_id = json_body['contextId']
    request_user_id = json_body['user']['id']

    debug_printer("%s: %s" % (session_user_id, request_user_id))
    debug_printer("%s: %s" % (session_collection_id, request_collection_id))
    debug_printer("%s: %s" % (session_object_id, request_object_id))
    debug_printer("%s: %s" % (session_context_id, request_context_id))

    # verifies the data queried against session so they can't get more than they should
    if (session_collection_id != request_collection_id
        or session_object_id != request_object_id
        or session_context_id != request_context_id
        or session_user_id != request_user_id):
        return HttpResponse("You are not authorized to create an annotation.")

    assignment = get_object_or_404(Assignment, assignment_id=session_collection_id)

    database_url = str(assignment.annotation_database_url).strip() + '/create'
    headers = {
        'x-annotator-auth-token': request.META['HTTP_X_ANNOTATOR_AUTH_TOKEN'],
        'content-type': 'application/json',
    }
    response = requests.post(database_url, data=json.dumps(json_body), headers=headers)

    return HttpResponse(response)

@csrf_exempt
def annotation_database_delete(request, annotation_id):
    session_user_id = request.session['hx_user_id']
    session_collection_id = request.session['hx_collection_id']
    json_body = json.loads(request.body)
    request_user_id = json_body['user']['id']

    debug_printer("%s: %s" % (session_user_id, request_user_id))

    # verifies the data queried against session so they can't get more than they should
    if (session_user_id != request_user_id):
        return HttpResponse("You are not authorized to create an annotation.")

    assignment = get_object_or_404(Assignment, assignment_id=session_collection_id)

    database_url = str(assignment.annotation_database_url).strip() + '/delete/' + str(annotation_id)
    headers = {
        'x-annotator-auth-token': request.META['HTTP_X_ANNOTATOR_AUTH_TOKEN'],
        'content-type': 'application/json',
    }
    response = requests.delete(database_url, headers=headers)

    return HttpResponse(response)

@csrf_exempt
def annotation_database_update(request, annotation_id):
    session_collection_id = request.session['hx_collection_id']
    session_object_id = str(request.session['hx_object_id'])
    session_context_id = request.session['hx_context_id']
    session_user_id = request.session['hx_user_id']

    json_body = json.loads(request.body)

    request_collection_id = json_body['collectionId']
    request_object_id = str(json_body['uri'])
    request_context_id = json_body['contextId']
    request_user_id = json_body['user']['id']

    debug_printer("%s %s %s" % (session_user_id, session_user_id != request_user_id, request_user_id))
    debug_printer("%s %s %s" % (session_collection_id, session_collection_id != request_collection_id,request_collection_id))
    debug_printer("%s %s %s" % (session_object_id, session_object_id != request_object_id, request_object_id))
    debug_printer("%s %s %s" % (session_context_id, session_context_id != request_context_id, request_context_id))

    # verifies the data queried against session so they can't get more than they should
    if (session_collection_id != request_collection_id
        or session_object_id != request_object_id
        or session_context_id != request_context_id
        or session_user_id != request_user_id):
        return HttpResponse("You are not authorized to create an annotation.")

    assignment = get_object_or_404(Assignment, assignment_id=session_collection_id)

    database_url = str(assignment.annotation_database_url).strip() + '/update/' + str(annotation_id)
    headers = {
        'x-annotator-auth-token': request.META['HTTP_X_ANNOTATOR_AUTH_TOKEN'],
        'content-type': 'application/json',
    }
    response = requests.post(database_url, data=json.dumps(json_body), headers=headers)

    return HttpResponse(response)
