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

        # Write permissions (PUT, PATCH, DELETE) are only allowed to the owner of the object.
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return obj.owner == request.user
        
        # For POST and other methods, allow if user is owner
        return obj.owner == request.user


class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission to ensure only participants in a conversation 
    can send, view, update and delete messages.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Check if user is a participant in the conversation.
        Works for both Message and Conversation objects.
        Allows PUT, PATCH, DELETE for participants.
        """
        # For Message objects - check if user is participant in the conversation
        if hasattr(obj, 'conversation'):
            is_participant = obj.conversation.participants.filter(id=request.user.id).exists()
            
            # Allow all operations (including PUT, PATCH, DELETE) for participants
            if request.method in permissions.SAFE_METHODS:
                return is_participant
            elif request.method in ['PUT', 'PATCH', 'DELETE', 'POST']:
                return is_participant
            
            return is_participant
        
        # For Conversation objects - check if user is participant
        if hasattr(obj, 'participants'):
            is_participant = obj.participants.filter(id=request.user.id).exists()
            
            # Allow all operations for participants
            if request.method in permissions.SAFE_METHODS:
                return is_participant
            elif request.method in ['PUT', 'PATCH', 'DELETE', 'POST']:
                return is_participant
            
            return is_participant
        
        return False


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
        Handles PUT, PATCH, DELETE operations.
        """
        # For Message objects
        if hasattr(obj, 'conversation'):
            is_participant = obj.conversation.participants.filter(id=request.user.id).exists()
            
            # Allow read operations for participants
            if request.method in permissions.SAFE_METHODS:
                return is_participant
            
            # Allow write operations (PUT, PATCH, DELETE) for message sender or participants
            elif request.method in ['PUT', 'PATCH', 'DELETE']:
                is_sender = hasattr(obj, 'sender') and obj.sender == request.user
                return is_sender or is_participant
            
            return is_participant
        
        # For objects that have a sender field (like Message)
        if hasattr(obj, 'sender'):
            is_sender = obj.sender == request.user
            is_participant = obj.conversation.participants.filter(id=request.user.id).exists()
            
            # Allow read for participants
            if request.method in permissions.SAFE_METHODS:
                return is_participant
            
            # Allow write operations for sender or participants
            elif request.method in ['PUT', 'PATCH', 'DELETE']:
                return is_sender or is_participant
            
            return is_sender or is_participant
        
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
        Handles PUT, PATCH, DELETE operations.
        """
        # For Conversation objects
        if hasattr(obj, 'participants'):
            is_participant = obj.participants.filter(id=request.user.id).exists()
            
            # Allow all operations for participants
            if request.method in permissions.SAFE_METHODS:
                return is_participant
            elif request.method in ['PUT', 'PATCH', 'DELETE', 'POST']:
                return is_participant
            
            return is_participant
        
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
        Handles PUT, PATCH, DELETE operations.
        """
        is_owner = False
        
        # For objects with owner field
        if hasattr(obj, 'owner'):
            is_owner = obj.owner == request.user
        # For objects with user field
        elif hasattr(obj, 'user'):
            is_owner = obj.user == request.user
        # For objects with sender field
        elif hasattr(obj, 'sender'):
            is_owner = obj.sender == request.user
        
        # Allow all operations for owners
        if request.method in permissions.SAFE_METHODS:
            return is_owner
        elif request.method in ['PUT', 'PATCH', 'DELETE', 'POST']:
            return is_owner
        
        return is_owner


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
        
        # Allow other methods (PUT, PATCH, DELETE) to be handled by object-level permissions
        elif request.method in ['PUT', 'PATCH', 'DELETE']:
            return True
        
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
        Handles PUT, PATCH, DELETE operations.
        """
        is_participant = obj.participants.filter(id=request.user.id).exists()
        
        # Allow all operations for participants
        if request.method in permissions.SAFE_METHODS:
            return is_participant
        elif request.method in ['PUT', 'PATCH', 'DELETE', 'POST']:
            return is_participant
        
        return is_participant


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
        Handles PUT, PATCH, DELETE operations.
        """
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        is_owner = False
        
        # Check ownership based on different field names
        if hasattr(obj, 'owner'):
            is_owner = obj.owner == request.user
        elif hasattr(obj, 'user'):
            is_owner = obj.user == request.user
        elif hasattr(obj, 'sender'):
            is_owner = obj.sender == request.user
        elif hasattr(obj, 'participants'):
            is_owner = obj.participants.filter(id=request.user.id).exists()
        
        # Allow all operations for admin or owners
        if request.method in permissions.SAFE_METHODS:
            return is_owner
        elif request.method in ['PUT', 'PATCH', 'DELETE', 'POST']:
            return is_owner
        
        return is_owner


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