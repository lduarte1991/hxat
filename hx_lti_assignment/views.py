import json
import logging
import sys
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from hx_lti_assignment.forms import (
    AssignmentForm,
    AssignmentTargetsForm,
    AssignmentTargetsFormSet,
    DeleteAssignmentForm,
)
from hx_lti_assignment.models import Assignment, AssignmentTargets
from hx_lti_initializer.models import LTICourse
from hx_lti_initializer.views import error_view  # should we centralize an error view?

logger = logging.getLogger(__name__)


def get_course_id(request):
    return request.LTI["hx_lti_course_id"]


@login_required
def create_new_assignment(request):
    debug = "Nothing"
    form = None
    if request.method == "POST":
        targets_form = AssignmentTargetsFormSet(request.POST)
        if targets_form.is_valid():
            assignment_targets = targets_form.save(commit=False)
            targets = []
            if len(assignment_targets) > 0:
                targets = "assignment_objects=" + str(
                    assignment_targets[0].target_object.id
                )
            for x in range(len(assignment_targets) - 1):
                targets += (
                    "&"
                    + "assignment_objects="
                    + str(assignment_targets[x + 1].target_object.id)
                )
            post_values = QueryDict(targets, mutable=True)
            post_values.update(request.POST)
            form = AssignmentForm(post_values)
            assignment = None
            if form.is_valid():
                assignment = form.save(commit=False)
                random_id = uuid.uuid4()
                assignment.assignment_id = str(random_id)
                assignment.save()
                for at in assignment_targets:
                    at.assignment = assignment
                    at.save()
                assignment.save()
                messages.success(request, "Assignment successfully created!")
                url = (
                    reverse("hx_lti_initializer:course_admin_hub")
                    + "?resource_link_id=%s" % request.LTI["resource_link_id"]
                )
                return redirect(url)
            else:
                target_num = (
                    0 if assignment_targets is None else len(assignment_targets)
                )
                messages.error(request, form.errors)
                logger.debug("form errors: {}".format(form.errors))
                template_used = "hx_lti_assignment/create_new_assignment2.html"
                if assignment and assignment.use_hxighlighter:
                    template_used = (
                        "hx_lti_assignment/create_new_assignment_hxighlighter.html"
                    )
                return render(
                    request,
                    template_used,
                    {
                        "form": form,
                        "targets_form": targets_form,
                        "username": request.LTI["hx_user_name"],
                        "number_of_targets": target_num,
                        "debug": debug,
                        "course_id": get_course_id(request),
                        "is_instructor": request.LTI["is_staff"],
                        "org": settings.ORGANIZATION,
                        "context_id": request.LTI["hx_context_id"],
                        "tag_list": [],
                    },
                )
        else:
            # "The AssignmentTargets could not be created because the data didn't validate."
            # we will never be able to use assignment_targets
            # assignment_targets = targets_form.save(commit=False)
            # TODO: is this the error functionality that we want?
            # try:
            #     target_num = len(assignment_targets)
            # except:
            #     return error_view(request, "Someone else is already using that object")

            # Old code - fails because there are (somehow) no assignment targets
            # target_num = len(assignment_targets)
            target_num = 0
            form = AssignmentForm(request.POST)
            debug = "Targets Form is NOT valid: " + str(request.POST)
            logger.debug("Form Errors: {}".format(targets_form.errors))
            return error_view(
                request,
                "Something went wrong with the source material. It's likely you have selected a source that is already in use elsewhere.",
            )

    # GET
    else:
        # Initialize with database settings so instructor doesn't have to do this manually
        form = AssignmentForm(
            initial={
                "annotation_database_url": getattr(settings, "ANNOTATION_DB_URL", ""),
                "annotation_database_apikey": getattr(
                    settings, "ANNOTATION_DB_API_KEY", ""
                ),
                "annotation_database_secret_token": getattr(
                    settings, "ANNOTATION_DB_SECRET_TOKEN", ""
                ),
                "pagination_limit": getattr(
                    settings, "ANNOTATION_PAGINATION_LIMIT_DEFAULT", 20
                ),
                "use_hxighlighter": None,
            }
        )
        targets_form = AssignmentTargetsFormSet()
        target_num = 0

    return render(
        request,
        "hx_lti_assignment/create_new_assignment_hxighlighter.html",
        {
            "form": form,
            "targets_form": targets_form,
            "username": request.LTI["hx_user_name"],
            "number_of_targets": target_num,
            "debug": debug,
            "course_id": get_course_id(request),
            "is_instructor": request.LTI["is_staff"],
            "org": settings.ORGANIZATION,
            "context_id": request.LTI["hx_context_id"],
            "tag_list": [],
        },
    )


