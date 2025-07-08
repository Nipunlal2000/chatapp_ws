# 1. Project Structure Overview

```
websocket_project/
├── websocket_project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py          ✅
│   └── wsgi.py
├── websocket_app/
│   ├── consumers.py     ✅
│   ├── routing.py       ✅
│   ├── views.py         ✅ (for test.html)
│   ├── templates/
│   │   └── test.html     ✅
│   └── urls.py          ✅
└── manage.py
```

# 2. Installed Libraries

```bash
pip install django djangorestframework channels daphne
```

## 3. Settings Updated

settings.py:
- channels and rest_framework added to INSTALLED_APPS ✅

ASGI_APPLICATION = 'websocket_project.asgi.application' ✅

## 4. ASGI Setup

websocket_project/asgi.py

```python 

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import websocket_app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websocket_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_app.routing.websocket_urlpatterns
        )
    ),
})
```

✅ AuthMiddlewareStack is ready for later when you add login/auth.

# 5. WebSocket Routing Setup

websocket_app/routing.py:

```python

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/$', consumers.ChatConsumer.as_asgi()),
]
```
✅ Good. This connects the /ws/chat/ WebSocket route.

# 6. Consumer Working

websocket_app/consumers.py:

```python

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({"message": "WebSocket connected"}))

    async def disconnect(self, close_code):
        print("WebSocket disconnected")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        await self.send(text_data=json.dumps({"message": f"You said: {message}"}))

```
✅ Looks good. This handles connection, message, and disconnection.

# 7. Testing Interface (HTML UI)

- test.html exists inside websocket_app/templates/test.html ✅

- You wrote a Django view and URL pattern to serve it at /test-ws/ ✅

```js
const socket = new WebSocket("ws://127.0.0.1:8000/ws/chat/");
```

# 8. Server Running with Daphne

```bash 

daphne websocket_project.asgi:application

```

## ✅ Summary
- Django Channels brings ASGI support.

- Daphne runs as an ASGI server.

- We wrote a ChatConsumer to handle connect, receive, and disconnect.

- URLs for WebSocket go in routing.py, not urls.py.





# 🔧 Setup 2: WebSocket Authentication using JWT

## ✅ Step 1: Install JWT Support

```bash 
pip install djangorestframework-simplejwt
```

## ✅ Step 2: Update settings.py for JWT

```python 

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}
```

urls.py

```python

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
```

## ✅ Step 3: Modify WebSocket Client to send token

test.html

```js
const token = "<PUT_YOUR_JWT_HERE>";  // later insert dynamically
const socket = new WebSocket(`ws://127.0.0.1:8000/ws/chat/?token=${token}`);

```

## ✅ Step 4: Modify the ChatConsumer to validate token

consumers.py, do this:

```python

from channels.generic.websocket import AsyncWebsocketConsumer
from urllib.parse import parse_qs
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser, User
from django.db import close_old_connections
from channels.db import database_sync_to_async
from rest_framework_simplejwt.authentication import JWTAuthentication

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = await self.get_user()
        if self.user is None or self.user.is_anonymous:
            await self.close()
        else:
            await self.accept()
            await self.send(text_data="Authenticated WebSocket connected")

    @database_sync_to_async
    def get_user(self):
        query_string = self.scope['query_string'].decode()
        token_param = parse_qs(query_string).get('token')
        if token_param:
            token = token_param[0]
            try:
                validated_token = JWTAuthentication().get_validated_token(token)
                user = JWTAuthentication().get_user(validated_token)
                close_old_connections()
                return user
            except (InvalidToken, TokenError) as e:
                return AnonymousUser()
        return AnonymousUser()

    async def receive(self, text_data):
        await self.send(text_data=f"Hello {self.user.username}, you sent: {text_data}")

    async def disconnect(self, close_code):
        print(f"Disconnected user: {self.user}")
```

# ✅ Setup 3: Real-Time Chat with Groups in Django Channels

### 🧠 Concepts:
- A chat room is a channel layer group

- Each connected user is added to the group during connect()

- Messages are sent using self.channel_layer.group_send()

## ✏️ Step 1: Install Channel Layers (using in-memory layer for now)

settings.py,

```python

# settings.py

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
```
✅ Later we can switch to Redis for production.

## ✏️ Step 2: Update ChatConsumer for Group Messaging

```python

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = await self.get_user()
        self.room_name = "global_chat"
        self.room_group_name = f"chat_{self.room_name}"

        if self.user is None or self.user.is_anonymous:
            await self.close(code=1008)
        else:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            await self.send(text_data=json.dumps({
                "message": f"👋 {self.user.username} joined the chat"
            }))

    @database_sync_to_async
    def get_user(self):
        from rest_framework_simplejwt.authentication import JWTAuthentication
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

        query_string = self.scope['query_string'].decode()
        token_param = parse_qs(query_string).get('token')
        if token_param:
            token = token_param[0]
            try:
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token)
                user = jwt_auth.get_user(validated_token)
                close_old_connections()
                return user
            except (InvalidToken, TokenError):
                return AnonymousUser()
        return AnonymousUser()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "")

        # Broadcast to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": f"{self.user.username}: {message}"
            }
        )

    async def chat_message(self, event):
        # Receive message from group
        await self.send(text_data=json.dumps({
            "message": event["message"]
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
```

