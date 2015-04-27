from django.shortcuts import render
from models import *

def open_target_object(request, collection_id, target_obj_id):
    try:
        targ_obj = TargetObject.objects.get(pk=target_obj_id)
    except TargetObject.DoesNotExist:
        raise Http404("File you are looking for does not exist.")
    return render(request, '%s/detail.html' % targ_obj.target_type, {'target_object': targ_obj})