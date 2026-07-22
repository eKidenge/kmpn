from django.db import models
from django.conf import settings
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field


class Event(models.Model):
    """Events and conferences"""
    
    EVENT_TYPES = (
        ('conference', 'Conference'),
        ('webinar', 'Webinar'),
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
        ('symposium', 'Symposium'),
        ('training', 'Training'),
        ('networking', 'Networking'),
        ('social', 'Social Event'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
    )
    
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500, unique=True)
    description = CKEditor5Field()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Organizer
    organizer_name = models.CharField(max_length=255)
    organizer_email = models.EmailField()
    organizer_phone = models.CharField(max_length=50, blank=True, null=True)
    organizer_website = models.URLField(max_length=500, blank=True, null=True)
    
    # Location
    is_virtual = models.BooleanField(default=False)
    venue = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    virtual_link = models.URLField(max_length=500, blank=True, null=True)
    
    # Dates and Times
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_deadline = models.DateTimeField(null=True, blank=True)
    
    # Capacity
    max_attendees = models.IntegerField(null=True, blank=True)
    current_attendees = models.IntegerField(default=0)
    
    # Registration
    requires_registration = models.BooleanField(default=True)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='KES')
    registration_link = models.URLField(max_length=500, blank=True, null=True)
    
    # Agenda
    agenda = CKEditor5Field(blank=True, null=True)
    speakers = CKEditor5Field(blank=True, null=True)
    program = CKEditor5Field(blank=True, null=True)
    
    # Media
    banner_image = models.ImageField(upload_to='events/banners/%Y/%m/%d/', blank=True, null=True)
    poster = models.ImageField(upload_to='events/posters/%Y/%m/%d/', blank=True, null=True)
    
    # Zoom Integration
    zoom_meeting_id = models.CharField(max_length=50, blank=True, null=True)
    zoom_password = models.CharField(max_length=50, blank=True, null=True)
    zoom_meeting_link = models.URLField(max_length=500, blank=True, null=True)
    
    # Recordings
    recording_url = models.URLField(max_length=500, blank=True, null=True)
    recording_file = models.FileField(upload_to='events/recordings/%Y/%m/%d/', blank=True, null=True)
    
    # Tags
    tags = models.JSONField(default=list, blank=True)
    
    # Statistics
    view_count = models.IntegerField(default=0)
    registration_count = models.IntegerField(default=0)
    attendance_count = models.IntegerField(default=0)
    
    # Timestamps
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_events'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'events'
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['event_type']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]
        ordering = ['-start_date']
    
    def __str__(self):
        return self.title[:100]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def is_past(self):
        """Check if event is past"""
        return timezone.now() > self.end_date
    
    def is_ongoing(self):
        """Check if event is ongoing"""
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    def is_upcoming(self):
        """Check if event is upcoming"""
        return timezone.now() < self.start_date
    
    def has_capacity(self):
        """Check if event has capacity"""
        if self.max_attendees:
            return self.current_attendees < self.max_attendees
        return True
    
    def get_available_slots(self):
        """Get available slots"""
        if self.max_attendees:
            return self.max_attendees - self.current_attendees
        return None
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        self.save()


class EventRegistration(models.Model):
    """Event registrations"""
    
    ATTENDANCE_STATUS = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('attended', 'Attended'),
        ('absent', 'Absent'),
        ('cancelled', 'Cancelled'),
    )
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Registration Details
    registration_date = models.DateTimeField(auto_now_add=True)
    attendance_status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS, default='pending')
    
    # Payment
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, default='pending')
    payment_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Zoom
    zoom_join_url = models.URLField(max_length=500, blank=True, null=True)
    zoom_meeting_id = models.CharField(max_length=50, blank=True, null=True)
    zoom_password = models.CharField(max_length=50, blank=True, null=True)
    
    # Certificate
    certificate_issued = models.BooleanField(default=False)
    certificate_file = models.FileField(upload_to='events/certificates/%Y/%m/%d/', blank=True, null=True)
    certificate_issued_at = models.DateTimeField(null=True, blank=True)
    
    # Feedback
    feedback_submitted = models.BooleanField(default=False)
    feedback_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    feedback_comment = models.TextField(blank=True, null=True)
    feedback_submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'event_registrations'
        verbose_name = 'Event Registration'
        verbose_name_plural = 'Event Registrations'
        unique_together = ('event', 'user')
        indexes = [
            models.Index(fields=['event', 'attendance_status']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.event.title[:50]}"
    
    def generate_certificate(self):
        """Generate attendance certificate"""
        # This would use a library like ReportLab to generate PDF
        # For now, we'll set a placeholder
        self.certificate_issued = True
        self.certificate_issued_at = timezone.now()
        self.save()
