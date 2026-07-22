from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    # Listings
    path('', views.resource_list, name='list'),
    
    # Create
    path('create/', views.resource_create, name='create'),
    path('<slug:slug>/edit/', views.edit_resource, name='edit'),
    
    # Detail
    path('<slug:slug>/', views.resource_detail, name='detail'),
    
    # Download
    path('<slug:slug>/download/', views.resource_download, name='download'),
    
    # Rating
    path('<slug:slug>/rate/', views.rate_resource, name='rate'),
]
