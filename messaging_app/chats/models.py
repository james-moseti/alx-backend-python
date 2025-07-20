from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
import uuid


class User(AbstractUser):
    """
    Extended User model that extends Django's AbstractUser
    with additional fields for the chat system
    """
    ROLE_CHOICES = [
        ('guest', 'Guest'),
        ('host', 'Host'),
        ('admin', 'Admin'),
    ]
    
    # Override the default id field to use UUID
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        db_index=True
    )
    
    # Django's AbstractUser already provides first_name, last_name, email
    # We just need to make email unique and required
    email = models.EmailField(unique=True, null=False, blank=False)
    
    # Additional fields not in AbstractUser
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='guest',
        null=False,
        blank=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Make email the username field for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']
    
    class Meta:
        db_table = 'auth_user'  # Keep Django's default user table name
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Conversation(models.Model):
    """
    Model to track conversations between users
    """
    conversation_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True
    )
    
    # Many-to-many relationship with User for participants
    participants = models.ManyToManyField(
        User,
        related_name='conversations',
        blank=False
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Track last activity
    
    class Meta:
        db_table = 'conversation'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
        ]
        ordering = ['-updated_at']
    
    def __str__(self):
        participant_names = ", ".join([
            f"{user.first_name} {user.last_name}" 
            for user in self.participants.all()[:3]
        ])
        participant_count = self.participants.count()
        if participant_count > 3:
            participant_names += f" and {participant_count - 3} others"
        return f"Conversation: {participant_names}"
    
    def get_last_message(self):
        """Get the most recent message in this conversation"""
        return self.messages.order_by('-sent_at').first()
    
    def add_participant(self, user):
        """Add a user to the conversation"""
        self.participants.add(user)
    
    def remove_participant(self, user):
        """Remove a user from the conversation"""
        self.participants.remove(user)


class Message(models.Model):
    """
    Model for individual messages within conversations
    """
    message_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True
    )
    
    # Foreign key to User (sender)
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        null=False,
        blank=False
    )
    
    # Foreign key to Conversation
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        null=False,
        blank=False
    )
    
    message_body = models.TextField(null=False, blank=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    # Additional fields for enhanced functionality
    is_read = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'message'
        indexes = [
            models.Index(fields=['sender']),
            models.Index(fields=['conversation']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['is_read']),
        ]
        ordering = ['sent_at']
    
    def __str__(self):
        preview = self.message_body[:50] + "..." if len(self.message_body) > 50 else self.message_body
        return f"{self.sender.first_name}: {preview}"
    
    def mark_as_read(self):
        """Mark this message as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
    
    def save(self, *args, **kwargs):
        """Override save to update conversation's updated_at timestamp"""
        super().save(*args, **kwargs)
        # Update the conversation's updated_at timestamp
        if self.conversation:
            self.conversation.updated_at = self.sent_at
            self.conversation.save(update_fields=['updated_at'])


# Additional model for tracking read status per user (optional enhancement)
class MessageReadStatus(models.Model):
    """
    Track which users have read which messages
    This allows for more granular read status tracking in group conversations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_statuses'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='message_read_statuses'
    )
    
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'message_read_status'
        unique_together = ['message', 'user']  # Ensure one read status per user per message
        indexes = [
            models.Index(fields=['message']),
            models.Index(fields=['user']),
            models.Index(fields=['read_at']),
        ]
    
    def __str__(self):
        return f"{self.user.first_name} read message from {self.message.sender.first_name}"