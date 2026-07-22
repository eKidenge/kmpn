from django.db import models
from django.conf import settings
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field


class CollaborationRequest(models.Model):
    """Research collaboration requests"""
    
    COLLABORATION_TYPES = (
        ('research', 'Research Collaboration'),
        ('co_authorship', 'Co-authorship'),
        ('data_collection', 'Data Collection'),
        ('peer_review', 'Peer Review'),
        ('mentorship', 'Mentorship'),
        ('funding', 'Funding Collaboration'),
        ('equipment', 'Equipment Sharing'),
        ('training', 'Training/Workshop'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    )
    
    title = models.CharField(max_length=500)
    description = CKEditor5Field()
    collaboration_type = models.CharField(max_length=20, choices=COLLABORATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Requestor
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collaboration_requests'
    )
    
    # Target collaborators (can be specific users or open)
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='targeted_collaborations',
        blank=True
    )
    is_open = models.BooleanField(default=True)
    
    # Requirements
    required_skills = models.JSONField(default=list, blank=True)
    required_expertise = models.JSONField(default=list, blank=True)
    required_institutions = models.JSONField(default=list, blank=True)
    
    # Timeline
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    duration_weeks = models.IntegerField(null=True, blank=True)
    
    # Location
    is_remote = models.BooleanField(default=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Funding
    has_funding = models.BooleanField(default=False)
    funding_details = models.TextField(blank=True, null=True)
    
    # Attachments
    attachments = models.JSONField(default=list, blank=True)
    
    # Statistics
    view_count = models.IntegerField(default=0)
    application_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'collaboration_requests'
        verbose_name = 'Collaboration Request'
        verbose_name_plural = 'Collaboration Requests'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['collaboration_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['requested_by', 'status']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title[:50]} - {self.requested_by.email}"
    
    def is_expired(self):
        """Check if collaboration request is expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def get_applications_count(self):
        """Get total applications count"""
        return self.applications.count()


class CollaborationApplication(models.Model):
    """Applications to collaboration requests"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )
    
    collaboration = models.ForeignKey(
        CollaborationRequest,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collaboration_applications'
    )
    
    # Application Details
    cover_letter = CKEditor5Field()
    skills = models.JSONField(default=list, blank=True)
    experience = models.TextField(blank=True, null=True)
    availability = models.TextField(blank=True, null=True)
    
    # Attachments
    attachments = models.JSONField(default=list, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review_notes = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'collaboration_applications'
        verbose_name = 'Collaboration Application'
        verbose_name_plural = 'Collaboration Applications'
        unique_together = ('collaboration', 'applicant')
        indexes = [
            models.Index(fields=['collaboration', 'status']),
            models.Index(fields=['applicant']),
        ]
    
    def __str__(self):
        return f"{self.applicant.email} - {self.collaboration.title[:30]}"


class SupervisorMatching(models.Model):
    """Supervisor matching system"""
    
    MATCHING_STATUS = (
        ('pending', 'Pending'),
        ('matched', 'Matched'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    )
    
    MATCHING_TYPES = (
        ('student', 'Student Seeking Supervisor'),
        ('supervisor', 'Supervisor Seeking Student'),
        ('mutual', 'Mutual Interest'),
    )
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_matches',
        null=True,
        blank=True
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='supervisor_matches',
        null=True,
        blank=True
    )
    
    matching_type = models.CharField(max_length=20, choices=MATCHING_TYPES)
    status = models.CharField(max_length=20, choices=MATCHING_STATUS, default='pending')
    
    # Research Information
    research_area = models.CharField(max_length=255)
    research_interest = models.TextField()
    specific_topic = models.CharField(max_length=500, blank=True, null=True)
    
    # Preferences
    preferred_institution = models.CharField(max_length=255, blank=True, null=True)
    preferred_location = models.CharField(max_length=255, blank=True, null=True)
    availability_start = models.DateField(null=True, blank=True)
    
    # Matching Score (AI-generated)
    match_score = models.FloatField(null=True, blank=True)
    match_reasons = models.JSONField(default=list, blank=True)
    
    # Supervisor Availability
    supervisor_availability = models.TextField(blank=True, null=True)
    supervision_capacity = models.IntegerField(default=1)
    current_students = models.IntegerField(default=0)
    
    # Communication
    communication_history = models.JSONField(default=list, blank=True)
    last_communication = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    matched_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'supervisor_matches'
        verbose_name = 'Supervisor Match'
        verbose_name_plural = 'Supervisor Matches'
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['supervisor', 'status']),
            models.Index(fields=['match_score']),
        ]
    
    def __str__(self):
        student_name = self.student.email if self.student else 'Unknown Student'
        supervisor_name = self.supervisor.email if self.supervisor else 'Unknown Supervisor'
        return f"{student_name} - {supervisor_name}"


class CollaborationMessage(models.Model):
    """Messages within collaborations"""
    
    collaboration = models.ForeignKey(
        CollaborationRequest,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_collaboration_messages'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_collaboration_messages'
    )
    
    message = CKEditor5Field()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Attachments
    attachments = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'collaboration_messages'
        verbose_name = 'Collaboration Message'
        verbose_name_plural = 'Collaboration Messages'
        indexes = [
            models.Index(fields=['collaboration', 'created_at']),
            models.Index(fields=['sender', 'receiver']),
            models.Index(fields=['is_read']),
        ]
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.email} -> {self.receiver.email} ({self.created_at})"
    
    def mark_as_read(self):
        """Mark message as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
