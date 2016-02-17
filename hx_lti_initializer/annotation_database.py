import json
import logging

logger = logging.getLogger(__name__)

ADMIN_GROUP_ID = '__admin__'

def update_read_permissions(data):
    '''
    Given an annotation data object, update the "read" permissions so that
    course admins can view private annotations.
    
    Instead of adding the specific user IDs of course admins, a group identifier is used
    so that the IDs aren't hard-coded, which would require updating if the list of admins
    changes in the tool. It's expected that when the tool searchs the annotation database on
    behalf of a course admin, it will use the admin group identifier.
    
    Possible read permissions:
       - permissions.read = []                        # world-readable (public)
       - permissions.read = [user_id]                 # private (user only)
       - permissions.read = [user_id, ADMIN_GROUP_ID] # semi-private (user + admins only)
    
    '''
    logger.debug("update_read_permissions(): %s" % json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))
    has_permissions = ('permissions' in data and 'read' in data['permissions'])
    if not has_permissions:
        return data

    # Do nothing if the annotation is world-readable
    if len(data['permissions']['read']) == 0:
        return data
    
    has_parent = ('parent' in data and data['parent'] != '' and data['parent'] != '0')
    if has_parent:
        # This is here to ensure that when a reply is created, it remains visible to the
        # author of the parent annotation, even if the reply has unchecked "Allow anyone to view
        # this annotation" in the annotator editor. Ideally, the annotator UI field should either 
        # be removed from the annotator editor for replies, or work as expected. That is, when checked, 
        # only the annotation author, reply author, and thread participants have read permission. 
        data['permissions']['read'] = []
        logger.debug("update_read_permissions(): reply: %s" % data['permissions']['read'])
    else:
        # Ensure the annotation is readable by course admins
        read_permissions = data['permissions']['read']
        if ADMIN_GROUP_ID not in read_permissions:
            read_permissions.append(ADMIN_GROUP_ID)
            logger.debug("update_read_permissions(): annotation: %s" % read_permissions)

    return data
