"""
This will launch the LTI Annotation tool.

This is basically the controller part of the app.
It will set up the tool provider, create/retrive the user and pass along any
other information that will be rendered to the access/init screen to the user.
"""

from abstract_base_classes.target_object_database_api import TOD_Implementation
from hxat.exceptions import AnnotationTargetDoesNotExist
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.templatetags.static import static
from django.core.exceptions import MultipleObjectsReturned, PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from hx_lti_assignment.models import Assignment, AssignmentTargets
from hx_lti_initializer.forms import CourseForm, EmbedLtiSelectionForm, EmbedLtiResponseForm
from hx_lti_initializer.models import (
    LTICourse,
    LTICourseAdmin,
    LTIProfile,
    LTIResourceLinkConfig,
)
from hx_lti_initializer.utils import (
    DashboardAnnotations,
    create_new_user,
    fetch_annotations_by_course,
    retrieve_token,
    save_session,
)
from lti import ToolConfig
from target_object_database.models import TargetObject

try:
    from django.contrib.sites.models import get_current_site
except ImportError:
    from django.contrib.sites.shortcuts import get_current_site

import json
import logging
import os.path
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@csrf_exempt
def launch_lti(request):
    """
    Gets a request from an LTI consumer.
    Passes along information to render a welcome screen to the user.

    Assumptions: LTI launch request has already been validated by middleware
    """

    # collect anonymous_id and consumer key in order to fetch LTIProfile
    # if it exists, we initialize the tool otherwise, we create a new user
    user_id = request.LTI["launch_params"]["user_id"]
    logger.debug("DEBUG - Found anonymous ID in request: %s" % user_id)

    course = request.LTI["launch_params"][settings.LTI_COURSE_ID]
    logger.debug("DEBUG - Found course being accessed: %s" % course)

    resource_link_id = request.LTI["launch_params"]["resource_link_id"]

    # This is where we identify the "scope" of the LTI user_id (anon_id), meaning
    # the scope in which the identifier is unique. In canvas this is the domain instance,
    # where as in edX this is the course instance.
    #
    # The idea is that the combination of the LTI user_id (anon_id) and scope should be
    # globally unique.
    # 28aug20 naomi: see [1] at the bottom of file
    if settings.ORGANIZATION == "HARVARDX":  # meaning, edx
        user_scope = "course:{}".format(course)
    else:  # assumes canvas
        tool_consumer_instance_guid = request.LTI["launch_params"].get(
            "tool_consumer_instance_guid", None
        )
        if tool_consumer_instance_guid:
            user_scope = "consumer:{}".format(tool_consumer_instance_guid)
        else:
            logger.debug(
                "organization({}) using user_scope:course({})".format(
                    settings.ORGANIZATION, course
                )
            )
            user_scope = "course:{}".format(course)
    logger.debug("DEBUG - user scope is: %s" % user_scope)

    # default to student
    save_session(request, is_staff=False)

    # this is where canvas will tell us what level individual is coming into
    # the tool the 'roles' field usually consists of just 'Instructor'
    # or 'Learner'
    roles = request.LTI["launch_params"][settings.LTI_ROLES]
    logger.debug("DEBUG - user logging in with roles: " + str(roles))

    # This is the name that we will show on the UI if provided...
    # EDX-NOTE: edx does not return the person's name!
    display_name = request.LTI["launch_params"].get("lis_person_name_full", None)
    if not display_name:
        display_name = request.LTI["launch_params"].get("lis_person_sourcedid", "")

    # This is the unique identifier for the person in the source system
    # In canvas this would be the SIS user id, in edX the registered username
    external_user_id = request.LTI["launch_params"].get("lis_person_sourcedid", "")

    # This handles the rare case in which we have neither display name nor external user id
    if not (display_name or external_user_id):
        try:
            lti_profile = LTIProfile.objects.get(anon_id=str(course))
        except LTIProfile.DoesNotExist:
            logger.error("username({}) not found.".format(course))
            raise PermissionDenied("username not found in LTI launch")
        except MultipleObjectsReturned as e:
            logger.error(
                "unable to guess username for course({}): {}".format(course, e)
            )
            raise PermissionDenied("unable to find username")
        else:
            roles = ["student"]
            display_name = lti_profile.user.username
            messages.warning(
                request, "edX still has not fixed issue with no user_id in studio."
            )
            messages.error(
                request,
                "Warning: you are logged in as a Preview user. Please view this in live to access admin hub.",
            )
    logger.debug("DEBUG - user name: " + display_name)

    # Check whether user is a admin, instructor or teaching assistant
    if set(roles) & set(settings.ADMIN_ROLES):
        try:
            # See if the user already has a profile, and use it if so.
            lti_profile = LTIProfile.objects.get(anon_id=user_id)
            logger.debug("DEBUG - LTI Profile was found via anonymous id.")
        except LTIProfile.DoesNotExist:
            # if it's a new user (profile doesn't exist), set up and save a new LTI Profile
            logger.debug("DEBUG - LTI Profile NOT found. New User to be created.")
            user, lti_profile = create_new_user(
                anon_id=user_id,
                username=external_user_id,
                display_name=display_name,
                roles=roles,
                scope=user_scope,
            )
            # log the user into the Django backend
        lti_profile.user.backend = "django.contrib.auth.backends.ModelBackend"
        saved_lti_launches = request.session["LTI_LAUNCH"]
        login(request, lti_profile.user)
        request.session.setdefault("LTI_LAUNCH", saved_lti_launches)
        save_session(
            request,
            user_id=user_id,
            user_name=display_name,
            user_scope=user_scope,
            context_id=course,
            roles=roles,
            is_staff=True,
            resource_link_id=resource_link_id,
        )
    else:
        # For HX, students only access one object or collection, and don't
        # have an index
        # For ATG, students have the index  to choose where to go, so
        # collection_id and object_id are probably blank for their session
        # right now.
        collection_id = request.LTI["launch_params"].get(settings.LTI_COLLECTION_ID)
        object_id = request.LTI["launch_params"].get(settings.LTI_OBJECT_ID)
        save_session(
            request,
            user_id=user_id,
            user_name=display_name,
            user_scope=user_scope,
            context_id=course,
            roles=roles,
            is_staff=False,
            resource_link_id=resource_link_id,
        )

    # now it's time to deal with the course_id it does not associate
    # with users as they can flow in and out in a MOOC
    try:
        course_object = LTICourse.get_course_by_id(course)
        logger.debug("DEBUG - Course was found %s" % course)

        # save the course name to the session so it auto-populate later.
        save_session(
            request,
            course_name=course_object.course_name,
            course_id=course_object.id,
        )

    except LTICourse.DoesNotExist:
        logger.debug("DEBUG - Course {} was NOT found. Will be created.".format(course))

        # Put a message on the screen to indicate to the user that the course doesn't exist
        message_error = "Sorry, the course you are trying to reach does not exist."
        messages.error(request, message_error)

        if set(roles) & set(settings.ADMIN_ROLES):
            # This must be the instructor's first time accessing the annotation tool
            # Make him/her a new course within the tool

            message_error = "Because you are an instructor, a course has been created for you, please refresh the page to begin editing your course."
            messages.warning(request, message_error)

            # create and save a new course for the instructor, with a default name of their canvas course's name
            context_title = "noname-{}".format(time.time())  # random name as anon_id
            if "context_title" in request.LTI["launch_params"]:
                context_title = request.LTI["launch_params"]["context_title"]
            course_object = LTICourse.create_course(
                course, lti_profile, name=context_title
            )
            create_new_user(
                anon_id=str(course),
                username="preview:{}".format(course_object.id),
                display_name="Preview {}".format(course_object),
                roles=["student"],
                scope=user_scope,
            )

            # save the course name to the session so it auto-populate later.
            save_session(
                request,
                course_name=course_object.course_name,
                course_id=course_object.id,
            )
        else:
            logger.info("Course not created because user does not have an admin role")
    try:
        logger.debug("DEBUG *-* resource_link_id={}".format(resource_link_id))
        config = LTIResourceLinkConfig.objects.get(resource_link_id=resource_link_id)
        collection_id = config.assignment_target.assignment.assignment_id
        object_id = config.assignment_target.target_object_id
        logger.debug(
            "DEBUG - LTIResourceLinkConfig: resource_link_id=%s collection_id=%s object_id=%s"
            % (resource_link_id, collection_id, object_id)
        )
        course_id = str(course)
        if set(roles) & set(settings.ADMIN_ROLES):
            try:
                userfound = LTICourseAdmin.objects.get(
                    admin_unique_identifier=lti_profile.user.username,
                    new_admin_course_id=course,
                )
                course_object.add_admin(lti_profile)
                logger.info("CourseAdmin Pending found: %s" % userfound)
                userfound.delete()
            except Exception as e:
                logger.info("Not waiting to be added as Admin: {}".format(e))
        logger.debug(
            "DEBUG - User wants to go directly to annotations for a specific target object using UI"
        )
        url = reverse(
            "hx_lti_initializer:access_annotation_target",
            args=[course_id, collection_id, object_id],
        )
        url += "?resource_link_id={}&utm_source={}".format(
            resource_link_id, request.session.session_key
        )
        return redirect(url)
    except AnnotationTargetDoesNotExist as e:
        logger.warning("Could not access annotation target using resource config.")
        logger.info("Deleting resource config because it is invalid.")
        LTIResourceLinkConfig.objects.filter(resource_link_id=resource_link_id).delete()
        logger.info("Proceed to the admin hub.")
    except PermissionDenied as e:
        raise e  # make sure to re-raise this exception since we shouldn't proceed
    except Exception as e:
        logger.debug("****** exception: {}".format(e))
        # For the use case where the course head wants to display an assignment object instead
        # of the admin_hub upon launch (i.e. for embedded use), this allows the user
        # to be routed directly to an assignment given the correct POST parameters,
        # as by Luis' original method of putting collection_id and object_id in the
        # LTI tool launch params.
        try:
            # Keeping the HX functionality whereby students are routed to specific assignment objects
            # This is motivated by the Poetry in America Course

            # If there are variables passed into the launch indicating a desired target object, render that object
            assignment_id = request.LTI["launch_params"].get(settings.LTI_COLLECTION_ID)
            object_id = request.LTI["launch_params"].get(settings.LTI_OBJECT_ID)
            if not assignment_id and not object_id:
                assignment_id = request.GET.get(settings.LTI_COLLECTION_ID)
                object_id = request.GET.get(settings.LTI_OBJECT_ID)
                if not assignment_id and not object_id:
                    logger.debug("no assignment object")
                    raise Exception("Assignment object not specified")
            course_id = str(course)
            if set(roles) & set(settings.ADMIN_ROLES):
                try:
                    userfound = LTICourseAdmin.objects.get(
                        admin_unique_identifier=lti_profile.user.username,
                        new_admin_course_id=course,
                    )
                    course_object.add_admin(lti_profile)
                    logger.info("CourseAdmin Pending found: %s" % userfound)
                    userfound.delete()
                except Exception as e:
                    logger.info(
                        "Not waiting to be added as admin: {}".format(e), exc_info=False
                    )
            logger.debug(
                "DEBUG - User wants to go directly to annotations for a specific target object({}--{}--{}".format(
                    course_id, assignment_id, object_id
                )
            )
            url = reverse(
                "hx_lti_initializer:access_annotation_target",
                args=[course_id, assignment_id, object_id],
            )
            url += "?resource_link_id={}&utm_source={}".format(
                resource_link_id, request.session.session_key
            )
            return redirect(url)
        except Exception as e:
            logger.debug(
                "DEBUG - User wants the index: {} --- {}".format(type(e), e),
                exc_info=False,
            )

    try:
        userfound = LTICourseAdmin.objects.get(
            admin_unique_identifier=lti_profile.user.username,
            new_admin_course_id=course,
        )
        course_object.add_admin(lti_profile)
        logger.info("CourseAdmin Pending found: %s" % userfound)
        userfound.delete()
    except Exception as e:
        logger.debug(
            "DEBUG - Not waiting to be added as admin: {}".format(e), exc_info=False
        )

    url = reverse(
        "hx_lti_initializer:course_admin_hub"
    ) + "?resource_link_id={}&utm_source={}".format(
        resource_link_id, request.session.session_key
    )
    return redirect(url)


