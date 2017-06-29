"""
middleware.py
by Arthur Barrett, ATG

For usage of the LTI tool within an iFrame. It checks to make sure that the
iframe is being loaded from one of the sites listed in the
X_FRAME_ALLOWED_SITES set in the settings for the instance of the project.

It then either Denies access to the site or sets an ALLOW-FROM attribute for
that particular URL.

Note: Chrome, Safari, and IE ignore Allow-From, though they should still
load the iframe.
"""
import collections

from django.conf import settings
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from ims_lti_py.tool_provider import DjangoToolProvider
import logging
import time
import urlparse
import json
import importlib
import oauth2

logger = logging.getLogger(__name__)

def ip_address(request):
    ''' Returns the real IP address from a request, or if that fails, returns 1.2.3.4.'''
    meta = request.META
    return meta.get('HTTP_X_FORWARDED_FOR', meta.get('HTTP_X_REAL_IP', meta.get('REMOTE_ADDR', '1.2.3.4')))


class XFrameOptionsMiddleware(object):
    def __init__(self):
        self.logger = logging.getLogger('{module}.{cls}'.format(module=__name__, cls=self.__class__.__name__))

    def process_response(self, request, response):
        self.logger.info("Inside %s process_response: %s" % (self.__class__.__name__, request.path))
        return self._set_xframe_options(request, response)

    def _set_xframe_options(self, request, response):
        referrer = request.META.get('HTTP_REFERER')
        self.logger.debug("server_name: %s http_referrer: %s" % (settings.SERVER_NAME, referrer))

        # if this is localhost and non-https (i.e. development), we won't
        # receive the referer header so just make the response exempt from xframe controls
        if settings.SERVER_NAME == 'localhost':
            setattr(response, 'xframe_options_exempt', True)
            return response

        # person accessed site directly (not via iframe) so leave response as is
        if referrer is None:
            return response

        # person is navigating the site internally, so just set the original reference
        if settings.SERVER_NAME in referrer:
            try:
                response['X-Frame-Options'] = "ALLOW-FROM " + request.session['hx_lti_original_ref']
                return response
            except:
                return response

        # otherwise check if the referrer is an allowed site
        else:
            # parse the url it came from and default to not allow
            parsed_uri = urlparse.urlparse(referrer)
            domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
            x_frame_allow = False

            # if it does exist within the allowed list, then allow it to enter
            # the map here is for situations in which the user is clicking
            # within the LTI tool but the iframe still needs to give
            # permissions to the consumer site.
            for item in settings.X_FRAME_ALLOWED_SITES:
                if domain.endswith(item):
                    x_frame_allow = domain

            # explicitly set it to deny or allow from the site if found
            if x_frame_allow is False:
                response['X-Frame-Options'] = "DENY"
            else:
                response['X-Frame-Options'] = "ALLOW-FROM " + x_frame_allow
                request.session["hx_lti_original_ref"] = x_frame_allow

            self.logger.debug('X-Frame-Options: %s' % response['X-Frame-Options'])

            return response



class CookielessSessionMiddleware(object):
    '''
    This middleware implements cookieless sessions by retrieving the session identifier 
    from  cookies (preferred, if available) or the request URL.
    
    This must be added to INSTALLED_APPS prior to other middleware that uses the session.
    '''
    def __init__(self):
        logger.debug("Starting session engine %s" % settings.SESSION_ENGINE)
        engine = importlib.import_module(settings.SESSION_ENGINE)
        self.SessionStore = engine.SessionStore
        self.logger = logging.getLogger('{module}.{cls}'.format(module=__name__, cls=self.__class__.__name__))

    def process_request(self, request):
        self.logger.info("Inside %s process_request: %s" % (self.__class__.__name__, request.path))

        # Retrieve the sessionid from the cookiejar, or if cookies are not allowed, attempt to
        # get the identifier from the URL query string. Note that the query parameter is obfuscated as 'utm_source'.
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, request.GET.get('utm_source'))
        request.session = self.SessionStore(session_key)
        self.logger.debug("Loaded session store using session_key: %s" % session_key)

        if not request.session.exists(session_key):
            self.logger.debug("Session does not exist. Creating new session.")
            request.session.create()

        # Mitigate security risks by ensuring the requesting user's IP matches the logged IP
        try:
            request_ip = ip_address(request)
            logged_ip = request.session['LOGGED_IP']
            if request_ip != logged_ip:
                self.logger.warning("IP address does not match IP logged in session: %s != %s" % (request_ip, logged_ip))
                request.session.flush()
        except:
            pass



