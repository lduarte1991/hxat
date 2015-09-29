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

from django.conf import settings
from urlparse import urlparse
from hx_lti_initializer.utils import debug_printer


class XFrameOptionsMiddleware(object):
    def process_response(self, request, response):
        debug_printer('DEBUG - X-Frame-Options Middleware')
        debug_printer(settings.SERVER_NAME)
        referrer = request.META.get('HTTP_REFERER')
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
