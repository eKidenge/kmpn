"""
URL configuration for kmpn project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Homepage
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
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
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)