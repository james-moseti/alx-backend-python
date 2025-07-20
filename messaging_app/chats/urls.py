from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import ConversationViewSet, MessageViewSet, ConversationBulkViewSet
from .auth_views import (
    RegisterView, LoginView, LogoutView, UserProfileView, 
    ChangePasswordView, user_search, current_user, UserListView,
    verify_token, check_email_availability
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'bulk', ConversationBulkViewSet, basename='bulk')

# URL patterns
urlpatterns = [
    # API routes
    path('api/v1/', include(router.urls)),
    
    # Authentication endpoints
    path('api/v1/auth/register/', RegisterView.as_view(), name='register'),
    path('api/v1/auth/login/', LoginView.as_view(), name='login'),
    path('api/v1/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/v1/auth/profile/', UserProfileView.as_view(), name='user-profile'),
    path('api/v1/auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('api/v1/auth/current-user/', current_user, name='current-user'),
    path('api/v1/auth/verify-token/', verify_token, name='verify-token'),
    path('api/v1/auth/check-email/', check_email_availability, name='check-email'),
    
    # User management endpoints
    path('api/v1/users/', UserListView.as_view(), name='user-list'),
    path('api/v1/users/search/', user_search, name='user-search'),
    
    # DRF built-in auth (optional - for browsable API)
    path('api/v1/auth/drf/', include('rest_framework.urls')),
    path('api/v1/auth/token/', obtain_auth_token, name='api-token-auth'),  # Alternative token endpoint
]