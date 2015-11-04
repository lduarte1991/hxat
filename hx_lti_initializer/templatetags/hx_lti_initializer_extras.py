from django.template.defaulttags import register
from django.conf import settings
from datetime import datetime
from dateutil import tz
from django import template
from django.core.urlresolvers import reverse
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
	