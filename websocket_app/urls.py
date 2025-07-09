from django.urls import path
from .views import *
from rest_framework_simplejwt.views import (TokenObtainPairView,TokenRefreshView,)

urlpatterns = [
    path('test-ws/', test_websocket_view, name='test-websocket'),

    path('api/chat/history/<str:room_name>/', ChatHistoryView.as_view(), name='chat-history'),
    path('api/chat/users/', UserListView.as_view(), name='user-list'),
    path('api/chat/rooms/', ChatRoomListCreateView.as_view()),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
