from django.shortcuts import get_object_or_404, render_to_response, render, redirect  # noqa
from django.urls import reverse
from django.template import RequestContext
from django.http import Http404, HttpResponse
from django.utils.html import escape
from django.forms import ValidationError
from .models import *
from .serializers import *
from .forms import SourceForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from rest_framework import generics
from hx_lti_initializer.utils import debug_printer

def get_course_id(request):
	return request.LTI['hx_lti_course_id']

def get_lti_profile(request):
    return LTIProfile.objects.get(anon_id=request.LTI['hx_user_id'])

def get_lti_profile_id(request):
    lti_profile = get_lti_profile(request)
    return lti_profile.id

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
            url = reverse('hx_lti_initializer:course_admin_hub') + '?resource_link_id=%s' % request.LTI['resource_link_id']
            return redirect(url)
        else:
            debug_printer(form.errors)
    else:
        form = SourceForm()
        print("AAAAAHHHHHHHH")
    return render(
        request,
        'target_object_database/source_form.html',
        {
            'form': form,
            'username': request.LTI['hx_user_name'],
            'org': settings.ORGANIZATION,
            'is_instructor': request.LTI['is_staff'],
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
            url = reverse('hx_lti_initializer:course_admin_hub') + '?resource_link_id=%s' % request.LTI['resource_link_id']
            return redirect(url)
        else:
            debug_printer(form.errors)
    else:
        form = SourceForm(instance=source)
    return render(
        request,
        'target_object_database/source_form.html',
        {
            'form': form,
            'username': request.LTI['hx_user_name'],
            'creator': get_lti_profile_id(request),
            'course': get_course_id(request),
            'org': settings.ORGANIZATION,
            'is_instructor': request.LTI['is_staff'],
        }
    )


def handlePopAdd(request, addForm, field):
    if request.method == "POST":
        form = addForm(request.POST)
        if form.is_valid():
            try:
                newObject = form.save()
            except (ValidationError, error):
                newObject = None
            if newObject:
                return HttpResponse('<script type="text/javascript">opener.dismissAddAnotherPopup(window, "%s", "%s", "%s", "%s", "%s");</script>' % (escape(newObject._get_pk_val()), escape(newObject.target_title), escape(newObject.target_author), escape(newObject.target_created), escape(newObject.target_type)))  # noqa
    else:
        form = addForm()
    pageContext = {
        'form': form,
        'field': field,
        'username': request.LTI['hx_user_name'],
        'creator': get_lti_profile_id(request),
        'course': get_course_id(request),
        'org': settings.ORGANIZATION,
        'is_instructor': request.LTI['is_staff'],
    }
    return render(
        request,
        "target_object_database/source_form.html",
        pageContext
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