class MultiLTILaunchMiddleware(object):
    '''
    This middleware detects an LTI launch request, validates it, and stores multiple LTI launches
    in a single session.

    The current LTI launch may be accessed via the request.LTI attribute, which maps to an entry
    in the request.session['LTI_LAUNCH'] dict keyed by the resource_link_id.

    Note: this middleware is derived from django_auth_lti.middleware_patched with some changes for
    this application.
    '''
    def __init__(self):
        self.logger = logging.getLogger('{module}.{cls}'.format(module=__name__, cls=self.__class__.__name__))

    def process_request(self, request):
        self.logger.info("Inside %s process_request: %s" % (self.__class__.__name__, request.path))
        is_basic_lti_launch = (request.method == 'POST' and request.POST.get('lti_message_type') == 'basic-lti-launch-request')
        self.logger.debug("basic-lti-launch-request? %s" % is_basic_lti_launch)
        if is_basic_lti_launch:
            self._validate_request(request)
            self._update_session(request)
            self._log_ip_address(request)
            self._set_current_session(request, resource_link_id=request.POST.get('resource_link_id'), raise_exception=True)
        else:
            self._set_current_session(request, resource_link_id=request.GET.get('resource_link_id'), raise_exception=False)

    def _validate_request(self, request):
        '''
        Validates an LTI launch request.
        '''
        consumer_key = getattr(settings, 'CONSUMER_KEY', None)
        secret = getattr(settings, 'LTI_SECRET', None)
        if consumer_key is None or secret is None:
            self.logger.error("missing consumer key/secret: %s/%s" % (consumer_key, secret))
            raise ImproperlyConfigured("Unable to validate LTI launch. Missing setting: CONSUMER_KEY or LTI_SECRET")

        request_key = request.POST.get('oauth_consumer_key', None)
        if request_key is None:
            self.logger.error("request doesn't contain an oauth_consumer_key; can't continue.")
            raise PermissionDenied

        if request_key != consumer_key:
            self.logger.error("could not get a secret for requested key: %s" % request_key)
            raise PermissionDenied

            self.logger.debug('using key/secret %s/%s' % (request_key, secret))
        tool_provider = DjangoToolProvider(request_key, secret, request.POST)

        postparams = request.POST.dict()
        self.logger.debug('request is secure: %s' % request.is_secure())
        for key in postparams:
            self.logger.debug('POST %s: %s' % (key, postparams.get(key)))
        self.logger.debug('request abs url is %s' % request.build_absolute_uri())
        for key in request.META:
            self.logger.debug('META %s: %s' % (key, request.META.get(key)))

        self.logger.info("about to check the signature")
        try:
            # NOTE: before validating the request, temporarily remove the
            # QUERY_STRING to work around an issue with how Canvas signs requests
            # that contain GET parameters. Before Canvas launches the tool, it duplicates the GET
            # parameters as POST parameters, and signs the POST parameters (*not* the GET parameters).
            # However, the oauth2 library that validates the request generates
            # the oauth signature based on the combination of POST+GET parameters together,
            # resulting in a signature mismatch. By removing the QUERY_STRING before
            # validating the request, the library will generate the signature based only on
            # the POST parameters like Canvas.
            qs = request.META.pop('QUERY_STRING', '')
            self.logger.debug('removed query string temporarily: %s' % qs)
            request_is_valid = tool_provider.is_valid_request(request, parameters={}, handle_error=False)
            request.META['QUERY_STRING'] = qs  # restore the query string
            self.logger.debug('restored query string: %s' % request.META['QUERY_STRING'])
        except oauth2.Error:
            self.logger.exception(u'error attempting to validate LTI launch %s' % postparams)
            request_is_valid = False

        if request_is_valid:
            self.logger.info("signature verified")
        else:
            self.logger.error("invalid request: signature check failed")
            raise PermissionDenied

        self.logger.info("about to check the timestamp: %d" % int(tool_provider.oauth_timestamp))
        if time.time() - int(tool_provider.oauth_timestamp) > 60 * 60:
            self.logger.error("OAuth timestamp is too old.")
            # raise PermissionDenied
        else:
            self.logger.info("OAuth timestamp looks good")
        self.logger.info("done checking the timestamp")

        for required_param in ('resource_link_id', 'context_id', 'user_id'):
            self.logger.info("about to check that %s was provided" % required_param)
            if required_param not in request.POST:
                self.logger.error('LTI param %s was not present in request' % required_param)
                raise PermissionDenied

        if ('lis_person_sourcedid' not in request.POST and 'lis_person_name_full' not in request.POST and request.POST['user_id'] != "student"):
            self.logger.error('person identifier (i.e. username) or full name was not present in request')
            raise PermissionDenied

    def _update_session(self, request):
        '''
        Updates the session with the current LTI launch request. There may be multiple LTI launches associated with a 
        single session. Each LTI launch is mapped to its POST parameters using the resource_link_id as the key.

        Example:

            session = {
                "LTI_LAUNCH": {
                    "5c5d07410": {},
                    "31b533624": {},
                    "023c227e2": {},
                }
            }

        The current LTI launch request may be accessed via the request.LTI attribute, which is automatically set
        to the correct entry in the LTI_LAUNCH mapping.
        '''
        resource_link_id = request.POST.get('resource_link_id', None)
        postparams = request.POST.dict()
        lti_params = dict(postparams)
        lti_params.update({
            'roles': [role for role in postparams.get('roles', '').split(',') if role != '']
        })

        lti_launches = request.session.get('LTI_LAUNCH', None)
        if not lti_launches:
            lti_launches = collections.OrderedDict()
            request.session['LTI_LAUNCH'] = lti_launches

        max_launches = getattr(settings, 'LTI_MAX_LAUNCHES', 10)
        self.logger.info("LTI launches in session: %s [max=%s]" % (lti_launches.keys(), max_launches))
        if len(lti_launches.keys()) >= max_launches:
            invalidated_launch = lti_launches.popitem(last=False)
            self.logger.info("LTI launch invalidated: %s", json.dumps(invalidated_launch, indent=4))

        lti_launches[resource_link_id] = {
            'launch_params': lti_params,
            'resource_link_id': resource_link_id,
        }
        request.session.modified = True
        self.logger.info("LTI launch session saved: %s" % resource_link_id)

    def _log_ip_address(self, request):
        '''
        Logs the IP address in the session.
        '''
        logged_ip = ip_address(request)
        request.session['LOGGED_IP'] = logged_ip
        self.logger.info("Logged IP address: %s" % logged_ip)

    def _set_current_session(self, request, resource_link_id=None, raise_exception=False):
        '''
         Sets the current session on the request object based on the given resource_link_id.
         The current session is available via the 'LTI' attribute on the request (e.g. request.LTI).
        '''
        setattr(request, 'LTI', LTILaunchSession(request.session, resource_link_id))
        #setattr(request, 'LTI', request.session.get('LTI_LAUNCH', {}).get(resource_link_id))
        self.logger.info("setting current LTI session to resource_link_id=%s" % resource_link_id)


