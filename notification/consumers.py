import json
import logging

from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer


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
        """
        if auth != "authenticated":
            logging.getLogger(__name__).debug(
                "{}|ws auth FAILED: {}, dropping connection".format(self.wsid, auth)
            )
            raise DenyConnection()  # return status_code=403

        (self.context, self.collection, self.target) = self.group_name.split("--")
        """

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
