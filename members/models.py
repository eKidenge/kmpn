from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image


class Member(models.Model):
    """Member model extending user"""
    
    MEMBERSHIP_TYPES = (
        ('student', 'Student'),
        ('researcher', 'Researcher'),
        ('professional', 'Professional'),
        ('alumni', 'Alumni'),
    )
    
    VERIFICATION_STATUS = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='member_profile')
    
    # Membership Details
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_TYPES, default='student')
    membership_number = models.CharField(max_length=50, unique=True, blank=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    
    # Verification Documents
    student_id = models.ImageField(
        upload_to='members/ids/%Y/%m/%d/',
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        blank=True, null=True
    )
    admission_letter = models.FileField(
        upload_to='members/admissions/%Y/%m/%d/',
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx'])],
        blank=True, null=True
    )
    transcript = models.FileField(
        upload_to='members/transcripts/%Y/%m/%d/',
        validators=[FileExtensionValidator(['pdf'])],
        blank=True, null=True
    )
    
    # Verification Details
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_members'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True, null=True)
    
    # Digital Card
    digital_card = models.ImageField(upload_to='members/cards/%Y/%m/%d/', blank=True, null=True)
    qr_code = models.ImageField(upload_to='members/qrcodes/%Y/%m/%d/', blank=True, null=True)
    card_issued_at = models.DateTimeField(null=True, blank=True)
    card_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Academic Information
    student_id_number = models.CharField(max_length=50, blank=True, null=True)
    registration_number = models.CharField(max_length=50, blank=True, null=True)
    year_of_study = models.IntegerField(null=True, blank=True)
    expected_graduation_year = models.IntegerField(null=True, blank=True)
    
    # Thesis/Research
    thesis_title = models.CharField(max_length=500, blank=True, null=True)
    thesis_abstract = models.TextField(blank=True, null=True)
    supervisor_name = models.CharField(max_length=255, blank=True, null=True)
    supervisor_email = models.EmailField(blank=True, null=True)
    
    # Publications
    publication_count = models.IntegerField(default=0)
    citation_count = models.IntegerField(default=0)
    h_index = models.IntegerField(default=0)
    
    # Skills and Expertise
    skills = models.JSONField(default=list, blank=True)
    expertise_areas = models.JSONField(default=list, blank=True)
    programming_languages = models.JSONField(default=list, blank=True)
    research_methodologies = models.JSONField(default=list, blank=True)
    
    # Interests
    collaboration_interests = models.JSONField(default=list, blank=True)
    mentoring_interests = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'members'
        verbose_name = 'Member'
        verbose_name_plural = 'Members'
        indexes = [
            models.Index(fields=['membership_number']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['membership_type']),
            models.Index(fields=['user', 'verification_status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.membership_number or 'Pending'}"
    
    def save(self, *args, **kwargs):
        if not self.membership_number:
            self.membership_number = self.generate_membership_number()
        
        if self.verification_status == 'verified' and not self.digital_card:
            self.generate_digital_card()
            self.generate_qr_code()
        
        super().save(*args, **kwargs)
    
    def generate_membership_number(self):
        """Generate unique membership number"""
        import random
        import string
        
        year = timezone.now().year
        count = Member.objects.filter(created_at__year=year).count() + 1
        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        return f"KMPN/{year}/{str(count).zfill(5)}/{random_chars}"
    
    def generate_digital_card(self):
        """Generate digital membership card"""
        # This would use a library like Pillow to create a card image
        # For now, we'll set a placeholder
        from PIL import Image, ImageDraw, ImageFont
        import os
        
        # Create a simple card
        img = Image.new('RGB', (800, 500), color='#1a237e')
        d = ImageDraw.Draw(img)
        
        # Add text
        d.text((50, 50), "KMPN Digital Membership Card", fill=(255, 255, 255))
        d.text((50, 150), f"Name: {self.user.get_full_name()}", fill=(255, 255, 255))
        d.text((50, 200), f"Member: {self.membership_number}", fill=(255, 255, 255))
        d.text((50, 250), f"Status: {self.verification_status.upper()}", fill=(255, 255, 255))
        
        # Save the card
        self.digital_card.save(
            f"card_{self.membership_number}.png",
            File(BytesIO(img.tobytes())),
            save=False
        )
    
    def generate_qr_code(self):
        """Generate QR code for member"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # QR code data
        qr_data = {
            'member_id': self.membership_number,
            'name': self.user.get_full_name(),
            'email': self.user.email,
            'type': 'KMPN_MEMBER'
        }
        import json
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        buffer = BytesIO()
        img.save(buffer, 'PNG')
        self.qr_code.save(
            f"qr_{self.membership_number}.png",
            File(buffer),
            save=False
        )
    
    def is_verified_member(self):
        """Check if member is verified"""
        return self.verification_status == 'verified'
    
    def is_membership_active(self):
        """Check if membership is active"""
        if self.card_expires_at:
            return timezone.now() < self.card_expires_at
        return self.verification_status == 'verified'
    
    def get_membership_duration(self):
        """Get membership duration in days"""
        if self.created_at:
            return (timezone.now() - self.created_at).days
        return 0


class MemberVerificationRequest(models.Model):
    """Member verification requests"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('additional_info', 'Additional Information Required'),
    )
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='verification_requests')
    
    # Request Details
    request_type = models.CharField(max_length=50, default='initial')
    request_notes = models.TextField(blank=True, null=True)
    
    # Documents submitted
    documents = models.JSONField(default=dict, blank=True)
    
    # Review Information
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_verifications'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, null=True)
    review_decision = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'member_verification_requests'
        verbose_name = 'Member Verification Request'
        verbose_name_plural = 'Member Verification Requests'
        indexes = [
            models.Index(fields=['member', 'review_decision']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.member.user.email} - {self.review_decision}"


class MemberActivity(models.Model):
    """Track member activities"""
    
    ACTIVITY_TYPES = (
        ('login', 'Login'),
        ('profile_view', 'Profile View'),
        ('profile_update', 'Profile Update'),
        ('community_join', 'Community Join'),
        ('community_post', 'Community Post'),
        ('event_registration', 'Event Registration'),
        ('event_attendance', 'Event Attendance'),
        ('opportunity_apply', 'Opportunity Apply'),
        ('resource_download', 'Resource Download'),
        ('forum_post', 'Forum Post'),
        ('collaboration_request', 'Collaboration Request'),
        ('collaboration_accept', 'Collaboration Accept'),
        ('publication_add', 'Publication Added'),
        ('skill_update', 'Skill Updated'),
    )
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    activity_description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'member_activities'
        verbose_name = 'Member Activity'
        verbose_name_plural = 'Member Activities'
        indexes = [
            models.Index(fields=['member', 'created_at']),
            models.Index(fields=['activity_type']),
        ]
    
    def __str__(self):
        return f"{self.member.user.email} - {self.activity_type} at {self.created_at}"