class LTILaunchSession(object):
    '''
    Dict-like object that provides access to the session dict containing for the LTI Launch,
    which is keyed by the resource_link_id.

    The main reason this object exists is to provide better error handling when accessing a
    key that does not exist, usually because the resource_link_id wasn't provided in the
    request. Otherwise, you would just get a generic KeyError from the session dict object.

    Note that we don't validate when the object is created, because it is added as an attribute
    to the request object for all types of requests, some of which don't have an LTI launch
    session associated with them. The Django Admin interface is an example of that. Ideally,
    we would only set the attribute on views where it is applicable.
    '''
    def __init__(self, session, resource_link_id=None):
        self.session = session
        self.resource_link_id = resource_link_id
        self.logger = logging.getLogger('{module}.{cls}'.format(module=__name__, cls=self.__class__.__name__))

    def valid(self):
        '''Returns true if the launch session dict is populated and can be keyed by the resource_link_id, otherwise False.'''
        return self.resource_link_id is not None and bool(self.session.get('LTI_LAUNCH', {}).get(self.resource_link_id)) is True

    def assert_valid(self):
        '''Raises an exception if a valid launch session is not present, usually because the resource_link_id is not provided.'''
        if not self.valid():
            logmsg = "Invalid LTI launch session [resource_link_id=%s]" % self.resource_link_id
            self.logger.error(logmsg)
            raise Exception(logmsg)

    def get(self, key, default_value=None):
        self.assert_valid()
        return self.session['LTI_LAUNCH'][self.resource_link_id].get(key, default_value)

    def __getitem__(self, key):
        self.assert_valid()
        return self.session['LTI_LAUNCH'][self.resource_link_id][key]

    def __setitem__(self, key, value):
        self.assert_valid()
        self.session['LTI_LAUNCH'][self.resource_link_id][key] = value
        self.session.modified = True

    def __delitem__(self, key):
        self.assert_valid()
        try:
            del self.session['LTI_LAUNCH'][self.resource_link_id][key]
            self.session.modified = True
        except KeyError:
            pass

    def __len__(self):
        self.assert_valid()
        return len(self.session['LTI_LAUNCH'][self.resource_link_id])

    def __iter__(self):
        self.assert_valid()
        return self.session['LTI_LAUNCH'][self.resource_link_id].iterkeys()

    def __contains__(self, item):
        self.assert_valid()
        return item in self.session['LTI_LAUNCH'][self.resource_link_id]

    def __repr__(self):
        self.assert_valid()
        return repr(self.session['LTI_LAUNCH'][self.resource_link_id])