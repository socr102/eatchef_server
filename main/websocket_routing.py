import os

import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

from . import consumers

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings.prod')

django.setup()

paths = [path('ws/base', consumers.BaseConsumer)]

application = ProtocolTypeRouter(
    {
        'websocket':
            URLRouter(paths),
    }
)
