"""
Custom permissions for the messaging app.
Ensures users can only access their own messages and conversations.
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user


class IsMessageParticipant(permissions.BasePermission):
    """
    Custom permission to ensure users can only access messages 
    in conversations they participate in.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Check if user is a participant in the conversation
        that contains this message.
        """
        # For Message objects
        if hasattr(obj, 'conversation'):
            return obj.conversation.participants.filter(id=request.user.id).exists()
        
        # For objects that have a sender field (like Message)
        if hasattr(obj, 'sender'):
            return obj.sender == request.user or \
                   obj.conversation.participants.filter(id=request.user.id).exists()
        
        return False


class IsConversationParticipant(permissions.BasePermission):
    """
    Custom permission to ensure users can only access conversations
    they participate in.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Check if user is a participant in the conversation.
        """
        # For Conversation objects
        if hasattr(obj, 'participants'):
            return obj.participants.filter(id=request.user.id).exists()
        
        return False


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Check if user owns the object.
        """
        # For objects with owner field
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        # For objects with user field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # For objects with sender field
        if hasattr(obj, 'sender'):
            return obj.sender == request.user
        
        return False


class CanCreateMessage(permissions.BasePermission):
    """
    Custom permission to check if user can create a message
    in a specific conversation.
    """

    def has_permission(self, request, view):
        """
        Check if user can create a message in the specified conversation.
        """
        if not (request.user and request.user.is_authenticated):
            return False

        # For POST requests, check if user is participant in the conversation
        if request.method == 'POST':
            conversation_id = request.data.get('conversation')
            if conversation_id:
                from .models import Conversation  # Import here to avoid circular imports
                try:
                    conversation = Conversation.objects.get(id=conversation_id)
                    return conversation.participants.filter(id=request.user.id).exists()
                except Conversation.DoesNotExist:
                    return False
        
        return True


class CanViewConversation(permissions.BasePermission):
    """
    Custom permission for viewing conversations with additional checks.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Check if user can view the conversation.
        Users can view conversations they participate in.
        """
        return obj.participants.filter(id=request.user.id).exists()


class IsAdminOrOwner(permissions.BasePermission):
    """
    Custom permission to allow admin users or owners to access objects.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Allow access to admin users or owners.
        """
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check ownership based on different field names
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'sender'):
            return obj.sender == request.user
        elif hasattr(obj, 'participants'):
            return obj.participants.filter(id=request.user.id).exists()
        
        return False


def get_user_conversations(user):
    """
    Helper function to get all conversations for a user.
    """
    from .models import Conversation  # Import here to avoid circular imports
    return Conversation.objects.filter(participants=user)


def get_user_messages(user):
    """
    Helper function to get all messages accessible to a user.
    """
    from .models import Message  # Import here to avoid circular imports
    user_conversations = get_user_conversations(user)
    return Message.objects.filter(conversation__in=user_conversations)


def can_user_access_conversation(user, conversation):
    """
    Helper function to check if a user can access a conversation.
    """
    return conversation.participants.filter(id=user.id).exists()


def can_user_access_message(user, message):
    """
    Helper function to check if a user can access a message.
    """
    return can_user_access_conversation(user, message.conversation)