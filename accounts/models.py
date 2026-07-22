from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator
import uuid

class User(AbstractUser):
    """Custom User model for KMPN"""
    
    # User Types
    USER_TYPES = (
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('executive', 'Executive'),
        ('admin', 'Administrator'),
    )
    
    # Basic Information
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True, max_length=255)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    
    # Profile Information
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='member')
    profile_picture = models.ImageField(upload_to='profiles/%Y/%m/%d/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    
    # Academic Information
    institution = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    degree_level = models.CharField(max_length=50, blank=True, null=True)
    research_interests = models.TextField(blank=True, null=True)
    
    # Verification Status
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Membership Information
    membership_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    membership_start_date = models.DateTimeField(null=True, blank=True)
    membership_expiry_date = models.DateTimeField(null=True, blank=True)
    is_active_member = models.BooleanField(default=False)
    
    # Timestamps
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # Social Media Links
    linkedin_url = models.URLField(max_length=200, blank=True, null=True)
    researchgate_url = models.URLField(max_length=200, blank=True, null=True)
    google_scholar_url = models.URLField(max_length=200, blank=True, null=True)
    orcid_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Preferences
    newsletter_subscribed = models.BooleanField(default=False)
    notification_preferences = models.JSONField(default=dict, blank=True)
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['membership_number']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['user_type']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.username})"
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
    
    def is_locked(self):
        """Check if user account is locked"""
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False
    
    def increment_login_attempts(self):
        """Increment login attempts and lock if exceeded"""
        self.login_attempts += 1
        if self.login_attempts >= 5:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
            self.save()
            return True
        self.save()
        return False
    
    def reset_login_attempts(self):
        """Reset login attempts"""
        self.login_attempts = 0
        self.locked_until = None
        self.save()
    
    def get_full_name(self):
        """Return full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_membership_status(self):
        """Get current membership status"""
        if self.is_active_member and self.membership_expiry_date:
            if timezone.now() > self.membership_expiry_date:
                self.is_active_member = False
                self.save()
                return 'expired'
            return 'active'
        return 'inactive'


class UserActivityLog(models.Model):
    """Track user activities"""
    
    ACTION_TYPES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('registration', 'Registration'),
        ('profile_update', 'Profile Update'),
        ('member_verification', 'Member Verification'),
        ('community_join', 'Community Join'),
        ('event_registration', 'Event Registration'),
        ('opportunity_apply', 'Opportunity Apply'),
        ('resource_download', 'Resource Download'),
        ('forum_post', 'Forum Post'),
        ('collaboration_request', 'Collaboration Request'),
        ('payment', 'Payment'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    action_description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    referer_url = models.URLField(max_length=500, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activity_logs'
        verbose_name = 'User Activity Log'
        verbose_name_plural = 'User Activity Logs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.action_type} at {self.created_at}"


class UserDevice(models.Model):
    """Track user devices for security"""
    
    DEVICE_TYPES = (
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    device_name = models.CharField(max_length=255)
    device_id = models.CharField(max_length=255, unique=True)
    browser = models.CharField(max_length=100, blank=True, null=True)
    browser_version = models.CharField(max_length=50, blank=True, null=True)
    os = models.CharField(max_length=100, blank=True, null=True)
    os_version = models.CharField(max_length=50, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_trusted = models.BooleanField(default=False)
    last_login = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_devices'
        verbose_name = 'User Device'
        verbose_name_plural = 'User Devices'
        indexes = [
            models.Index(fields=['user', 'device_id']),
            models.Index(fields=['last_login']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.device_name}"
