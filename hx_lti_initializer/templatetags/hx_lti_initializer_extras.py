from django.template.defaulttags import register
from django.conf import settings
from datetime import datetime
from dateutil import tz
from django import template
from django.template.defaultfilters import stringfilter
from django.contrib.staticfiles.templatetags.staticfiles import static
from re import sub

from hx_lti_assignment.models import Assignment
from hx_lti_initializer.utils import debug_printer
from abstract_base_classes.target_object_database_api import TOD_Implementation
from target_object_database.models import TargetObject
import re

def convert_tz(datetimeobj):
	'''
		Converts a datetimeobj from UTC to the local timezone
	'''
	from_zone = tz.tzutc()
	to_zone = tz.gettz('America/New_York')
	# Tell datetime object it's in UTC
	utc = datetimeobj.replace(tzinfo=from_zone)
	# Convert to local time
	local = utc.astimezone(to_zone)

	return local

@register.filter
def format_date(str):
	'''
		Converts a date string into a more readable format
	'''
	
	# Check for None case
	if str is None:
		return ""

	# Clean string by stripping all non numeric characters
	cleaned = sub("[^0-9]", "", str)

	try:
		# Store formatted date as datetimeobject and convert timezone
		dformatted = convert_tz(datetime.strptime(cleaned, "%Y%m%d%H%M%S"))
		# Date string in format for display on webpage
		date = dformatted.strftime('%b %d')
	except ValueError:
		date = str

	return date
			
@register.filter
def format_tags(tagslist):
	'''
		Pretty-prints list of tags
	'''
	return ', '.join(tagslist)
	
@register.simple_tag
def get_assignment_name(collection_id):
	# Filter for the assignment with assignment_id matching collection_id
	try:
		assignment = Assignment.objects.get(assignment_id=collection_id);
		return unicode(assignment)
	# TODO: Currently fails silently. Eventually we will want to improve the model design so this doesn't happen.
	except:
		return ''

@register.simple_tag
def get_target_object_name(object_id):
	try:
		targ_obj = TargetObject.objects.get(pk=object_id)
		return unicode(targ_obj)
	# TODO: Currently fails silently. Eventually we will want to improve the model design so this doesn't happen.
	except:
		try:
			# if it is an image, the object_id will not match as it follows mirador conventions
			trimmed_object_id = re.sub(r'/canvas/.*', '', object_id)
			target_obj = TargetObject.objects.filter(target_content__icontains=trimmed_object_id)[0]
			return unicode(target_obj)
		except:
			debug_printer("Failed:%s" % object_id)
			return ''

@register.simple_tag
def get_target_id(object_id):
	try:
		targ_obj = TargetObject.objects.get(pk=object_id)
		return targ_obj.id
	# TODO: Currently fails silently. Eventually we will want to improve the model design so this doesn't happen.
	except:
		try:
			# if it is an image, the object_id will not match as it follows mirador conventions
			trimmed_object_id = re.sub(r'/canvas/.*', '', object_id)
			target_obj = TargetObject.objects.filter(target_content__icontains=trimmed_object_id)[0]
			return target_obj.id
		except:
			debug_printer("Failed:%s" % object_id)
			return ''

@register.assignment_tag
def assignment_object_exists(object_id, collection_id):
	'''
		Checks to make sure that both the assignment and the target object exist
	'''
	
	try:
		targ_obj = TargetObject.objects.get(pk=object_id)
		assignment = Assignment.objects.get(assignment_id=collection_id)
		return True
	except:
		try:
			# if it is an image, the object_id will not match as it follows mirador conventions
			trimmed_object_id = re.sub(r'/canvas/.*', '', object_id)
			target_obj = TargetObject.objects.filter(target_content__icontains=trimmed_object_id)[0]
			assignment = Assignment.objects.get(assignment_id=collection_id)
			return True
		except:
			debug_printer("Failed:%s" % object_id)
			return False

@register.simple_tag
def get_annotation_by_id(annotation_id, annotations):
	'''
		Given the id of an annotation and a dictionary of annotations keyed by id,
		this returns the text of the annotation with that id	
	'''
	annotation_id = int(annotation_id)
	if annotation_id in annotations:
		return annotations[annotation_id]['text']
	return '<i>Deleted Annotation</i>'

@register.simple_tag
def get_url_to_annotation_manual(**kwargs):
	'''
	Returns the URL to the annotation manual. When the URL is present in the django settings,
	it returns this URL, otherwise it will return the static url passed in to this function.
	'''
	url = kwargs.get('default', '')
	if settings.ANNOTATION_MANUAL_URL is not None:
		url = settings.ANNOTATION_MANUAL_URL
	if not url.startswith('http'):
		url = static(url)
	return url
	