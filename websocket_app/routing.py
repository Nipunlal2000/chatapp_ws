from django.urls import re_path
from websocket_app.consumers import ChatConsumer  # safe if ChatConsumer doesn't have early DRF imports

websocket_urlpatterns = [
    re_path(r'ws/chat/$', ChatConsumer.as_asgi()),
]
