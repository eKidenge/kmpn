from django.db import models
from django.conf import settings
from django.utils import timezone


class PageView(models.Model):
    """Track page views"""
    
    page_url = models.CharField(max_length=500)
    page_title = models.CharField(max_length=500, blank=True, null=True)
    referer_url = models.CharField(max_length=500, blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    session_id = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    device_type = models.CharField(max_length=50, blank=True, null=True)
    browser = models.CharField(max_length=100, blank=True, null=True)
    os = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    time_on_page = models.IntegerField(default=0)  # Seconds
    scroll_depth = models.IntegerField(default=0)  # Percentage
    bounce = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_pageviews'
        verbose_name = 'Page View'
        verbose_name_plural = 'Page Views'
        indexes = [
            models.Index(fields=['page_url']),
            models.Index(fields=['created_at']),
            models.Index(fields=['session_id']),
        ]
    
    def __str__(self):
        return f"{self.page_url} at {self.created_at}"


class UserActivityAnalytics(models.Model):
    """User activity analytics"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    
    # Activity counts
    logins = models.IntegerField(default=0)
    profile_views = models.IntegerField(default=0)
    content_views = models.IntegerField(default=0)
    interactions = models.IntegerField(default=0)
    posts_created = models.IntegerField(default=0)
    comments_made = models.IntegerField(default=0)
    collaborations_joined = models.IntegerField(default=0)
    opportunities_applied = models.IntegerField(default=0)
    events_attended = models.IntegerField(default=0)
    resources_downloaded = models.IntegerField(default=0)
    
    # Time metrics
    total_time_spent = models.IntegerField(default=0)  # Seconds
    average_session_length = models.IntegerField(default=0)  # Seconds
    last_active = models.DateTimeField(null=True, blank=True)
    
    # Engagement metrics
    engagement_score = models.IntegerField(default=0)
    community_score = models.IntegerField(default=0)
    research_score = models.IntegerField(default=0)
    
    # Activity streaks
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    
    # Timestamps
    date = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_user_activity'
        verbose_name = 'User Activity Analytics'
        verbose_name_plural = 'User Activity Analytics'
        unique_together = ('user', 'date')
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['engagement_score']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.date}"
    
    def update_engagement_score(self):
        """Calculate engagement score"""
        score = 0
        
        # Add points for different activities
        score += self.logins * 1
        score += self.profile_views * 0.5
        score += self.content_views * 0.5
        score += self.interactions * 2
        score += self.posts_created * 5
        score += self.comments_made * 3
        score += self.collaborations_joined * 4
        score += self.opportunities_applied * 3
        score += self.events_attended * 4
        score += self.resources_downloaded * 2
        
        self.engagement_score = score
        self.save()
        return score


class CampaignAnalytics(models.Model):
    """Email and campaign analytics"""
    
    CAMPAIGN_TYPES = (
        ('email', 'Email'),
        ('newsletter', 'Newsletter'),
        ('push', 'Push Notification'),
        ('sms', 'SMS'),
    )
    
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPES)
    campaign_name = models.CharField(max_length=255)
    subject = models.CharField(max_length=500, blank=True, null=True)
    
    # Statistics
    total_sent = models.IntegerField(default=0)
    total_delivered = models.IntegerField(default=0)
    total_opened = models.IntegerField(default=0)
    total_clicked = models.IntegerField(default=0)
    total_bounced = models.IntegerField(default=0)
    total_unsubscribed = models.IntegerField(default=0)
    total_spam = models.IntegerField(default=0)
    
    # Rates
    open_rate = models.FloatField(default=0.0)
    click_rate = models.FloatField(default=0.0)
    bounce_rate = models.FloatField(default=0.0)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'analytics_campaigns'
        verbose_name = 'Campaign Analytics'
        verbose_name_plural = 'Campaign Analytics'
        indexes = [
            models.Index(fields=['campaign_type']),
            models.Index(fields=['sent_at']),
        ]
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.campaign_name} - {self.sent_at or 'Draft'}"
    
    def calculate_rates(self):
        """Calculate open, click, and bounce rates"""
        if self.total_sent > 0:
            self.open_rate = (self.total_opened / self.total_sent) * 100
            self.click_rate = (self.total_clicked / self.total_sent) * 100
            self.bounce_rate = (self.total_bounced / self.total_sent) * 100
        else:
            self.open_rate = 0
            self.click_rate = 0
            self.bounce_rate = 0
        self.save()
