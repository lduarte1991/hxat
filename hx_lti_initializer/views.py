"""
This will launch the LTI Annotation tool.

This is basically the controller part of the app.
It will set up the tool provider, create/retrive the user and pass along any
other information that will be rendered to the access/init screen to the user.
"""

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
from hx_lti_initializer.models import LTIProfile, LTICourse, User
from hx_lti_assignment.models import Assignment, AssignmentTargets
from hx_lti_initializer.forms import CourseForm
from hx_lti_initializer.utils import (debug_printer, get_lti_value, retrieve_token,
    save_session, create_new_user, initialize_lti_tool_provider, validate_request,
    fetch_annotations_by_course, get_annotations_keyed_by_user_id, get_annotations_keyed_by_annotation_id,
    get_distinct_users_from_annotations)
from django.conf import settings
from abstract_base_classes.target_object_database_api import TOD_Implementation
from django.contrib.sites.models import get_current_site

from urlparse import urlparse
import urllib2
import urllib
import json
import sys
import requests

import logging
logging.basicConfig()


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
    user_id = get_lti_value('user_id', tool_provider)
    debug_printer('DEBUG - Found anonymous ID in request: %s' % user_id)

    course = get_lti_value(settings.LTI_COURSE_ID, tool_provider)
    debug_printer('DEBUG - Found course being accessed: %s' % course)

    # default to student
    request.session['is_instructor'] = False

    # this is where canvas will tell us what level individual is coming into
    # the tool the 'roles' field usually consists of just 'Instructor'
    # or 'Learner'
    roles = get_lti_value(settings.LTI_ROLES, tool_provider)
    debug_printer("DEBUG - user logging in with roles: " + str(roles))

    lti_username = get_lti_value('lis_person_name_full', tool_provider)
    if lti_username is None:
        lti_username = get_lti_value('lis_person_sourcedid', tool_provider)
        if not lti_username:
            debug_printer('DEBUG - user_id not found in post.')
            raise PermissionDenied()

    # Check whether user is a admin, instructor or teaching assistant
    if set(roles) & set(settings.ADMIN_ROLES):
        try:
            # See if the user already has a profile, and use it if so.
            lti_profile = LTIProfile.objects.get(anon_id=user_id)
            debug_printer('DEBUG - LTI Profile was found via anonymous id.')
        except LTIProfile.DoesNotExist:
            # if it's a new user (profile doesn't exist), set up and save a new LTI Profile
            debug_printer('DEBUG - LTI Profile not found. New User to be created.')
            debug_printer("DEBUG - Creating a user with role(s): " + str(roles))
            user, lti_profile = create_new_user(lti_username, user_id, roles)
            # log the user into the Django backend
        lti_profile.user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, lti_profile.user)
        save_session(
            request,
            user_id=user_id,
            user_name=lti_username,
            context_id=course,
            roles=roles,
            is_staff=True
        )
    else:
        # For HX, students only access one object or collection, and don't
        # have an index
        # For ATG, students have the index  to choose where to go, so
        # collection_id and object_id are probably blank for their session
        # right now.
        collection_id = get_lti_value(
            settings.LTI_COLLECTION_ID,
            tool_provider
        )
        object_id = get_lti_value(
            settings.LTI_OBJECT_ID,
            tool_provider
        )
        save_session(
            request,
            user_id=user_id,
            user_name=lti_username,
            context_id=course,
            roles=roles,
            is_staff=False
        )

    # now it's time to deal with the course_id it does not associate
    # with users as they can flow in and out in a MOOC
    try:
        course_object = LTICourse.get_course_by_id(course)
        debug_printer('DEBUG - Course was found %s' % course)

        # save the course name to the session so it auto-populate later.
        save_session(
            request,
            course_name=course_object.course_name,
            course_id=course_object.id,
        )

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
            if get_lti_value('context_title', tool_provider) is not None:
                course_object.course_name = get_lti_value('context_title', tool_provider)
                course_object.save()

                # save the course name to the session so it auto-populate later.
                save_session(
                    request,
                    course_name=course_object.course_name,
                    hx_lti_course_id=course_object.id,
                )

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
        if set(roles) & set(settings.ADMIN_ROLES):
            return course_admin_hub(request)
        else:
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
            request.session['course_name'] = course.course_name

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