@csrf_exempt
@require_http_methods(["POST"])
def embed_lti(request):
    '''
    Generates a content selection view to insert the LTI tool into a page in the LMS.
    Assumes that the LTI ContentItemSelectionRequest has been validated (e.g. oauth signature).

    This is part of the "Deep Linking" specification.
    See also:
    - https://www.imsglobal.org/specs/lticiv1p0-intro
    - https://www.imsglobal.org/specs/lticiv1p0/specification
    '''
    user_id = request.POST.get('user_id')
    roles = request.POST.get('roles', '').split(",")
    context_id = request.POST.get('context_id')
    content_item_return_url = request.POST.get('content_item_return_url')

    # initial checks to ensure we have a return URL for the content selection
    # and that the user has permission
    if not content_item_return_url:
        return HttpResponse(status=400, content="Error: ContentItemSelectionRequest is missing content_item_return_url")

    is_admin = set(roles) & set(settings.ADMIN_ROLES)
    if not is_admin:
        return HttpResponse(status=403, content="You must be a course admin to insert content items")

    # ensure that the course and user profile exist, otherwise we can't proceed
    # TODO: refactor the course/user profile creation logic in launch_lti() so that we can automatically do that here too.
    try:
        course_instance = LTICourse.objects.get(course_id=context_id)
    except LTICourse.DoesNotExist:
        return HttpResponse(status=404, content="Content not found for course. Please launch the tool through the course navigation and create some content.")

    try:
        lti_profile = LTIProfile.objects.get(anon_id=user_id)
        login(request, lti_profile.user)  # required since the form is POSTed to embed_lti_response
    except LTIProfile.DoesNotExist:
        return HttpResponse(status=404, content="User profile not found. Please launch the tool through the course navigation so that your profile is created automatically.")

    # render a form with the content items (annotation objects) that can be selected
    selection_form = EmbedLtiSelectionForm(
        course_instance=course_instance,
        content_item_return_url=content_item_return_url,
    )
    context = {
        "selection_form": selection_form,
    }
    return render(request, "hx_lti_initializer/embed_lti_selection.html", context)


