from django.db import models
from django.conf import settings
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field


class ForumCategory(models.Model):
    """Forum categories"""
    
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    
    # Ordering
    order = models.IntegerField(default=0)
    
    # Statistics
    thread_count = models.IntegerField(default=0)
    post_count = models.IntegerField(default=0)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    requires_moderation = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'forum_categories'
        verbose_name = 'Forum Category'
        verbose_name_plural = 'Forum Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ForumThread(models.Model):
    """Forum threads/discussions"""
    
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('pinned', 'Pinned'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
    )
    
    title = models.CharField(max_length=500)
    category = models.ForeignKey(
        ForumCategory,
        on_delete=models.CASCADE,
        related_name='threads'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forum_threads'
    )
    
    # Content
    content = CKEditor5Field()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    is_sticky = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    
    # Statistics
    view_count = models.IntegerField(default=0)
    reply_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    
    # Tags
    tags = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'forum_threads'
        verbose_name = 'Forum Thread'
        verbose_name_plural = 'Forum Threads'
        indexes = [
            models.Index(fields=['category', 'created_at']),
            models.Index(fields=['author']),
            models.Index(fields=['status']),
            models.Index(fields=['last_activity']),
        ]
        ordering = ['-is_sticky', '-last_activity']
    
    def __str__(self):
        return self.title
    
    def update_statistics(self):
        """Update thread statistics"""
        self.reply_count = self.replies.count()
        self.save()


class ForumReply(models.Model):
    """Replies to forum threads"""
    
    thread = models.ForeignKey(
        ForumThread,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forum_replies'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    
    # Content
    content = CKEditor5Field()
    
    # Statistics
    like_count = models.IntegerField(default=0)
    
    # Status
    is_approved = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'forum_replies'
        verbose_name = 'Forum Reply'
        verbose_name_plural = 'Forum Replies'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Reply by {self.author.email} on {self.thread.title[:30]}"


class ForumLike(models.Model):
    """Likes on forum threads and replies"""
    
    LIKE_TYPES = (
        ('thread', 'Thread'),
        ('reply', 'Reply'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forum_likes'
    )
    like_type = models.CharField(max_length=10, choices=LIKE_TYPES)
    thread = models.ForeignKey(
        ForumThread,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='likes'
    )
    reply = models.ForeignKey(
        ForumReply,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='likes'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'forum_likes'
        unique_together = ('user', 'thread', 'reply')
    
    def __str__(self):
        target = self.thread if self.thread else self.reply
        return f"{self.user.email} liked {target}"


class ForumReport(models.Model):
    """Reports for inappropriate content"""
    
    REPORT_STATUS = (
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    )
    
    REPORT_TYPES = (
        ('spam', 'Spam'),
        ('offensive', 'Offensive Content'),
        ('harassment', 'Harassment'),
        ('copyright', 'Copyright Violation'),
        ('duplicate', 'Duplicate'),
        ('other', 'Other'),
    )
    
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forum_reports'
    )
    thread = models.ForeignKey(
        ForumThread,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reports'
    )
    reply = models.ForeignKey(
        ForumReply,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reports'
    )
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='pending')
    
    # Review
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_reports'
    )
    review_notes = models.TextField(blank=True, null=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'forum_reports'
        verbose_name = 'Forum Report'
        verbose_name_plural = 'Forum Reports'
    
    def __str__(self):
        return f"Report by {self.reported_by.email} - {self.report_type}"
