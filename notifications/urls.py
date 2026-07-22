from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notifications
    path('', views.notification_list, name='list'),
    path('<int:notif_id>/read/', views.mark_as_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('<int:notif_id>/delete/', views.delete_notification, name='delete'),
    path('delete-all/', views.delete_all_notifications, name='delete_all'),
    
    # Preferences
    path('preferences/', views.notification_preferences, name='preferences'),
    
    # AJAX
    path('count/', views.get_notification_count, name='count'),
]