@login_required
@require_http_methods(["POST"])
def embed_lti_response(request):
    '''
    This view returns a POSTed response back to the tool consumer that is oauth
    signed to verify its authenticity.

    Assumes that the admin user has already been logged in via ContentItemSelectionRequest
    and has made a selection.

    A specific annotation assignment target must be returned to the tool consumer rather
    than just a reference to the launch URL and setting a starting resource after the fact.
    The reason is that an embedded LTI link item will NOT have a distinct resource link ID
    compared to a module item, assignment item or course navigation item. So if the tool is
    embedded on multiple pages, they will all share the same resource_link_id.
    '''
    content_item_return_url = request.POST.get('content_item_return_url')
    content_item = request.POST.get("content_item", "")
    (collection_id, object_id) = content_item.split("/", 2)

    # Build LTI response to tool consumer
    base_url = request.build_absolute_uri("/")[:-1]
    launch_url = base_url + reverse("hx_lti_initializer:launch_lti")
    launch_url_with_custom_params = f"{launch_url}?custom_collection_id={collection_id}&custom_object_id={object_id}"
    content_items = {
        "@context": "http://purl.imsglobal.org/ctx/lti/v1/ContentItem",
        "@graph": [
            {
                "@type": "LtiLinkItem",
                "@id": launch_url_with_custom_params,
                "url": launch_url_with_custom_params,
                "title": "HarvardX Annotation Tool",
                "text": "HarvardX Annotation Tool",
                "mediaType": "application/vnd.ims.lti.v1.ltilink",
                "placementAdvice": {
                    "presentationDocumentTarget": "iframe",
                    "displayWidth": "100%",
                    "displayHeight": "700",
                },
                # NOTE: canvas does not actually copy these params into launch request body.
                # One workaround for this is to use GET params with the launch URL.
                # See also: https://github.com/instructure/canvas-lms/issues/1025
                "custom": {
                    "collection_id": collection_id,
                    "object_id": object_id,
                },
            }
        ]
    }
    data = {
        "lti_message_type": "ContentItemSelection",
        "lti_version": "LTI-1p0",
        "content_items": json.dumps(content_items),
    }
    form = EmbedLtiResponseForm(data)
    form.set_oauth_signature(
        url=content_item_return_url,
        consumer_key=settings.CONSUMER_KEY,
        consumer_secret=settings.LTI_SECRET,
    )

    context = {
        "content_item_return_url": content_item_return_url,
        "embed_lti_response_form": form,
    }
    return render(request, "hx_lti_initializer/embed_lti_response.html", context)


