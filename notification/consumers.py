
from importlib import import_module
import json
import logging
import re
from urllib.parse import parse_qs

from asgiref.sync import async_to_sync
from django.conf import settings
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        for key in self.scope.keys():
            logging.getLogger(__name__).debug(
                "SCOPE[{}] = {}".format(key, self.scope[key])
            )

        self.group_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.wsid = "{}--{}".format(
            self.group_name, self.scope.get("hx_user_id", "unknown")
        )

        # check that this connection is authorized
        (self.context, self.collection, self.target) = self.scope["hx_auth"]
        logging.getLogger(__name__).debug(
            "{}|channel_name({}), context({}), collection({}), object({}), user({})".format(
                self.wsid,
                self.channel_name,
                self.context,
                self.collection,
                self.target,
                self.scope["hx_user_id"],
            )
        )
        if not self.context or not self.collection or not self.target:
            logging.getLogger(__name__).warning(
                "{}|ws auth FAILED, dropping connection".format(self.wsid)
            )
            raise DenyConnection()  # return status_code=403

        # join room group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        logging.getLogger(__name__).debug(
            "{}|added group to channel({})".format(self.wsid, self.channel_name)
        )
        await self.accept()
        logging.getLogger(__name__).debug(
            "{}|CONNECTION ACCEPTED".format(self.wsid)
        )

    async def disconnect(self, close_code):
        # leave room group
        logging.getLogger(__name__).debug(
            "{}|DISCONNECT[{}]".format(self.wsid, close_code)
        )
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # receive message from websocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        logging.getLogger(__name__).debug(
            "{}|WSRECEIVE[{}]".format(self.wsid, text_data_json.keys())
        )

        # send message to room group
        # await self.channel_layer.group_send(
        #    self.group_name,
        #    {
        #        'type': 'chat_message',
        #        'message': message
        #    }
        # )

    # receive message from room group
    async def annotation_notification(self, event):
        message = event["message"]
        action = event["action"]

        # send message to websocket
        await self.send(
            text_data=json.dumps({"type": action, "message": "{}".format(message),})
        )


