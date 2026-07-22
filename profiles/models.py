from django.db import models
from django.conf import settings
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field


class Profile(models.Model):
    """Extended member profile"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Personal Information
    title = models.CharField(max_length=100, blank=True, null=True)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=20,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('prefer_not', 'Prefer not to say')],
        blank=True, null=True
    )
    nationality = models.CharField(max_length=100, blank=True, null=True)
    country_of_residence = models.CharField(max_length=100, blank=True, null=True)
    
    # Academic Profile
    academic_bio = CKEditor5Field(blank=True, null=True)
    research_statement = CKEditor5Field(blank=True, null=True)
    teaching_interests = models.TextField(blank=True, null=True)
    
    # Professional Experience
    current_position = models.CharField(max_length=255, blank=True, null=True)
    current_employer = models.CharField(max_length=255, blank=True, null=True)
    years_of_experience = models.IntegerField(default=0)
    
    # Education History
    education = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    
    # Research Areas
    primary_research_area = models.CharField(max_length=255, blank=True, null=True)
    secondary_research_areas = models.JSONField(default=list, blank=True)
    research_keywords = models.JSONField(default=list, blank=True)
    
    # Grants and Funding
    grants_awarded = models.JSONField(default=list, blank=True)
    funding_sources = models.JSONField(default=list, blank=True)
    
    # Awards and Honors
    awards = models.JSONField(default=list, blank=True)
    honors = models.JSONField(default=list, blank=True)
    
    # Professional Memberships
    professional_memberships = models.JSONField(default=list, blank=True)
    
    # Public Profile
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('members_only', 'Members Only'),
            ('private', 'Private')
        ],
        default='public'
    )
    show_email = models.BooleanField(default=False)
    show_phone = models.BooleanField(default=False)
    
    # Profile Completion
    profile_completion = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'profiles'
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
    
    def __str__(self):
        return f"{self.user.email} - Profile"
    
    def calculate_completion(self):
        """Calculate profile completion percentage"""
        fields = [
            self.user.first_name,
            self.user.last_name,
            self.user.bio,
            self.user.institution,
            self.user.department,
            self.academic_bio,
            self.research_statement,
            self.primary_research_area,
            self.current_position,
            self.education,
            self.research_keywords,
        ]
        
        filled = sum(1 for field in fields if field)
        self.profile_completion = int((filled / len(fields)) * 100)
        self.save()
        return self.profile_completion


class ResearchInterest(models.Model):
    """Research interests model"""
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    sub_category = models.CharField(max_length=100, blank=True, null=True)
    
    # Related fields
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_interests'
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'research_interests'
        verbose_name = 'Research Interest'
        verbose_name_plural = 'Research Interests'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.name


class Publication(models.Model):
    """Member publications"""
    
    PUBLICATION_TYPES = (
        ('journal', 'Journal Article'),
        ('conference', 'Conference Paper'),
        ('book', 'Book'),
        ('book_chapter', 'Book Chapter'),
        ('thesis', 'Thesis/Dissertation'),
        ('report', 'Report'),
        ('working_paper', 'Working Paper'),
        ('preprint', 'Preprint'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('published', 'Published'),
        ('in_press', 'In Press'),
        ('under_review', 'Under Review'),
        ('draft', 'Draft'),
    )
    
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='publications',
        through='PublicationAuthor'
    )
    
    title = models.CharField(max_length=500)
    abstract = models.TextField(blank=True, null=True)
    publication_type = models.CharField(max_length=20, choices=PUBLICATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Publication Details
    journal_name = models.CharField(max_length=255, blank=True, null=True)
    journal_volume = models.CharField(max_length=50, blank=True, null=True)
    journal_issue = models.CharField(max_length=50, blank=True, null=True)
    pages = models.CharField(max_length=50, blank=True, null=True)
    doi = models.CharField(max_length=100, blank=True, null=True)
    isbn = models.CharField(max_length=20, blank=True, null=True)
    issn = models.CharField(max_length=20, blank=True, null=True)
    
    # Dates
    publication_date = models.DateField(null=True, blank=True)
    acceptance_date = models.DateField(null=True, blank=True)
    submission_date = models.DateField(null=True, blank=True)
    
    # Links
    url = models.URLField(max_length=500, blank=True, null=True)
    pdf_file = models.FileField(upload_to='publications/pdfs/%Y/%m/%d/', blank=True, null=True)
    
    # Metrics
    citation_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)
    
    # Keywords
    keywords = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'publications'
        verbose_name = 'Publication'
        verbose_name_plural = 'Publications'
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['publication_type']),
            models.Index(fields=['status']),
            models.Index(fields=['publication_date']),
        ]
        ordering = ['-publication_date', '-created_at']
    
    def __str__(self):
        return self.title[:100]
    
    def get_authors_list(self):
        """Get list of authors with order"""
        return self.publicationauthor_set.order_by('order')
    
    def get_citation(self, format='apa'):
        """Get citation in specified format"""
        # Simplified citation generator
        authors = ', '.join([author.author.get_full_name() for author in self.get_authors_list()])
        year = self.publication_date.year if self.publication_date else 'n.d.'
        return f"{authors} ({year}). {self.title}. {self.journal_name}."
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        self.save()


class PublicationAuthor(models.Model):
    """Through model for publication authors"""
    
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.IntegerField()
    corresponding_author = models.BooleanField(default=False)
    affiliation = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'publication_authors'
        unique_together = ('publication', 'author')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.author.get_full_name()} - {self.publication.title[:50]}"