@login_required
def edit_course(request, id):
    course = get_object_or_404(LTICourse, pk=id)
    user_scope = request.LTI.get("hx_user_scope", None)
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            course.save()
            # this removes an administrator if they were checked off the list
            admins = course.course_admins.all()
            selected_list = request.POST.getlist("select_existing_user") + request.POST[
                "new_admin_list"
            ].split(",")
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
                                new_admin_course_id=course.course_id,
                            )
                            new_course_admin.save()
                        except:
                            # admin already pending
                            logger.info("Admin already pending.")

            # save the course name to the session so it auto-populate later.
            save_session(request, course_name=course.course_name)

            messages.success(request, "Course was successfully edited!")
            url = reverse(
                "hx_lti_initializer:course_admin_hub"
            ) + "?resource_link_id={}&utm_source={}".format(
                request.LTI["resource_link_id"], request.session.session_key
            )
            return redirect(url)
    else:
        form = CourseForm(instance=course, user_scope=user_scope)

    try:
        pending_admins = LTICourseAdmin.objects.filter(
            new_admin_course_id=course.course_id
        )
    except:
        pending_admins = None

    return render(
        request,
        "hx_lti_initializer/edit_course.html",
        {
            "form": form,
            "user": request.user,
            "pending": pending_admins,
            "org": settings.ORGANIZATION,
            "is_instructor": request.LTI["is_staff"],
        },
    )


