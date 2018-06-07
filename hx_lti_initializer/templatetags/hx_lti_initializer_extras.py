from django.template.defaulttags import register
from django.utils.safestring import mark_safe
from django.conf import settings
import dateutil.parser
import dateutil.tz
from django.contrib.staticfiles.templatetags.staticfiles import static

def convert_tz(datetimeobj):
	'''
		Converts a datetimeobj from UTC to the local timezone
	'''
	from_zone = dateutil.tz.tzutc()
	to_zone = dateutil.tz.gettz('America/New_York')
	# Tell datetime object it's in UTC
	utc = datetimeobj.replace(tzinfo=from_zone)
	# Convert to local time
	local = utc.astimezone(to_zone)

	return local

@register.filter
def format_date(str):
    if str is None:
        return ""
    try:
        date_parsed = convert_tz(dateutil.parser.parse(str))
        date_formatted = date_parsed.strftime('%b %d, %Y')
    except ValueError:
        date_formatted = str

    return date_formatted

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
	# This is only relevant for Canvas (i.e. ATG uses the tool in Canvas so...)
	if settings.ORGANIZATION != 'ATG':
		return ''

	receiver = kwargs.get('receiver', 'https://canvas.harvard.edu')
	max_height = kwargs.get('max_height', None)
	min_height = kwargs.get('min_height', None) or 600
	target_type = kwargs.get('target_type', None)

	# Video and image types should constrain height automatically
	# Text types don't necessarily need/want to constrain the height
	if target_type in ('vd', 'ig') and max_height is None:
		max_height = 900;

	# This creates a JS expression to constrain the height
	height_expr = '(h + 200)'
	if max_height is not None:
		height_expr = '(h > %d ? %d : %s)' % (int(max_height), int(max_height), height_expr)
	if min_height is not None:
		height_expr = '(h < %d ? %d : %s)' % (int(min_height), int(min_height), height_expr)

	javascript = '''
// Sends message to parent to resize the iframe so we don't have scrolling issues
jQuery(document).ready(function() {
	var receiver = "%s";
	var h = jQuery("#viewer").height() || jQuery("body").height();
	var height = %s;
	var message = {
	  subject: "lti.frameResize",
	  height: height
	};
	console.log("sending lti.frameResize message", message, receiver);
	window.parent.postMessage(JSON.stringify(message), receiver);
}, 1000);
''' % (receiver, height_expr)

	return mark_safe(javascript)

@register.filter(name='only_published')
def only_published(assignments, is_instructor):
	if is_instructor:
		return assignments
	else:
		return assignments.filter(is_published=True)
