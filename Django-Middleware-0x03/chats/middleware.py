import logging
from datetime import datetime
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from django.utils import timezone

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