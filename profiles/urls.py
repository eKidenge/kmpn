from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    # Profile Views
    path('view/<str:username>/', views.profile_view, name='view'),
    path('edit/', views.profile_edit, name='edit'),
    
    # Profile Sections
    path('edit/basic/', views.edit_basic_info, name='edit_basic'),
    path('edit/academic/', views.edit_academic, name='edit_academic'),
    path('edit/research/', views.edit_research, name='edit_research'),
    path('edit/skills/', views.edit_skills, name='edit_skills'),
    path('edit/publications/', views.edit_publications, name='edit_publications'),
    
    # Visibility
    path('visibility/', views.profile_visibility, name='visibility'),
    
    # Research Interests
    path('interests/', views.research_interests, name='research_interests'),
    path('interests/add/', views.add_interest, name='add_interest'),
    path('interests/remove/', views.remove_interest, name='remove_interest'),
    
    # Publications
    path('publications/add/', views.add_publication, name='add_publication'),
    path('publications/<int:pub_id>/edit/', views.edit_publication, name='edit_publication'),
    path('publications/<int:pub_id>/delete/', views.delete_publication, name='delete_publication'),
    path('publications/<int:pub_id>/citation/', views.get_citation, name='get_citation'),
    
    # AJAX
    path('api/completion/', views.get_profile_completion, name='profile_completion'),
    path('api/publications/search/', views.search_publications, name='search_publications'),
]
