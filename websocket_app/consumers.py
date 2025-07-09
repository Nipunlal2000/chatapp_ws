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
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "system_message",
                    "message": f"👋 {self.user.username} joined the chat"
                }
            )

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

        # Handle typing indicator
        if "typing" in data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "typing_user": self.user.username if data["typing"] else None,
                    "sender": self.user.username
                }
            )
            return

        # Handle normal message
        message = data.get("message", "")
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender": self.user.username
            }
        )

    async def chat_message(self, event):
        # Only send to other clients (not the sender)
        if self.channel_name != event.get("sender_channel", None):
            await self.send(text_data=json.dumps({
                "message": event["message"],
                "sender": event["sender"],
                "type": "chat"
            }))

    async def typing_indicator(self, event):
        # Only send to other clients
        if self.user.username != event["sender"]:
            await self.send(text_data=json.dumps({
                "typing_user": event["typing_user"],
                "type": "typing"
            }))

    async def system_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "type": "system"
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "system_message",
                    "message": f"🚪 {self.user.username} left the chat"
                }
            )
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )