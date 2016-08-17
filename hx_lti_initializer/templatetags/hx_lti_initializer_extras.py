from django.template.defaulttags import register
from django.utils.safestring import mark_safe
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

@register.assignment_tag
def get_annotation_manual(**kwargs):
	'''
	Returns the URL to the annotation manual. When the URL is present in the django settings,
	it returns this URL, otherwise it will return the default url passed in to this function.
	'''
	url = kwargs.get('default_url', '')
	target = kwargs.get('default_target', '_self')
	if settings.ANNOTATION_MANUAL_URL is not None:
		url = settings.ANNOTATION_MANUAL_URL
	if not url.startswith('http'):
		url = static(url)
	if settings.ANNOTATION_MANUAL_TARGET is not None:
		target = settings.ANNOTATION_MANUAL_TARGET
	return {'url': url, 'target': target}
	
@register.simple_tag
def get_lti_frame_resize_js(**kwargs):
	receiver = kwargs.get('receiver', 'https://canvas.harvard.edu')
	max_height = kwargs.get('max_height', None)
	target_type = kwargs.get('target_type', None)
	if target_type in ('vd', 'ig') and max_height is None:
		max_height = 900;
	if max_height is None:
		height_expr = 'body_height+100'
	else:
		height_expr = '(body_height > %d ? %d : body_height+100)' % (int(max_height), int(max_height));
	javascript = '''
// Sends message to parent to resize the iframe so we don't have scrolling issues
jQuery(document).ready(function() {
	var receiver = "%s";
	var body_height = jQuery("body").height();
	var message = {subject:"lti.frameResize", height: %s};
	console.log("sending lti.frameResize message", message, receiver);
	window.parent.postMessage(JSON.stringify(message), receiver);
}, 1000);
''' % (receiver, height_expr)
	if settings.ORGANIZATION == 'ATG':
		return mark_safe(javascript)
	return ''

