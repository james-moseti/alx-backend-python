from django.urls import path, include
from rest_framework import routers
from .views import (
    ConversationViewSet,
    MessageViewSet,
    ConversationBulkViewSet,
    UserViewSet
)

router = routers.DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'bulk', ConversationBulkViewSet, basename='conversation-bulk')
router.register(r'users', UserViewSet, basename='user')

app_name = 'messaging'

urlpatterns = [
    path('', include(router.urls)),
]