def course_admin_hub(request):
    """
    The index view for both students and instructors. Without the 'is_instructor' flag,
    students are directed to a version of admin_hub with reduced privileges
    """
    is_instructor = request.LTI["is_staff"]
    courses_for_user = LTICourse.objects.filter(course_id=request.LTI["hx_context_id"])
    files_in_courses = TOD_Implementation.get_dict_of_files_from_courses(
        courses_for_user
    )

    logger.debug("course_admin_hub view")
    try:
        config = LTIResourceLinkConfig.objects.get(
            resource_link_id=request.LTI["resource_link_id"]
        )
        collection_id = config.assignment_target.assignment.assignment_id
        object_id = config.assignment_target.target_object_id
        to = TargetObject.objects.get(pk=object_id)
        starter_object = to.target_title

    except:
        object_id = None
        collection_id = None
        to = None
        starter_object = None

    logger.debug(
        "resource_link_config object_id=%s collection_id=%s target_object=%s"
        % (object_id, collection_id, to)
    )

    debug = files_in_courses
    return render(
        request,
        "hx_lti_initializer/admin_hub.html",
        {
            "username": request.LTI["hx_user_name"],
            "is_instructor": request.LTI["is_staff"],
            "courses": courses_for_user,
            "files": files_in_courses,
            "org": settings.ORGANIZATION,
            "debug": debug,
            "starter_object": starter_object,
            "starter_object_id": object_id,
            "starter_collection_id": collection_id,
        },
    )


