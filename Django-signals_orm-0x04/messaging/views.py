from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Message, MessageHistory

User = get_user_model()

def message_history(request, message_id):
    """View to display edit history for a specific message"""
    message = get_object_or_404(Message, message_id=message_id)
    history = MessageHistory.objects.filter(message=message).order_by('-edited_at')
    
    if request.headers.get('Accept') == 'application/json':
        # Return JSON response for API calls
        history_data = [
            {
                'old_content': h.old_content,
                'edited_at': h.edited_at.isoformat(),
            }
            for h in history
        ]
        return JsonResponse({
            'message_id': str(message.message_id),
            'current_content': message.content,
            'edited': message.edited,
            'history': history_data
        })
    
    # Return HTML template for regular requests
    return render(request, 'messaging/message_history.html', {
        'message': message,
        'history': history
    })

@login_required
def delete_user(request):
    """View to allow a user to delete their account"""
    if request.method == 'POST':
        user = request.user
        logout(request)  # Log out the user before deletion
        user.delete()    # This will trigger the post_delete signal
        messages.success(request, 'Your account has been successfully deleted.')
        return redirect('/')  # Redirect to homepage or login page
    
    return render(request, 'messaging/delete_user.html')

def threaded_messages(request):
    """View to display threaded conversations with optimized queries"""
    # Get all root messages (messages without parent) with optimized queries
    root_messages = Message.objects.filter(parent_message=None).select_related('sender', 'receiver').prefetch_related('replies__sender', 'replies__receiver')
    
    return render(request, 'messaging/threaded_messages.html', {
        'root_messages': root_messages
    })

def message_thread(request, message_id):
    """View to display a specific message thread with all replies"""
    message = get_object_or_404(
        Message.objects.select_related('sender', 'receiver').prefetch_related('replies'),
        message_id=message_id
    )
    
    # Get all replies recursively using ORM
    all_replies = message.get_all_replies()
    
    return render(request, 'messaging/message_thread.html', {
        'message': message,
        'replies': all_replies
    })

def optimized_messages(request):
    """View with specific optimization patterns for testing"""
    # Query with select_related for foreign keys and prefetch_related for reverse relations
    messages = Message.objects.filter(
        sender=request.user
    ).select_related(
        'sender', 'receiver'
    ).prefetch_related(
        'replies__sender', 'replies__receiver'
    )
    
    return render(request, 'messaging/optimized_messages.html', {
        'messages': messages
    })

@login_required
def unread_messages(request):
    """View to display unread messages using custom manager"""
    # Use custom manager to get unread messages with optimization
    unread_msgs = Message.unread.optimized_for_user(request.user)
    unread_count = Message.unread.unread_count(request.user)
    
    return render(request, 'messaging/unread_messages.html', {
        'unread_messages': unread_msgs,
        'unread_count': unread_count
    })

@login_required
def inbox(request):
    """User inbox showing only unread messages with .only() optimization"""
    # Use custom manager with .only() to retrieve only necessary fields
    unread_messages = Message.unread.for_user(request.user).only(
        'message_id', 'content', 'timestamp', 'sender'
    )
    
    return render(request, 'messaging/inbox.html', {
        'messages': unread_messages
    })

@login_required
def mark_message_read(request, message_id):
    """Mark a specific message as read"""
    message = get_object_or_404(Message, message_id=message_id, receiver=request.user)
    message.mark_as_read()
    
    return JsonResponse({'status': 'success', 'message': 'Message marked as read'})