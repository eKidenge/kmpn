from django.db import models
from django.conf import settings
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field


class ResourceCategory(models.Model):
    """Resource categories"""
    
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=100, blank=True, null=True)
    
    # Ordering
    order = models.IntegerField(default=0)
    
    # Statistics
    resource_count = models.IntegerField(default=0)
    
    # Parent category (for hierarchy)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'resource_categories'
        verbose_name = 'Resource Category'
        verbose_name_plural = 'Resource Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Resource(models.Model):
    """Academic resources"""
    
    RESOURCE_TYPES = (
        ('guide', 'Guide'),
        ('template', 'Template'),
        ('tutorial', 'Tutorial'),
        ('tool', 'Tool'),
        ('dataset', 'Dataset'),
        ('ebook', 'E-Book'),
        ('presentation', 'Presentation'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('other', 'Other'),
    )
    
    ACCESS_TYPES = (
        ('public', 'Public'),
        ('members_only', 'Members Only'),
        ('premium', 'Premium'),
    )
    
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=500, unique=True)
    description = CKEditor5Field()
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES, default='public')
    
    # Categories
    categories = models.ManyToManyField(ResourceCategory, related_name='resources')
    
    # File Information
    file = models.FileField(upload_to='resources/files/%Y/%m/%d/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='resources/covers/%Y/%m/%d/', blank=True, null=True)
    file_size = models.CharField(max_length=50, blank=True, null=True)
    file_type = models.CharField(max_length=100, blank=True, null=True)
    
    # External Link
    external_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Content
    content = CKEditor5Field(blank=True, null=True)
    
    # Metadata
    author = models.CharField(max_length=255, blank=True, null=True)
    author_email = models.EmailField(blank=True, null=True)
    publisher = models.CharField(max_length=255, blank=True, null=True)
    publication_date = models.DateField(null=True, blank=True)
    
    # Versioning
    version = models.CharField(max_length=20, default='1.0')
    is_latest_version = models.BooleanField(default=True)
    
    # Keywords
    keywords = models.JSONField(default=list, blank=True)
    
    # Statistics
    view_count = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    rating_count = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    
    # Status
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Timestamps
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_resources'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'resources'
        verbose_name = 'Resource'
        verbose_name_plural = 'Resources'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['resource_type']),
            models.Index(fields=['access_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_featured']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title[:100]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        self.save()
    
    def increment_download_count(self):
        """Increment download count"""
        self.download_count += 1
        self.save()


class ResourceRating(models.Model):
    """Ratings for resources"""
    
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    review = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'resource_ratings'
        unique_together = ('resource', 'user')
    
    def __str__(self):
        return f"{self.user.email} - {self.rating} - {self.resource.title[:50]}"


class ResourceDownload(models.Model):
    """Track resource downloads"""
    
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='downloads')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    downloaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'resource_downloads'
        indexes = [
            models.Index(fields=['resource', 'downloaded_at']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.email} downloaded {self.resource.title[:50]} at {self.downloaded_at}"