def access_annotation_target(
    request,
    course_id,
    assignment_id,
    object_id,
    user_id=None,
    user_name=None,
    roles=None,
):
    """
    Renders an assignment page
    """
    if user_id is None:
        user_name = request.LTI["hx_user_name"]
        user_id = request.LTI["hx_user_id"]
        roles = request.LTI["hx_roles"]
    try:
        assignment = Assignment.objects.get(assignment_id=assignment_id)
        targ_obj = TargetObject.objects.get(pk=object_id)
        assignment_target = AssignmentTargets.objects.get(
            assignment=assignment, target_object=targ_obj
        )
        object_uri = targ_obj.get_target_content_uri()
        course_obj = LTICourse.objects.get(course_id=course_id)
    except Assignment.DoesNotExist or TargetObject.DoesNotExist:
        logger.error(
            "User attempted to access an Assignment or Target Object that does not exist: assignment_id={assignment_id} object_id={object_id}".format(
                assignment_id=assignment_id, object_id=object_id
            )
        )
        raise AnnotationTargetDoesNotExist("Assignment or target object does not exist")

    is_instructor = request.LTI.get("is_staff", False)
    if not is_instructor and not assignment.is_published:
        raise PermissionDenied(
            "Permission to access unpublished assignment by a non-instructor is denied"
        )

    try:
        hide_sidebar = request.LTI["launch_params"][
            "custom_hide_sidebar_instance"
        ].split(",")
    except:
        hide_sidebar = []

    save_session(
        request,
        collection_id=assignment_id,
        object_id=object_id,
        object_uri=object_uri,
        context_id=course_id,
    )

    # Dynamically pass in the address that the detail view will use to fetch annotations.
    # there's definitely a more elegant way (or a library function) to do this.
    # also, we may want to consider denying if theres no ssl
    protocol = "https://" if request.is_secure() else "http://"
    abstract_db_url = (
        protocol
        + get_current_site(request).domain
        + reverse("annotation_store:api_root")
    )
    logger.debug("DEBUG - Abstract Database URL: " + abstract_db_url)
    original = {
        "user_id": user_id,
        "username": user_name,
        "is_instructor": request.LTI["is_staff"],
        "collection": assignment_id,
        "course": course_id,
        "object": object_id,
        "target_object": targ_obj,
        "token": retrieve_token(
            user_id,
            assignment.annotation_database_apikey,
            assignment.annotation_database_secret_token,
        ),
        "assignment": assignment,
        "roles": [str(role) for role in roles],
        "instructions": assignment_target.target_instructions,
        "abstract_db_url": abstract_db_url,
        "session": request.session.session_key,
        "org": settings.ORGANIZATION,
        "logger_url": settings.ANNOTATION_LOGGER_URL,
        "accessibility": settings.ACCESSIBILITY,
        "hide_sidebar_instance": hide_sidebar,
        "is_graded": request.LTI["launch_params"].get("lis_outcome_service_url", None)
        is not None,
    }
    if not assignment.object_before(object_id) is None:
        original["prev_object"] = assignment.object_before(object_id)
        original["assignment_target"] = assignment_target

    if not assignment.object_after(object_id) is None:
        original["next_object"] = assignment.object_after(object_id)
        original["assignment_target"] = assignment_target

    if targ_obj.target_type == "vd":
        srcurl = targ_obj.target_content
        if "youtu" in srcurl:
            typeSource = "video/youtube"
        else:
            disassembled = urlparse(srcurl)
            file_ext = os.path.splitext(os.path.basename(disassembled.path))[1]
            typeSource = "video/" + file_ext.replace(".", "")
        original.update({"typeSource": typeSource})
    elif targ_obj.target_type == "ig":
        original.update({"osd_json": targ_obj.target_content})
        viewtype = assignment_target.get_view_type_for_mirador()
        canvas_id = assignment_target.get_canvas_id_for_mirador()
        logger.debug("CANVAS: %s" % canvas_id)

        if viewtype is not None:
            original.update({"viewType": viewtype})
        if canvas_id is not None:
            original.update({"canvas_id": canvas_id})

    if assignment_target.target_external_css:
        original.update({"custom_css": assignment_target.target_external_css})
    elif course_obj.course_external_css_default:
        original.update({"custom_css": course_obj.course_external_css_default})

    original.update({"dashboard_hidden": assignment_target.get_dashboard_hidden()})

    original.update({"transcript_hidden": assignment_target.get_transcript_hidden()})

    original.update(
        {"transcript_download": assignment_target.get_transcript_download()}
    )

    original.update({"video_download": assignment_target.get_video_download()})

    get_paras = {}
    for k in request.GET.keys():
        get_paras[k] = request.GET[k]

    original.update(get_paras)
    if (
        targ_obj.target_type == "tx" or targ_obj.target_type == "ig" or targ_obj.target_type == "vd"
    ) and assignment.use_hxighlighter:
        return render(
            request, "%s/detail_hxighlighter.html" % targ_obj.target_type, original
        )
    else:
        return render(request, "%s/detail.html" % targ_obj.target_type, original)


