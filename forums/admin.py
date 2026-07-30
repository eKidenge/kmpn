# forums/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count
from .models import ForumCategory, ForumThread, ForumReply, ForumLike, ForumReport


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Forum Category"""
    
    list_display = (
        'id',
        'name',
        'slug',
        'thread_count',
        'post_count',
        'order',
        'is_active',
        'requires_moderation',
        'created_at',
    )
    
    list_filter = (
        'is_active',
        'requires_moderation',
        'created_at',
    )
    
    search_fields = (
        'name',
        'description',
        'slug',
    )
    
    readonly_fields = (
        'slug',
        'thread_count',
        'post_count',
        'created_at',
        'updated_at',
        'threads_link',
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'slug',
                'description',
            )
        }),
        ('Settings', {
            'fields': (
                'order',
                'is_active',
                'requires_moderation',
            )
        }),
        ('Statistics', {
            'fields': (
                'thread_count',
                'post_count',
                'threads_link',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'activate_categories',
        'deactivate_categories',
        'enable_moderation',
        'disable_moderation',
        'reset_statistics',
    ]
    
    def threads_link(self, obj):
        """Display link to threads in this category"""
        url = reverse('admin:forums_forumthread_changelist') + f'?category__id={obj.id}'
        return format_html(
            '<a href="{}" style="font-weight: bold; color: #c9a84c;">{} threads</a>',
            url,
            obj.thread_count
        )
    threads_link.short_description = 'Threads'
    
    def activate_categories(self, request, queryset):
        """Activate selected categories"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} category(ies) activated successfully.')
    activate_categories.short_description = 'Activate selected categories'
    
    def deactivate_categories(self, request, queryset):
        """Deactivate selected categories"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} category(ies) deactivated successfully.')
    deactivate_categories.short_description = 'Deactivate selected categories'
    
    def enable_moderation(self, request, queryset):
        """Enable moderation for selected categories"""
        count = queryset.update(requires_moderation=True)
        self.message_user(request, f'Moderation enabled for {count} category(ies).')
    enable_moderation.short_description = 'Enable moderation'
    
    def disable_moderation(self, request, queryset):
        """Disable moderation for selected categories"""
        count = queryset.update(requires_moderation=False)
        self.message_user(request, f'Moderation disabled for {count} category(ies).')
    disable_moderation.short_description = 'Disable moderation'
    
    def reset_statistics(self, request, queryset):
        """Reset statistics for selected categories"""
        for category in queryset:
            category.thread_count = category.threads.count()
            category.post_count = sum(thread.reply_count for thread in category.threads.all())
            category.save()
        self.message_user(request, f'Statistics reset for {queryset.count()} category(ies).')
    reset_statistics.short_description = 'Reset statistics'
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


class ForumReplyInline(admin.TabularInline):
    """Inline for forum replies"""
    model = ForumReply
    fields = ('author', 'content_preview', 'like_count', 'is_approved', 'created_at')
    readonly_fields = ('content_preview', 'like_count', 'created_at')
    extra = 0
    can_delete = True
    show_change_link = True
    
    def content_preview(self, obj):
        """Display content preview"""
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'


@admin.register(ForumThread)
class ForumThreadAdmin(admin.ModelAdmin):
    """Admin configuration for Forum Thread"""
    
    list_display = (
        'id',
        'title',
        'category',
        'author',
        'status',
        'reply_count',
        'view_count',
        'like_count',
        'is_sticky',
        'is_locked',
        'created_at',
        'status_badge',
    )
    
    list_filter = (
        'status',
        'category',
        'is_sticky',
        'is_locked',
        'created_at',
        'author',
    )
    
    search_fields = (
        'title',
        'content',
        'author__username',
        'author__email',
        'author__first_name',
        'author__last_name',
        'tags',
    )
    
    readonly_fields = (
        'view_count',
        'reply_count',
        'like_count',
        'created_at',
        'updated_at',
        'last_activity',
        'replies_link',
        'likes_count_display',
    )
    
    fieldsets = (
        ('Thread Information', {
            'fields': (
                'title',
                'content',
                'category',
            )
        }),
        ('Author', {
            'fields': (
                'author',
            )
        }),
        ('Status & Settings', {
            'fields': (
                'status',
                'is_sticky',
                'is_locked',
            )
        }),
        ('Tags', {
            'fields': (
                'tags',
            ),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': (
                'view_count',
                'reply_count',
                'like_count',
                'replies_link',
                'likes_count_display',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'last_activity',
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ForumReplyInline]
    
    actions = [
        'pin_threads',
        'unpin_threads',
        'lock_threads',
        'unlock_threads',
        'archive_threads',
        'restore_threads',
        'delete_threads',
        'mark_as_open',
    ]
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        status_colors = {
            'open': '#28a745',
            'pinned': '#c9a84c',
            'closed': '#dc3545',
            'archived': '#6c757d',
            'deleted': '#6c757d',
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 10px; '
            'border-radius: 3px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def replies_link(self, obj):
        """Display link to replies"""
        url = reverse('admin:forums_forumreply_changelist') + f'?thread__id={obj.id}'
        return format_html(
            '<a href="{}" style="font-weight: bold; color: #c9a84c;">{} replies</a>',
            url,
            obj.reply_count
        )
    replies_link.short_description = 'Replies'
    
    def likes_count_display(self, obj):
        """Display likes count"""
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">❤️ {}</span>',
            obj.like_count
        )
    likes_count_display.short_description = 'Likes'
    
    def pin_threads(self, request, queryset):
        """Pin selected threads"""
        count = queryset.update(is_sticky=True)
        self.message_user(request, f'{count} thread(s) pinned successfully.')
    pin_threads.short_description = 'Pin selected threads'
    
    def unpin_threads(self, request, queryset):
        """Unpin selected threads"""
        count = queryset.update(is_sticky=False)
        self.message_user(request, f'{count} thread(s) unpinned successfully.')
    unpin_threads.short_description = 'Unpin selected threads'
    
    def lock_threads(self, request, queryset):
        """Lock selected threads"""
        count = queryset.update(is_locked=True)
        self.message_user(request, f'{count} thread(s) locked successfully.')
    lock_threads.short_description = 'Lock selected threads'
    
    def unlock_threads(self, request, queryset):
        """Unlock selected threads"""
        count = queryset.update(is_locked=False)
        self.message_user(request, f'{count} thread(s) unlocked successfully.')
    unlock_threads.short_description = 'Unlock selected threads'
    
    def archive_threads(self, request, queryset):
        """Archive selected threads"""
        count = queryset.update(status='archived')
        self.message_user(request, f'{count} thread(s) archived successfully.')
    archive_threads.short_description = 'Archive selected threads'
    
    def restore_threads(self, request, queryset):
        """Restore selected threads"""
        count = queryset.update(status='open')
        self.message_user(request, f'{count} thread(s) restored successfully.')
    restore_threads.short_description = 'Restore selected threads'
    
    def delete_threads(self, request, queryset):
        """Delete selected threads"""
        count = queryset.update(status='deleted')
        self.message_user(request, f'{count} thread(s) deleted successfully.')
    delete_threads.short_description = 'Mark as deleted'
    
    def mark_as_open(self, request, queryset):
        """Mark selected threads as open"""
        count = queryset.update(status='open')
        self.message_user(request, f'{count} thread(s) marked as open.')
    mark_as_open.short_description = 'Mark as open'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('category', 'author')
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


@admin.register(ForumReply)
class ForumReplyAdmin(admin.ModelAdmin):
    """Admin configuration for Forum Reply"""
    
    list_display = (
        'id',
        'thread',
        'author',
        'content_preview',
        'like_count',
        'is_approved',
        'is_deleted',
        'created_at',
    )
    
    list_filter = (
        'is_approved',
        'is_deleted',
        'created_at',
        'author',
    )
    
    search_fields = (
        'content',
        'author__username',
        'author__email',
        'author__first_name',
        'author__last_name',
        'thread__title',
    )
    
    readonly_fields = (
        'like_count',
        'created_at',
        'updated_at',
        'thread_link',
    )
    
    fieldsets = (
        ('Reply Information', {
            'fields': (
                'thread',
                'thread_link',
                'content',
            )
        }),
        ('Author', {
            'fields': (
                'author',
            )
        }),
        ('Status', {
            'fields': (
                'is_approved',
                'is_deleted',
            )
        }),
        ('Statistics', {
            'fields': (
                'like_count',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'approve_replies',
        'unapprove_replies',
        'delete_replies',
        'restore_replies',
    ]
    
    def content_preview(self, obj):
        """Display content preview"""
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'
    
    def thread_link(self, obj):
        """Display link to thread"""
        if obj.thread:
            url = reverse('admin:forums_forumthread_change', args=[obj.thread.id])
            return format_html('<a href="{}">{}</a>', url, obj.thread.title[:50])
        return '-'
    thread_link.short_description = 'Thread'
    
    def approve_replies(self, request, queryset):
        """Approve selected replies"""
        count = queryset.update(is_approved=True)
        self.message_user(request, f'{count} reply(ies) approved successfully.')
    approve_replies.short_description = 'Approve selected replies'
    
    def unapprove_replies(self, request, queryset):
        """Unapprove selected replies"""
        count = queryset.update(is_approved=False)
        self.message_user(request, f'{count} reply(ies) unapproved successfully.')
    unapprove_replies.short_description = 'Unapprove selected replies'
    
    def delete_replies(self, request, queryset):
        """Delete selected replies"""
        count = queryset.update(is_deleted=True)
        self.message_user(request, f'{count} reply(ies) deleted successfully.')
    delete_replies.short_description = 'Mark as deleted'
    
    def restore_replies(self, request, queryset):
        """Restore selected replies"""
        count = queryset.update(is_deleted=False)
        self.message_user(request, f'{count} reply(ies) restored successfully.')
    restore_replies.short_description = 'Restore selected replies'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('thread', 'author')


@admin.register(ForumLike)
class ForumLikeAdmin(admin.ModelAdmin):
    """Admin configuration for Forum Like"""
    
    list_display = (
        'id',
        'user',
        'like_type',
        'content_target',
        'created_at',
    )
    
    list_filter = (
        'like_type',
        'created_at',
    )
    
    search_fields = (
        'user__username',
        'user__email',
        'thread__title',
        'reply__content',
    )
    
    readonly_fields = (
        'created_at',
    )
    
    def content_target(self, obj):
        """Display the liked content"""
        if obj.thread:
            return format_html(
                '<a href="{}">Thread: {}</a>',
                reverse('admin:forums_forumthread_change', args=[obj.thread.id]),
                obj.thread.title[:50]
            )
        elif obj.reply:
            return format_html(
                '<a href="{}">Reply: {}</a>',
                reverse('admin:forums_forumreply_change', args=[obj.reply.id]),
                obj.reply.content[:50]
            )
        return '-'
    content_target.short_description = 'Content'


@admin.register(ForumReport)
class ForumReportAdmin(admin.ModelAdmin):
    """Admin configuration for Forum Report"""
    
    list_display = (
        'id',
        'reported_by',
        'report_type',
        'status',
        'content_target',
        'created_at',
        'status_badge',
    )
    
    list_filter = (
        'report_type',
        'status',
        'created_at',
    )
    
    search_fields = (
        'reported_by__username',
        'reported_by__email',
        'description',
        'thread__title',
        'reply__content',
    )
    
    readonly_fields = (
        'created_at',
        'reviewed_at',
        'content_display',
    )
    
    fieldsets = (
        ('Report Information', {
            'fields': (
                'report_type',
                'description',
                'status',
            )
        }),
        ('Reported By', {
            'fields': (
                'reported_by',
            )
        }),
        ('Content', {
            'fields': (
                'content_display',
            )
        }),
        ('Review', {
            'fields': (
                'reviewed_by',
                'review_notes',
                'reviewed_at',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_as_resolved',
        'mark_as_rejected',
        'mark_as_reviewing',
    ]
    
    def content_display(self, obj):
        """Display the reported content"""
        if obj.thread:
            return format_html(
                '<strong>Thread:</strong> <a href="{}">{}</a>',
                reverse('admin:forums_forumthread_change', args=[obj.thread.id]),
                obj.thread.title
            )
        elif obj.reply:
            return format_html(
                '<strong>Reply:</strong> <a href="{}">{}</a>',
                reverse('admin:forums_forumreply_change', args=[obj.reply.id]),
                obj.reply.content[:100]
            )
        return '-'
    content_display.short_description = 'Reported Content'
    
    def content_target(self, obj):
        """Display the content target"""
        if obj.thread:
            return f"Thread: {obj.thread.title[:50]}"
        elif obj.reply:
            return f"Reply: {obj.reply.content[:50]}"
        return '-'
    content_target.short_description = 'Content'
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        status_colors = {
            'pending': '#ffc107',
            'reviewing': '#17a2b8',
            'resolved': '#28a745',
            'rejected': '#dc3545',
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 10px; '
            'border-radius: 3px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def mark_as_resolved(self, request, queryset):
        """Mark selected reports as resolved"""
        count = queryset.update(status='resolved', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f'{count} report(s) marked as resolved.')
    mark_as_resolved.short_description = 'Mark as resolved'
    
    def mark_as_rejected(self, request, queryset):
        """Mark selected reports as rejected"""
        count = queryset.update(status='rejected', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f'{count} report(s) marked as rejected.')
    mark_as_rejected.short_description = 'Mark as rejected'
    
    def mark_as_reviewing(self, request, queryset):
        """Mark selected reports as reviewing"""
        count = queryset.update(status='reviewing', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f'{count} report(s) marked as reviewing.')
    mark_as_reviewing.short_description = 'Mark as reviewing'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('reported_by', 'reviewed_by', 'thread', 'reply')


# Register the models with custom admin
admin.site.site_header = 'KMPN Forums Administration'
admin.site.site_title = 'KMPN Forums Admin'
admin.site.index_title = 'Forums Administration'