from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Message, Notification

User = get_user_model()

class SignalTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='sender', 
            email='sender@test.com',
            first_name='John',
            last_name='Sender',
            password='test'
        )
        self.user2 = User.objects.create_user(
            username='receiver', 
            email='receiver@test.com',
            first_name='Jane',
            last_name='Receiver',
            password='test'
        )

    def test_notification_created_on_message_save(self):
        # Create a message
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Test message"
        )
        
        # Check that notification was created
        self.assertTrue(
            Notification.objects.filter(
                user=self.user2,
                message=message
            ).exists()
        )

    def test_notification_not_created_on_message_update(self):
        # Create a message
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Test message"
        )
        
        initial_count = Notification.objects.count()
        
        # Update the message
        message.content = "Updated message"
        message.save()
        
        # Should not create another notification
        self.assertEqual(Notification.objects.count(), initial_count)