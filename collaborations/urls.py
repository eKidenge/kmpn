from django.urls import path
from . import views

app_name = 'collaborations'

urlpatterns = [
    # Collaboration List
    path('', views.collaboration_list, name='list'),
    path('my/', views.my_collaborations, name='my'),
    path('create/', views.collaboration_create, name='create'),
    path('<int:collab_id>/', views.collaboration_detail, name='detail'),
    
    # Applications
    path('<int:collab_id>/apply/', views.collaboration_apply, name='apply'),
    path('application/<int:app_id>/<str:action>/', 
         views.collaboration_application_action, name='application_action'),
    
    # Messages
    path('<int:collab_id>/messages/', views.collaboration_message, name='messages'),
    
    # Supervisor Matching
    path('supervisor-matching/', views.supervisor_matching, name='supervisor_matching'),
    path('supervisor-match/<int:match_id>/<str:action>/', 
         views.supervisor_match_action, name='supervisor_match_action'),
]
