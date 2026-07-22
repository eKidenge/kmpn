from django.db import models
from django.conf import settings
from django.utils import timezone


class SystemLog(models.Model):
    """System activity logs"""
    
    LOG_LEVELS = (
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    )
    
    LOG_SOURCES = (
        ('system', 'System'),
        ('user', 'User'),
        ('payment', 'Payment'),
        ('email', 'Email'),
        ('cron', 'Cron'),
        ('api', 'API'),
    )
    
    level = models.CharField(max_length=20, choices=LOG_LEVELS, default='info')
    source = models.CharField(max_length=20, choices=LOG_SOURCES, default='system')
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'system_logs'
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
        indexes = [
            models.Index(fields=['level']),
            models.Index(fields=['source']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.level.upper()} - {self.source} at {self.created_at}"


class SiteSettings(models.Model):
    """Site-wide settings"""
    
    key = models.CharField(max_length=255, unique=True)
    value = models.JSONField()
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=False)
    
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'site_settings'
        verbose_name = 'Site Setting'
        verbose_name_plural = 'Site Settings'
    
    def __str__(self):
        return self.key


class Announcement(models.Model):
    """Site announcements"""
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    title = models.CharField(max_length=255)
    content = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='low')
    
    # Display options
    show_on_homepage = models.BooleanField(default=True)
    show_on_dashboard = models.BooleanField(default=True)
    show_to_all = models.BooleanField(default=True)
    target_audience = models.JSONField(default=list, blank=True)  # User types or groups
    
    # Schedule
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_announcements'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'announcements'
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def is_current(self):
        """Check if announcement is current"""
        now = timezone.now()
        if self.end_date:
            return self.start_date <= now <= self.end_date
        return self.start_date <= now


class DashboardWidget(models.Model):
    """Custom dashboard widgets"""
    
    WIDGET_TYPES = (
        ('stat', 'Statistics'),
        ('chart', 'Chart'),
        ('table', 'Table'),
        ('list', 'List'),
        ('calendar', 'Calendar'),
        ('activity', 'Activity Feed'),
        ('custom', 'Custom'),
    )
    
    title = models.CharField(max_length=255)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    configuration = models.JSONField(default=dict)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Visibility
    visible_to = models.JSONField(default=list, blank=True)  # User types
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_widgets'
        verbose_name = 'Dashboard Widget'
        verbose_name_plural = 'Dashboard Widgets'
        ordering = ['order']
    
    def __str__(self):
        return self.title
