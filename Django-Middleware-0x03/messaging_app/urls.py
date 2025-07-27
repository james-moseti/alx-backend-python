"""
URL configuration for messaging_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.documentation import include_docs_urls
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenRefreshView
from chats.auth import (
    CustomTokenObtainPairView,
    UserRegistrationView,
    logout_view,
    user_profile_view,
    update_profile_view
)

# Swagger/OpenAPI schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Messaging API",
        default_version='v1',
        description="A messaging application API with conversations and real-time messaging",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@messaging.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # REMOVE THIS LINE - it's causing circular import:
    # path('api/', include('messaging_app.urls')),
    
    # Authentication URLs (if using Django REST framework's built-in auth)
    path('api-auth/', include('rest_framework.urls')),
    
    # API Documentation
    path('docs/', include_docs_urls(title='Messaging API')),
    
    # Swagger/OpenAPI Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Authentication endpoints
    path('api/auth/', include([
        # JWT Token endpoints
        path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('logout/', logout_view, name='logout'),
        
        # User management endpoints
        path('register/', UserRegistrationView.as_view(), name='user_register'),
        path('profile/', user_profile_view, name='user_profile'),
        path('profile/update/', update_profile_view, name='update_profile'),
    ])),
    
    # Chats API endpoints
    path('api/chats/', include('chats.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers (optional) - commented out since views.py doesn't exist
# handler404 = 'messaging_app.views.custom_404'
# handler500 = 'messaging_app.views.custom_500'