def instructor_dashboard_view(request):
    """
    Renders the instructor dashboard (without annotations).
    """
    if not request.LTI["is_staff"]:
        raise PermissionDenied("You must be a staff member to view the dashboard.")

    resource_link_id = request.LTI["resource_link_id"]
    context_id = request.LTI["hx_context_id"]
    user_id = request.LTI["hx_user_id"]
    context = {
        "username": request.LTI["hx_user_name"],
        "is_instructor": request.LTI["is_staff"],
        "user_annotations": [],
        "fetch_annotations_time": 0,
        "org": settings.ORGANIZATION,
        "session": request.session.session_key,
        "dashboard_context_js": json.dumps(
            {
                "student_list_view_url": reverse(
                    "hx_lti_initializer:instructor_dashboard_student_list_view"
                )
                + "?resource_link_id={}&utm_source={}".format(
                    resource_link_id, request.session.session_key
                ),
            }
        ),
    }
    return render(request, "hx_lti_initializer/dashboard_view.html", context)


def instructor_dashboard_student_list_view(request):
    """
    Renders the student annotations for the instructor dashboard.
    Intended to be called via AJAX.
    """
    if not request.LTI["is_staff"]:
        raise PermissionDenied("You must be a staff member to view the dashboard.")

    context_id = request.LTI["hx_context_id"]
    user_id = request.LTI["hx_user_id"]
    resource_link_id = request.LTI["resource_link_id"]

    # Fetch the annotations and time how long the request takes
    fetch_start_time = time.time()
    course_annotations = fetch_annotations_by_course(
        context_id, settings.ADMIN_GROUP_ID
    )
    fetch_end_time = time.time()
    fetch_elapsed_time = fetch_end_time - fetch_start_time

    # Transform the raw annotation results into something useful for the dashboard
    user_annotations = DashboardAnnotations(
        request, course_annotations
    ).get_annotations_by_user()
    context = {
        "username": request.LTI["hx_user_name"],
        "is_instructor": request.LTI["is_staff"],
        "user_annotations": user_annotations,
        "fetch_annotations_time": fetch_elapsed_time,
        "org": settings.ORGANIZATION,
        "resource_link_id": resource_link_id,
    }
    return render(
        request, "hx_lti_initializer/dashboard_student_list_view.html", context
    )


def error_view(request, message):
    """
    Implements graceful and user-friendly (also debugger-friendly) error displays
    If used properly, we can use this to have better bug reproducibility down the line.
    While we won't dump any sensitive information, we can at least describe what went wrong
    uniquely and get an indication from the user which part of our code failed.
    """

    context = {"message": message}

    return render(request, "hx_lti_initializer/error_page.html", context)


def delete_assignment(request):
    """
    Assignment deletion from Postgres databases
    """
    try:
        collection_id = request.POST["assignment_id"]
        assignment = Assignment.objects.get(assignment_id=collection_id)
        assignment.delete()
        logger.debug("DEBUG - Assignment Deleted: {}".format(assignment))
    except Exception as e:
        logger.error("error in delete assignment({}): {}".format(assignment, e))
        return error_view(request, "The assignment deletion may have failed")

    url = reverse(
        "hx_lti_initializer:course_admin_hub"
    ) + "?resource_link_id={}&utm_source={}".format(
        request.LTI["resource_link_id"], request.session.session_key
    )
    return redirect(url)


@login_required
@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def change_starting_resource(request, assignment_id, object_id):
    data = {"response": "Success"}
    resource_link_id = request.LTI["resource_link_id"]
    data.update(
        {
            "resource_link_id": resource_link_id,
            "assignment_id": assignment_id,
            "object_id": object_id,
        }
    )
    logger.info("change_starting_resource (%s): %s" % (request.method, data))

    if request.method == "POST":
        assignment_target = AssignmentTargets.get_by_assignment_id(
            assignment_id=assignment_id, target_object_id=int(object_id)
        )
        if not assignment_target:
            return HttpResponse(
                json.dumps({"response": "Failure: AssignmentTarget not found"}),
                content_type="application/json",
            )
        try:
            config = LTIResourceLinkConfig.objects.get(
                resource_link_id=resource_link_id
            )
            config.assignment_target = assignment_target
            created = False
        except:
            config = LTIResourceLinkConfig(
                resource_link_id=resource_link_id, assignment_target=assignment_target
            )
            created = True
        config.save()
        data["response"] = "Success: Created" if created else "Success: Updated"
    elif request.method == "DELETE":
        LTIResourceLinkConfig.objects.filter(resource_link_id=resource_link_id).delete()
        data["response"] = "Success: Deleted"

    return HttpResponse(json.dumps(data), content_type="application/json")


