from django.template import Library

register = Library()

@register.filter_function
def list_of_ids(admin_profiles):
    admins = []
    for instructors in admin_profiles.all():
    	if instructors.anon_id is not None:
    		admins.append(str(instructors.anon_id))
    return admins