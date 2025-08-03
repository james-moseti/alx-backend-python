# messaging/managers.py
from django.db import models

class UnreadMessagesManager(models.Manager):
    """Custom manager to filter unread messages for a specific user"""
    
    def for_user(self, user):
        """Get all unread messages for a specific user"""
        return self.filter(receiver=user, read=False)
    
    def unread_count(self, user):
        """Get count of unread messages for a user"""
        return self.for_user(user).count()
    
    def optimized_for_user(self, user):
        """Get unread messages with optimized query using only() and select_related()"""
        return self.for_user(user).select_related('sender').only(
            'message_id', 'content', 'timestamp', 'read',
            'sender__first_name', 'sender__last_name', 'sender__email'
        )