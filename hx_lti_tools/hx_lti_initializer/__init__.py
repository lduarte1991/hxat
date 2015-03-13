"""
Default settings for the LTI Initializer

Should set up all things needed for the Annotation tool to be set up including the url for the tool to be accessed and for any other variables to be stored.
"""

from django.conf import settings

def setconf(name, default_value):
    """set default value in django.conf.settings"""
    value = getattr(settings, name, default_value)
    setattr(settings, name, value)

# once in production, make sure to turn this to false
setconf('LTI_DEBUG', True)

# change the url to the proper point to verify they are trying to access the correct location
setconf('CONSUMER_URL', 'http://54.69.120.77:8000/lti_init/launch_lti/')

# note that consumer key will be visible via the request
setconf('CONSUMER_KEY', '123key')

# the secret token will be encoded in the request. Only places visible are here and the secret given to the LTI consumer, in other words, keep it hidden!
setconf('LTI_SECRET', 'secret')

# should change depending on the information given by the various platforms using it
setconf('LTI_EMAIL','lis_person_contact_email_primary')
setconf('LTI_USERNAME', 'lis_person_sourcedid')
setconf('LTI_ANON_ID', 'user_id')
setconf('LTI_ROLES', 'roles')
setconf('LTI_COURSE_ID', 'context_id')

# should be changed depending on platform roles, these are set up for edX
setconf('ALL_ROLES', {'Student', 'Administrator', 'Instructor'})
setconf('ADMIN_ROLES', {'Administrator', 'Instructor'})

