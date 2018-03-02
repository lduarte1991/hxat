def resource_link_id_processor(request):
    '''
    This template context processor adds the "resource_link_id" value to the context for all templates.

    Templates will need to add this to URLs as a GET parameter so that the the correct LTI launch session is used
    on subsequent requests, as users may have multiple LTI sessions active at one time.
    '''
    if hasattr(request, 'LTI') and request.LTI.valid():
        return {'resource_link_id': request.LTI['resource_link_id']}
    return {}

def utm_source_processor(request):
    '''
    This template context processor adds the "utm_source" value to the context for all templates.
    '''
    if hasattr(request, 'LTI') and request.LTI.valid():
        return {'utm_source': request.session.session_key, 'utm_source_param': 'utm_source=%s' % request.session.session_key}
    return {}
