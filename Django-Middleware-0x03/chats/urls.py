from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from .views import ConversationViewSet, MessageViewSet, UserViewSet

# Main router - use DefaultRouter for the parent
router = DefaultRouter(trailing_slash=False)
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'users', UserViewSet, basename='user')

# Nested messages under conversations
convo_router = NestedDefaultRouter(router, r'conversations', lookup='conversation', trailing_slash=False)
convo_router.register(r'messages', MessageViewSet, basename='conversation-messages')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(convo_router.urls)),
]