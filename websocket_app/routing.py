from django.urls import re_path
from . consumers import * # safe if ChatConsumer doesn't have early DRF imports

websocket_urlpatterns = [
    # re_path(r'ws/chat/$', ChatConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<room_name>\w+)/$', ChatConsumer.as_asgi()),
]
