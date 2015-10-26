from django.template import Library
from django import template

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
        return ""
    else:
        if result[2].strip() == "true":
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


class CaptureasNode(template.Node):
    def __init__(self, nodelist, varname):
        self.nodelist = nodelist
        self.varname = varname

    def render(self, context):
        output = self.nodelist.render(context)
        context[self.varname] = output
        return ''
