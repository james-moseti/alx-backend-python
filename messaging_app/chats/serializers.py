from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, Conversation, Message, MessageReadStatus


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with password handling
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'role', 'created_at', 'password', 'confirm_password'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'created_at': {'read_only': True},
            'id': {'read_only': True},
        }
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if 'password' in attrs and 'confirm_password' in attrs:
            if attrs['password'] != attrs['confirm_password']:
                raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user, handle password separately"""
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Simplified user serializer for displaying user info in messages/conversations
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'full_name', 'email', 'role']
        read_only_fields = ['id', 'email', 'role']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model
    """
    sender = UserProfileSerializer(read_only=True)
    sender_id = serializers.UUIDField(write_only=True, required=False)
    conversation_id = serializers.UUIDField(write_only=True, required=False)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'message_id', 'sender', 'sender_id', 'conversation', 'conversation_id',
            'message_body', 'sent_at', 'time_ago', 'is_read', 'edited_at'
        ]
        extra_kwargs = {
            'message_id': {'read_only': True},
            'sent_at': {'read_only': True},
            'conversation': {'read_only': True},
            'edited_at': {'read_only': True},
        }
    
    def get_time_ago(self, obj):
        """Calculate human-readable time difference"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.sent_at
        
        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return obj.sent_at.strftime("%b %d, %Y")
    
    def create(self, validated_data):
        """Create message with current user as sender"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['sender'] = request.user
        return super().create(validated_data)


class MessageReadStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for MessageReadStatus model
    """
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = MessageReadStatus
        fields = ['id', 'user', 'read_at']
        read_only_fields = ['id', 'read_at']


class ConversationListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for conversation lists
    """
    participants = UserProfileSerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(), 
        write_only=True, 
        required=False
    )
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'participants', 'participant_ids', 
            'created_at', 'updated_at', 'last_message', 'unread_count', 
            'participant_count'
        ]
        read_only_fields = ['conversation_id', 'created_at', 'updated_at']
    
    def get_last_message(self, obj):
        """Get the most recent message preview"""
        last_message = obj.get_last_message()
        if last_message:
            return {
                'message_id': last_message.message_id,
                'sender_name': f"{last_message.sender.first_name} {last_message.sender.last_name}",
                'message_body': last_message.message_body[:100] + "..." if len(last_message.message_body) > 100 else last_message.message_body,
                'sent_at': last_message.sent_at,
            }
        return None
    
    def get_unread_count(self, obj):
        """Get count of unread messages for current user"""
        request = self.context.get('request')
        if request and request.user:
            return obj.messages.filter(
                is_read=False
            ).exclude(sender=request.user).count()
        return 0
    
    def get_participant_count(self, obj):
        """Get total number of participants"""
        return obj.participants.count()
    
    def create(self, validated_data):
        """Create conversation with participants"""
        participant_ids = validated_data.pop('participant_ids', [])
        request = self.context.get('request')
        
        conversation = Conversation.objects.create()
        
        # Add current user as participant
        if request and request.user:
            conversation.participants.add(request.user)
        
        # Add other participants
        if participant_ids:
            users = User.objects.filter(id__in=participant_ids)
            conversation.participants.add(*users)
        
        return conversation


class ConversationDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual conversation with messages
    """
    participants = UserProfileSerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(), 
        write_only=True, 
        required=False
    )
    messages = MessageSerializer(many=True, read_only=True)
    participant_count = serializers.SerializerMethodField()
    is_group_chat = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'participants', 'participant_ids',
            'messages', 'created_at', 'updated_at', 
            'participant_count', 'is_group_chat'
        ]
        read_only_fields = ['conversation_id', 'created_at', 'updated_at']
    
    def get_participant_count(self, obj):
        """Get total number of participants"""
        return obj.participants.count()
    
    def get_is_group_chat(self, obj):
        """Determine if this is a group chat (more than 2 participants)"""
        return obj.participants.count() > 2
    
    def to_representation(self, instance):
        """Customize serialization to limit message count for performance"""
        representation = super().to_representation(instance)
        
        # Limit messages to last 50 by default, can be overridden in view
        request = self.context.get('request')
        message_limit = 50
        
        if request:
            try:
                message_limit = int(request.query_params.get('message_limit', 50))
                message_limit = min(message_limit, 100)  # Cap at 100 messages
            except (ValueError, TypeError):
                message_limit = 50
        
        # Get limited messages (most recent first, then reverse for chronological order)
        messages = instance.messages.select_related('sender').order_by('-sent_at')[:message_limit]
        messages = reversed(messages)
        
        representation['messages'] = MessageSerializer(
            messages, 
            many=True, 
            context=self.context
        ).data
        
        return representation


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user authentication
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password.')
        
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user password
    """
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    confirm_password = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs
    
    def validate_old_password(self, value):
        request = self.context.get('request')
        if request and request.user:
            if not request.user.check_password(value):
                raise serializers.ValidationError("Old password is incorrect.")
        return value