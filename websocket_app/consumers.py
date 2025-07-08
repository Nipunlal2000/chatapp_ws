# # import json
# # from channels.generic.websocket import AsyncWebsocketConsumer

# # class ChatConsumer(AsyncWebsocketConsumer):
# #     async def connect(self):
# #         await self.accept()
# #         await self.send(text_data=json.dumps({"message": "WebSocket connected"}))

# #     async def disconnect(self, close_code):
# #         print("WebSocket disconnected")

# #     async def receive(self, text_data):
# #         data = json.loads(text_data)
# #         message = data['message']
# #         await self.send(text_data=json.dumps({"message": f"You said: {message}"}))

# from channels.generic.websocket import AsyncWebsocketConsumer
# from urllib.parse import parse_qs
# from rest_framework_simplejwt.tokens import UntypedToken
# from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
# from django.contrib.auth.models import AnonymousUser, User
# from django.db import close_old_connections
# from channels.db import database_sync_to_async
# from rest_framework_simplejwt.authentication import JWTAuthentication

# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.user = await self.get_user()
#         if self.user is None or self.user.is_anonymous:
#             await self.close()  # Reject connection if unauthenticated
#         else:
#             await self.accept()  # Accept only if valid token

#     @database_sync_to_async
#     def get_user(self):
#         query_string = self.scope['query_string'].decode()
#         token_param = parse_qs(query_string).get('token')
#         if token_param:
#             token = token_param[0]
#             try:
#                 validated_token = JWTAuthentication().get_validated_token(token)
#                 user = JWTAuthentication().get_user(validated_token)
#                 close_old_connections()
#                 return user
#             except (InvalidToken, TokenError) as e:
#                 return AnonymousUser()
#         return AnonymousUser()

#     async def receive(self, text_data):
#         await self.send(text_data=f"Hello {self.user.username}, you sent: {text_data}")

#     async def disconnect(self, close_code):
#         print(f"Disconnected user: {self.user}")

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

    # async def receive(self, text_data):
    #     data = json.loads(text_data)
    #     message = data.get("message", "")

    #     # Broadcast to group
    #     await self.channel_layer.group_send(
    #         self.room_group_name,
    #         {
    #             "type": "chat_message",
    #             "message": f"{self.user.username}: {message}"
    #         }
    #     )

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get("type", "message")

        if msg_type == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_typing",
                    "username": self.user.username,
                }
            )
        elif msg_type == "stop_typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_stopped_typing",
                    "username": self.user.username,
                }
            )
        else:
            message = data.get("message", "")
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

    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            "typing": True,
            "username": event["username"]
        }))

    async def user_stopped_typing(self, event):
        await self.send(text_data=json.dumps({
            "typing": False,
            "username": event["username"]
        }))
