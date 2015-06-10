from django.shortcuts import get_object_or_404, render_to_response, render, redirect
from django.http import Http404
from models import *
from forms import SourceForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def open_target_object(request, collection_id, target_obj_id):
    try:
        targ_obj = TargetObject.objects.get(pk=target_obj_id)
    except TargetObject.DoesNotExist:
        raise Http404("File you are looking for does not exist.")
    return render(request, '%s/detail.html' % targ_obj.target_type, {'target_object': targ_obj})

@login_required
def create_new_source(request):
    """
    """
    if request.method == "POST":
        form = SourceForm(request.POST)
        if form.is_valid():
            source = form.save()
            source.save()

            messages.success(request, 'Source was successfully created!')
            return redirect('hx_lti_initializer:course_admin_hub') 
        else:
            debug_printer(form.errors)
    else:
        form = SourceForm()
    return render(
        request,
        'target_object_database/source_form.html',
        {
            'form': form,
            'user': request.user,
        }
    )

@login_required
def edit_source(request, id):
    """
    """
    source = get_object_or_404(TargetObject, pk=id)
    if request.method == "POST":
        form = SourceForm(request.POST, instance=source)
        if form.is_valid():
            source = form.save()
            source.save()

            messages.success(request, 'Source was successfully edited!')
            return redirect('hx_lti_initializer:course_admin_hub')
        else:
            debug_printer(form.errors)
    else: 
        form = SourceForm(instance=source)
    return render(
        request,
        'target_object_database/source_form.html', 
        {
            'form': form,
            'user': request.user,
        }
    )