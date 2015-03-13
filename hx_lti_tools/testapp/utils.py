import base64

def get_lti_value(key, tool_provider, encoding=None):
    """ Searches for the given key in the tool_provider and its custom and external params.  
        If not found returns None """
    
    lti_value = None
    
    if "custom" in key:
        lti_value = tool_provider.custom_params[key]
    if "ext" in key:
        lti_value = tool_provider.ext_params[key]
    if not lti_value:
        try:
            lti_value = getattr(tool_provider,key)
        except AttributeError:
            print "Attribute: %s not found in LTI tool_provider" % key

    if encoding == "base64": 
        if isinstance(lti_value, list):
            lti_value = [base64.b64decode(val) for val in lti_value] 
        else:
            lti_value = base64.b64decode(lti_value)
    if encoding == "utf8": lti_value = lti_value.decode('utf-8')
    if encoding == "iso": lti_value = lti_value.decode('latin-1')

    return lti_value

