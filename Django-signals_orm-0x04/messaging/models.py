from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class UnreadMessagesManager(models.Manager):
    """Custom manager to filter unread messages for a specific user"""
    
    def for_user(self, user):
        """Get all unread messages for a specific user"""
        return self.filter(receiver=user, read=False)
    
    def unread_count(self, user):
        """Get count of unread messages for a user"""
        return self.for_user(user).count()
    
    def optimized_for_user(self, user):
        """Get unread messages with optimized query using only()"""
        return self.for_user(user).select_related('sender').only(
            'message_id', 'content', 'timestamp', 'sender__first_name', 
            'sender__last_name', 'sender__email'
        )

class Message(models.Model):
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    read = models.BooleanField(default=False)

    # Managers
    objects = models.Manager()  # Default manager
    unread = UnreadMessagesManager()  # Custom manager for unread messages

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver}"
    
    def edited_by(self):
        """Method to display edit history - required by tests"""
        return self.history.all().order_by('-edited_at')
    
    def get_all_replies(self):
        """Recursively get all replies to this message"""
        replies = []
        direct_replies = self.replies.select_related('sender', 'receiver').prefetch_related('replies')
        for reply in direct_replies:
            replies.append(reply)
            replies.extend(reply.get_all_replies())
        return replies
    
    def mark_as_read(self):
        """Mark this message as read"""
        if not self.read:
            self.read = True
            self.save(update_fields=['read'])

class Notification(models.Model):
    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user} about message from {self.message.sender}"

class MessageHistory(models.Model):
    history_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='history')
    old_content = models.TextField()
    edited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-edited_at']

    def __str__(self):
        return f"History for message {self.message.message_id} at {self.edited_at}"