def course_admin_hub(request):
    """
    The index view for both students and instructors. Without the 'is_instructor' flag,
    students are directed to a version of admin_hub with reduced privileges
    """
    courses_for_user = LTICourse.objects.filter(course_id=request.session['hx_context_id'])
    files_in_courses = TOD_Implementation.get_dict_of_files_from_courses(
        courses_for_user
    )

    debug = files_in_courses
    return render(
        request,
        'hx_lti_initializer/admin_hub.html',
        {
            'username': request.session['hx_user_name'],
            'is_instructor': request.session["is_staff"],
            'roles': request.session["hx_roles"],
            'courses': courses_for_user,
            'files': files_in_courses,
            'org': settings.ORGANIZATION,
            'debug': debug,
        }
    )


def access_annotation_target(
        request, course_id, assignment_id,
        object_id, user_id=None, user_name=None, roles=None):
    """
    Renders an assignment page
    """
    if user_id is None:
        user_name = request.session["hx_user_name"]
        user_id = request.session["hx_user_id"]
        roles = request.session["hx_roles"]
    try:
        assignment = Assignment.objects.get(assignment_id=assignment_id)
        targ_obj = TargetObject.objects.get(pk=object_id)
        assignment_target = AssignmentTargets.objects.get(
            assignment=assignment,
            target_object=targ_obj
        )
        course_obj = LTICourse.objects.get(course_id=course_id)
    except Assignment.DoesNotExist or TargetObject.DoesNotExist:
        debug_printer("DEBUG - User attempted to access a non-existant Assignment or Target Object")
        raise PermissionDenied()
    try:
        is_instructor = request.session['is_instructor']
    except:
        is_instructor = False

    save_session(
        request,
        collection_id=assignment_id,
        object_id=object_id,
        context_id=course_id,
    )
    for item in request.session.keys():
        debug_printer(
            u'DEBUG SESSION - %s: %s \r' % (item, request.session[item])
        )

    # Dynamically pass in the address that the detail view will use to fetch annotations.
    # there's definitely a more elegant way (or a library function) to do this.
    # also, we may want to consider denying if theres no ssl
    protocol = 'https://' if request.is_secure() else 'http://'
    abstract_db_url = protocol + get_current_site(request).domain + "/lti_init/annotation_api"
    debug_printer("DEBUG - Abstract Database URL: " + abstract_db_url)

    original = {
        'user_id': user_id,
        'username': user_name,
        'is_instructor': request.session["is_staff"],
        'collection': assignment_id,
        'course': course_id,
        'object': object_id,
        'target_object': targ_obj,
        'token': retrieve_token(
            user_id,
            assignment.annotation_database_apikey,
            assignment.annotation_database_secret_token
        ),
        'assignment': assignment,
        'roles': roles,
        'instructions': assignment_target.target_instructions,
        'abstract_db_url': abstract_db_url,
        'org': settings.ORGANIZATION,
    }
    if not assignment.object_before(object_id) is None:
        original['prev_object'] = assignment.object_before(object_id)

    if not assignment.object_after(object_id) is None:
        original['next_object'] = assignment.object_after(object_id)

    if targ_obj.target_type == 'vd':
        srcurl = targ_obj.target_content
        if 'youtu' in srcurl:
            typeSource = 'video/youtube'
        else:
            disassembled = urlparse(srcurl)
            file_ext = splitext(basename(disassembled.path))[1]
            typeSource = 'video/' + file_ext.replace('.', '')
        original.update({'typeSource': typeSource})
    elif targ_obj.target_type == 'ig':
        original.update({'osd_json': targ_obj.target_content})
        viewtype = assignment_target.get_view_type_for_mirador()
        canvas_id = assignment_target.get_canvas_id_for_mirador()

        if viewtype is not None:
            original.update({'viewType': viewtype})
        if canvas_id is not None:
            original.update({'canvas_id': canvas_id})

    if assignment_target.target_external_css:
        original.update({
            'custom_css': assignment_target.target_external_css
        })
    elif course_obj.course_external_css_default:
        original.update({
            'custom_css': course_obj.course_external_css_default
        })

    original.update({
            'dashboard_hidden': assignment_target.get_dashboard_hidden()
        })

    return render(request, '%s/detail.html' % targ_obj.target_type, original)