class NotificationSyncConsumer(WebsocketConsumer):


    def parse_querystring(self, scope):
        # parse query string for session-id and resource-link-id
        parsed_query = parse_qs(scope.get("query_string", ""))
        if parsed_query:
            session_id = parsed_query.get(b"utm_source", [b""])[0].decode()
            resource_link_id = parsed_query.get(b"resource_link_id", [b""])[0].decode()
            logging.getLogger(__name__).info(
                "CONSUMER: rid({}) sid({})".format(resource_link_id, session_id)
            )
            return (session_id, resource_link_id)
        else:
            logging.getLogger(__name__).error("CONSUMER: missing querystring")
            return (None, None)


    def lti_launch_valid(self, lti_launch, context, collection, target):
        # validate room_name from path with session info
        #
        # when authenticated returns used_id, and non-zero context, collection, target

        # check the context-id matches the channel being connected
        pat = re.compile("[^a-zA-Z0-9-.]")
        try:
            clean_context_id = pat.sub("-", lti_launch["hx_context_id"])
            clean_collection_id = pat.sub("-", lti_launch["hx_collection_id"])
            clean_target_id = str(lti_launch["hx_object_id"])
        except ValueError as e:
            logging.getLogger(__name__).error(
                "CONSUMER: missing from lti_launch: {}".format(e)
            )
        else:
            if clean_context_id == context:
                if clean_collection_id == collection:
                    if clean_target_id == target:
                        # AUTHENTICATED!
                        logging.getLogger(__name__).info("CONSUMER AUTHENTICATED AUTHENTICATED AUTHENTICATED AUTHENTICATED")
                        return True
                    else:
                        logging.getLogger(__name__).error(
                            "CONSUMER: unknown target-object-id({}|{})".format(
                                target, clean_target_id
                            )
                        )
                else:
                    logging.getLogger(__name__).error(
                        "CONSUMER: unknown collection-id({}|{})".format(
                            collection, clean_collection_id
                        )
                    )
            else:
                logging.getLogger(__name__).error(
                    "CONSUMER: unknown context-id({}|{})".format(
                        context, clean_context_id
                    )
                )
        # if we've got here is because NOT authenticated
        return False


    def connect(self):
        for key in self.scope.keys():
            logging.getLogger(__name__).debug(
                "CONSUMER SCOPE[{}] = {}".format(key, self.scope[key])
            )

        context_id = self.scope["url_route"]["kwargs"]["contextid"]
        collection_id = self.scope["url_route"]["kwargs"]["collectionid"]
        targetid = self.scope["url_route"]["kwargs"]["targetid"]
        try:
            target_id, _ = targetid.split("-")  # hxighliter appends a canvas-id
        except ValueError:
            target_id = targetid

        # get resource_link_id from querystring
        (sessionid_qs, resource_link_id) = self.parse_querystring(self.scope)

        # check session_id from cookie
        sessionid_cookie = self.scope.get("cookies", {}).get(settings.SESSION_COOKIE_NAME, None)
        session_id = sessionid_cookie if sessionid_cookie else sessionid_qs
        if not session_id:
            logging.getLogger(__name__).error("CONSUMER 403: missing session_id")
            # disconnect
            raise DenyConnection()

        # get lti launch
        SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
        exists = SessionStore(session_id).exists(session_id)
        multi_launch = None
        if exists:
            multi_launch = SessionStore(session_id).get("LTI_LAUNCH", {})
            if not multi_launch:
                logging.getLogger(__name__).warning("CONSUMER 403: lti_launch empty")
                # disconnect
                raise DenyConnection()
        else:
            logging.getLogger(__name__).error(
                "CONSUMER 403: session({}) not found".format(session_id)
            )
            # disconnect
            raise DenyConnection()

        # need multi_launch from session and resource_link_id to continue
        if multi_launch and resource_link_id:
            lti_launch = multi_launch.get(resource_link_id, {})
            if not lti_launch:
                logging.getLogger(__name__).error(
                    "CONSUMER 403: resource_link_id({}) not found".format(resource_link_id)
                )
                # disconnect
                raise DenyConnection()
            else:
                for key in lti_launch:
                    logging.getLogger(__name__).debug(
                        "CONSUMER LTI_LAUNCH[{}]: {}".format(key, lti_launch[key])
                    )
                self.scope["hx_user_id"] = lti_launch.get("hx_user_id", "anonymous")

                if self.lti_launch_valid(lti_launch, context_id, collection_id, target_id):
                    self.group_name = "{}--{}--{}".format(
                        context_id, collection_id, target_id
                    )
                    self.wsid = "{}--{}".format(self.group_name, self.scope["hx_user_id"])

                    logging.getLogger(__name__).debug(
                        "{}|channel_name({}), context({}), collection({}), object({}), user({})".format(
                            self.wsid,
                            self.channel_name,
                            context_id,
                            collection_id,
                            target_id,
                            self.scope["hx_user_id"],
                        )
                    )

                    # join room group
                    async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
                    logging.getLogger(__name__).info(
                        "{}|added group to channel({})".format(self.wsid, self.channel_name)
                    )

                    self.accept()

                    logging.getLogger(__name__).info(
                        "{}|CONNECTION ACCEPTED".format(self.wsid)
                    )
                else:
                    logging.getLogger(__name__).error("CONSUMER 403: LTI_LAUNCH not valid")
                    # disconnect
                    raise DenyConnection()

        else:  # no lti_launch or resource_link_id
            if not resource_link_id:
                logging.getLogger(__name__).error(
                    "CONSUMER 403: missing resource_link_id in querystring"
                )
            elif not multi_launch:
                logging.getLogger(__name__).error(
                    "CONSUMER 403: multi_launch not found in session"
                )
            # disconnect, return 403
            raise DenyConnection()


    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        logging.getLogger(__name__).debug(
            "{}|WSRECEIVE[{}]".format(self.wsid, text_data_json.keys())
        )

        # send message to room group
        # async_to_sync(self.channel_layer.group_send)(
        #    self.group_name,
        #    {
        #        'type': 'chat_message',
        #        'message': message
        #    }
        # )


    def disconnect(self, close_code):
        # leave room group
        logging.getLogger(__name__).debug(
            "{}|DISCONNECT[{}]".format(self.wsid, close_code)
        )
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

    def annotation_notification(self, event):
        """ receives msg from room group and respond to ws to display badge."""
        message = event["message"]
        action = event["action"]

        # send message to websocket
        self.send(
            text_data=json.dumps({"type": action, "message": "{}".format(message)})
        )

