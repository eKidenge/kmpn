from django.urls import path
from . import views

app_name = 'communities'

urlpatterns = [
    # Community List
    path('', views.community_list, name='list'),
    path('browse/', views.community_browse, name='browse'),
    path('create/', views.community_create, name='create'),
    
    # Single Community
    path('<str:slug>/', views.community_detail, name='detail'),
    path('<str:slug>/members/', views.community_members, name='members'),
    path('<str:slug>/join/', views.community_join, name='join'),
    path('<str:slug>/leave/', views.community_leave, name='leave'),
    path('<str:slug>/settings/', views.community_settings, name='settings'),
    
    # Posts
    path('<str:slug>/post/create/', views.create_post, name='create_post'),
    path('<str:slug>/post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('<str:slug>/post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('<str:slug>/post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('<str:slug>/post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('<str:slug>/post/<int:post_id>/pin/', views.pin_post, name='pin_post'),
    
    # Comments
    path('<str:slug>/post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('<str:slug>/comment/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('<str:slug>/comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('<str:slug>/comment/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    
    # AJAX
    path('api/search/', views.search_communities, name='search'),
    path('api/community-data/<str:slug>/', views.get_community_data, name='community_data'),
]
