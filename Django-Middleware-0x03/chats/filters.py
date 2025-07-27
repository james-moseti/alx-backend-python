import django_filters
from django_filters import rest_framework as filters
from .models import Message, Conversation


class MessageFilter(filters.FilterSet):
    sender = filters.NumberFilter(field_name='sender__id')
    conversation = filters.NumberFilter(field_name='conversation__id')
    created_after = filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    content = filters.CharFilter(field_name='content', lookup_expr='icontains')
    
    class Meta:
        model = Message
        fields = ['sender', 'conversation', 'created_after', 'created_before', 'content']


class ConversationFilter(filters.FilterSet):
    participant = filters.NumberFilter(field_name='participants__id')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Conversation
        fields = ['participant', 'created_after', 'created_before']