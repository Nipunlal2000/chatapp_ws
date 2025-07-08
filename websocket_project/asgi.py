# asgi.py
import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websocket_project.settings')
django.setup()  # This initializes Django

from channels.routing import ProtocolTypeRouter, URLRouter
import websocket_app.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(
        websocket_app.routing.websocket_urlpatterns
    ),
})