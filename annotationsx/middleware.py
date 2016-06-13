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
import time
from django.conf import settings
from urlparse import urlparse
from hx_lti_initializer.utils import debug_printer
from importlib import import_module
from django.utils.cache import patch_vary_headers
from django.utils.http import cookie_date


class XFrameOptionsMiddleware(object):
    def process_response(self, request, response):
        debug_printer('DEBUG - X-Frame-Options Middleware')
        debug_printer(settings.SERVER_NAME)
        referrer = request.META.get('HTTP_REFERER')

        # if this is localhost and non-https (i.e. development), we won't
        # receive the referer header so just make the response exempt from xframe controls
        if settings.SERVER_NAME == 'localhost':
            setattr(response, 'xframe_options_exempt', True)
            return response

        # means the person accessed site directly and not via iframe so
        # leave response as is
        if referrer is None:
            return response

        if settings.SERVER_NAME in referrer:
            try:
                response['X-Frame-Options'] = "ALLOW-FROM " +\
                    request.session['hx_lti_original_ref']
                return response
            except:
                return response
        else:
            # parse the url it came from and default to not allow
            parsed_uri = urlparse(referrer)
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

            debug_printer('DEBUG - URI: %s' % domain)
            debug_printer('DEBUG - X-Frame: %s' % response['X-Frame-Options'])

            return response


class SessionMiddleware(object):
    '''
    session middleware that support multiple sessions based on url
    '''

    def __init__(self):
        engine = import_module(settings.SESSION_ENGINE)
        self.SessionStore = engine.SessionStore
        print "STarting engine"

    def get_cookie_name(self, request):
        '''
        get session cookie name based on url
        '''
        return "sessionid_" + request.path.split("/")[1]

    def process_request(self, request):
        session_key = request.COOKIES.get(self.get_cookie_name(request), None)
        request.session = self.SessionStore(session_key)

    def process_response(self, request, response):
        """
        If request.session was modified, or if the configuration is to save the
        session every time, save the changes and set a session cookie or delete
        the session cookie if the session has been emptied.
        """
        try:
            accessed = request.session.accessed
            print str(accessed)
            modified = request.session.modified
            print str(modified)
            empty = request.session.is_empty()
            print str(empty)
        except AttributeError:
            pass
        else:
            # First check if we need to delete this cookie.
            # The session should be deleted only if the session is entirely empty
            if self.get_cookie_name(request) in request.COOKIES and empty:
                response.delete_cookie(self.get_cookie_name(request),
                    domain=settings.SESSION_COOKIE_DOMAIN)
            else:
                if accessed:
                    patch_vary_headers(response, ('Cookie',))
                if modified or settings.SESSION_SAVE_EVERY_REQUEST:
                    if request.session.get_expire_at_browser_close():
                        max_age = None
                        expires = None
                    else:
                        max_age = request.session.get_expiry_age()
                        expires_time = time.time() + max_age
                        expires = cookie_date(expires_time)
                    # Save the session data and refresh the client cookie.
                    # Skip session save for 500 responses, refs #3881.
                    if response.status_code != 500:
                        request.session.save()
                        response.set_cookie(self.get_cookie_name(request),
                                request.session.session_key, max_age=max_age,
                                expires=expires, domain=settings.SESSION_COOKIE_DOMAIN,
                                path=settings.SESSION_COOKIE_PATH,
                                secure=settings.SESSION_COOKIE_SECURE or None,
                                httponly=settings.SESSION_COOKIE_HTTPONLY or None)
        return response