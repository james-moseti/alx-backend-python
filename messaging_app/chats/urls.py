from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ConversationViewSet,
    MessageViewSet,
    ConversationBulkViewSet,
    UserViewSet
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'bulk', ConversationBulkViewSet, basename='conversation-bulk')
router.register(r'users', UserViewSet, basename='user')

app_name = 'messaging'

urlpatterns = [
    # Include all router URLs
    path('', include(router.urls)),
]