def resource_link_id_processor(request):
    '''
    This template context processor adds the "resource_link_id" value to the context for all templates.

    Templates will need to add this to URLs as a GET parameter so that the the correct LTI launch session is used
    on subsequent requests, as users may have multiple LTI sessions active at one time.

    For example:

    http://localhost:8000/lti_init/admin_hub/:course_id/:assignment_id/:object_id/preview/?resource_link_id=2a8b2d3fa51ea413d19e480fb6c2eb085b7866a9

    '''
    if hasattr(request, 'LTI') and request.LTI.valid():
        return {'resource_link_id': request.LTI['resource_link_id']}
    return {}

def utm_source_processor(request):
    if hasattr(request, 'LTI') and request.LTI.valid():
        return {'utm_source': '' if request.LTI.get('is_staff', False) else request.session.session_key}
    return {}
