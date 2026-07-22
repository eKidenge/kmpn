from django.urls import path
from . import views

app_name = 'opportunities'

urlpatterns = [
    # Listings
    path('', views.opportunity_list, name='list'),
    path('saved/', views.saved_opportunities, name='saved'),
    path('my-applications/', views.my_applications, name='my_applications'),
    
    # Create
    path('create/', views.opportunity_create, name='create'),
    
    # Detail
    path('<int:opp_id>/', views.opportunity_detail, name='detail'),
    
    # Apply
    path('<int:opp_id>/apply/', views.opportunity_apply, name='apply'),
    
    # Save
    path('<int:opp_id>/save/', views.save_opportunity, name='save'),
    
    # Moderate (admin only)
    path('moderate/', views.moderate_opportunities, name='moderate'),
]
