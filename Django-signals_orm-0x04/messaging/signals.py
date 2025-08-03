from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Message, Notification

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