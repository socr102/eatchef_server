import json

from channels.generic.websocket import AsyncWebsocketConsumer


class BaseConsumer(AsyncWebsocketConsumer):
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        if text_data_json['event'] == 'subscribe':
            await self.channel_layer.group_add(
                text_data_json['data'],
                self.channel_name
            )

        if text_data_json['event'] == 'unsubscribe':
            await self.channel_layer.group_discard(
                text_data_json['data'],
                self.channel_name
            )

    async def send_data(self, payload):
        await self.send(text_data=json.dumps({
            'event': payload['event'],
            'data': payload['data']
        }))
