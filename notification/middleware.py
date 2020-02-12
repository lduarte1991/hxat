
import logging

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
            self.log.debug('******************** sid and rid NOT NONE')
            session = SessionStore(session_id)
            # -------------------------------------------------
            '''
            try:
                session = Session.objects.get(pk=session_id)
                self.log.debug('******************** session[{}] = ({})'.format(type(session), session))
                for k,v in vars(session).items():
                    self.log.debug('******************** session[{}] = ({})'.format(k,v))

            except DoesNotExist as e:
                self.log.debug('******************** unknown session-id({})'.format(session_id))
                scope['hxat_auth'] = 'forbidden'


            s = session.get_decoded()
            self.log.debug('******************** SESSION({}) len({})'.format(s, len(s)))
            for key, value in s.items():
                self.log.debug('******************** SESSION[{}] = {}'.format(key, value))


            '''
            # -------------------------------------------------
            if session.exists(session_id):
                for attr, value in vars(session).items():
                    self.log.debug('******************** SESSION[{}] = {}'.format(attr, value))

                lti_launch = session.get('LTI_LAUNCH', {})
                for attr, value in lti_launch.items():
                    self.log.debug('******************** LTI_LAUTCH[{}] = {}'.format(attr, value))

                lti_obj = lti_launch.get(resource_link_id, None)
                if lti_obj is not None:
                    for key in lti_obj.keys():
                        self.log.debug('******************** lti-session[{}] = {}'.format(key, lti_obj[key]))
                    scope['hxat_auth'] = 'authenticated'
                else:
                    self.log.debug(
                            '******************** session({}) lti_obj({})'.format(session, lti_obj))

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

