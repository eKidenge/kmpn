from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Sum, Avg, Max, Min, F, Value, IntegerField
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek, TruncDay
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import logging
from datetime import datetime, timedelta
import csv
from io import StringIO

from .models import (
    PageView, UserActivityAnalytics, CampaignAnalytics
)
from .forms import (
    AnalyticsDateFilterForm, CampaignAnalyticsForm
)
from accounts.models import User, UserActivityLog
from accounts.decorators import user_type_required
from members.models import Member, MemberActivity
from communities.models import Community, CommunityPost, CommunityMember
from opportunities.models import Opportunity
from events.models import Event, EventRegistration
from resources.models import Resource, ResourceDownload

logger = logging.getLogger(__name__)


# ============================================================
# ANALYTICS DASHBOARD
# ============================================================

@login_required
@user_type_required(['admin', 'executive'])
def analytics_dashboard(request):
    """Main analytics dashboard"""
    # Date range filter
    date_range = request.GET.get('date_range', '30')
    end_date = timezone.now()
    start_date = end_date - timedelta(days=int(date_range))
    
    # Get analytics data
    analytics_data = get_analytics_data(start_date, end_date)
    
    # Get charts data
    charts_data = get_charts_data(start_date, end_date)
    
    context = {
        'analytics': analytics_data,
        'charts': charts_data,
        'date_range': date_range,
        'page_title': 'Analytics Dashboard - Admin',
    }
    return render(request, 'analytics/dashboard.html', context)


@login_required
@user_type_required(['admin', 'executive'])
def analytics_overview(request):
    """Overview analytics"""
    date_range = request.GET.get('date_range', '30')
    end_date = timezone.now()
    start_date = end_date - timedelta(days=int(date_range))
    
    # Overview statistics
    total_users = User.objects.filter(is_active=True).count()
    new_users = User.objects.filter(date_joined__gte=start_date).count()
    
    total_members = Member.objects.count()
    verified_members = Member.objects.filter(verification_status='verified').count()
    new_members = Member.objects.filter(created_at__gte=start_date).count()
    
    total_communities = Community.objects.filter(is_active=True).count()
    active_communities = Community.objects.filter(
        is_active=True,
        last_activity__gte=start_date
    ).count()
    
    total_posts = CommunityPost.objects.filter(status__in=['published', 'pinned']).count()
    new_posts = CommunityPost.objects.filter(
        created_at__gte=start_date,
        status__in=['published', 'pinned']
    ).count()
    
    total_opportunities = Opportunity.objects.filter(status='published').count()
    new_opportunities = Opportunity.objects.filter(
        created_at__gte=start_date,
        status='published'
    ).count()
    
    total_events = Event.objects.filter(status__in=['published', 'ongoing']).count()
    upcoming_events = Event.objects.filter(
        start_date__gte=timezone.now(),
        status__in=['published', 'ongoing']
    ).count()
    
    total_resources = Resource.objects.filter(is_published=True).count()
    new_resources = Resource.objects.filter(
        created_at__gte=start_date,
        is_published=True
    ).count()
    
    # Engagement metrics
    total_page_views = PageView.objects.filter(
        created_at__gte=start_date
    ).count()
    
    unique_visitors = PageView.objects.filter(
        created_at__gte=start_date
    ).values('session_id').distinct().count()
    
    context = {
        'total_users': total_users,
        'new_users': new_users,
        'total_members': total_members,
        'verified_members': verified_members,
        'new_members': new_members,
        'total_communities': total_communities,
        'active_communities': active_communities,
        'total_posts': total_posts,
        'new_posts': new_posts,
        'total_opportunities': total_opportunities,
        'new_opportunities': new_opportunities,
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'total_resources': total_resources,
        'new_resources': new_resources,
        'total_page_views': total_page_views,
        'unique_visitors': unique_visitors,
        'date_range': date_range,
        'page_title': 'Analytics Overview - Admin',
    }
    return render(request, 'analytics/overview.html', context)