def instructor_dashboard_view(request):
    '''
        Renders the instructor dashboard
    '''
    # Get all the relevant objects we're going to need for the dashboard
    user_id = request.session['hx_user_id']
    context_id = request.session['hx_context_id']
    course_object = LTICourse.objects.get(course_id=context_id)
    token = retrieve_token(user_id, settings.ANNOTATION_DB_API_KEY, settings.ANNOTATION_DB_SECRET_TOKEN)
    course_annotations = fetch_annotations_by_course(context_id, token)
    
    # Transform the data
    annotations_by_user = get_annotations_keyed_by_user_id(course_annotations)
    annotations_by_anno = get_annotations_keyed_by_annotation_id(course_annotations)
    annotation_users    = get_distinct_users_from_annotations(course_annotations)

    user_objects = [{
        'id': user['id'],
        'name': user['name'],
        'annotations': annotations_by_user[user['id']],
    } for user in annotation_users]

    user_objects = list(sorted(user_objects, key=lambda user: user['name'].lower()))

    context = {
        'username': request.session['hx_user_name'],
        'is_instructor': request.session["is_staff"],
        'user_objects': user_objects, # user objects with their associated annotations
        'annotation_dict': annotations_by_anno, # annotations keyed by id for easy reply lookup
    }

    return render(request, 'hx_lti_initializer/dashboard_view.html', context)


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
#
#  Annotation Database Methods
##
#  Creates a wall between the Annotation tool (mostly JS) and the backend
#  database, making it harder to spoof a request.
##
######################


def annotation_database_search(request):
    '''
    This view is intended to be called by the annotation dashboard when searching
    the CATCH database for annotations.
    
    It's essentially a proxy for annotatorJS requests, with a permission check to
    make sure the user is authorized to search the given course and collection.
    
    Required GET parameters:
     - collectionId: this is the assignment model
     - contextId: this is the course identifier as defined by LTI (the "course context")
    
    The optional GET parameters include those specified by the CATCH database as
    search fields.
    '''
    session_collection_id = request.session['hx_collection_id']
    session_context_id = request.session['hx_context_id']

    request_collection_id = request.GET.get('collectionId', None)
    request_context_id = request.GET.get('contextId', None)

    # verifies the query against session so they can't get unauthorized items
    if (session_collection_id != request_collection_id or
            session_context_id != request_context_id):
        return HttpResponse("You are not authorized to search for annotations")

    assignment = get_object_or_404(Assignment, assignment_id=request_collection_id)

    url_values = request.GET.urlencode()
    database_url = str(assignment.annotation_database_url).strip() + '/search?'
    headers = {
        'x-annotator-auth-token': request.META['HTTP_X_ANNOTATOR_AUTH_TOKEN']
    }

    response = requests.post(database_url, headers=headers, params=url_values)
    return HttpResponse(response)


