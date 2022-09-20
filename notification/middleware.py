import logging
import re
from importlib import import_module
from urllib.parse import parse_qs

from django.conf import settings
from django.contrib.sessions.models import Session
from django.db import close_old_connections
from asgiref.sync import sync_to_async

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
def _async_session_get_ltilaunch(session_id):
    '''
    Returns an awaitable for loading the LTI_LAUNCH data from the session.

    NOTE: `sync_to_async` is necessary because the SessionStore
    uses the DB, and therefore is a synchronous operation. The `sync_to_async`
    utility turns `session.get()` into an awaitable.
    '''
    return SessionStore(session_id).get("LTI_LAUNCH", {})


class SessionAuthMiddleware(object):
    """auth via session_id in query string."""

    def __init__(self, app):
        self.app = app
        self.log = logging.getLogger(__name__)

    async def __call__(self, scope, receive, send):
        # not authorized yet
        scope["hxat_auth"] = "403"
        scope["hx_user_id"] = "anonymous"

        # parse path to get context_id, collection_id, target_source_id
        path = scope.get("path")
        room_name = path.split("/")[-2]  # assumes path ends with a '/'
        (context, collection, target) = room_name.split("--")
        try:
            tgt, _ = target.split("-")  # hxighliter appends a canvas-id
        except ValueError:
            tgt = target

        # parse query string for session-id and resource-link-id
        query_string = scope.get("query_string", "")
        parsed_query = parse_qs(query_string)

        if not parsed_query:
            scope["hxat_auth"] = "403: missing querystring"
            self.log.debug("NOTIFY {}".format(scope["hxat_auth"]))
            return await self.app(scope, receive, send)

        session_id = parsed_query.get(b"utm_source", [b""])[0].decode()
        resource_link_id = parsed_query.get(b"resource_link_id", [b""])[0].decode()

        self.log.debug("NOTIFY sid({}) rid({})".format(session_id, resource_link_id))

        if not session_id or not resource_link_id:
            scope["hxat_auth"] = "403: missing session-id or resource-link-id"
            self.log.debug("NOTIFY {}".format(scope["hxat_auth"]))
            return await self.app(scope, receive, send)

        # close old db conn to prevent usage of timed out conn
        # see https://channels.readthedocs.io/en/latest/topics/authentication.html#custom-authentication
        close_old_connections()
        session_exists = await _async_session_exists(session_id)
        if not session_exists:
            scope["hxat_auth"] = "403: unknown session-id({})".format(session_id)
        else:
            # get lti params from session
            multi_launch = await _async_session_get_ltilaunch(session_id)
            lti_launch = multi_launch.get(resource_link_id, {})
            lti_params = lti_launch.get("launch_params", {})

            for key in lti_launch:
                self.log.debug("NOTIFY LTI_LAUNCH[{}]: {}".format(key, lti_launch[key]))

            # get used_id
            scope["hx_user_id"] = lti_launch.get("hx_user_id", "anonymous")

            # check the context-id matches the channel being connected
            pat = re.compile("[^a-zA-Z0-9-.]")
            clean_context_id = pat.sub("-", lti_launch.get("hx_context_id", ""))
            clean_collection_id = pat.sub("-", lti_launch.get("hx_collection_id", ""))
            clean_target_id = str(lti_launch.get("hx_object_id", ""))
            if clean_context_id == context:
                if clean_collection_id == collection:
                    if clean_target_id == tgt:
                        scope["hxat_auth"] = "authenticated"
                    else:
                        scope[
                            "hxat_auth"
                        ] = "403: unknown target-object-id({}|{})".format(
                            tgt, clean_target_id
                        )
                else:
                    scope["hxat_auth"] = "403: unknown collection-id({}|{})".format(
                        collection, clean_collection_id
                    )
            else:
                scope["hxat_auth"] = "403: unknown context-id({}|{})".format(
                    context, clean_context_id
                )

        self.log.debug("NOTIFY {}".format(scope["hxat_auth"]))
        self.log.debug("NOTIFY finished with middleware")
        return await self.app(scope, receive, send)


"""
09jun20 naomi:
empirically, found that, to be in the target_object page the ui client has to
have to go through a workflow that guarantees that the session object has:
    session['resource_link_id']
    session['hx_context_id']
    session['hx_collection_id']
    session['hx_object_id']
    session['hx_user_id']
so, using these to validate the ws connect request.

"""