# ============================================================
# USER ANALYTICS
# ============================================================

@login_required
@user_type_required(['admin', 'executive'])
def user_analytics(request):
    """User analytics"""
    date_range = request.GET.get('date_range', '30')
    end_date = timezone.now()
    start_date = end_date - timedelta(days=int(date_range))
    
    # User growth
    user_growth = User.objects.filter(
        date_joined__gte=start_date
    ).annotate(
        date=TruncDate('date_joined')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # User types distribution
    user_types = User.objects.values('user_type').annotate(
        count=Count('id')
    )
    
    # Member verification status
    verification_status = Member.objects.values('verification_status').annotate(
        count=Count('id')
    )
    
    # Active users
    active_users = UserActivityLog.objects.filter(
        created_at__gte=start_date
    ).values('user').distinct().count()
    
    # New vs returning users
    new_users = User.objects.filter(date_joined__gte=start_date).count()
    returning_users = active_users - new_users
    
    # User engagement
    user_engagement = UserActivityAnalytics.objects.filter(
        date__gte=start_date.date()
    ).aggregate(
        avg_engagement=Avg('engagement_score'),
        max_engagement=Max('engagement_score'),
        total_logins=Sum('logins'),
        total_interactions=Sum('interactions')
    )
    
    # Top users by engagement
    top_users = UserActivityAnalytics.objects.filter(
        date__gte=start_date.date()
    ).values('user__email', 'user__first_name', 'user__last_name').annotate(
        total_engagement=Sum('engagement_score'),
        total_logins=Sum('logins'),
        total_posts=Sum('posts_created'),
        total_comments=Sum('comments_made')
    ).order_by('-total_engagement')[:10]
    
    context = {
        'user_growth': user_growth,
        'user_types': user_types,
        'verification_status': verification_status,
        'active_users': active_users,
        'new_users': new_users,
        'returning_users': returning_users,
        'user_engagement': user_engagement,
        'top_users': top_users,
        'date_range': date_range,
        'page_title': 'User Analytics - Admin',
    }
    return render(request, 'analytics/users.html', context)


@login_required
@user_type_required(['admin', 'executive'])
def user_activity_report(request):
    """User activity report"""
    date_range = request.GET.get('date_range', '30')
    end_date = timezone.now()
    start_date = end_date - timedelta(days=int(date_range))
    
    activities = UserActivityLog.objects.filter(
        created_at__gte=start_date
    ).order_by('-created_at')
    
    # Filters
    user_filter = request.GET.get('user')
    if user_filter:
        activities = activities.filter(user__email__icontains=user_filter)
    
    action_type = request.GET.get('action_type')
    if action_type:
        activities = activities.filter(action_type=action_type)
    
    paginator = Paginator(activities, 50)
    page = request.GET.get('page', 1)
    
    try:
        activities = paginator.page(page)
    except PageNotAnInteger:
        activities = paginator.page(1)
    except EmptyPage:
        activities = paginator.page(paginator.num_pages)
    
    # Summary statistics
    activity_summary = activities[:100].values('action_type').annotate(
        count=Count('id')
    )
    
    context = {
        'activities': activities,
        'activity_summary': activity_summary,
        'action_types': UserActivityLog.ACTION_TYPES,
        'date_range': date_range,
        'page_title': 'User Activity Report - Admin',
    }
    return render(request, 'analytics/user_activity_report.html', context)


# ============================================================
# CONTENT ANALYTICS
# ============================================================

@login_required
@user_type_required(['admin', 'executive'])
def content_analytics(request):
    """Content analytics"""
    date_range = request.GET.get('date_range', '30')
    end_date = timezone.now()
    start_date = end_date - timedelta(days=int(date_range))
    
    # Community analytics
    community_stats = Community.objects.filter(
        is_active=True
    ).aggregate(
        total_communities=Count('id'),
        total_members=Sum('member_count'),
        total_posts=Sum('post_count'),
        total_views=Sum('view_count'),
        avg_members=Avg('member_count'),
        avg_posts=Avg('post_count')
    )
    
    top_communities = Community.objects.filter(
        is_active=True
    ).order_by('-member_count', '-post_count')[:10]
    
    community_growth = Community.objects.filter(
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Post analytics
    post_stats = CommunityPost.objects.filter(
        status__in=['published', 'pinned']
    ).aggregate(
        total_posts=Count('id'),
        total_views=Sum('view_count'),
        total_likes=Sum('like_count'),
        total_comments=Sum('comment_count'),
        avg_views=Avg('view_count'),
        avg_likes=Avg('like_count'),
        avg_comments=Avg('comment_count')
    )
    
    popular_posts = CommunityPost.objects.filter(
        status__in=['published', 'pinned'],
        created_at__gte=start_date
    ).order_by('-like_count', '-comment_count', '-view_count')[:10]
    
    # Post types distribution
    post_types = CommunityPost.objects.filter(
        status__in=['published', 'pinned']
    ).values('post_type').annotate(
        count=Count('id')
    )
    
    context = {
        'community_stats': community_stats,
        'top_communities': top_communities,
        'community_growth': community_growth,
        'post_stats': post_stats,
        'popular_posts': popular_posts,
        'post_types': post_types,
        'date_range': date_range,
        'page_title': 'Content Analytics - Admin',
    }
    return render(request, 'analytics/content.html', context)


# ============================================================
# OPPORTUNITY AND EVENT ANALYTICS
# ============================================================

@login_required
@user_type_required(['admin', 'executive'])
def opportunity_analytics(request):
    """Opportunity analytics"""
    date_range = request.GET.get('date_range', '30')
    end_date = timezone.now()
    start_date = end_date - timedelta(days=int(date_range))
    
    # Opportunity statistics
    opp_stats = Opportunity.objects.filter(
        status='published'
    ).aggregate(
        total_opportunities=Count('id'),
        total_views=Sum('view_count'),
        total_applications=Sum('application_count'),
        avg_views=Avg('view_count'),
        avg_applications=Avg('application_count')
    )
    
    # Opportunities by type
    opp_by_type = Opportunity.objects.filter(
        status='published'
    ).values('opportunity_type').annotate(
        count=Count('id'),
        total_views=Sum('view_count'),
        total_applications=Sum('application_count')
    ).order_by('-count')
    
    # Top opportunities
    top_opportunities = Opportunity.objects.filter(
        status='published'
    ).order_by('-application_count', '-view_count')[:10]
    
    # Opportunities by country
    opp_by_country = Opportunity.objects.filter(
        status='published',
        country__isnull=False
    ).values('country').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Upcoming deadlines
    upcoming_deadlines = Opportunity.objects.filter(
        status='published',
        application_deadline__gte=timezone.now(),
        application_deadline__lte=timezone.now() + timedelta(days=30)
    ).order_by('application_deadline')[:10]
    
    context = {
        'opp_stats': opp_stats,
        'opp_by_type': opp_by_type,
        'top_opportunities': top_opportunities,
        'opp_by_country': opp_by_country,
        'upcoming_deadlines': upcoming_deadlines,
        'date_range': date_range,
        'page_title': 'Opportunity Analytics - Admin',
    }
    return render(request, 'analytics/opportunities.html', context)


@login_required
@user_type_required(['admin', 'executive'])
def event_analytics(request):
    """Event analytics"""
    date_range = request.GET.get('date_range', '30')
    end_date = timezone.now()
    start_date = end_date - timedelta(days=int(date_range))
    
    # Event statistics
    event_stats = Event.objects.filter(
        status__in=['published', 'ongoing', 'completed']
    ).aggregate(
        total_events=Count('id'),
        total_attendees=Sum('current_attendees'),
        total_registrations=Sum('registration_count'),
        total_views=Sum('view_count'),
        avg_attendees=Avg('current_attendees'),
        avg_registrations=Avg('registration_count')
    )
    
    # Events by type
    event_by_type = Event.objects.values('event_type').annotate(
        count=Count('id'),
        total_attendees=Sum('current_attendees')
    ).order_by('-count')
    
    # Upcoming events
    upcoming_events = Event.objects.filter(
        start_date__gte=timezone.now(),
        status__in=['published', 'ongoing']
    ).order_by('start_date')[:10]
    
    # Past events performance
    past_events = Event.objects.filter(
        end_date__lt=timezone.now(),
        status='completed'
    ).order_by('-end_date')[:10]
    
    # Registration trends
    registration_trends = EventRegistration.objects.filter(
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    context = {
        'event_stats': event_stats,
        'event_by_type': event_by_type,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'registration_trends': registration_trends,
        'date_range': date_range,
        'page_title': 'Event Analytics - Admin',
    }
    return render(request, 'analytics/events.html', context)


# ============================================================
# RESOURCE ANALYTICS
# ============================================================

@login_required
@user_type_required(['admin', 'executive'])
def resource_analytics(request):
    """Resource analytics"""
    date_range = request.GET.get('date_range', '30')
    end_date = timezone.now()
    start_date = end_date - timedelta(days=int(date_range))
    
    # Resource statistics
    resource_stats = Resource.objects.filter(
        is_published=True
    ).aggregate(
        total_resources=Count('id'),
        total_downloads=Sum('download_count'),
        total_views=Sum('view_count'),
        avg_downloads=Avg('download_count'),
        avg_views=Avg('view_count'),
        avg_rating=Avg('average_rating')
    )
    
    # Resources by type
    resource_by_type = Resource.objects.filter(
        is_published=True
    ).values('resource_type').annotate(
        count=Count('id'),
        total_downloads=Sum('download_count'),
        total_views=Sum('view_count')
    ).order_by('-count')
    
    # Top resources
    top_resources = Resource.objects.filter(
        is_published=True
    ).order_by('-download_count', '-view_count')[:10]
    
    # Resource downloads trend
    download_trends = ResourceDownload.objects.filter(
        downloaded_at__gte=start_date
    ).annotate(
        date=TruncDate('downloaded_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Resources by access type
    access_types = Resource.objects.filter(
        is_published=True
    ).values('access_type').annotate(
        count=Count('id')
    )
    
    context = {
        'resource_stats': resource_stats,
        'resource_by_type': resource_by_type,
        'top_resources': top_resources,
        'download_trends': download_trends,
        'access_types': access_types,
        'date_range': date_range,
        'page_title': 'Resource Analytics - Admin',
    }
    return render(request, 'analytics/resources.html', context)


# ============================================================
# CAMPAIGN ANALYTICS
# ============================================================

@login_required
@user_type_required(['admin', 'executive'])
def campaign_analytics(request):
    """Campaign analytics"""
    campaigns = CampaignAnalytics.objects.all().order_by('-sent_at', '-created_at')
    
    # Filters
    campaign_type = request.GET.get('campaign_type')
    if campaign_type:
        campaigns = campaigns.filter(campaign_type=campaign_type)
    
    paginator = Paginator(campaigns, 20)
    page = request.GET.get('page', 1)
    
    try:
        campaigns = paginator.page(page)
    except PageNotAnInteger:
        campaigns = paginator.page(1)
    except EmptyPage:
        campaigns = paginator.page(paginator.num_pages)
    
    # Summary statistics
    total_campaigns = campaigns.count()
    avg_open_rate = campaigns.aggregate(Avg('open_rate'))['open_rate__avg'] or 0
    avg_click_rate = campaigns.aggregate(Avg('click_rate'))['click_rate__avg'] or 0
    
    context = {
        'campaigns': campaigns,
        'total_campaigns': total_campaigns,
        'avg_open_rate': avg_open_rate,
        'avg_click_rate': avg_click_rate,
        'campaign_types': CampaignAnalytics.CAMPAIGN_TYPES,
        'page_title': 'Campaign Analytics - Admin',
    }
    return render(request, 'analytics/campaigns.html', context)


@login_required
@user_type_required(['admin', 'executive'])
def campaign_detail(request, campaign_id):
    """Campaign detail"""
    campaign = get_object_or_404(CampaignAnalytics, id=campaign_id)
    
    context = {
        'campaign': campaign,
        'page_title': f'Campaign: {campaign.campaign_name}',
    }
    return render(request, 'analytics/campaign_detail.html', context)


# ============================================================
# EXPORT ANALYTICS
# ============================================================

@login_required
@user_type_required(['admin', 'executive'])
def export_analytics(request, data_type):
    """Export analytics data"""
    date_range = request.GET.get('date_range', '30')
    end_date = timezone.now()
    start_date = end_date - timedelta(days=int(date_range))
    
    if data_type == 'users':
        data = export_user_data(start_date, end_date)
        filename = f'users_analytics_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
    elif data_type == 'content':
        data = export_content_data(start_date, end_date)
        filename = f'content_analytics_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
    elif data_type == 'opportunities':
        data = export_opportunity_data(start_date, end_date)
        filename = f'opportunities_analytics_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
    elif data_type == 'events':
        data = export_event_data(start_date, end_date)
        filename = f'events_analytics_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
    elif data_type == 'resources':
        data = export_resource_data(start_date, end_date)
        filename = f'resources_analytics_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
    else:
        messages.error(request, 'Invalid export type.')
        return redirect('analytics:dashboard')
    
    response = HttpResponse(data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ============================================================
# AJAX ENDPOINTS
# ============================================================

@login_required
@user_type_required(['admin', 'executive'])
def get_analytics_chart_data(request):
    """Get chart data for AJAX requests"""
    chart_type = request.GET.get('chart_type')
    date_range = request.GET.get('date_range', '30')
    end_date = timezone.now()
    start_date = end_date - timedelta(days=int(date_range))
    
    data = {}
    
    if chart_type == 'user_growth':
        data = get_user_growth_data(start_date, end_date)
    elif chart_type == 'content_activity':
        data = get_content_activity_data(start_date, end_date)
    elif chart_type == 'engagement':
        data = get_engagement_data(start_date, end_date)
    elif chart_type == 'popular_content':
        data = get_popular_content_data(start_date, end_date)
    
    return JsonResponse(data)


@login_required
@user_type_required(['admin', 'executive'])
def get_realtime_stats(request):
    """Get real-time statistics"""
    now = timezone.now()
    today = now.date()
    
    stats = {
        'today_users': User.objects.filter(date_joined__date=today).count(),
        'today_visits': PageView.objects.filter(created_at__date=today).count(),
        'today_posts': CommunityPost.objects.filter(created_at__date=today).count(),
        'today_registrations': Member.objects.filter(created_at__date=today).count(),
        'online_users': UserActivityLog.objects.filter(
            created_at__gte=now - timedelta(minutes=15)
        ).values('user').distinct().count(),
        'total_users': User.objects.filter(is_active=True).count(),
        'total_members': Member.objects.filter(verification_status='verified').count(),
    }
    
    return JsonResponse(stats)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_analytics_data(start_date, end_date):
    """Get comprehensive analytics data"""
    return {
        'users': {
            'total': User.objects.filter(is_active=True).count(),
            'new': User.objects.filter(date_joined__gte=start_date).count(),
            'active': UserActivityLog.objects.filter(
                created_at__gte=start_date
            ).values('user').distinct().count(),
        },
        'members': {
            'total': Member.objects.count(),
            'verified': Member.objects.filter(verification_status='verified').count(),
            'pending': Member.objects.filter(verification_status='pending').count(),
            'new': Member.objects.filter(created_at__gte=start_date).count(),
        },
        'communities': {
            'total': Community.objects.filter(is_active=True).count(),
            'members': CommunityMember.objects.filter(
                joined_at__gte=start_date
            ).count(),
            'posts': CommunityPost.objects.filter(
                created_at__gte=start_date,
                status__in=['published', 'pinned']
            ).count(),
        },
        'opportunities': {
            'total': Opportunity.objects.filter(status='published').count(),
            'applications': Opportunity.objects.filter(
                created_at__gte=start_date
            ).aggregate(Sum('application_count'))['application_count__sum'] or 0,
            'new': Opportunity.objects.filter(
                created_at__gte=start_date,
                status='published'
            ).count(),
        },
        'events': {
            'total': Event.objects.filter(status__in=['published', 'ongoing']).count(),
            'registrations': EventRegistration.objects.filter(
                created_at__gte=start_date
            ).count(),
            'upcoming': Event.objects.filter(
                start_date__gte=timezone.now(),
                status__in=['published', 'ongoing']
            ).count(),
        },
        'resources': {
            'total': Resource.objects.filter(is_published=True).count(),
            'downloads': ResourceDownload.objects.filter(
                downloaded_at__gte=start_date
            ).count(),
            'new': Resource.objects.filter(
                created_at__gte=start_date,
                is_published=True
            ).count(),
        }
    }


def get_charts_data(start_date, end_date):
    """Get chart data for visualizations"""
    return {
        'user_growth': get_user_growth_data(start_date, end_date),
        'content_activity': get_content_activity_data(start_date, end_date),
        'engagement': get_engagement_data(start_date, end_date),
        'popular_content': get_popular_content_data(start_date, end_date),
    }


def get_user_growth_data(start_date, end_date):
    """Get user growth data for charts"""
    # Daily user growth
    daily_growth = User.objects.filter(
        date_joined__gte=start_date
    ).annotate(
        date=TruncDate('date_joined')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Monthly user growth
    monthly_growth = User.objects.filter(
        date_joined__gte=start_date
    ).annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    return {
        'daily': list(daily_growth),
        'monthly': list(monthly_growth),
    }


def get_content_activity_data(start_date, end_date):
    """Get content activity data for charts"""
    # Daily posts
    daily_posts = CommunityPost.objects.filter(
        created_at__gte=start_date,
        status__in=['published', 'pinned']
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Daily comments
    daily_comments = Comment.objects.filter(
        created_at__gte=start_date,
        is_approved=True,
        is_deleted=False
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Content by type
    content_by_type = CommunityPost.objects.filter(
        status__in=['published', 'pinned']
    ).values('post_type').annotate(
        count=Count('id')
    )
    
    return {
        'daily_posts': list(daily_posts),
        'daily_comments': list(daily_comments),
        'content_by_type': list(content_by_type),
    }


def get_engagement_data(start_date, end_date):
    """Get engagement data for charts"""
    # Engagement by user type
    engagement_by_type = UserActivityAnalytics.objects.filter(
        date__gte=start_date.date()
    ).values('user__user_type').annotate(
        avg_engagement=Avg('engagement_score'),
        total_engagement=Sum('engagement_score')
    )
    
    # Engagement trends
    engagement_trends = UserActivityAnalytics.objects.filter(
        date__gte=start_date.date()
    ).annotate(
        week=TruncWeek('date')
    ).values('week').annotate(
        avg_engagement=Avg('engagement_score'),
        total_engagement=Sum('engagement_score')
    ).order_by('week')
    
    return {
        'by_type': list(engagement_by_type),
        'trends': list(engagement_trends),
    }


def get_popular_content_data(start_date, end_date):
    """Get popular content data for charts"""
    # Popular communities
    popular_communities = Community.objects.filter(
        is_active=True
    ).order_by('-member_count')[:10].values('name', 'member_count')
    
    # Popular posts
    popular_posts = CommunityPost.objects.filter(
        status__in=['published', 'pinned']
    ).order_by('-like_count', '-comment_count')[:10].values('title', 'like_count', 'comment_count')
    
    # Popular resources
    popular_resources = Resource.objects.filter(
        is_published=True
    ).order_by('-download_count')[:10].values('title', 'download_count', 'view_count')
    
    return {
        'communities': list(popular_communities),
        'posts': list(popular_posts),
        'resources': list(popular_resources),
    }


def export_user_data(start_date, end_date):
    """Export user analytics data"""
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Date', 'New Users', 'Active Users', 'Total Users',
        'New Members', 'Verified Members', 'Total Members'
    ])
    
    # Get daily data
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.date())
        current += timedelta(days=1)
    
    for date in dates:
        new_users = User.objects.filter(date_joined__date=date).count()
        active_users = UserActivityLog.objects.filter(
            created_at__date=date
        ).values('user').distinct().count()
        total_users = User.objects.filter(date_joined__lte=date).count()
        
        new_members = Member.objects.filter(created_at__date=date).count()
        verified_members = Member.objects.filter(
            verification_status='verified',
            created_at__lte=date
        ).count()
        total_members = Member.objects.filter(created_at__lte=date).count()
        
        writer.writerow([
            date.strftime('%Y-%m-%d'),
            new_users,
            active_users,
            total_users,
            new_members,
            verified_members,
            total_members
        ])
    
    return output.getvalue()


def export_content_data(start_date, end_date):
    """Export content analytics data"""
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Date', 'New Posts', 'New Comments', 'New Communities',
        'Total Posts', 'Total Comments', 'Total Communities'
    ])
    
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.date())
        current += timedelta(days=1)
    
    for date in dates:
        new_posts = CommunityPost.objects.filter(
            created_at__date=date,
            status__in=['published', 'pinned']
        ).count()
        
        new_comments = Comment.objects.filter(
            created_at__date=date,
            is_approved=True,
            is_deleted=False
        ).count()
        
        new_communities = Community.objects.filter(
            created_at__date=date,
            is_active=True
        ).count()
        
        total_posts = CommunityPost.objects.filter(
            status__in=['published', 'pinned'],
            created_at__lte=date
        ).count()
        
        total_comments = Comment.objects.filter(
            is_approved=True,
            is_deleted=False,
            created_at__lte=date
        ).count()
        
        total_communities = Community.objects.filter(
            is_active=True,
            created_at__lte=date
        ).count()
        
        writer.writerow([
            date.strftime('%Y-%m-%d'),
            new_posts,
            new_comments,
            new_communities,
            total_posts,
            total_comments,
            total_communities
        ])
    
    return output.getvalue()


def export_opportunity_data(start_date, end_date):
    """Export opportunity analytics data"""
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Opportunity', 'Type', 'Posted Date', 'Deadline',
        'Views', 'Applications', 'Status'
    ])
    
    opportunities = Opportunity.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    for opp in opportunities:
        writer.writerow([
            opp.title[:100],
            opp.opportunity_type,
            opp.created_at.strftime('%Y-%m-%d'),
            opp.application_deadline.strftime('%Y-%m-%d') if opp.application_deadline else 'N/A',
            opp.view_count,
            opp.application_count,
            opp.status
        ])
    
    return output.getvalue()


def export_event_data(start_date, end_date):
    """Export event analytics data"""
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Event', 'Type', 'Date', 'Location',
        'Attendees', 'Registrations', 'Status'
    ])
    
    events = Event.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    for event in events:
        writer.writerow([
            event.title[:100],
            event.event_type,
            event.start_date.strftime('%Y-%m-%d'),
            event.venue or 'Virtual',
            event.current_attendees,
            event.registration_count,
            event.status
        ])
    
    return output.getvalue()


def export_resource_data(start_date, end_date):
    """Export resource analytics data"""
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Resource', 'Type', 'Added Date',
        'Views', 'Downloads', 'Rating'
    ])
    
    resources = Resource.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        is_published=True
    )
    
    for resource in resources:
        writer.writerow([
            resource.title[:100],
            resource.resource_type,
            resource.created_at.strftime('%Y-%m-%d'),
            resource.view_count,
            resource.download_count,
            resource.average_rating or 0
        ])
    
    return output.getvalue()
