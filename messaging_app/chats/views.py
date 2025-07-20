from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Conversation, Message, MessageReadStatus
from .serializers import (
    ConversationListSerializer,
    ConversationDetailSerializer, 
    MessageSerializer,
    UserSerializer,
    UserProfileSerializer,
    MessageReadStatusSerializer
)

User = get_user_model()


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling conversation operations
    Provides CRUD operations for conversations
    """
    serializer_class = ConversationListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['participants__username', 'participants__email']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Return conversations where the current user is a participant"""
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related(
            'participants',
            Prefetch(
                'messages',
                queryset=Message.objects.select_related('sender').order_by('-sent_at')[:1],
                to_attr='last_message_list'
            )
        ).distinct()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationListSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new conversation
        Expected payload: {"participant_ids": ["uuid1", "uuid2"]} or {"participant_emails": ["email1@example.com", "email2@example.com"]}
        """
        # Handle both participant_ids and participant_emails for flexibility
        participant_emails = request.data.get('participant_emails', [])
        participant_ids = request.data.get('participant_ids', [])
        
        if participant_emails:
            # Convert emails to user IDs
            users = User.objects.filter(email__in=participant_emails)
            if users.count() != len(participant_emails):
                existing_emails = set(users.values_list('email', flat=True))
                missing_emails = set(participant_emails) - existing_emails
                return Response(
                    {"error": f"Users not found for emails: {list(missing_emails)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            participant_ids = list(users.values_list('id', flat=True))  # Use 'id' instead of 'user_id'
        
        # Add current user to participants if not already included
        if request.user.id not in participant_ids:
            participant_ids.append(request.user.id)
        
        # Prepare data for serializer
        data = {'participant_ids': participant_ids}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        conversation = serializer.save()
        
        # Return detailed conversation
        response_serializer = ConversationDetailSerializer(conversation, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Add a participant to the conversation"""
        conversation = self.get_object()
        email = request.data.get('email')
        user_id = request.data.get('user_id')
        
        if not email and not user_id:
            return Response(
                {"error": "Either email or user_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if email:
                user = User.objects.get(email=email)
            else:
                user = User.objects.get(id=user_id)
                
            if user not in conversation.participants.all():
                conversation.participants.add(user)
                return Response(
                    {"message": f"User {user.email} added to conversation"},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"message": f"User {user.email} is already in this conversation"},
                    status=status.HTTP_200_OK
                )
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        """Remove a participant from the conversation"""
        conversation = self.get_object()
        email = request.data.get('email')
        user_id = request.data.get('user_id')
        
        if not email and not user_id:
            return Response(
                {"error": "Either email or user_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if email:
                user = User.objects.get(email=email)
            else:
                user = User.objects.get(id=user_id)
                
            if user in conversation.participants.all():
                conversation.participants.remove(user)
                return Response(
                    {"message": f"User {user.email} removed from conversation"},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": f"User {user.email} is not in this conversation"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get all messages for a specific conversation"""
        conversation = self.get_object()
        messages = conversation.messages.select_related('sender').order_by('sent_at')
        
        # Pagination
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling message operations
    Provides CRUD operations for messages
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['message_body', 'sender__username']
    ordering_fields = ['sent_at']
    ordering = ['-sent_at']
    
    def get_queryset(self):
        """Return messages for conversations where the current user is a participant"""
        return Message.objects.filter(
            conversation__participants=self.request.user
        ).select_related('sender', 'conversation').distinct()
    
    def create(self, request, *args, **kwargs):
        """
        Send a message to a conversation
        Expected payload: {"conversation": "uuid", "message_body": "text"}
        """
        conversation_id = request.data.get('conversation') or request.data.get('conversation_id')
        
        if not conversation_id:
            return Response(
                {"error": "conversation or conversation_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify user is participant in the conversation
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                participants=request.user
            )
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found or you are not a participant"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Prepare data for serializer
        data = request.data.copy()
        data['conversation'] = conversation_id
        data['sender'] = request.user.id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Save message
        message = serializer.save(sender=request.user, conversation=conversation)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a message as read by the current user"""
        message = self.get_object()
        
        # Don't mark own messages as read
        if message.sender == request.user:
            return Response(
                {"message": "Cannot mark your own message as read"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update read status
        read_status, created = MessageReadStatus.objects.get_or_create(
            message=message,
            user=request.user,
            defaults={'read_at': timezone.now()}
        )
        
        if created:
            return Response(
                {"message": "Message marked as read"},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"message": "Message already marked as read"},
                status=status.HTTP_200_OK
            )
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get all unread messages for the current user"""
        # Get messages where user is a participant but hasn't marked as read
        # Exclude messages sent by the user themselves
        unread_messages = Message.objects.filter(
            conversation__participants=request.user
        ).exclude(
            sender=request.user
        ).exclude(
            read_statuses__user=request.user
        ).select_related('sender', 'conversation').distinct()
        
        # Pagination
        page = self.paginate_queryset(unread_messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(unread_messages, many=True, context={'request': request})
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update a message (only sender can edit their own messages)"""
        message = self.get_object()
        
        # Check if user is the sender
        if message.sender != request.user:
            return Response(
                {"error": "You can only edit your own messages"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update message
        serializer = self.get_serializer(message, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Set edited timestamp
        message.edited_at = timezone.now()
        message.save(update_fields=['edited_at'])
        
        self.perform_update(serializer)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a message (only sender can delete their own messages)"""
        message = self.get_object()
        
        # Check if user is the sender
        if message.sender != request.user:
            return Response(
                {"error": "You can only delete your own messages"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)


class ConversationBulkViewSet(viewsets.ViewSet):
    """
    ViewSet for bulk conversation operations
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all messages in user's conversations as read"""
        user_conversations = Conversation.objects.filter(participants=request.user)
        
        # Get all unread messages in user's conversations (excluding own messages)
        unread_messages = Message.objects.filter(
            conversation__in=user_conversations
        ).exclude(
            sender=request.user
        ).exclude(
            read_statuses__user=request.user
        )
        
        # Create read statuses for all unread messages
        read_statuses_to_create = [
            MessageReadStatus(message=message, user=request.user, read_at=timezone.now())
            for message in unread_messages
        ]
        
        created_count = len(read_statuses_to_create)
        if created_count > 0:
            MessageReadStatus.objects.bulk_create(
                read_statuses_to_create,
                ignore_conflicts=True
            )
        
        return Response(
            {"message": f"Marked {created_count} messages as read"},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread messages for the current user"""
        unread_count = Message.objects.filter(
            conversation__participants=request.user
        ).exclude(
            sender=request.user
        ).exclude(
            read_statuses__user=request.user
        ).distinct().count()
        
        return Response({"unread_count": unread_count})
    
    @action(detail=False, methods=['get'])
    def conversation_unread_counts(self, request):
        """Get unread message counts per conversation"""
        user_conversations = Conversation.objects.filter(participants=request.user)
        
        conversation_counts = []
        for conversation in user_conversations:
            unread_count = Message.objects.filter(
                conversation=conversation
            ).exclude(
                sender=request.user
            ).exclude(
                read_statuses__user=request.user
            ).count()
            
            conversation_counts.append({
                'conversation_id': str(conversation.id),
                'unread_count': unread_count
            })
        
        return Response(conversation_counts)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user operations (read-only for search/lookup)
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def get_queryset(self):
        """Return all users for search purposes"""
        return User.objects.all().order_by('username')
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)