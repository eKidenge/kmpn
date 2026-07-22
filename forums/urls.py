from django.urls import path
from . import views

app_name = 'forums'

urlpatterns = [
    # Forum List
    path('', views.forum_list, name='list'),
    path('category/<str:slug>/', views.forum_category, name='category'),
    
    # Threads
    path('thread/<int:thread_id>/', views.thread_detail, name='thread_detail'),
    path('thread/create/', views.create_thread, name='create_thread'),
    path('thread/create/<str:category_slug>/', views.create_thread, name='create_thread_category'),
    path('thread/<int:thread_id>/edit/', views.edit_thread, name='edit_thread'),
    path('thread/<int:thread_id>/like/', views.like_thread, name='like_thread'),
    
    # Replies
    path('thread/<int:thread_id>/reply/', views.create_reply, name='create_reply'),
    path('reply/<int:reply_id>/edit/', views.edit_reply, name='edit_reply'),
    path('reply/<int:reply_id>/like/', views.like_reply, name='like_reply'),
    
    # Reports
    path('report/<str:content_type>/<int:content_id>/', views.report_content, name='report'),
]
