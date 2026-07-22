from django.db import models
from django.conf import settings
from django.utils import timezone

# Note: Most models are already defined in other apps.
# The API app doesn't need its own models since it works with existing app models.
# However, if you want to store API-specific data like API keys, rate limiting, etc.
# you can add them here.

class APIAccessLog(models.Model):
    """Track API access for analytics and rate limiting"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='api_logs'
    )
    
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    response_time = models.FloatField(help_text="Response time in seconds")
    
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Request and response data (limited for privacy)
    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'api_access_logs'
        verbose_name = 'API Access Log'
        verbose_name_plural = 'API Access Logs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['status_code']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} - {self.endpoint} - {self.status_code} at {self.created_at}"


class APIToken(models.Model):
    """Extended API token model with additional features"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='api_tokens'
    )
    
    token = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, help_text="Token name for identification")
    
    # Permissions
    permissions = models.JSONField(default=dict, blank=True, help_text="Custom permissions for this token")
    
    # Expiry
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_reason = models.TextField(blank=True, null=True)
    
    # Rate limiting
    rate_limit = models.IntegerField(default=1000, help_text="Requests per day")
    requests_today = models.IntegerField(default=0)
    last_reset = models.DateTimeField(auto_now_add=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'api_tokens'
        verbose_name = 'API Token'
        verbose_name_plural = 'API Tokens'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"
    
    def is_expired(self):
        """Check if token is expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def is_valid(self):
        """Check if token is valid and not revoked"""
        return self.is_active and not self.is_revoked and not self.is_expired()
    
    def increment_requests(self):
        """Increment request count for rate limiting"""
        # Reset daily count if needed
        if timezone.now().date() != self.last_reset.date():
            self.requests_today = 0
            self.last_reset = timezone.now()
        
        self.requests_today += 1
        self.last_used = timezone.now()
        self.save()
    
    def can_make_request(self):
        """Check if token can make another request"""
        # Reset daily count if needed
        if timezone.now().date() != self.last_reset.date():
            self.requests_today = 0
            self.last_reset = timezone.now()
            self.save()
        
        return self.requests_today < self.rate_limit


class APIWebhook(models.Model):
    """Webhook configuration for external integrations"""
    
    WEBHOOK_EVENTS = (
        ('user_registered', 'User Registered'),
        ('user_verified', 'User Verified'),
        ('member_verified', 'Member Verified'),
        ('community_created', 'Community Created'),
        ('opportunity_created', 'Opportunity Created'),
        ('event_created', 'Event Created'),
        ('payment_completed', 'Payment Completed'),
        ('subscription_updated', 'Subscription Updated'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='webhooks'
    )
    
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    secret = models.CharField(max_length=255, blank=True, null=True)
    
    events = models.JSONField(default=list, help_text="List of events to trigger this webhook")
    
    # Status
    is_active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True, blank=True)
    last_response_code = models.IntegerField(null=True, blank=True)
    failure_count = models.IntegerField(default=0)
    
    # Retry settings
    retry_enabled = models.BooleanField(default=True)
    max_retries = models.IntegerField(default=3)
    retry_delay = models.IntegerField(default=300, help_text="Retry delay in seconds")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'api_webhooks'
        verbose_name = 'API Webhook'
        verbose_name_plural = 'API Webhooks'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['url']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.url}"


class APIWebhookLog(models.Model):
    """Webhook execution logs"""
    
    webhook = models.ForeignKey(
        APIWebhook,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    
    event = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    response_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    
    duration = models.FloatField(help_text="Response time in seconds")
    
    success = models.BooleanField(default=False)
    retry_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'api_webhook_logs'
        verbose_name = 'API Webhook Log'
        verbose_name_plural = 'API Webhook Logs'
        indexes = [
            models.Index(fields=['webhook', 'created_at']),
            models.Index(fields=['success']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.webhook.name} - {self.event} - {'Success' if self.success else 'Failed'}"