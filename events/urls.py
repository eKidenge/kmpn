from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    # Listings
    path('', views.event_list, name='list'),
    path('my/', views.my_events, name='my_events'),
    
    # Create
    path('create/', views.event_create, name='create'),
    
    # Detail
    path('<slug:slug>/', views.event_detail, name='detail'),
    
    # Edit/Delete
    path('<slug:slug>/edit/', views.edit_event, name='edit'),
    path('<slug:slug>/delete/', views.delete_event, name='delete'),
    
    # Register
    path('<slug:slug>/register/', views.event_register, name='register'),
    path('<slug:slug>/cancel/', views.cancel_registration, name='cancel'),
    
    # Feedback
    path('<slug:slug>/feedback/', views.event_feedback, name='feedback'),
    
    # Certificates
    path('<slug:slug>/certificates/', views.generate_certificates, name='generate_certificates'),
    path('certificate/<int:registration_id>/', views.download_certificate, name='certificate'),
    
    # AJAX
    path('api/<slug:slug>/status/', views.get_registration_status, name='registration_status'),
    path('api/<slug:slug>/stats/', views.get_event_stats, name='event_stats'),
    path('api/search/', views.search_events_ajax, name='search_ajax'),
]