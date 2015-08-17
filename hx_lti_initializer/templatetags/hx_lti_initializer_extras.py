from django.template.defaulttags import register

from datetime import datetime
from dateutil import tz
from django import template
from django.template.defaultfilters import stringfilter
from re import sub

from hx_lti_assignment.models import Assignment
from abstract_base_classes.target_object_database_api import TOD_Implementation
from target_object_database.models import TargetObject

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
	if tagslist == ['']:
		return "None"
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
		return ''

@register.assignment_tag
def assignment_object_exists(object_id, collection_id):
	'''
		Checks to make sure that both the assignment and the target object exist
	'''
	try:
		targ_obj = TargetObject.objects.get(pk=object_id)
		assignment = Assignment.objects.get(assignment_id=collection_id);
		return True
	except:
		return False
	
@register.simple_tag
def get_annotation_by_id(id, students):
	'''
		Given the id of an annotation and a list of student_objects, this searches through
		the student_objects and returns the text of the annotation with that id	
	'''
	# O(n^2) - maximum of students*student_annotations executions.
	# TODO: Performance?
	# alternative is a network request to get annotation by ID.
	for student in students:
		for annotation in student['annotations']:
			if annotation['id'] == int(id):
				return annotation["text"]

	return "None"