from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    """User notifications"""
    
    NOTIFICATION_TYPES = (
        ('system', 'System'),
        ('event', 'Event'),
        ('opportunity', 'Opportunity'),
        ('community', 'Community'),
        ('message', 'Message'),
        ('collaboration', 'Collaboration'),
        ('member', 'Membership'),
        ('payment', 'Payment'),
        ('reminder', 'Reminder'),
        ('alert', 'Alert'),
        ('forum', 'Forum'),
        ('resource', 'Resource'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.URLField(max_length=500, blank=True, null=True)
    
    # Related object
    content_type = models.CharField(max_length=100, blank=True, null=True)
    object_id = models.IntegerField(blank=True, null=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery
    sent_via_email = models.BooleanField(default=False)
    sent_via_sms = models.BooleanField(default=False)
    sent_via_push = models.BooleanField(default=False)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['notification_type']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title[:50]}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class NotificationPreference(models.Model):
    """User notification preferences"""
    
    CHANNEL_CHOICES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App'),
    )
    
    DIGEST_FREQUENCY = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_pref'
    )
    
    # Preferences
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)
    
    # Specific preferences
    event_notifications = models.BooleanField(default=True)
    opportunity_notifications = models.BooleanField(default=True)
    community_notifications = models.BooleanField(default=True)
    message_notifications = models.BooleanField(default=True)
    collaboration_notifications = models.BooleanField(default=True)
    membership_notifications = models.BooleanField(default=True)
    payment_notifications = models.BooleanField(default=True)
    reminder_notifications = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    quiet_hours_enabled = models.BooleanField(default=False)
    
    # Digest
    digest_enabled = models.BooleanField(default=False)
    digest_frequency = models.CharField(
        max_length=20,
        choices=DIGEST_FREQUENCY,
        default='weekly'
    )
    last_digest_sent = models.DateTimeField(null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.email}"