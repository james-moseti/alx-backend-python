from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('message/<uuid:message_id>/history/', views.message_history, name='message_history'),
    path('delete-user/', views.delete_user, name='delete_user'),
    path('threaded/', views.threaded_messages, name='threaded_messages'),
    path('message/<uuid:message_id>/thread/', views.message_thread, name='message_thread'),
    path('unread/', views.unread_messages, name='unread_messages'),
    path('inbox/', views.inbox, name='inbox'),
    path('message/<uuid:message_id>/mark-read/', views.mark_message_read, name='mark_message_read'),
]