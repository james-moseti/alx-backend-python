from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.views.decorators.cache import cache_page
from .models import Message, MessageHistory

User = get_user_model()

@cache_page(60)
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

@cache_page(60)
def threaded_messages(request):
    """View to display threaded conversations with optimized queries"""
    # Get all root messages (messages without parent) with optimized queries
    root_messages = Message.objects.filter(parent_message=None).select_related('sender', 'receiver').prefetch_related('replies__sender', 'replies__receiver')
    
    return render(request, 'messaging/threaded_messages.html', {
        'root_messages': root_messages
    })

@cache_page(60)
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
@cache_page(60)
def inbox(request):
    """User inbox showing only unread messages with optimized query"""
    # Use custom manager with optimized query
    unread_messages = Message.unread.optimized_for_user(request.user)
    unread_count = Message.unread.unread_count(request.user)
    
    return render(request, 'messaging/inbox.html', {
        'messages': unread_messages,
        'unread_count': unread_count
    })

@login_required
def mark_message_read(request, message_id):
    """Mark a specific message as read"""
    message = get_object_or_404(Message, message_id=message_id, receiver=request.user)
    message.mark_as_read()
    
    return JsonResponse({'status': 'success', 'message': 'Message marked as read'})

@login_required
def mark_all_read(request):
    """Mark all unread messages as read for the current user"""
    Message.unread.for_user(request.user).update(read=True)
    
    return JsonResponse({'status': 'success', 'message': 'All messages marked as read'})

@login_required
def get_unread_count(request):
    """API endpoint to get unread message count"""
    count = Message.unread.unread_count(request.user)
    
    return JsonResponse({'unread_count': count})

@login_required
def bulk_mark_read(request):
    """Mark multiple messages as read"""
    if request.method == 'POST':
        message_ids = request.POST.getlist('message_ids')
        if message_ids:
            messages_to_mark = Message.objects.filter(
                message_id__in=message_ids,
                receiver=request.user,
                read=False
            )
            messages_to_mark.update(read=True)
            
            return JsonResponse({
                'status': 'success', 
                'message': f'{messages_to_mark.count()} messages marked as read'
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})