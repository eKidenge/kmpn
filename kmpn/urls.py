# kmpn/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from accounts.views import home

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Homepage - USE YOUR VIEW
    path('', home, name='home'),
    
    # Accounts - CUSTOM FIRST, allauth SECOND
    path('accounts/', include('accounts.urls')),   # Your custom views FIRST
    path('accounts/', include('allauth.urls')),    # Social auth SECOND
    
    # Members
    path('members/', include('members.urls')),
    
    # Profiles
    path('profiles/', include('profiles.urls')),
    
    # Communities
    path('communities/', include('communities.urls')),
    
    # Collaborations
    path('collaborations/', include('collaborations.urls')),
    
    # Forums
    path('forums/', include('forums.urls')),
    
    # Opportunities
    path('opportunities/', include('opportunities.urls')),
    
    # Resources
    path('resources/', include('resources.urls')),
    
    # Events
    path('events/', include('events.urls')),
    
    # Admin Panel
    path('dashboard/', include('admin_panel.urls')),
    
    # Notifications
    path('notifications/', include('notifications.urls')),
    
    # Analytics
    path('analytics/', include('analytics.urls')),
    
    # Payments
    path('payments/', include('payments.urls')),
    
    # Newsletters
    path('newsletters/', include('newsletters.urls')),
    
    # API
    path('api/', include('api.urls')),
    
    # ============================================================
    # CKEDITOR 5 - ADD THIS
    # ============================================================
    path('ckeditor5/', include('django_ckeditor_5.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)