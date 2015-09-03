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
from hx_lti_initializer.utils import debug_printer, get_lti_value
from django.conf import settings
from abstract_base_classes.target_object_database_api import TOD_Implementation
from django.contrib.sites.models import get_current_site

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

# If we were to restructure (not recommended because then we can't reconcile with HX),
# these first 4 functions would be in utils.py
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
    
    try: 
        # both of these will give key errors if there is no key or it's the wrong key, respectively.
        consumer_key = req.POST['oauth_consumer_key']
        secret = settings.LTI_OAUTH_CREDENTIALS[consumer_key]
    except:
        debug_printer("DEBUG - authentication failed")
        raise PermissionDenied()
        
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

    # default to student
    request.session['is_instructor'] = False
    
    # this is where canvas will tell us what level individual is coming into the tool
    # the 'roles' field usually consists of just 'Instructor' or 'Learner'
    roles = get_lti_value(settings.LTI_ROLES, tool_provider)
    debug_printer("DEBUG - user logging in with roles: " + str(roles))
    
    # Set creator name, to be used later as default in addition of source material
    request.session['creator_default'] = get_lti_value('lis_person_name_full', tool_provider)

    # Check whether user is a admin, instructor or teaching assistant
    if set(roles) & set(settings.ADMIN_ROLES):
        # Set flag in session to later direct user to the appropriate version of the index
        request.session['is_instructor'] = True
        
        # For HX, students only access one object or collection, and don't have an index
        # For ATG, students have the index  to choose where to go, so collection_id
        # and object_id are probably blank for their session right now.
        collection_id = get_lti_value(settings.LTI_COLLECTION_ID, tool_provider)
        object_id = get_lti_value(settings.LTI_OBJECT_ID, tool_provider)
        save_session(request, user_id, collection_id, object_id, course, roles)
    
    try:
        # See if the user already has a profile, and use it if so.
        lti_profile = LTIProfile.objects.get(anon_id=user_id)
        debug_printer('DEBUG - LTI Profile was found via anonymous id.')
    
    except LTIProfile.DoesNotExist:
        # if it's a new user (profile doesn't exist), set up and save a new LTI Profile
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
        
        # Wait, this code might be pointless - is it just for printing the roles?
        # My guess is this was used for something earlier but was then made redundant.
        '''
        # checks to see if roles were passed in. Defaults to student role.
        all_user_roles = []
        if not roles:
            debug_printer('DEBUG - ALL_ROLES is set but user was not passed in any roles via the request. Defaults to student.')
            all_user_roles += "Student"
        else:
            # Make sure we're constructing the proper data type (list of strings)
            if not isinstance(roles, list):
                roles = [roles]
            all_user_roles += roles
        debug_printer('DEBUG - User had an acceptable role: %s' % all_user_roles)
        '''
        
        debug_printer("DEBUG - Creating a user with role(s): " + str(roles))
        
        user, lti_profile = create_new_user(lti_username, user_id, roles)
    
    # now it's time to deal with the course_id it does not associate
    # with users as they can flow in and out in a MOOC
    try:
        course_object = LTICourse.get_course_by_id(course)
        debug_printer('DEBUG - Course was found %s' % course)
        # Add user to course_users if not already there
        course_object.add_user(lti_profile)
        
        # save the course name to the session so it auto-populate later.
        request.session['course_name'] = course_object.course_name 
        
    except LTICourse.DoesNotExist:
        debug_printer('DEBUG - Course %s was NOT found. Will be created.' %course)
        
        # Put a message on the screen to indicate to the user that the course doesn't exist
        message_error = "Sorry, the course you are trying to reach does not exist."
        messages.error(request, message_error)
        
        if set(roles) & set(settings.ADMIN_ROLES):
            # This must be the instructor's first time accessing the annotation tool
            # Make him/her a new course within the tool
            
            message_error = "Because you are an instructor, a course has been created for you, please refresh the page to begin editing your course."
            messages.warning(request, message_error)
            
            # create and save a new course for the instructor, with a default name of their canvas course's name
            course_object = LTICourse.create_course(course, lti_profile)
            course_object.course_name = get_lti_value('context_title', tool_provider)
            course_object.save()
            
            # save the course name to the session so it auto-populate later.
            request.session['course_name'] = course_object.course_name 
            
            # Right now there's an issue where instructors have to refresh the page after creating
            # his/her course in order to recieve admin rights.
            # I Wanted to have a recursive call solve this, but I haven't been able to get it working.
            #return launch_lti(request)
            
    # log the user into the Django backend
    lti_profile.user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, lti_profile.user)
    
    # Save id of current course in the session so we know what data to display 
    # in course_admin_hub and instructor_dashboard_view
    request.session['active_course'] = course
    save_session(request, user_id, "", "", "", roles)
    
    # For the use case where the course head wants to display an assignment object instead
    # of the admin_hub upon launch (i.e. for embedded use), this allows the user
    # to be routed directly to an assignment given the correct POST parameters,
    # as by Luis' original method of putting collection_id and object_id in the
    # LTI tool launch params.
    try:
        # Keeping the HX functionality whereby students are routed to specific assignment objects
        # This is motivated by the Poetry in America Course
    
        # If there are variables passed into the launch indicating a desired target object, render that object
        assignment_id = get_lti_value(settings.LTI_COLLECTION_ID, tool_provider)
        object_id = get_lti_value(settings.LTI_OBJECT_ID, tool_provider)
        course_id = str(course)
        debug_printer("DEBUG - User wants to go directly to annotations for a specific target object")
        return access_annotation_target(request, course_id, assignment_id, object_id)
    except:
        debug_printer("DEBUG - User wants the index")
    
    return course_admin_hub(request)

