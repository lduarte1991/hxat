from django.shortcuts import get_object_or_404, render_to_response, render, redirect  # noqa
from django.template import RequestContext
from django.http import Http404, HttpResponse
from django.utils.html import escape
from models import *
from serializers import *
from forms import SourceForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from rest_framework import generics


def open_target_object(request, collection_id, target_obj_id):
    try:
        targ_obj = TargetObject.objects.get(pk=target_obj_id)
    except TargetObject.DoesNotExist:
        raise Http404("File you are looking for does not exist.")
    return render(
        request,
        '%s/detail.html' % targ_obj.target_type,
        {'target_object': targ_obj}
    )


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
            'creator': request.session['creator_default'],
            'course': request.session['course_name'],
        }
    )


def handlePopAdd(request, addForm, field):
    if request.method == "POST":
        form = addForm(request.POST)
        if form.is_valid():
            try:
                newObject = form.save()
            except forms.ValidationError, error:
                newObject = None
            if newObject:
                return HttpResponse('<script type="text/javascript">opener.dismissAddAnotherPopup(window, "%s", "%s");</script>' % (escape(newObject._get_pk_val()), escape(newObject)))  # noqa
    else:
        form = addForm()
    pageContext = {
        'form': form,
        'field': field,
        'user': request.user,
        'creator': request.session['creator_default'],
        'course': request.session['course_name'],
    }
    return render_to_response(
        "target_object_database/source_form.html",
        RequestContext(request, pageContext)
    )


@login_required
def newSource(request):
    return handlePopAdd(request, SourceForm, 'target_object')


class SourceView(generics.ListAPIView):
    model = TargetObject
    serializer_class = TargetObjectSerializer

    def get_queryset(self):
        object_id = self.kwargs['object_id']
        return TargetObject.objects.filter(pk=object_id)
