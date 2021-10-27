from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from notifications.serializers import NotifySerializer


def get_user_base_channel_name(user_pk) -> str:
    return f'user_{user_pk}'


def send(channel, event, data):
    async_to_sync(get_channel_layer().group_send)(
        channel,
        {
            'type': 'send.data',
            'event': event,
            'data': data
        })


def send_new_notification(notify):
    send(get_user_base_channel_name(notify.user_id), 'new_notification', NotifySerializer(notify).data)