@login_required
def edit_course(request, id):
    course = get_object_or_404(LTICourse, pk=id)
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            course.save()
            
            # save the course name to the session so it auto-populate later.
            request.session['course_name'] = course_object.course_name
            
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
    The index view for both students and instructors. Without the 'is_instructor' flag,
    students are directed to a version of admin_hub with reduced privileges
    """
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
    Renders an assignment page
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
        debug_printer("DEBUG - User attempted to access a non-existant Assignment or Target Object")
        raise PermissionDenied() 
        
    try:
        is_instructor = request.session['is_instructor']
    except:
        is_instructor = False

    save_session(request, None, assignment_id, object_id, course_id, None)
    for item in request.session.keys():
        debug_printer('DEBUG SESSION - %s: %s \r' % (item, request.session[item]))

    # Dynamically pass in the address that the detail view will use to fetch annotations.
    # there's definitely a more elegant way (or a library function) to do this.
    # also, we may want to consider denying if theres no ssl
    protocol = 'https://' if request.is_secure() else 'http://'
    abstract_db_url = protocol + get_current_site(request).domain + "/lti_init/annotation_api"
    debug_printer("DEBUG - Abstract Database URL: " + abstract_db_url)

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
        'abstract_db_url': abstract_db_url,
    }
    if not assignment.object_before(object_id) is None:
        original['prev_object'] = assignment.object_before(object_id)

    if not assignment.object_after(object_id) is None:
        original['next_object'] = assignment.object_after(object_id)

    # TODO: Currently image and video are not supported
    
    # if (targ_obj.target_type == 'vd'):
    #     srcurl = targ_obj.target_content
    #     if 'youtu' in srcurl:
    #         typeSource = 'video/youtube'
    #     else:
    #         disassembled = urlparse(srcurl)
    #         file_ext = splitext(basename(disassembled.path))[1]
    #         typeSource = 'video/' + file_ext.replace('.', '')
    #     original.update({'typeSource': typeSource})
    # elif (targ_obj.target_type == 'ig'):
    #     original.update({'osd_json': targ_obj.target_content})

    return render(request, '%s/detail.html' % targ_obj.target_type, original)

def instructor_dashboard_view(request):
    '''
        Renders the instructor dashboard
    '''
    # Get all the relevant objects we're going to need for the dashboard
    active_course_id = request.session['active_course']
    course = LTICourse.objects.get(course_id=active_course_id)
    user_id = request.user.email #for some reason
    user_profiles = course.course_users.all()
    
    # Authenticate and fetch the annotations for this course
    token = retrieve_token(user_id, settings.ANNOTATION_DB_API_KEY, settings.ANNOTATION_DB_SECRET_TOKEN)
    annotations_for_course = fetch_annotations(active_course_id, token)

    # Dictionary of annotations, keyed by id of annotation for O(1) lookup later
    annotation_dict = {}
    
    # get only the annotations for a specific user, while at the same updating annotation_dict
    def filter_annotations(annotations, id):
        user_annotations = []
        for anno in annotations['rows']:
            # Insert into annotation dictionary
            annotation_dict[unicode(anno['id'])] = anno
            # Get id of user who made the annotation
            a = anno['user']['id']
            # If id matches, append to list of annotations for that user
            if id == a:
                user_annotations.append(anno)
        return user_annotations

    # Create an object/dict for each user that contains his/her name, id, and annotations.
    user_objects = []
    for profile in user_profiles:
        user_objects.append({
            # A user_object is a dictionary containing name, id and annotations for a user
            'name': unicode(profile),  #the model is set up to return the name of the user on a unicode call.
            'id': profile.get_id(),
            'annotations': filter_annotations(annotations_for_course, profile.get_id())
        })
    
    context = {
        # Pass alphabetically sorted version of user_objects
        'user_objects': sorted(user_objects, lambda x,y:cmp(str(x['name']).lower(), str(y['name']).lower())),
        # Dictionary of annotations, keyed by id for easy reply lookup
        'annotation_dict': annotation_dict,
    }
    
    return render(request, 'hx_lti_initializer/dashboard_view.html', context)

 
def fetch_annotations (course_id, token):
    '''
        Fetches the annotations of a given course from the CATCH database
    '''
    
    
    
    # build request
    
    headers = {"x-annotator-auth-token": token, "Content-Type":"application/json"}
    baseurl = settings.ANNOTATION_DB_URL + "/"
    limit = 10000 #TODO: How do we want to handle this?
    requesturl = baseurl + "search?contextId=" + course_id + "&limit=" + str(limit)
    
    # Make request
    r = requests.get(requesturl, headers=headers)
    debug_printer("DEBUG - Database Response: " + str(r))
    
    try:
        # this gets the whole request, including such things as 'count'
        # however, that also means that the annotations come in as an object called 'rows,'
        # where each row represents an annotation object.
        # if more convenient, we could cut the top level and just return flat annotations.
        annotations = r.json()
    except:
        # If there are no annotations, the database should return a dictionary with empty rows,
        # but in the event of another exception such as an authentication error, fail
        # gracefully by manually passing in that empty response
        annotations = {'rows':[]}
        logging.error('Error decoding JSON from CATCH. Check to see if authentication is correctly configured')
        
    return annotations


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


def delete_assignment(request):
    """
        Assignment deletion from Postgres databases
    """
    try:
        collection_id = request.POST['assignment_id']
        assignment = Assignment.objects.get(assignment_id=collection_id)
        assignment.delete()
        debug_printer("DEBUG - Assignment Deleted: " + unicode(assignment))
    except:
        return error_view(request, "The assignment deletion may have failed")
    
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

    url_values = request.GET.urlencode()
    database_url = str(assignment.annotation_database_url).strip() + '/search?'
    headers = {'x-annotator-auth-token': request.META['HTTP_X_ANNOTATOR_AUTH_TOKEN']}

    response = requests.post(database_url, headers=headers, params=url_values)
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
    
    admin_ids = get_admin_ids()
    
    # verifies the data queried against session so they can't get more than they should
    # Give admins universal delete privilege
    if (session_user_id != request_user_id and session_user_id not in admin_ids):
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

    admin_ids = get_admin_ids()
    
    # Give admins universal edit privileges
    # verifies the data queried against session so they can't get more than they should
    if (session_collection_id != request_collection_id
        or session_object_id != request_object_id
        or session_context_id != request_context_id
        or (session_user_id != request_user_id and session_user_id not in admin_ids)):
        return HttpResponse("You are not authorized to create an annotation.")

    assignment = get_object_or_404(Assignment, assignment_id=session_collection_id)

    database_url = str(assignment.annotation_database_url).strip() + '/update/' + str(annotation_id)
    headers = {
        'x-annotator-auth-token': request.META['HTTP_X_ANNOTATOR_AUTH_TOKEN'],
        'content-type': 'application/json',
    }
    response = requests.post(database_url, data=json.dumps(json_body), headers=headers)

    return HttpResponse(response)
    
def get_admin_ids():
    """
        Returns a set of the user ids of all users with an admin role
    """
    admins = []
    admin_ids = set()
    
    # Get users with an admin role
    for role in settings.ADMIN_ROLES:
        admins += list(LTIProfile.objects.filter(roles=role))
    
    # Add their ids to admin_ids
    for admin in admins:
        admin_ids.add(admin.get_id())
    
    return admin_ids
