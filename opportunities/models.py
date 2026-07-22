from django.db import models
from django.conf import settings
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field


class Opportunity(models.Model):
    """Opportunities (scholarships, jobs, grants, etc.)"""
    
    OPPORTUNITY_TYPES = (
        ('scholarship', 'Scholarship'),
        ('phd_position', 'PhD Position'),
        ('masters_position', 'Master\'s Position'),
        ('postdoc', 'Postdoctoral Fellowship'),
        ('conference', 'Conference'),
        ('call_for_papers', 'Call for Papers'),
        ('grant', 'Grant'),
        ('job', 'Job'),
        ('internship', 'Internship'),
        ('training', 'Training/Workshop'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('expired', 'Expired'),
        ('archived', 'Archived'),
    )
    
    # Basic Information
    title = models.CharField(max_length=500)
    description = CKEditor5Field()
    opportunity_type = models.CharField(max_length=20, choices=OPPORTUNITY_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Organization
    organization_name = models.CharField(max_length=255)
    organization_website = models.URLField(max_length=500, blank=True, null=True)
    organization_logo = models.ImageField(upload_to='opportunities/logos/%Y/%m/%d/', blank=True, null=True)
    
    # Location
    location = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    is_remote = models.BooleanField(default=False)
    
    # Dates
    posted_date = models.DateTimeField(auto_now_add=True)
    application_deadline = models.DateTimeField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Financial
    has_funding = models.BooleanField(default=False)
    funding_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='KES')
    funding_details = models.TextField(blank=True, null=True)
    
    # Eligibility
    eligibility_criteria = CKEditor5Field(blank=True, null=True)
    required_qualifications = CKEditor5Field(blank=True, null=True)
    preferred_qualifications = CKEditor5Field(blank=True, null=True)
    
    # Requirements
    application_requirements = CKEditor5Field(blank=True, null=True)
    required_documents = models.JSONField(default=list, blank=True)
    
    # Application
    application_url = models.URLField(max_length=500, blank=True, null=True)
    application_email = models.EmailField(blank=True, null=True)
    application_instructions = CKEditor5Field(blank=True, null=True)
    
    # Contact
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=50, blank=True, null=True)
    
    # Tags
    tags = models.JSONField(default=list, blank=True)
    disciplines = models.JSONField(default=list, blank=True)
    
    # Statistics
    view_count = models.IntegerField(default=0)
    application_count = models.IntegerField(default=0)
    save_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_opportunities'
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_opportunities'
    )
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'opportunities'
        verbose_name = 'Opportunity'
        verbose_name_plural = 'Opportunities'
        indexes = [
            models.Index(fields=['opportunity_type']),
            models.Index(fields=['status']),
            models.Index(fields=['application_deadline']),
            models.Index(fields=['created_at']),
            models.Index(fields=['country']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title[:100]
    
    def is_expired(self):
        """Check if opportunity is expired"""
        return timezone.now() > self.application_deadline
    
    def get_days_remaining(self):
        """Get days remaining until deadline"""
        if self.application_deadline:
            delta = self.application_deadline - timezone.now()
            return delta.days if delta.days > 0 else 0
        return 0
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        self.save()


class OpportunityApplication(models.Model):
    """Applications to opportunities"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('shortlisted', 'Shortlisted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )
    
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='opportunity_applications'
    )
    
    # Application Details
    cover_letter = CKEditor5Field(blank=True, null=True)
    message = CKEditor5Field(blank=True, null=True)
    
    # Documents
    documents = models.JSONField(default=list, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review_notes = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications_opp'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'opportunity_applications'
        verbose_name = 'Opportunity Application'
        verbose_name_plural = 'Opportunity Applications'
        unique_together = ('opportunity', 'applicant')
        indexes = [
            models.Index(fields=['opportunity', 'status']),
            models.Index(fields=['applicant']),
        ]
    
    def __str__(self):
        return f"{self.applicant.email} - {self.opportunity.title[:50]}"


class OpportunitySave(models.Model):
    """Saved opportunities"""
    
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='saves'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_opportunities'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'opportunity_saves'
        unique_together = ('opportunity', 'user')
    
    def __str__(self):
        return f"{self.user.email} saved {self.opportunity.title[:50]}"
