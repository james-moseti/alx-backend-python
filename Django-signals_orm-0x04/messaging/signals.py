from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Message, Notification

User = get_user_model()

@receiver(post_save, sender=Message)
def create_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.receiver,
            message=instance
        )

@receiver(pre_save, sender=Message)
def log_message_edit(sender, instance, **kwargs):
    if instance.pk:  # Only for existing messages (updates)
        try:
            from .models import MessageHistory
            old_message = Message.objects.get(pk=instance.pk)
            # Check if content has changed
            if old_message.content != instance.content:
                # Log the old content
                MessageHistory.objects.create(
                    message=instance,
                    old_content=old_message.content
                )
                # Mark message as edited
                instance.edited = True
                instance.edited_at = timezone.now()
        except Message.DoesNotExist:
            pass

@receiver(post_delete, sender=User)
def delete_user_related_data(sender, instance, **kwargs):
    """Clean up user-related data when a user is deleted"""
    # Delete all messages where user is sender or receiver
    Message.objects.filter(sender=instance).delete()
    Message.objects.filter(receiver=instance).delete()
    
    # Delete all notifications for this user
    Notification.objects.filter(user=instance).delete()