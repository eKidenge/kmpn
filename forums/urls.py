# forums/urls.py

from django.urls import path
from . import views

app_name = 'forums'

urlpatterns = [
    # Main views
    path('', views.forum_list, name='list'),
    path('category/<slug:slug>/', views.forum_category, name='category'),
    
    # Thread views
    path('thread/<int:thread_id>/', views.thread_detail, name='thread_detail'),
    path('thread/create/', views.create_thread, name='create_thread'),
    path('thread/create/<slug:category_slug>/', views.create_thread, name='create_thread_category'),
    path('thread/<int:thread_id>/reply/', views.create_reply, name='create_reply'),
    path('thread/<int:thread_id>/edit/', views.edit_thread, name='edit_thread'),
    path('thread/<int:thread_id>/delete/', views.delete_thread, name='delete_thread'),  # ← ADD THIS
    path('thread/<int:thread_id>/like/', views.like_thread, name='like_thread'),
    
    # Reply views
    path('reply/<int:reply_id>/edit/', views.edit_reply, name='edit_reply'),
    path('reply/<int:reply_id>/delete/', views.delete_reply, name='delete_reply'),  # ← ADD THIS
    path('reply/<int:reply_id>/like/', views.like_reply, name='like_reply'),
    
    # Report views
    path('report/<str:content_type>/<int:content_id>/', views.report_content, name='report_content'),
    
    # Admin views
    path('moderate/reports/', views.moderate_reports, name='moderate_reports'),
    path('manage/threads/', views.manage_threads, name='manage_threads'),
    
    # AJAX endpoints
    path('api/thread/<int:thread_id>/replies/', views.get_thread_replies, name='get_thread_replies'),
    path('api/search/', views.search_threads_ajax, name='search_threads_ajax'),
]