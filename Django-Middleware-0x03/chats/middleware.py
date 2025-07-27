import logging
from datetime import datetime
from django.utils.deprecation import MiddlewareMixin

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