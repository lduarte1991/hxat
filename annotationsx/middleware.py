class XFrameOptionsMiddleware(object):
    def process_response(self, request, response):
        parsed_uri = urlparse(request.META.get('HTTP_REFERER'))
        referer = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
        x_frame_allow = False
        debug_printer('DEBUG - X-Frame-Options Middleware Referer: %s' % referer)
        for item in settings.X_FRAME_ALLOWED_SITES:
            if referer.endswith(item):
                if item in settings.X_FRAME_ALLOWED_SITES_MAP:
                    x_frame_allow = '{uri.scheme}://{domain}'.format(uri=parsed_uri, domain=settings.X_FRAME_ALLOWED_SITES_MAP[item])
                else:
                    x_frame_allow = referer
                break
        response = django.shortcuts.render(request, template, context)
        debug_printer('DEBUG - X-Frame-Options Middleware ALLOW-FROM: %s' % x_frame_allow)
        if x_frame_allow is False:
            response['X-Frame-Options'] = "DENY"
        else :
            response['X-Frame-Options'] = "ALLOW-FROM " + x_frame_allow
        return response
