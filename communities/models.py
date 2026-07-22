from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django_ckeditor_5.fields import CKEditor5Field


class Community(models.Model):
    """Discipline-based community"""
    
    COMMUNITY_TYPES = (
        ('academic', 'Academic'),
        ('professional', 'Professional'),
        ('research', 'Research'),
        ('special_interest', 'Special Interest'),
        ('regional', 'Regional'),
    )
    
    ACCESS_TYPES = (
        ('public', 'Public'),
        ('members_only', 'Members Only'),
        ('private', 'Private'),
        ('invite_only', 'Invite Only'),
    )
    
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = CKEditor5Field()
    community_type = models.CharField(max_length=20, choices=COMMUNITY_TYPES)
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES, default='members_only')
    
    # Leadership
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_communities'
    )
    moderators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='moderated_communities',
        blank=True
    )
    
    # Statistics
    member_count = models.IntegerField(default=0)
    post_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    
    # Settings
    allow_member_posts = models.BooleanField(default=True)
    require_moderation = models.BooleanField(default=False)
    allow_attachments = models.BooleanField(default=True)
    allow_discussions = models.BooleanField(default=True)
    
    # Media
    logo = models.ImageField(upload_to='communities/logos/%Y/%m/%d/', blank=True, null=True)
    banner = models.ImageField(upload_to='communities/banners/%Y/%m/%d/', blank=True, null=True)
    
    # Tags and Categories
    tags = models.JSONField(default=list, blank=True)
    categories = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'communities'
        verbose_name = 'Community'
        verbose_name_plural = 'Communities'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['community_type']),
            models.Index(fields=['access_type']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-member_count', '-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def update_statistics(self):
        """Update community statistics"""
        self.member_count = self.members.count()
        self.post_count = self.posts.count()
        self.save()


class CommunityMember(models.Model):
    """Community membership model"""
    
    ROLE_CHOICES = (
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('admin', 'Administrator'),
    )
    
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    # Activity
    last_active = models.DateTimeField(auto_now=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    # Preferences
    notification_preferences = models.JSONField(default=dict, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'community_members'
        verbose_name = 'Community Member'
        verbose_name_plural = 'Community Members'
        unique_together = ('community', 'user')
        indexes = [
            models.Index(fields=['community', 'role']),
            models.Index(fields=['last_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.community.name}"
    
    def is_moderator(self):
        return self.role in ['moderator', 'admin']


class CommunityPost(models.Model):
    """Community posts/discussions"""
    
    POST_TYPES = (
        ('discussion', 'Discussion'),
        ('question', 'Question'),
        ('announcement', 'Announcement'),
        ('resource', 'Resource'),
        ('event', 'Event'),
        ('poll', 'Poll'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('pinned', 'Pinned'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
    )
    
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    content = CKEditor5Field()
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='discussion')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    
    # Media
    attachments = models.JSONField(default=list, blank=True)
    cover_image = models.ImageField(upload_to='community/posts/%Y/%m/%d/', blank=True, null=True)
    
    # Poll (if post_type is poll)
    poll_data = models.JSONField(default=dict, blank=True)
    poll_votes = models.JSONField(default=dict, blank=True)
    
    # Statistics
    view_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    
    # Tags
    tags = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'community_posts'
        verbose_name = 'Community Post'
        verbose_name_plural = 'Community Posts'
        indexes = [
            models.Index(fields=['community', 'created_at']),
            models.Index(fields=['author']),
            models.Index(fields=['status']),
            models.Index(fields=['post_type']),
        ]
        # FIXED: Changed from '-pinned' to '-status' since pinned is a status value
        ordering = ['-status', '-created_at']
    
    def __str__(self):
        return f"{self.title[:50]} - {self.community.name}"
    
    def increment_view_count(self):
        self.view_count += 1
        self.save()
    
    def get_comment_count(self):
        return self.comments.count()


class Comment(models.Model):
    """Comments on community posts"""
    
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    content = CKEditor5Field()
    
    # Statistics
    like_count = models.IntegerField(default=0)
    report_count = models.IntegerField(default=0)
    
    # Status
    is_approved = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'community_comments'
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['author']),
        ]
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.email} on {self.post.title[:30]}"


class CommunityLike(models.Model):
    """Likes on posts and comments"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'community_likes'
        verbose_name = 'Community Like'
        verbose_name_plural = 'Community Likes'
        unique_together = ('user', 'post', 'comment')
        indexes = [
            models.Index(fields=['user', 'post']),
            models.Index(fields=['user', 'comment']),
        ]
    
    def __str__(self):
        target = self.post if self.post else self.comment
        return f"{self.user.email} liked {target}"