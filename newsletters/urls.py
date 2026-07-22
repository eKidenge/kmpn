from django.urls import path
from . import views

app_name = 'newsletters'

urlpatterns = [
    # Admin
    path('admin/', views.newsletter_list, name='list'),
    path('admin/create/', views.create_newsletter, name='create'),
    path('admin/<int:newsletter_id>/', views.newsletter_detail, name='detail'),
    path('admin/<int:newsletter_id>/send/', views.send_newsletter, name='send'),
    
    # Public
    path('subscribe/', views.subscribe_newsletter, name='subscribe'),
    path('unsubscribe/', views.unsubscribe_newsletter, name='unsubscribe'),
    path('unsubscribe/<str:email>/<str:token>/', views.unsubscribe_newsletter, name='unsubscribe_confirm'),
    
    # Tracking
    path('track/open/<str:tracking_id>/<int:subscriber_id>/', views.track_open, name='track_open'),
    path('track/click/<str:tracking_id>/<int:subscriber_id>/<path:url>/', views.track_click, name='track_click'),
]
