from django.db import models
from django.conf import settings
from django.utils import timezone


class Newsletter(models.Model):
    """Newsletter management"""
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )
    
    subject = models.CharField(max_length=500)
    content = models.TextField()
    html_content = models.TextField(blank=True, null=True)
    
    # Sender
    from_email = models.EmailField(default=settings.DEFAULT_FROM_EMAIL)
    reply_to = models.EmailField(blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Audience
    send_to_all = models.BooleanField(default=True)
    target_groups = models.JSONField(default=list, blank=True)
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='newsletters',
        blank=True
    )
    
    # Statistics
    total_recipients = models.IntegerField(default=0)
    delivered_count = models.IntegerField(default=0)
    opened_count = models.IntegerField(default=0)
    clicked_count = models.IntegerField(default=0)
    bounced_count = models.IntegerField(default=0)
    unsubscribed_count = models.IntegerField(default=0)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Tracking
    tracking_id = models.CharField(max_length=100, unique=True, blank=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_newsletters'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'newsletters'
        verbose_name = 'Newsletter'
        verbose_name_plural = 'Newsletters'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['scheduled_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return self.subject[:100]
    
    def save(self, *args, **kwargs):
        if not self.tracking_id:
            import uuid
            self.tracking_id = uuid.uuid4().hex[:12]
        super().save(*args, **kwargs)
    
    def get_open_rate(self):
        """Calculate open rate"""
        if self.delivered_count > 0:
            return (self.opened_count / self.delivered_count) * 100
        return 0
    
    def get_click_rate(self):
        """Calculate click rate"""
        if self.delivered_count > 0:
            return (self.clicked_count / self.delivered_count) * 100
        return 0


class NewsletterSubscriber(models.Model):
    """Newsletter subscribers"""
    
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    
    # Preferences
    subscribed = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    
    # User relationship
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='newsletter_subscriptions'
    )
    
    # Groups
    groups = models.JSONField(default=list, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    
    # Tracking
    opened_count = models.IntegerField(default=0)
    clicked_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'newsletter_subscribers'
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['subscribed']),
        ]
    
    def __str__(self):
        return self.email


class NewsletterOpen(models.Model):
    """Track newsletter opens"""
    
    newsletter = models.ForeignKey(
        Newsletter,
        on_delete=models.CASCADE,
        related_name='opens'
    )
    subscriber = models.ForeignKey(
        NewsletterSubscriber,
        on_delete=models.CASCADE,
        related_name='opens'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    
    opened_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'newsletter_opens'
        verbose_name = 'Newsletter Open'
        verbose_name_plural = 'Newsletter Opens'
        indexes = [
            models.Index(fields=['newsletter', 'subscriber']),
        ]
    
    def __str__(self):
        return f"{self.subscriber.email} opened {self.newsletter.subject[:50]}"


class NewsletterClick(models.Model):
    """Track newsletter clicks"""
    
    newsletter = models.ForeignKey(
        Newsletter,
        on_delete=models.CASCADE,
        related_name='clicks'
    )
    subscriber = models.ForeignKey(
        NewsletterSubscriber,
        on_delete=models.CASCADE,
        related_name='clicks'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    url = models.URLField(max_length=500)
    link_text = models.CharField(max_length=500, blank=True, null=True)
    
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    
    clicked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'newsletter_clicks'
        verbose_name = 'Newsletter Click'
        verbose_name_plural = 'Newsletter Clicks'
        indexes = [
            models.Index(fields=['newsletter', 'subscriber']),
        ]
    
    def __str__(self):
        return f"{self.subscriber.email} clicked {self.url[:50]}"
