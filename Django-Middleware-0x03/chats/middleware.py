import logging
from datetime import datetime, timedelta
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from collections import defaultdict
import time

# Set up logger for request logging
logger = logging.getLogger('chats.middleware')

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware that logs each user's requests to a file, including timestamp, user, and request path.
    """
    
    def __init__(self, get_response=None):
        """Initialize the middleware."""
        super().__init__(get_response)
        self.get_response = get_response
    
    def __call__(self, request):
        """
        Process the request and log the information.
        This method is called for each request when using the new-style middleware.
        """
        # Log the request information
        self._log_request(request)
        
        # Continue processing the request
        response = self.get_response(request)
        return response
    
    def process_request(self, request):
        """
        Process the request (for old-style middleware compatibility).
        This method is called for each request before the view is called.
        """
        self._log_request(request)
        return None
    
    def _log_request(self, request):
        """
        Log the request information in the specified format.
        Format: "[datetime.now()] - User: [user] - Path: [request.path]"
        """
        # Get current timestamp
        timestamp = datetime.now()
        
        # Get user information
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = str(request.user)
        else:
            user = 'Anonymous'
        
        # Get request path
        path = request.path
        
        # Format the log message
        log_message = f"[{timestamp}] - User: {user} - Path: {path}"
        
        # Log the message
        logger.info(log_message)


class RestrictAccessByTimeMiddleware(MiddlewareMixin):
    """
    Middleware that restricts access to the messaging app during certain hours.
    Access is only allowed between 9AM (09:00) and 6PM (18:00).
    """
    
    def __init__(self, get_response=None):
        """Initialize the middleware."""
        super().__init__(get_response)
        self.get_response = get_response
        # Define allowed hours (9AM to 6PM)
        self.start_hour = 9  # 9AM
        self.end_hour = 18   # 6PM
    
    def __call__(self, request):
        """
        Process the request and check if access is allowed during current time.
        Returns 403 Forbidden if accessed outside allowed hours.
        """
        # Check if current time is within allowed hours
        if not self._is_access_allowed():
            return HttpResponse(
                '<h1>403 Forbidden</h1>'
                '<p>Access to the messaging application is restricted.</p>'
                '<p>Please access the application between 9:00 AM and 6:00 PM.</p>',
                status=403,
                content_type='text/html'
            )
        
        # Continue processing the request if time is allowed
        response = self.get_response(request)
        return response
    
    def _is_access_allowed(self):
        """
        Check if the current server time is within allowed hours.
        Returns True if current time is between 9AM and 6PM, False otherwise.
        """
        # Get current server time
        current_time = timezone.now()
        current_hour = current_time.hour
        
        # Check if current hour is within allowed range (9AM to 6PM)
        return self.start_hour <= current_hour < self.end_hour


class OffensiveLanguageMiddleware(MiddlewareMixin):
    """
    Middleware that limits the number of chat messages a user can send within a certain time window,
    based on their IP address. Implements rate limiting for POST requests (messages).
    """
    
    def __init__(self, get_response=None):
        """Initialize the middleware with rate limiting configuration."""
        super().__init__(get_response)
        self.get_response = get_response
        
        # Rate limiting configuration
        self.max_messages = 5  # Maximum messages per time window
        self.time_window = 60  # Time window in seconds (1 minute)
        
        # Dictionary to track message counts per IP
        # Structure: {ip_address: [(timestamp1, timestamp2, ...], ...}
        self.ip_message_counts = defaultdict(list)
    
    def __call__(self, request):
        """
        Process the request and implement rate limiting for POST requests.
        Returns 429 Too Many Requests if limit is exceeded.
        """
        # Only apply rate limiting to POST requests (chat messages)
        if request.method == 'POST':
            client_ip = self._get_client_ip(request)
            
            # Check if IP has exceeded rate limit
            if self._is_rate_limited(client_ip):
                return JsonResponse(
                    {
                        'error': 'Rate limit exceeded',
                        'message': f'You can only send {self.max_messages} messages per minute. Please wait before sending another message.',
                        'retry_after': 60
                    },
                    status=429
                )
            
            # Record this POST request for the IP
            self._record_message(client_ip)
        
        # Continue processing the request
        response = self.get_response(request)
        return response
    
    def _get_client_ip(self, request):
        """
        Get the client's IP address from the request.
        Handles cases where the request might be behind a proxy.
        """
        # Check for IP in various headers (for proxy scenarios)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP if there are multiple
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            # Get IP from REMOTE_ADDR
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
        return ip
    
    def _is_rate_limited(self, ip_address):
        """
        Check if the IP address has exceeded the rate limit.
        Returns True if rate limited, False otherwise.
        """
        current_time = time.time()
        
        # Get message timestamps for this IP
        message_times = self.ip_message_counts[ip_address]
        
        # Remove old timestamps outside the time window
        cutoff_time = current_time - self.time_window
        self.ip_message_counts[ip_address] = [
            timestamp for timestamp in message_times 
            if timestamp > cutoff_time
        ]
        
        # Check if current count exceeds limit
        current_count = len(self.ip_message_counts[ip_address])
        return current_count >= self.max_messages
    
    def _record_message(self, ip_address):
        """
        Record a new message timestamp for the given IP address.
        """
        current_time = time.time()
        
        # Add current timestamp to the IP's message list
        self.ip_message_counts[ip_address].append(current_time)
        
        # Clean up old timestamps to prevent memory buildup
        cutoff_time = current_time - self.time_window
        self.ip_message_counts[ip_address] = [
            timestamp for timestamp in self.ip_message_counts[ip_address]
            if timestamp > cutoff_time
        ]


class RolePermissionMiddleware(MiddlewareMixin):
    """
    Middleware that checks the user's role (admin, moderator) before allowing access to specific actions.
    Returns 403 Forbidden if user doesn't have required permissions.
    """
    
    def __init__(self, get_response=None):
        """Initialize the middleware with role-based access control."""
        super().__init__(get_response)
        self.get_response = get_response
        
        # Define protected paths that require admin/moderator access
        self.protected_paths = [
            '/admin/',
            '/api/chats/users/',  # User management endpoints
            '/api/chats/conversations/',  # Conversation management (for moderators)
        ]
        
        # Define paths that require admin-only access
        self.admin_only_paths = [
            '/admin/',
        ]
    
    def __call__(self, request):
        """
        Process the request and check user role permissions.
        Returns 403 Forbidden if user doesn't have required role.
        """
        # Check if the request path requires role-based access control
        if self._requires_permission_check(request):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return JsonResponse(
                    {
                        'error': 'Authentication required',
                        'message': 'You must be logged in to access this resource.'
                    },
                    status=401
                )
            
            # Check if user has required role permissions
            if not self._has_required_role(request):
                return JsonResponse(
                    {
                        'error': 'Insufficient permissions',
                        'message': 'You do not have the required role (admin or moderator) to access this resource.',
                        'required_role': 'admin or moderator'
                    },
                    status=403
                )
        
        # Continue processing the request
        response = self.get_response(request)
        return response
    
    def _requires_permission_check(self, request):
        """
        Check if the current request path requires role-based permission checking.
        Returns True if permission check is needed, False otherwise.
        """
        request_path = request.path
        
        # Check if any protected path matches the current request path
        for protected_path in self.protected_paths:
            if request_path.startswith(protected_path):
                return True
        
        return False
    
    def _has_required_role(self, request):
        """
        Check if the user has the required role (admin or moderator) for the requested resource.
        Returns True if user has required permissions, False otherwise.
        """
        user = request.user
        request_path = request.path
        
        # Check for admin-only paths
        if any(request_path.startswith(path) for path in self.admin_only_paths):
            return self._is_admin(user)
        
        # For other protected paths, check if user is admin or moderator
        return self._is_admin(user) or self._is_moderator(user)
    
    def _is_admin(self, user):
        """
        Check if the user has admin role.
        Returns True if user is admin, False otherwise.
        """
        # Check Django's built-in admin permissions
        if user.is_superuser or user.is_staff:
            return True
        
        # Check for custom admin role (if you have a custom role field)
        if hasattr(user, 'role') and user.role == 'admin':
            return True
        
        # Check for admin group membership
        if user.groups.filter(name='admin').exists():
            return True
        
        return False
    
    def _is_moderator(self, user):
        """
        Check if the user has moderator role.
        Returns True if user is moderator, False otherwise.
        """
        # Check for custom moderator role (if you have a custom role field)
        if hasattr(user, 'role') and user.role == 'moderator':
            return True
        
        # Check for moderator group membership
        if user.groups.filter(name='moderator').exists():
            return True
        
        # Check for specific permissions that moderators might have
        if user.has_perm('chats.moderate_conversations'):
            return True
        
        return False