@login_required
def edit_assignment(request, id):
    assignment = get_object_or_404(Assignment, pk=id)
    target_num = len(AssignmentTargets.objects.filter(assignment=assignment))
    debug = "TEST"
    if request.method == "POST":
        targets_form = AssignmentTargetsFormSet(request.POST, instance=assignment)
        targets = "id=" + id + "&assignment_id=" + assignment.assignment_id
        if targets_form.is_valid():
            assignment_targets = targets_form.save(commit=False)
            changed = False
            if len(targets_form.deleted_objects) > 0:
                debug += "Trying to delete a bunch of assignments\n"
                for del_obj in targets_form.deleted_objects:
                    del_obj.delete()
                changed = True
            if len(assignment_targets) > 0:
                for at in assignment_targets:
                    at.save()
                changed = True
            if changed:
                targets_form = AssignmentTargetsFormSet(instance=assignment)
        else:
            return error_view(
                request,
                "Something went wrong. It's likely you have selected source material that is already in use elsewhere.",
            )

        for targs in assignment.assignment_objects.all():
            targets += "&assignment_objects=" + str(targs.id)
        post_values = QueryDict(targets, mutable=True)
        post_values.update(request.POST)
        form = AssignmentForm(post_values, instance=assignment)
        if form.is_valid():
            assign1 = form.save(commit=False)
            assign1.save()
            messages.success(request, "Assignment was successfully edited!")
            url = (
                reverse("hx_lti_initializer:course_admin_hub")
                + "?resource_link_id=%s" % request.LTI["resource_link_id"]
            )
            return redirect(url)
        else:
            template_used = "hx_lti_assignment/create_new_assignment2.html"
            if assignment.use_hxighlighter:
                template_used = (
                    "hx_lti_assignment/create_new_assignment_hxighlighter.html"
                )
            return render(
                request,
                template_used,
                {
                    "form": form,
                    "targets_form": targets_form,
                    "username": request.LTI["hx_user_name"],
                    "number_of_targets": target_num,
                    "debug": debug,
                    "assignment_id": assignment.assignment_id,
                    "course_id": get_course_id(request),
                    "is_instructor": request.LTI["is_staff"],
                    "org": settings.ORGANIZATION,
                    "context_id": request.LTI["hx_context_id"],
                    "tag_list": assignment.array_of_tags(),
                },
            )
    else:
        targets_form = AssignmentTargetsFormSet(instance=assignment)
        form = AssignmentForm(instance=assignment)

    try:
        course_name = request.LTI["course_name"]
    except:
        course_name = None

    template_used = "hx_lti_assignment/create_new_assignment2.html"
    if assignment.use_hxighlighter:
        template_used = "hx_lti_assignment/create_new_assignment_hxighlighter.html"
    return render(
        request,
        template_used,
        {
            "form": form,
            "targets_form": targets_form,
            "number_of_targets": target_num,
            "username": request.LTI["hx_user_name"],
            "debug": debug,
            "assignment_id": assignment.assignment_id,
            "course_id": get_course_id(request),
            "is_instructor": request.LTI["is_staff"],
            "org": settings.ORGANIZATION,
            "context_id": request.LTI["hx_context_id"],
            "tag_list": assignment.array_of_tags(),
        },
    )


@login_required
def delete_assignment(request, id):
    assignment = get_object_or_404(Assignment, pk=id)

    if request.method == "POST":
        form = DeleteAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            aTargets = AssignmentTargets.objects.filter(assignment=assignment)
            for at in aTargets:
                at.delete()
            assignment.delete()
            url = (
                reverse("hx_lti_initializer:course_admin_hub")
                + "?resource_link_id=%s" % request.LTI["resource_link_id"]
            )
            return redirect(url)

    raise PermissionDenied()


@login_required
def import_assignment(request):
    return render(
        request,
        "hx_lti_assignment/import_assignment.html",
        {
            "courses": LTICourse.objects.all(),
            "is_instructor": request.LTI["is_staff"],
            "org": settings.ORGANIZATION,
            "current_course_id": get_course_id(request),
        },
    )


@login_required
def assignments_from_course(request, course_id):
    course = get_object_or_404(LTICourse, pk=course_id)
    result = course.assignments.all()
    data = serializers.serialize("json", result)
    return HttpResponse(data, content_type="application/json")


@login_required
def moving_assignment(request, old_course_id, new_course_id, assignment_id):
    old_course = LTICourse.objects.get(pk=old_course_id)
    new_course = LTICourse.objects.get(pk=new_course_id)

    try:
        result = dict()
        result.update({"old_course_id": str(old_course.course_id)})
        result.update({"new_course_id": str(new_course.course_id)})

        assignment = Assignment.objects.get(pk=assignment_id)
        aTargets = AssignmentTargets.objects.filter(assignment=assignment)
        assignment.course = new_course
        assignment.pk = None

        result.update({"old_assignment_id": str(assignment.assignment_id)})
        assignment.assignment_id = uuid.uuid4()
        assignment.save()
        result.update({"new_assignment_id": str(assignment.assignment_id)})
        result.update({"assignment_name": str(assignment.assignment_name)})

        pks = []
        for at in aTargets:
            at.pk = None
            at.assignment = assignment
            at.save()
            pks.append(str(at.target_object.pk))
        result.update({"object_ids": pks, "result": 200})
        data = json.dumps(result)
        return HttpResponse(data, content_type="application/json")
    except:
        data = json.dumps(
            {
                "result": 500,
                "message": "There was an error in importing your object.",
                "error_message": str(sys.exc_info()[1]),
                "assignment_id": assignment_id,
            }
        )
        return HttpResponse(data, content_type="application/json")
