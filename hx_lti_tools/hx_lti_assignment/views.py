from hx_lti_assignment.forms import AssignmentForm
from hx_lti_assignment.models import Assignment
from hx_lti_initializer.utils import debug_printer
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response, render, redirect
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import PermissionDenied

@login_required
def create_new_assignment(request):
    """
    """
    if request.method == "POST":
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            assignment.save()

            messages.success(request, 'Assignment was successfully edited!')
            return redirect('hx_lti_initializer:course_admin_hub')
        else:
            debug_printer(form.errors)
    else:
        form = AssignmentForm()
    return render(
        request,
        'hx_lti_assignment/create_new_assignment.html',
        {
            'form': form,
            'user': request.user,
        }
    )

@login_required
def edit_assignment(request, id):
    """
    """
    assignment = get_object_or_404(Assignment, pk=id)
    if request.method == "POST":
        form = AssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            assignment = form.save()
            assignment.save()

            messages.success(request, 'Assignment was successfully edited!')
            return redirect('hx_lti_initializer:course_admin_hub')
        else:
            debug_printer(form.errors)
    else: 
        form = AssignmentForm(instance=assignment)
    return render(
        request,
        'hx_lti_assignment/create_new_assignment.html', 
        {
            'form': form,
            'user': request.user,
        }
    )