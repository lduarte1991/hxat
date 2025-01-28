import logging
import re
from importlib import import_module
from urllib.parse import parse_qs

from django.conf import settings
from django.contrib.sessions.models import Session
from django.db import close_old_connections

from asgiref.sync import sync_to_async
from channels.middleware import BaseMiddleware
from channels.sessions import CookieMiddleware, SessionMiddleware

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


@sync_to_async
def _async_session_exists(session_id):
    '''
    Returns an awaitable for checking if a session exists.

    NOTE: `sync_to_async` is necessary because the SessionStore
    uses the DB, and therefore is a synchronous operation. The `sync_to_async`
    utility turns `session.exists()` into an awaitable.
    '''
    return SessionStore(session_id).exists(session_id)


@sync_to_async
def _async_session_get_ltilaunch(session=None, session_id=None):
    '''
    Returns an awaitable for loading the LTI_LAUNCH data from the session.

    expect either session or session_id non-null

    NOTE: `sync_to_async` is necessary because the SessionStore
    uses the DB, and therefore is a synchronous operation. The `sync_to_async`
    utility turns `session.get()` into an awaitable.
    '''
    logging.getLogger(__name__).info("################ lti_launch from session_id({})".format(session_id))
    SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
    exists = SessionStore(session_id).exists(session_id)
    logging.getLogger(__name__).info("################ EXISTS ({})".format(exists))
    session = SessionStore(session_id)
    logging.getLogger(__name__).info("################ session ({})".format(session.keys()))

    multi_launch = SessionStore(session_id).get("LTI_LAUNCH", {})
    logging.getLogger(__name__).info("################ launch ({})".format(multi_launch))

    return SessionStore(session_id).get("LTI_LAUNCH", {})


    if session is None:
        logging.getLogger(__name__).info("################ lti_launch({}) from session in scope".format(session.get("LTI_LAUNCH")))
        return session.get("LTI_LAUNCH")
    elif session_id:
        logging.getLogger(__name__).info("################ lti_launch from session_id")
        return SessionStore(session_id).get("LTI_LAUNCH")
    else:
        logging.getLogger(__name__).info("################ lti_launch empty")
        return {}


