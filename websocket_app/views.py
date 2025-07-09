from django.shortcuts import render
from django.contrib.auth.models import User
from .models import Message
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from .mixins import *

def test_websocket_view(request):
    return render(request, 'test.html')

class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_name):
        try:
            messages = Message.objects.filter(room__name=room_name).order_by('-timestamp')
            serialized = MessageSerializer(messages, many=True)
            return custom200("Chat history fetched successfully", serialized.data)
        except Exception as e:
            return custom400("Failed to fetch chat history", {"error": str(e)})
    
class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            users = User.objects.all()
            serialized = UserSerializer(users, many=True)
            return custom200("User list fetched successfully", serialized.data)
        except Exception as e:
            return custom400("Failed to fetch users", {"error": str(e)})
    
class ChatRoomListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            rooms = ChatRoom.objects.all()
            serialized = ChatRoomSerializer(rooms, many=True)
            return custom200("Chat rooms fetched successfully", serialized.data)
        except Exception as e:
            return custom400("Failed to fetch chat rooms", {"error": str(e)})

    def post(self, request):
        serializer = ChatRoomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return custom201("Chat room created successfully", serializer.data)
        return custom400("Failed to create chat room", serializer.errors)