def tool_config(request):
    '''
    Generates XML tool config.
    See also: https://canvas.instructure.com/doc/api/file.tools_xml.html
    '''
    base_url = request.build_absolute_uri("/")[:-1]

    title = settings.LTI_TOOL_CONFIGURATION["title"]
    description = settings.LTI_TOOL_CONFIGURATION["description"]
    course_navigation_enabled = settings.LTI_TOOL_CONFIGURATION.get("course_navigation_enabled", False)
    new_tab = settings.LTI_TOOL_CONFIGURATION.get("new_tab", False)
    embed_enabled = settings.LTI_TOOL_CONFIGURATION.get("embed_enabled", False)
    embed_url = base_url + reverse(settings.LTI_TOOL_CONFIGURATION["embed_url"])
    embed_icon_url = base_url + static(settings.LTI_TOOL_CONFIGURATION["embed_icon_url"])
    launch_url = base_url + reverse(settings.LTI_TOOL_CONFIGURATION["launch_url"])

    lti_tool_config = ToolConfig(
        title=title,
        description=description,
        launch_url=launch_url,
        secure_launch_url=launch_url,
        extensions={
            "canvas.instructure.com": {
                # The oauth_compliant parameter allows an external tool provider to specify how it wants Canvas
                # to handle launch URLs with query parameters: if set to true LTI query parameters will not be
                # copied to the POST body. Note that this is required if the launch URL includes GET parameters,
                # such as passing a custom assignment ID and object ID.
                "oauth_compliant": "true",

                # The privacy_level parameter determines what personal information to provide to the tool.
                # Valid values include: "anonymous", "name_only", "public"
                "privacy_level": "public",

                # Configuration for course navigation link
                "course_navigation": {
                    "enabled": "true" if course_navigation_enabled else "false",
                    "default": "disabled",
                    "text": title,
                    "windowTarget": "_blank" if new_tab else "_self",
                },

                # Configuration for WYSIWYG editor button
                "editor_button": {
                    "enabled": "true" if embed_enabled else "false",
                    "visibility": "admins",
                    "message_type": "ContentItemSelectionRequest",
                    "text": f"Add from {title}",
                    "url": embed_url,
                    "icon_url": embed_icon_url,
                    "selection_height": "400",
                    "selection_width": "500",
                },
            },
        },
    )

    return HttpResponse(lti_tool_config.to_xml(), content_type="text/xml")


"""
[1] tool_consumer_instance_id and user-scope

* tool_consumer_instance_id is an OPTIONAL lti-param that identifies an instance of the
  consumer/platform (because lti specs covers multi-tenancy, say, a hxat connected to 2
  instances of edx: one from HUGSE and other from HX
* hxat creates user/profile with lti-role in settings.ADMIN_ROLES (e.g. "Administrator",
  "Instructor", "urn:lti:instrole:ims/lis/Administrator"). This is for authorization for
  editing course, assignments, target objects, etc.
* in edx, each course has a set of user-ids, meaning the same person can register for
  different courses and in each course this person will have a different user-id; it's
  called anonymous-id and has to do with privacy.
* in canvas, the user-id is the same across the platform; so a canvas user-id identifies
  the person.
* So, hxat needs a user-id and user-scope to identify a person, for edx the user-scope
  is the course, for canvas is the platform or the tool_consumer_instance_id.
* as stated, tool_consumer_instance_id is OPTIONAL and the fact that the platform does
  not include it in its lti-params means the platform expects the tool to be
  single-tenancy and doesn't refer at all of to the user-scope.
* this all means that settings.ORGANIZATION implies that, regarding user-scope:
  . HARVARDX == user_scope is course as in edx
  . !HARVARDX and consumer_instance == user_scope is platform_instance as in canvas
  . !HARVARDX and !consumer_instance == user_scope assumes course as in edx
* TODO: review user of ORGANIZATION; maybe lti 1.3 solves it? still depends on the
  platform implementation of lti 1.3 though...

"""