class NotificationAuthMiddleware(BaseMiddleware):
    """
    Middleware to check session and validate notification connection.
    Requires SessionMiddleware and CookieMiddleware to function.
    """

    def parse_room_name(self, scope):
        # parse path to get context_id, collection_id, target_source_id
        path = scope.get("path")
        room_name = path.split("/")[-2]  # assumes path ends with a '/'
        try:
            (context, collection, target) = room_name.split("--")
        except ValueError:
            return (None, None, None)
        try:
            tgt, _ = target.split("-")  # hxighliter appends a canvas-id
        except ValueError:
            tgt = target
        return (context, collection, tgt)


    def parse_querystring(self, scope):
        # parse query string for session-id and resource-link-id
        parsed_query = parse_qs(scope.get("query_string", ""))
        if parsed_query:
            session_id = parsed_query.get(b"utm_source", [b""])[0].decode()
            resource_link_id = parsed_query.get(b"resource_link_id", [b""])[0].decode()
            logging.getLogger(__name__).info(
                "NOTIFY: rid({}) sid({})".format(resource_link_id, session_id)
            )
            return (session_id, resource_link_id)
        else:
            logging.getLogger(__name__).error("NOTIFY: missing querystring")
            return (None, None)


    async def get_ltilaunch(self, scope, session_id=None):
        # pull session from scope or querystring
        try:
            # prefer session from scope
            session = scope["session"]
            logging.getLogger(__name__).error("--------------- session from scope({})")
        except ValueError:
            # not available via cookie, trying session_id from query_string
            if session_id is not None:
                # close old db conn to prevent usage of timed out conn
                # see https://channels.readthedocs.io/en/latest/topics/authentication.html#custom-authentication
                close_old_connections()
                session_exists = await _async_session_exists(session_id)
                if session_exists:
                    # get lti launch from session
                    multi_launch = await _async_session_get_ltilaunch(session_id=session_id)
                else:
                    # no session found!
                    logging.getLogger(__name__).error(
                        "NOTIFY: session_id({}) not found".format(session_id)
                    )
                    return {}
            else:  # no session via cookie nor querystring
                logging.getLogger(__name__).error(
                    "NOTIFY: missing session_id from querystring"
                )
                return {}
        else:  # session from scope, note that multi-launch might be empty!
            close_old_connections()
            multi_launch = await _async_session_get_ltilaunch(session=session)
            logging.getLogger(__name__).error("--------------- mlaunch from scope({})".format(multi_launch.keys()))

        return multi_launch


    def check_lti_launch(self, scope, lti_launch):
        # validate room_name from path with session info
        #
        # when authenticated returns used_id, and non-zero context, collection, target

        (context, collection, target) = self.parse_room_name(scope)
        if not context or not collection or not target:
            logging.getLogger(__name__).error(
                "NOTIFY 403: invalid room_name from path({})".format(scope["path"])
            )
        else:
            # check the context-id matches the channel being connected
            pat = re.compile("[^a-zA-Z0-9-.]")
            try:
                clean_context_id = pat.sub("-", lti_launch["hx_context_id"])
                clean_collection_id = pat.sub("-", lti_launch["hx_collection_id"])
                clean_target_id = str(lti_launch["hx_object_id"])
            except ValueError as e:
                logging.getLogger(__name__).error(
                    "NOTIFY 403: missing from lti_launch: {}".format(e)
                )
            else:
                if clean_context_id == context:
                    if clean_collection_id == collection:
                        if clean_target_id == target:
                            # AUTHENTICATED!
                            logging.getLogger(__name__).info("NOTIFY AUTHENTICATED AUTHENTICATED AUTHENTICATED AUTHENTICATED")
                            return (context, collection, target)
                        else:
                            logging.getLogger(__name__).error(
                                "NOTIFY 403: unknown target-object-id({}|{})".format(
                                    target, clean_target_id
                                )
                            )
                    else:
                        logging.getLogger(__name__).error(
                            "NOTIFY 403: unknown collection-id({}|{})".format(
                                collection, clean_collection_id
                            )
                        )
                else:
                    logging.getLogger(__name__).error(
                        "NOTIFY 403: unknown context-id({}|{})".format(
                            context, clean_context_id
                        )
                    )

        # if we've got here is because NOT authenticated
        return (None, None, None)


    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        scope["hx_user_id"] = "anonymous"
        scope["hx_auth"] = (None, None, None)

        # get resource_link_id from querystring
        (session_id, resource_link_id) = self.parse_querystring(scope)

        # get session_id from cookie
        session_key = scope.get("cookies", {}).get(settings.SESSION_COOKIE_NAME, None)
        if session_key:
            session_id = session_key

        logging.getLogger(__name__).error("&&&&&&&&&&&&&&&&&&&& scope({})".format(scope.keys()))

        # get lti launch
        #multi_launch = await self.get_ltilaunch(scope, session_id=session_id)
        multi_launch = await  _async_session_get_ltilaunch(session=None, session_id=session_id)
        if multi_launch and resource_link_id:
            lti_launch = multi_launch.get(resource_link_id, {})
            if not lti_launch:
                logging.getLogger(__name__).error(
                    "NOTIFY 403: resource_link_id({}) not in multi_launch".format(resource_link_id)
                )
            else:
                for key in lti_launch:
                    logging.getLogger(__name__).info(
                        "NOTIFY LTI_LAUNCH[{}]: {}".format(key, lti_launch[key])
                    )
                scope["hx_user_id"] = lti_launch.get("hx_user_id", "anonymous")
                scope["hx_auth"] = self.check_lti_launch(scope, lti_launch)

        else:  # no lti_launch or resource_link_id
            if not resource_link_id:
                logging.getLogger(__name__).error(
                    "NOTIFY 403: missing resource_link_id in querystring"
                )
            elif not multi_launch:
                logging.getLogger(__name__).error(
                    "NOTIFY 403: multi_launch not found in session"
                )

        return await super().__call__(scope, receive, send)


# Handy shortcut for applying all three layers at once
def NotificationMiddlewareStack(inner):
    return CookieMiddleware(SessionMiddleware(NotificationAuthMiddleware(inner)))


"""
09jun20 naomi:
empirically, found that, to be in the target_object page, the ui client has to
have to go through a workflow that guarantees that the session object has:
    session['resource_link_id']
    session['hx_context_id']
    session['hx_collection_id']
    session['hx_object_id']
    session['hx_user_id']
so, using these to validate the ws connect request.

"""
