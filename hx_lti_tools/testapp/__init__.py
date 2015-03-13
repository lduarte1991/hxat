"""
File contains default settings.
"""

from django.conf import settings

def setconf(name, default_value):
    """set default value in django.conf.settings"""
    value = getattr(settings, name, default_value)
    setattr(settings, name, value)

setconf('LTI_DEBUG', True)
setconf('AUTH_PROFILE_MODULE', 'uocLTI.LTIProfile')
setconf('CONSUMER_URL', 'http://54.69.120.77:8000/testapp/launch_lti/')
setconf('CONSUMER_KEY', '123key')
setconf('LTI_SECRET', 'secret')
setconf('LTI_FIRST_NAME','lis_person_name_given')
setconf('LTI_LAST_NAME','lis_person_name_family')
setconf('LTI_EMAIL','lis_person_contact_email_primary')
setconf('LTI_ROLES', 'roles')

