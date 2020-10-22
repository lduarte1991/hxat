from django import template
from django.conf import settings
from django.template import Library
from target_object_database.models import get_extension

register = Library()


@register.filter_function
def just_the_view_type(extra_options):
    if extra_options is None:
        return "ImageView"
    result = extra_options.split(',')
    if len(result) < 2:
        return "ImageView"
    else:
        return result[0].strip()


@register.filter_function
def just_the_canvas_id(extra_options):
    if extra_options is None:
        return ""
    result = extra_options.split(',')
    if len(result) < 2:
        return ""
    else:
        return result[1].strip()


@register.filter_function
def just_dashboard_hidden(extra_options):
    if extra_options is None:
        return False
    result = extra_options.split(',')
    if len(result) < 3:
        return False
    else:
        if result[2].strip() == "true":
            return True
        else:
            return False


@register.filter_function
def just_transcript_hidden(extra_options):
    if extra_options is None:
        return False
    result = extra_options.split(',')
    if len(result) < 4:
        return False
    else:
        if result[3].strip() == "true":
            return True
        else:
            return False


@register.filter_function
def just_transcript_download(extra_options):
    if extra_options is None:
        return False
    result = extra_options.split(',')
    if len(result) < 5:
        return False
    else:
        if result[4].strip() == "true":
            return True
        else:
            return False


@register.filter_function
def just_video_download(extra_options):
    if extra_options is None:
        return False
    result = extra_options.split(',')
    if len(result) < 6:
        return False
    else:
        if result[5].strip() == "true":
            return True
        else:
            return False


@register.tag(name='captureas')
def do_captureas(parser, token):
    try:
        tag_name, args = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("'captureas' requires a variable.")
    nodelist = parser.parse(('endcaptureas',))
    parser.delete_first_token()
    return CaptureasNode(nodelist, args)


@register.filter_function
def just_the_youtube_vid_link(content, target_type='vd'):
    if content is None or target_type != 'vd':
        return ""
    result = content.split(';')
    if len(result) < 3:
        if get_extension(result[0]) == "video/youtube":
            return result[0]
        else:
            return ""
    if len(result) == 3:
        return result[0]

@register.filter_function
def just_the_html5_vid_link(content, target_type='vd'):
    if content is None or target_type != 'vd':
        return ""
    result = content.split(';')
    if len(result) < 3:
        if get_extension(result[0]) != "video/youtube":
            return result[0]
        else:
            return ""
    if len(result) == 3:
        return result[1]


@register.filter_function
def just_the_transcript_link(content, target_type='vd'):
    if content is None or target_type != 'vd':
        if settings.ANNOTATION_TRANSCRIPT_LINK_DEFAULT:
            return settings.ANNOTATION_TRANSCRIPT_LINK_DEFAULT
        else:
            return ""
    result = content.split(';')
    return result[len(result) - 1]


class CaptureasNode(template.Node):
    def __init__(self, nodelist, varname):
        self.nodelist = nodelist
        self.varname = varname

    def render(self, context):
        output = self.nodelist.render(context)
        context[self.varname] = output
        return ''