@csrf_exempt
def annotation_database_create(request):
    session_collection_id = request.session['hx_collection_id']
    session_object_id = str(request.session['hx_object_id'])
    session_context_id = request.session['hx_context_id']
    session_user_id = request.session['hx_user_id']
    session_is_staff = request.session['is_staff']

    json_body = json.loads(request.body)

    request_collection_id = json_body['collectionId']
    request_object_id = str(json_body['uri'])
    request_context_id = json_body['contextId']
    request_user_id = json_body['user']['id']

    debug_printer("%s: %s" % (session_user_id, request_user_id))
    debug_printer("%s: %s" % (session_collection_id, request_collection_id))
    debug_printer("%s: %s" % (session_object_id, request_object_id))
    debug_printer("%s: %s" % (session_context_id, request_context_id))

    # verifies the query against session so they can't get unauthorized items
    if (session_collection_id != request_collection_id or
            session_context_id != request_context_id or
            (session_user_id != request_user_id and not session_is_staff)):
        return HttpResponse("You are not authorized to create an annotation.")

    assignment = get_object_or_404(
        Assignment,
        assignment_id=session_collection_id
    )

    database_url = str(assignment.annotation_database_url).strip() + '/create'
    headers = {
        'x-annotator-auth-token': request.META['HTTP_X_ANNOTATOR_AUTH_TOKEN'],
        'content-type': 'application/json',
    }
    response = requests.post(
        database_url,
        data=json.dumps(json_body),
        headers=headers
    )

    return HttpResponse(response)


@csrf_exempt
def annotation_database_delete(request, annotation_id):
    session_user_id = request.session['hx_user_id']
    session_collection_id = request.session['hx_collection_id']
    session_is_staff = request.session['is_staff']
    try:
        json_body = json.loads(request.body)
        request_user_id = json_body['user']['id']

        debug_printer("%s: %s" % (session_user_id, request_user_id))

        # verifies queries against session so they can't get unauthorized items
        if (session_user_id != request_user_id and not session_is_staff):
            return HttpResponse("You are not allowed to create an annotation.")
    except:
        debug_printer("Probably a Mirador instance")
    assignment = get_object_or_404(
        Assignment,
        assignment_id=session_collection_id
    )

    database_url = str(assignment.annotation_database_url).strip() +\
        '/delete/' + str(annotation_id)
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
    session_is_staff = request.session['is_staff']

    json_body = json.loads(request.body)

    request_collection_id = json_body['collectionId']
    request_object_id = str(json_body['uri'])
    request_context_id = json_body['contextId']
    request_user_id = json_body['user']['id']

    debug_printer("%s %s %s" % (session_user_id, session_user_id != request_user_id, request_user_id))  # noqa
    debug_printer("%s %s %s" % (session_collection_id, session_collection_id != request_collection_id, request_collection_id))  # noqa
    debug_printer("%s %s %s" % (session_object_id, session_object_id != request_object_id, request_object_id))  # noqa
    debug_printer("%s %s %s" % (session_context_id, session_context_id != request_context_id, request_context_id))  # noqa

    # verifies query against session so they can't get more than they should
    if (session_collection_id != request_collection_id or
            session_context_id != request_context_id or
            (session_user_id != request_user_id and not session_is_staff)):
    # TODO: ADD MORE CHECKS HERE, TOOK OUT OBJECT AND CONTEXT BECAUSE OF IMG ANNOTATIONS
    # Give admins universal edit privileges
    # verifies the data queried against session so they can't get more than they should
    # if (session_collection_id != request_collection_id
    #     or session_object_id != request_object_id
    #     or session_context_id != request_context_id
    #     or (session_user_id != request_user_id and session_user_id not in admin_ids)):
        return HttpResponse("You are not authorized to create an annotation.")

    assignment = get_object_or_404(
        Assignment,
        assignment_id=session_collection_id
    )

    database_url = str(assignment.annotation_database_url).strip() + \
        '/update/' + str(annotation_id)
    headers = {
        'x-annotator-auth-token': request.META['HTTP_X_ANNOTATOR_AUTH_TOKEN'],
        'content-type': 'application/json',
    }
    response = requests.post(
        database_url,
        data=json.dumps(json_body),
        headers=headers
    )

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
