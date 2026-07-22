from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('', views.admin_dashboard, name='dashboard'),
    
    # Logs
    path('logs/', views.system_logs, name='logs'),
    
    # Settings
    path('settings/', views.site_settings, name='settings'),
    
    # Announcements
    path('announcements/', views.announcements, name='announcements'),
    path('announcements/create/', views.create_announcement, name='create_announcement'),
    path('announcements/<int:ann_id>/delete/', views.delete_announcement, name='delete_announcement'),
    
    # User Management
    path('users/', views.user_management, name='user_management'),
    path('users/<int:user_id>/toggle/', views.toggle_user_status, name='toggle_user'),
]
