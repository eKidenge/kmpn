from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Dashboard
    path('', views.analytics_dashboard, name='dashboard'),
    path('overview/', views.analytics_overview, name='overview'),
    
    # User Analytics
    path('users/', views.user_analytics, name='users'),
    path('users/activity/', views.user_activity_report, name='user_activity'),
    
    # Content Analytics
    path('content/', views.content_analytics, name='content'),
    
    # Opportunity Analytics
    path('opportunities/', views.opportunity_analytics, name='opportunities'),
    
    # Event Analytics
    path('events/', views.event_analytics, name='events'),
    
    # Resource Analytics
    path('resources/', views.resource_analytics, name='resources'),
    
    # Campaign Analytics
    path('campaigns/', views.campaign_analytics, name='campaigns'),
    path('campaigns/<int:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    
    # Export
    path('export/<str:data_type>/', views.export_analytics, name='export'),
    
    # AJAX
    path('api/chart-data/', views.get_analytics_chart_data, name='chart_data'),
    path('api/realtime/', views.get_realtime_stats, name='realtime_stats'),
]
