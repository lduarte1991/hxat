from django.template import Library
from hx_lti_initializer.models import LTIProfile

register = Library()


@register.filter_function
def list_of_possible_admins(already_in_course):
    list_of_usernames_already_in_course = []
    list_of_unique_names = []
    result = []

    for profile in LTIProfile.objects.all():
        if profile.id in already_in_course:
            list_of_usernames_already_in_course.append(profile.user.username)
        if profile.user.username not in list_of_unique_names and "preview:" not in profile.user.username:
            list_of_unique_names.append(profile.user.username)

    for name in list_of_unique_names:
        result.append((name in list_of_usernames_already_in_course, name))

    return result
