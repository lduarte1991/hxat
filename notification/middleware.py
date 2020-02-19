
import logging
import re

from importlib import import_module
from urllib.parse import parse_qs

from django.conf import settings
from django.contrib.sessions.models import Session
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

        # not authorized yet
        scope['hxat_auth'] = 'forbidden'

        # parse path to get context_id, collection_id, target_source_id
        path = scope.get('path')
        room_name = path.split('/')[-2]  # assumes path ends with a '/'
        (context, collection, target) = room_name.split('--')
        self.log.debug('******************** context({}) collection({}) target({})'.format(context, collection, target))

        query_string = scope.get('query_string', '')
        parsed_query = parse_qs(query_string)
        self.log.debug('******************** parsed({})'.format(parsed_query)),

        if not parsed_query:
            self.log.debug('******************** finished with middleware EARLY: no query string')
            return self.inner(scope)

        session_id = parsed_query.get(b'utm_source', None)[0].decode()
        resource_link_id = parsed_query.get(b'resource_link_id', None)[0].decode()

        self.log.debug('******************** sid({}) rid({})'.format(session_id,
            resource_link_id))

        if session_id is None or resource_link_id is None:
            # forbidden: missing session id in query string
            self.log.debug('******************** missing session-id or resource-link-id')
            return self.inner(scope)

        session = SessionStore(session_id)
        if not session.exists(session_id):
            # forbidden: unknown session id
            self.log.debug('******************** unknown session-id({})'.format(session_id))
        else:
            multi_launch = session.get('LTI_LAUNCH', {})
            lti_launch = multi_launch.get(resource_link_id, {})
            lti_params = lti_launch.get('launch_params', {})

            # check the context-id matches the channel being connected
            clean_context_id = re.sub('[\W_]', '-', lti_params.get('context_id', ''))
            self.log.debug('******************** context_id[{}] = {}'.format(clean_context_id, context))
            if clean_context_id == context:
                scope['hxat_auth'] = 'authenticated'

        self.log.debug('******************** finished with middleware')
        return self.inner(scope)




