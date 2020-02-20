
import json
import logging

from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        for key in self.scope.keys():
            logging.getLogger(__name__).debug('--------------- scope[{}] = {}'.format(key,
                self.scope[key]))

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = '{}'.format(self.room_name)

        logging.getLogger(__name__).debug('--------------- room_name({}) room_group_name({})'.format(self.room_name, self.room_group_name))
        logging.getLogger(__name__).debug('--------------- channel_layer({})'.format(self.channel_layer))

        auth = self.scope.get('hxat_auth', '403')
        if auth != 'authenticated':
            logging.getLogger(__name__).debug('--------------- ws auth FAILED, dropping connection')
            raise DenyConnection()  # return status_code=403
        else:
            # join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            logging.getLogger(__name__).debug('--------------- added group to channel layer')
            await self.accept()
            logging.getLogger(__name__).debug('--------------- connection accepted')


    async def disconnect(self, close_code):
        # leave room group
        logging.getLogger(__name__).debug('-------------- DISCONNECT[{}]'.format(close_code))
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # receive message from websocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # receive message from room group
    async def annotation_notification(self, event):
        message = event['message']
        action = event['action']

        # send message to websocket
        await self.send(text_data=json.dumps({
            'type': action,
            'message': '{}'.format(message),
        }))

