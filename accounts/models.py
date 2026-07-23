# accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid


# ============================================================
# HELPER FUNCTIONS FOR DEFAULT VALUES (MUST BE TOP-LEVEL)
# ============================================================

def default_notification_preferences():
    return {
        'email_notifications': True,
        'event_reminders': True,
        'opportunity_alerts': True,
        'community_updates': True,
        'research_matching': True,
        'mentorship_alerts': True,
    }


def default_research_keywords():
    return []


def default_mentor_areas():
    return []


def default_collaboration_interests():
    return []


def default_collaboration_preferences():
    return {}


def default_security_questions():
    return {}


class User(AbstractUser):
    """Custom User model for KPSN - Role-Based Registration"""
    
    # ============================================================
    # USER ROLES
    # ============================================================
    class Roles(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Administrator'
        ADMIN = 'admin', 'Administrator'
        EXECUTIVE = 'executive', 'Executive Committee'
        MODERATOR = 'moderator', 'Community Moderator'
        VERIFIED_MEMBER = 'verified_member', 'Verified Member'
        BASIC_MEMBER = 'basic_member', 'Basic Member'
        PROSPECTIVE_MEMBER = 'prospective_member', 'Prospective Member'
        ALUMNI = 'alumni', 'Alumni'
        RESEARCHER = 'researcher', 'Researcher'
        PARTNER = 'partner', 'Institutional Partner'
        GUEST = 'guest', 'Guest'
    
    # ============================================================
    # REGISTRATION STATUS
    # ============================================================
    class RegistrationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        SUSPENDED = 'suspended', 'Suspended'
        BANNED = 'banned', 'Banned'
        REQUIRES_VERIFICATION = 'requires_verification', 'Requires Verification'
    
    # ============================================================
    # ACADEMIC LEVELS
    # ============================================================
    class AcademicLevel(models.TextChoices):
        MASTERS = 'masters', "Master's Student"
        PHD = 'phd', 'PhD Candidate'
        POSTDOC = 'postdoc', 'Postdoctoral Researcher'
        EARLY_CAREER = 'early_career', 'Early Career Researcher'
        SENIOR_RESEARCHER = 'senior_researcher', 'Senior Researcher'
        PROFESSOR = 'professor', 'Professor'
        OTHER = 'other', 'Other'
    
    # ============================================================
    # BASIC INFORMATION
    # ============================================================
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True, max_length=255)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    
    # ============================================================
    # ROLE & REGISTRATION
    # ============================================================
    role = models.CharField(
        max_length=30,
        choices=Roles.choices,
        default=Roles.BASIC_MEMBER
    )
    registration_status = models.CharField(
        max_length=30,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.PENDING
    )
    
    # ============================================================
    # PROFILE INFORMATION
    # ============================================================
    profile_picture = models.ImageField(upload_to='profiles/%Y/%m/%d/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    
    # ============================================================
    # ACADEMIC INFORMATION
    # ============================================================
    academic_level = models.CharField(
        max_length=30,
        choices=AcademicLevel.choices,
        blank=True,
        null=True
    )
    institution = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    research_interests = models.TextField(blank=True, null=True)
    research_keywords = models.JSONField(default=default_research_keywords, blank=True)
    
    # ============================================================
    # VERIFICATION
    # ============================================================
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    id_document = models.FileField(upload_to='documents/ids/%Y/%m/%d/', blank=True, null=True)
    id_document_verified = models.BooleanField(default=False)
    institutional_email_verified = models.BooleanField(default=False)
    
    # ============================================================
    # MEMBERSHIP
    # ============================================================
    membership_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    membership_start_date = models.DateTimeField(null=True, blank=True)
    membership_expiry_date = models.DateTimeField(null=True, blank=True)
    is_active_member = models.BooleanField(default=False)
    membership_fee_paid = models.BooleanField(default=False)
    membership_fee_paid_at = models.DateTimeField(null=True, blank=True)
    
    # ============================================================
    # ROLE-SPECIFIC FIELDS
    # ============================================================
    executive_position = models.CharField(max_length=100, blank=True, null=True)
    executive_tenure_start = models.DateField(null=True, blank=True)
    executive_tenure_end = models.DateField(null=True, blank=True)
    partner_organization = models.CharField(max_length=255, blank=True, null=True)
    partner_type = models.CharField(max_length=100, blank=True, null=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    current_position = models.CharField(max_length=255, blank=True, null=True)
    publication_count = models.IntegerField(default=0)
    citation_count = models.IntegerField(default=0)
    h_index = models.IntegerField(default=0)
    
    # ============================================================
    # SOCIAL MEDIA
    # ============================================================
    linkedin_url = models.URLField(max_length=200, blank=True, null=True)
    researchgate_url = models.URLField(max_length=200, blank=True, null=True)
    google_scholar_url = models.URLField(max_length=200, blank=True, null=True)
    orcid_id = models.CharField(max_length=50, blank=True, null=True)
    twitter_url = models.URLField(max_length=200, blank=True, null=True)
    website_url = models.URLField(max_length=200, blank=True, null=True)
    
    # ============================================================
    # PREFERENCES
    # ============================================================
    newsletter_subscribed = models.BooleanField(default=False)
    notification_preferences = models.JSONField(default=default_notification_preferences, blank=True)
    language_preference = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')
    
    # ============================================================
    # MENTORSHIP
    # ============================================================
    is_mentor = models.BooleanField(default=False)
    mentor_areas = models.JSONField(default=default_mentor_areas, blank=True)
    is_mentee = models.BooleanField(default=False)
    mentee_goals = models.TextField(blank=True, null=True)
    mentor_id = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mentees',
        limit_choices_to={'is_mentor': True}
    )
    
    # ============================================================
    # COLLABORATION
    # ============================================================
    collaboration_interests = models.JSONField(default=default_collaboration_interests, blank=True)
    available_for_collaboration = models.BooleanField(default=False)
    collaboration_preferences = models.JSONField(default=default_collaboration_preferences, blank=True)
    
    # ============================================================
    # SECURITY
    # ============================================================
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=255, blank=True, null=True)
    security_questions = models.JSONField(default=default_security_questions, blank=True)
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    # ============================================================
    # META
    # ============================================================
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['membership_number']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['role']),
            models.Index(fields=['registration_status']),
            models.Index(fields=['academic_level']),
            models.Index(fields=['is_active_member']),
            models.Index(fields=['created_at']),
        ]
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email}) - {self.get_role_display()}"
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        if not self.membership_number:
            self.membership_number = self.generate_membership_number()
        super().save(*args, **kwargs)
    
    def generate_membership_number(self):
        import random
        import string
        prefix = "KPSN"
        year = str(timezone.now().year)
        random_digits = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}{year}{random_digits}"
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_short_name(self):
        if self.first_name:
            return self.first_name
        return self.username
    
    def is_locked(self):
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False
    
    def increment_login_attempts(self):
        self.login_attempts += 1
        if self.login_attempts >= 5:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
            self.save()
            return True
        self.save()
        return False
    
    def reset_login_attempts(self):
        self.login_attempts = 0
        self.locked_until = None
        self.save()
    
    def get_membership_status(self):
        if self.is_active_member and self.membership_expiry_date:
            if timezone.now() > self.membership_expiry_date:
                self.is_active_member = False
                self.save()
                return 'expired'
            return 'active'
        return 'inactive'
    
    def has_role(self, role):
        role_hierarchy = {
            'super_admin': 10,
            'admin': 9,
            'executive': 8,
            'moderator': 7,
            'verified_member': 6,
            'basic_member': 5,
            'prospective_member': 4,
            'researcher': 3,
            'alumni': 3,
            'partner': 3,
            'guest': 1,
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(role, 0)


# ============================================================
# USER ACTIVITY LOG
# ============================================================

class UserActivityLog(models.Model):
    ACTION_TYPES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('registration', 'Registration'),
        ('profile_update', 'Profile Update'),
        ('role_change', 'Role Change'),
        ('member_verification', 'Member Verification'),
        ('community_join', 'Community Join'),
        ('event_registration', 'Event Registration'),
        ('opportunity_apply', 'Opportunity Apply'),
        ('resource_download', 'Resource Download'),
        ('forum_post', 'Forum Post'),
        ('collaboration_request', 'Collaboration Request'),
        ('payment', 'Payment'),
        ('mentorship_request', 'Mentorship Request'),
        ('report_submitted', 'Report Submitted'),
        ('profile_view', 'Profile View'),
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


# ============================================================
# USER DEVICE
# ============================================================

class UserDevice(models.Model):
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


# ============================================================
# REGISTRATION APPLICATION
# ============================================================

class RegistrationApplication(models.Model):
    class ApplicationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        UNDER_REVIEW = 'under_review', 'Under Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        NEEDS_INFO = 'needs_info', 'Needs More Information'
    
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='registration_application')
    requested_role = models.CharField(max_length=30, choices=User.Roles.choices)
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, default=ApplicationStatus.PENDING)
    
    motivation = models.TextField()
    experience = models.TextField(blank=True, null=True)
    publications = models.TextField(blank=True, null=True)
    references = models.JSONField(default=list, blank=True)
    
    cv = models.FileField(upload_to='applications/cv/%Y/%m/%d/', blank=True, null=True)
    recommendation_letter = models.FileField(upload_to='applications/recommendations/%Y/%m/%d/', blank=True, null=True)
    additional_documents = models.FileField(upload_to='applications/additional/%Y/%m/%d/', blank=True, null=True)
    
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registration_applications_reviewed'
    )
    review_notes = models.TextField(blank=True, null=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'registration_applications'
        verbose_name = 'Registration Application'
        verbose_name_plural = 'Registration Applications'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['requested_role']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.requested_role} ({self.status})"


# ============================================================
# ROLE CHANGE REQUEST
# ============================================================

class RoleChangeRequest(models.Model):
    class RequestStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_change_requests')
    requested_role = models.CharField(max_length=30, choices=User.Roles.choices)
    current_role = models.CharField(max_length=30, choices=User.Roles.choices)
    reason = models.TextField()
    supporting_documents = models.FileField(upload_to='role_changes/%Y/%m/%d/', blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='role_change_requests_reviewed'
    )
    review_notes = models.TextField(blank=True, null=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'role_change_requests'
        verbose_name = 'Role Change Request'
        verbose_name_plural = 'Role Change Requests'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email}: {self.current_role} -> {self.requested_role}"