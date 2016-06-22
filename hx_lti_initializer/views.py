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
from django.core.urlresolvers import reverse
from django.http import Http404
from django.contrib.auth import login
from django.contrib import messages
from django.db import IntegrityError

from target_object_database.models import TargetObject
from hx_lti_initializer.models import LTIProfile, LTICourse, User, LTICourseAdmin
from hx_lti_assignment.models import Assignment, AssignmentTargets
from hx_lti_initializer.forms import CourseForm
from hx_lti_initializer.utils import (debug_printer, get_lti_value, retrieve_token, save_session,create_new_user, initialize_lti_tool_provider,
    validate_request, fetch_annotations_by_course, get_admin_ids, DashboardAnnotations)
from hx_lti_initializer import annotation_database
from django.conf import settings
from abstract_base_classes.target_object_database_api import TOD_Implementation
from django.contrib.sites.models import get_current_site
from ims_lti_py.tool_provider import DjangoToolProvider

from urlparse import urlparse
import urllib2
import urllib
import json
import sys
import requests
import time

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

    # This is where we identify the "scope" of the LTI user_id (anon_id), meaning
    # the scope in which the identifier is unique. In canvas this is the domain instance,
    # where as in edX this is the course instance.
    #
    # The idea is that the combination of the LTI user_id (anon_id) and scope should be
    # globally unique.
    user_scope = None
    if settings.ORGANIZATION == "HARVARDX":
        user_scope = "course:%s" % course
    else:
        tool_consumer_instance_guid = get_lti_value('tool_consumer_instance_guid', tool_provider)
        if tool_consumer_instance_guid:
            user_scope = "consumer:%s" % tool_consumer_instance_guid
    debug_printer("DEBUG - user scope is: %s" % user_scope)

    # default to student
    request.session['is_instructor'] = False

    # this is where canvas will tell us what level individual is coming into
    # the tool the 'roles' field usually consists of just 'Instructor'
    # or 'Learner'
    roles = get_lti_value(settings.LTI_ROLES, tool_provider)
    debug_printer("DEBUG - user logging in with roles: " + str(roles))


    # This is the name that we will show on the UI
    display_name = get_lti_value('lis_person_name_full', tool_provider)
    if not display_name:
        display_name = get_lti_value('lis_person_sourcedid', tool_provider)

    # This is the unique identifier for the person in the source system
    # In canvas this would be the SIS user id, in edX the registered username
    external_user_id = get_lti_value('lis_person_sourcedid', tool_provider)

    # This handles the rare case in which we have neither display name nor external user id
    if not display_name or not external_user_id:
        try:
            lti_profile = LTIProfile.objects.get(anon_id=str(course))
            roles = ['student']
            display_name = lti_profile.user.username
            messages.warning(request, "edX still has not fixed issue with no user_id in studio.")
            messages.error(request, "Warning: you are logged in as a Preview user. Please view this in live to access admin hub.")
        except:
            debug_printer('DEBUG - username not found in post.')
            raise PermissionDenied()
    debug_printer("DEBUG - user name: " + display_name)
    lti_grade_url = get_lti_value('lis_outcome_service_url', tool_provider)
    if lti_grade_url is not None:
        save_session(request, is_graded=True)
    save_session(request, lti_params=request.POST)

    # Check whether user is a admin, instructor or teaching assistant
    if set(roles) & set(settings.ADMIN_ROLES):
        try:
            # See if the user already has a profile, and use it if so.
            lti_profile = LTIProfile.objects.get(anon_id=user_id)
            debug_printer('DEBUG - LTI Profile was found via anonymous id.')
        except LTIProfile.DoesNotExist:
            # if it's a new user (profile doesn't exist), set up and save a new LTI Profile
            debug_printer('DEBUG - LTI Profile NOT found. New User to be created.')
            user, lti_profile = create_new_user(anon_id=user_id, username=external_user_id, display_name=display_name, roles=roles, scope=user_scope)
            # log the user into the Django backend
        lti_profile.user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, lti_profile.user)
        save_session(
            request,
            user_id=user_id,
            user_name=display_name,
            user_scope=user_scope,
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
            user_name=display_name,
            user_scope=user_scope,
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
            context_title = None
            if get_lti_value('context_title', tool_provider) is not None:
                context_title = get_lti_value('context_title', tool_provider)
            course_object = LTICourse.create_course(course, lti_profile, name=context_title)
            create_new_user(anon_id=str(course), username='preview:%s' % course_object.id, display_name="Preview %s" % str(course_object), roles=['student'], scope=user_scope)

            # save the course name to the session so it auto-populate later.
            save_session(
                request,
                course_name=course_object.course_name,
                course_id=course_object.id,
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
            try:
                userfound = LTICourseAdmin.objects.get(
                    admin_unique_identifier=lti_profile.user.username,
                    new_admin_course_id=course
                )
                course_object.add_admin(lti_profile)
                debug_printer("DEBUG - CourseAdmin Pending found: %s" % userfound)
                userfound.delete()
            except:
                debug_printer("DEBUG - Not waiting to be added as admin")
            return course_admin_hub(request)
        else:
            debug_printer("DEBUG - User wants to go directly to annotations for a specific target object")
            return access_annotation_target(request, course_id, assignment_id, object_id)
    except:
        debug_printer("DEBUG - User wants the index")

    try:
        userfound = LTICourseAdmin.objects.get(
            admin_unique_identifier=lti_profile.user.username,
            new_admin_course_id=course
        )
        course_object.add_admin(lti_profile)
        debug_printer("DEBUG - CourseAdmin Pending found: %s" % userfound)
        userfound.delete()
    except:
        debug_printer("DEBUG - Not waiting to be added as admin")

    return course_admin_hub(request)


@login_required
def edit_course(request, id):
    course = get_object_or_404(LTICourse, pk=id)
    user_scope = request.session.get('hx_user_scope', None)
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            course.save()
            # this removes an administrator if they were checked off the list
            admins = course.course_admins.all()
            selected_list = request.POST.getlist('select_existing_user') + request.POST['new_admin_list'].split(',')
            for admin in admins:
                if admin.user.username not in selected_list:
                    course.course_admins.remove(admin)
                else:
                    selected_list.remove(admin.user.username)
            course.save()

            # this will create an item in the database so when the user
            # that was just added as an admin logs in, they get added
            # to the list of admins in the course.
            if len(selected_list) > 0:
                for name in selected_list:
                    if str(name.strip()) != "":
                        try:
                            new_course_admin = LTICourseAdmin(
                                admin_unique_identifier=name,
                                new_admin_course_id=course.course_id
                            )
                            new_course_admin.save()
                        except:
                            # admin already pending
                            debug_printer("Admin already pending.")

            # save the course name to the session so it auto-populate later.
            request.session['course_name'] = course.course_name

            messages.success(request, 'Course was successfully edited!')
            return redirect('hx_lti_initializer:course_admin_hub')
        else:
            raise PermissionDenied()
    else:
        form = CourseForm(instance=course, user_scope=user_scope)

    try:
        pending_admins = LTICourseAdmin.objects.filter(new_admin_course_id=course.course_id)
    except:
        pending_admins = None

    return render(
        request,
        'hx_lti_initializer/edit_course.html',
        {
            'form': form,
            'user': request.user,
            'pending': pending_admins,
            'org': settings.ORGANIZATION,
            'is_instructor': request.session["is_staff"],
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
        original['assignment_target'] = assignment_target

    if not assignment.object_after(object_id) is None:
        original['next_object'] = assignment.object_after(object_id)
        original['assignment_target'] = assignment_target

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

    original.update({
        'transcript_hidden': assignment_target.get_transcript_hidden()
    })

    original.update({
        'transcript_download': assignment_target.get_transcript_download()
    })

    original.update({
        'video_download': assignment_target.get_video_download()
    })

    get_paras = {}
    for k in request.GET.keys():
        get_paras[k] = request.GET[k]

    original.update(get_paras)
    return render(request, '%s/detail.html' % targ_obj.target_type, original)


def instructor_dashboard_view(request):
    '''
        Renders the instructor dashboard (without annotations).
    '''
    if not request.session['is_staff']:
        raise PermissionDenied("You must be a staff member to view the dashboard.")

    context_id = request.session['hx_context_id']
    user_id = request.session['hx_user_id']
    context = {
        'username': request.session['hx_user_name'],
        'is_instructor': request.session["is_staff"],
        'user_annotations': [],
        'fetch_annotations_time': 0,
        'dashboard_context_js': json.dumps({
            'student_list_view_url': reverse('hx_lti_initializer:instructor_dashboard_student_list_view'),
        })
    }
    return render(request, 'hx_lti_initializer/dashboard_view.html', context)

def instructor_dashboard_student_list_view(request):
    '''
    Renders the student annotations for the instructor dashboard.
    Intended to be called via AJAX.
    '''
    if not request.session['is_staff']:
        raise PermissionDenied("You must be a staff member to view the dashboard.")
    
    context_id = request.session['hx_context_id']
    user_id = request.session['hx_user_id']    
    
    # Fetch the annotations and time how long the request takes
    fetch_start_time = time.time()
    course_annotations = fetch_annotations_by_course(context_id, annotation_database.ADMIN_GROUP_ID)
    fetch_end_time = time.time()
    fetch_elapsed_time = fetch_end_time - fetch_start_time

    # Transform the raw annotation results into something useful for the dashboard
    user_annotations = DashboardAnnotations(course_annotations).get_annotations_by_user()
    context = {
        'username': request.session['hx_user_name'],
        'is_instructor': request.session["is_staff"],
        'user_annotations': user_annotations,
        'fetch_annotations_time': fetch_elapsed_time,
    }
    return render(request, 'hx_lti_initializer/dashboard_student_list_view.html', context)

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
    session_is_staff = request.session['is_staff']

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
        'x-annotator-auth-token': request.META['HTTP_X_ANNOTATOR_AUTH_TOKEN'],
        'content-type': 'application/json',
    }
    
    # Override the auth token for ATG when the user is a course administrator,
    # so they can query against private annotations that have granted permission to the admin group.
    if settings.ORGANIZATION == "ATG" and session_is_staff:
        headers['x-annotator-auth-token'] = retrieve_token(
            annotation_database.ADMIN_GROUP_ID,
            assignment.annotation_database_apikey,
            assignment.annotation_database_secret_token
        )

    response = requests.post(database_url, headers=headers, params=url_values)
    return HttpResponse(response.content, status=response.status_code, content_type='application/json')


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
    
    if settings.ORGANIZATION == "ATG":
        annotation_database.update_read_permissions(json_body)

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

    try:
        if request.session['is_graded'] and response.status_code == 200:
            consumer_key = settings.CONSUMER_KEY
            secret = settings.LTI_SECRET
            params = request.session['lti_params']
            tool_provider = DjangoToolProvider(consumer_key, secret, params)
            outcome = tool_provider.post_replace_result(1)
            debug_printer(u"LTI grade request was {successful}. Description is {description}".format(
                successful="successful" if outcome.is_success() else "unsuccessful", description=outcome.description
            ))
    except:
        debug_printer("is_graded was not found in the session")

    return HttpResponse(response.content, status=response.status_code, content_type='application/json')


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
    if settings.ORGANIZATION == "ATG":
        annotation_database.update_read_permissions(json_body)

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

    return HttpResponse(response.content, status=response.status_code, content_type='application/json')


@login_required
def transfer_annotations(request, instructor_only):
    session_is_staff = request.session['is_staff']
    user_id = request.session['hx_user_id']

    old_assignment_id = request.POST.get('old_assignment_id')
    new_assignment_id = request.POST.get('new_assignment_id')
    old_course_id = request.POST.get('old_course_id')
    new_course_id = request.POST.get('new_course_id')
    old_course = LTICourse.objects.get(course_id=old_course_id)
    new_course = LTICourse.objects.get(course_id=new_course_id)
    old_admins = []
    new_admins = dict()
    for ads in old_course.course_admins.all():
        old_admins.append(ads.anon_id)
    for ads in new_course.course_admins.all():
        new_admins[ads.name] = ads.anon_id

    assignment = Assignment.objects.get(assignment_id=old_assignment_id)
    object_ids = request.POST.getlist('object_ids[]')
    token = retrieve_token(
            user_id,
            assignment.annotation_database_apikey,
            assignment.annotation_database_secret_token
    )

    types = {
        "ig": "image",
        "tx": "text",
        "vd": "video"
    }
    responses = []
    for pk in object_ids:
        obj = TargetObject.objects.get(pk=pk)
        uri = pk
        target_type = types[obj.target_type]
        if target_type == "image":
            result = requests.get(obj.target_content)
            uri = json.loads(result.text)["sequences"][0]["canvases"][0]["@id"]
        search_database_url = str(assignment.annotation_database_url).strip() + '/search?'
        create_database_url = str(assignment.annotation_database_url).strip() + '/create'
        headers = {
            'x-annotator-auth-token': token,
            'content-type': 'application/json',
        }

        params = {
            'uri': uri,
            'contextId': old_course_id,
            'collectionId': old_assignment_id,
            'media': target_type,
            'limit': -1,
        }

        if str(instructor_only) == "1":
            params.update({'userid': old_admins})
        url_values = urllib.urlencode(params, True)
        response = requests.get(search_database_url, headers=headers, params=url_values)
        annotations = json.loads(response.text)
        for ann in annotations['rows']:
            ann['contextId'] = unicode(new_course_id)
            ann['collectionId'] = unicode(new_assignment_id)
            ann['id'] = None
            debug_printer("%s" % ann['user']['id'])
            if ann['user']['id'] in old_admins:
                try:
                    if new_admins[ann['user']['name']]:
                        ann['user']['id'] = new_admins[ann['user']['name']]
                except:
                    ann['user']['id'] = user_id
            response2 = requests.post(create_database_url, headers=headers, data=json.dumps(ann))

    #debug_printer("%s" % str(request.POST.getlist('assignment_inst[]')))
    data = dict()
    return HttpResponse(json.dumps(data), content_type='application/json')
