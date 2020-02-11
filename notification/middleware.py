
import logging

from importlib import import_module
from urllib.parse import parse_qs

from django.conf import settings
from django.db import close_old_connections


SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


class SessionAuthMiddleware(object):
    """auth via session_id in query string."""



    def __init__(self, inner):
        self.inner = inner
        self.log = logging.getLogger(__name__)


    def __call__(self, scope):
        for key in scope.keys():
            self.log.debug('******************** scope({}) = ({})'.format(key,
                scope.get(key)))

        query_string = scope.get('query_string', '')
        self.log.debug('******************** qs({})'.format(query_string)),

        parsed_query = parse_qs(query_string)
        self.log.debug('******************** parsed({})'.format(parsed_query)),

        if not parsed_query:
            scope['hxat_auth'] = 'forbiden'
            self.log.debug('******************** finished with middleware EARLY: no query string')
            return self.inner(scope)

        session_id = parsed_query.get(b'utm_source', None)[0].decode()
        resource_link_id = parsed_query.get(b'resource_link_id', None)[0].decode()

        self.log.debug('******************** sid({}) rid({})'.format(session_id,
            resource_link_id))

        if session_id is not None and resource_link_id is not None:
            session = SessionStore(session_id)
            if session.exists(session_id):
                lti_obj = session.get(resource_link_id, None)
                if lti_obj is not None:
                    for key in lti_obj.keys():
                        self.log.debug('******************** lti-session[{}] = {}'.format(key, lti_obj[key]))
                    scope['hxat_auth'] = 'authenticated'
            else:
                # forbidden: unknown session id
                self.log.debug('******************** unknown session-id({})'.format(session_id))
                scope['hxat_auth'] = 'forbidden'
                pass
        else:
            # forbidden: missing session id in query string
            self.log.debug('******************** missing session-id or resource-link-id')
            scope['hxat_auth'] = 'forbidden'
            pass

        self.log.debug('******************** finished with middleware')
        return self.inner(scope)

