"""
middleware.py
by Arthur Barrett, ATG

For usage of the LTI tool within an iFrame. It checks to make sure that the iframe is being loaded from one
of the sites listed in the X_FRAME_ALLOWED_SITES set in the settings for the instance of the project.

It then either Denies access to the site or sets an ALLOW-FROM attribute for that particular URL.

Note: Chrome, Safari, and IE ignore Allow-From, though they should still load the iframe.
"""

from django.conf import settings
from urlparse import urlparse
from hx_lti_initializer.utils import debug_printer

class XFrameOptionsMiddleware(object):
    def process_response(self, request, response):
        debug_printer('DEBUG - X-Frame-Options Middleware')
        
        referrer = request.META.get('HTTP_REFERER')
        
        # means the person accessed site directly and not via iframe so leave response as is
        if referrer == None:
            return response
        
        # parse the url it came from and default to not allow
        parsed_uri = urlparse(referrer)
        domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
        x_frame_allow = False

        # if it does exist within the allowed list, then allow it to enter
        # the map here is for situations in which the user is clicking within the LTI tool but the iframe
        # still needst o give permissions to the consumer site.
        for item in settings.X_FRAME_ALLOWED_SITES:
            if domain.endswith(item):
                if item in settings.X_FRAME_ALLOWED_SITES_MAP:
                    x_frame_allow = '{uri.scheme}://{domain}'.format(uri=parsed_uri, domain=settings.X_FRAME_ALLOWED_SITES_MAP[item])
                else:
                    x_frame_allow = domain
                break

        # explicitly set it to deny or allow from the site if found
        if x_frame_allow is False:
            response['X-Frame-Options'] = "DENY"
        else :
            response['X-Frame-Options'] = "ALLOW-FROM " + x_frame_allow
        
        debug_printer('DEBUG - URI: %s' % domain)
        debug_printer('DEBUG - X-Frame-Options: %s' % response['X-Frame-Options'])
        
        return response