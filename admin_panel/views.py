from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.core.paginator import Paginator
from .models import SystemLog, SiteSettings, Announcement, DashboardWidget
from accounts.models import User
from members.models import Member
from communities.models import Community
from opportunities.models import Opportunity
from events.models import Event
from resources.models import Resource
from accounts.decorators import user_type_required


@login_required
@user_type_required(['admin', 'executive', 'moderator'])
def admin_dashboard(request):
    """Admin dashboard"""
    # Statistics
    total_users = User.objects.filter(is_active=True).count()
    total_members = Member.objects.filter(verification_status='verified').count()
    total_communities = Community.objects.filter(is_active=True).count()
    total_opportunities = Opportunity.objects.filter(status='published').count()
    total_events = Event.objects.filter(status__in=['published', 'ongoing']).count()
    total_resources = Resource.objects.filter(is_published=True).count()
    
    # Recent activity
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_opportunities = Opportunity.objects.filter(status='published').order_by('-created_at')[:5]
    upcoming_events = Event.objects.filter(
        start_date__gte=timezone.now(),
        status__in=['published', 'ongoing']
    ).order_by('start_date')[:5]
    
    # Community growth
    communities_by_type = Community.objects.values('community_type').annotate(
        count=Count('id')
    )
    
    # Opportunities by type
    opportunities_by_type = Opportunity.objects.filter(
        status='published'
    ).values('opportunity_type').annotate(
        count=Count('id')
    )
    
    # Member growth (last 30 days)
    from datetime import timedelta
    start_date = timezone.now() - timedelta(days=30)
    member_growth = Member.objects.filter(
        created_at__gte=start_date
    ).count()
    
    context = {
        'total_users': total_users,
        'total_members': total_members,
        'total_communities': total_communities,
        'total_opportunities': total_opportunities,
        'total_events': total_events,
        'total_resources': total_resources,
        'member_growth': member_growth,
        'recent_users': recent_users,
        'recent_opportunities': recent_opportunities,
        'upcoming_events': upcoming_events,
        'communities_by_type': communities_by_type,
        'opportunities_by_type': opportunities_by_type,
        'page_title': 'Dashboard - KMPN',
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
@user_type_required(['admin', 'executive'])
def system_logs(request):
    """View system logs"""
    logs = SystemLog.objects.all().order_by('-created_at')
    
    # Filters
    level = request.GET.get('level')
    if level:
        logs = logs.filter(level=level)
    
    source = request.GET.get('source')
    if source:
        logs = logs.filter(source=source)
    
    search = request.GET.get('search')
    if search:
        logs = logs.filter(message__icontains=search)
    
    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs = paginator.get_page(page)
    
    context = {
        'logs': logs,
        'page_title': 'System Logs - Admin',
        'log_levels': SystemLog.LOG_LEVELS,
        'log_sources': SystemLog.LOG_SOURCES,
    }
    return render(request, 'admin_panel/logs.html', context)


@login_required
@user_type_required(['admin'])
def site_settings(request):
    """Manage site settings"""
    if request.method == 'POST':
        # Update settings
        for key, value in request.POST.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                try:
                    setting = SiteSettings.objects.get(key=setting_key)
                    setting.value = value
                    setting.updated_by = request.user
                    setting.save()
                except SiteSettings.DoesNotExist:
                    pass
        messages.success(request, 'Settings updated successfully!')
        return redirect('admin_panel:settings')
    
    settings = SiteSettings.objects.all()
    
    context = {
        'settings': settings,
        'page_title': 'Site Settings - Admin',
    }
    return render(request, 'admin_panel/settings.html', context)


@login_required
@user_type_required(['admin', 'executive'])
def announcements(request):
    """Manage announcements"""
    announcements = Announcement.objects.all().order_by('-created_at')
    
    context = {
        'announcements': announcements,
        'page_title': 'Announcements - Admin',
    }
    return render(request, 'admin_panel/announcements.html', context)


@login_required
@user_type_required(['admin', 'executive'])
def create_announcement(request):
    """Create announcement"""
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        priority = request.POST.get('priority')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        announcement = Announcement.objects.create(
            title=title,
            content=content,
            priority=priority,
            start_date=start_date,
            end_date=end_date,
            created_by=request.user
        )
        
        messages.success(request, 'Announcement created successfully!')
        return redirect('admin_panel:announcements')
    
    context = {
        'page_title': 'Create Announcement - Admin',
        'priority_choices': Announcement.PRIORITY_CHOICES,
    }
    return render(request, 'admin_panel/create_announcement.html', context)


@login_required
@user_type_required(['admin', 'executive'])
def delete_announcement(request, ann_id):
    """Delete announcement"""
    announcement = get_object_or_404(Announcement, id=ann_id)
    announcement.delete()
    messages.success(request, 'Announcement deleted successfully!')
    return redirect('admin_panel:announcements')


@login_required
@user_type_required(['admin'])
def user_management(request):
    """Manage users"""
    users = User.objects.all().order_by('-date_joined')
    
    # Filters
    user_type = request.GET.get('user_type')
    if user_type:
        users = users.filter(user_type=user_type)
    
    is_verified = request.GET.get('is_verified')
    if is_verified:
        users = users.filter(is_verified=is_verified == 'true')
    
    search = request.GET.get('search')
    if search:
        users = users.filter(
            Q(email__icontains=search) |
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    paginator = Paginator(users, 20)
    page = request.GET.get('page')
    users = paginator.get_page(page)
    
    context = {
        'users': users,
        'page_title': 'User Management - Admin',
        'user_types': User.USER_TYPES,
    }
    return render(request, 'admin_panel/users.html', context)


@login_required
@user_type_required(['admin'])
def toggle_user_status(request, user_id):
    """Toggle user active status"""
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {status} successfully!')
    return redirect('admin_panel:user_management')
