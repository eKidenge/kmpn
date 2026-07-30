# newsletters/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count, Sum
from .models import (
    Newsletter, 
    NewsletterSubscriber, 
    NewsletterOpen, 
    NewsletterClick
)


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Admin configuration for Newsletter model"""
    
    list_display = (
        'id',
        'subject',
        'status',
        'status_badge',
        'total_recipients',
        'delivered_count',
        'open_rate_display',
        'click_rate_display',
        'created_by',
        'created_at',
        'sent_at',
    )
    
    list_filter = (
        'status',
        'created_at',
        'send_to_all',
    )
    
    search_fields = (
        'subject',
        'content',
        'from_email',
        'created_by__email',
        'created_by__username',
    )
    
    readonly_fields = (
        'tracking_id',
        'total_recipients',
        'delivered_count',
        'opened_count',
        'clicked_count',
        'bounced_count',
        'unsubscribed_count',
        'created_at',
        'updated_at',
        'sent_at',
        'open_rate_display',
        'click_rate_display',
        'statistics_display',
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'subject',
                'content',
                'html_content',
            )
        }),
        ('Sender Information', {
            'fields': (
                'from_email',
                'reply_to',
            )
        }),
        ('Status & Scheduling', {
            'fields': (
                'status',
                'scheduled_at',
                'sent_at',
            )
        }),
        ('Audience', {
            'fields': (
                'send_to_all',
                'target_groups',
                'target_users',
            )
        }),
        ('Statistics', {
            'fields': (
                'statistics_display',
                'open_rate_display',
                'click_rate_display',
                'total_recipients',
                'delivered_count',
                'opened_count',
                'clicked_count',
                'bounced_count',
                'unsubscribed_count',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'tracking_id',
                'metadata',
                'created_by',
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
    
    filter_horizontal = ('target_users',)
    
    actions = [
        'send_newsletters',
        'schedule_newsletters',
        'duplicate_newsletters',
        'archive_newsletters',
        'preview_newsletters',
    ]
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        status_colors = {
            'draft': '#6c757d',
            'scheduled': '#17a2b8',
            'sending': '#ffc107',
            'sent': '#28a745',
            'failed': '#dc3545',
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def open_rate_display(self, obj):
        """Display open rate"""
        rate = obj.get_open_rate()
        return format_html(
            '<span style="font-weight: bold; color: {};">{:.1f}%</span>',
            '#28a745' if rate > 50 else '#ffc107' if rate > 20 else '#dc3545',
            rate
        )
    open_rate_display.short_description = 'Open Rate'
    
    def click_rate_display(self, obj):
        """Display click rate"""
        rate = obj.get_click_rate()
        return format_html(
            '<span style="font-weight: bold; color: {};">{:.1f}%</span>',
            '#28a745' if rate > 30 else '#ffc107' if rate > 10 else '#dc3545',
            rate
        )
    click_rate_display.short_description = 'Click Rate'
    
    def statistics_display(self, obj):
        """Display statistics in a formatted way"""
        return format_html(
            '''
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; max-width: 400px;">
                <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: #28a745;">{}</div>
                    <div style="font-size: 0.7rem; color: #6c757d;">Delivered</div>
                </div>
                <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: #17a2b8;">{}</div>
                    <div style="font-size: 0.7rem; color: #6c757d;">Opened</div>
                </div>
                <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: #ffc107;">{}</div>
                    <div style="font-size: 0.7rem; color: #6c757d;">Clicked</div>
                </div>
            </div>
            ''',
            obj.delivered_count,
            obj.opened_count,
            obj.clicked_count
        )
    statistics_display.short_description = 'Statistics'
    
    def send_newsletters(self, request, queryset):
        """Send selected newsletters"""
        from .tasks import send_newsletter
        count = 0
        for newsletter in queryset:
            if newsletter.status == 'draft':
                # In production, this would use Celery
                # send_newsletter.delay(newsletter.id)
                newsletter.status = 'sending'
                newsletter.save()
                count += 1
        self.message_user(request, f'{count} newsletter(s) queued for sending.')
    send_newsletters.short_description = 'Send selected newsletters'
    
    def schedule_newsletters(self, request, queryset):
        """Schedule selected newsletters"""
        count = queryset.update(status='scheduled')
        self.message_user(request, f'{count} newsletter(s) scheduled.')
    schedule_newsletters.short_description = 'Schedule selected newsletters'
    
    def duplicate_newsletters(self, request, queryset):
        """Duplicate selected newsletters"""
        count = 0
        for newsletter in queryset:
            old_id = newsletter.id
            newsletter.pk = None
            newsletter.subject = f"{newsletter.subject} (Copy)"
            newsletter.status = 'draft'
            newsletter.tracking_id = None
            newsletter.total_recipients = 0
            newsletter.delivered_count = 0
            newsletter.opened_count = 0
            newsletter.clicked_count = 0
            newsletter.bounced_count = 0
            newsletter.unsubscribed_count = 0
            newsletter.sent_at = None
            newsletter.scheduled_at = None
            newsletter.created_at = timezone.now()
            newsletter.updated_at = timezone.now()
            newsletter.save()
            count += 1
        self.message_user(request, f'{count} newsletter(s) duplicated.')
    duplicate_newsletters.short_description = 'Duplicate selected newsletters'
    
    def archive_newsletters(self, request, queryset):
        """Archive selected newsletters"""
        count = queryset.update(status='archived')
        self.message_user(request, f'{count} newsletter(s) archived.')
    archive_newsletters.short_description = 'Archive selected newsletters'
    
    def preview_newsletters(self, request, queryset):
        """Preview selected newsletters"""
        if queryset.count() == 1:
            newsletter = queryset.first()
            return render(request, 'newsletters/preview.html', {'newsletter': newsletter})
        self.message_user(request, 'Please select only one newsletter to preview.')
    preview_newsletters.short_description = 'Preview selected newsletters'
    
    def save_model(self, request, obj, form, change):
        """Set created_by when creating new newsletter"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('created_by')
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    """Admin configuration for Newsletter Subscriber"""
    
    list_display = (
        'id',
        'email',
        'name',
        'subscribed',
        'opened_count',
        'clicked_count',
        'subscribed_at',
    )
    
    list_filter = (
        'subscribed',
        'created_at',
        'groups',
    )
    
    search_fields = (
        'email',
        'name',
        'user__email',
        'user__username',
    )
    
    readonly_fields = (
        'subscribed_at',
        'unsubscribed_at',
        'opened_count',
        'clicked_count',
        'created_at',
        'updated_at',
    )
    
    fieldsets = (
        ('Subscriber Information', {
            'fields': (
                'email',
                'name',
                'user',
            )
        }),
        ('Subscription Status', {
            'fields': (
                'subscribed',
                'subscribed_at',
                'unsubscribed_at',
            )
        }),
        ('Groups & Preferences', {
            'fields': (
                'groups',
            )
        }),
        ('Metadata', {
            'fields': (
                'ip_address',
                'location',
            ),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': (
                'opened_count',
                'clicked_count',
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
        'subscribe_users',
        'unsubscribe_users',
        'export_subscribers',
        'add_to_group',
        'remove_from_group',
    ]
    
    def subscribe_users(self, request, queryset):
        """Subscribe selected users"""
        count = queryset.update(subscribed=True)
        self.message_user(request, f'{count} subscriber(s) subscribed.')
    subscribe_users.short_description = 'Subscribe selected users'
    
    def unsubscribe_users(self, request, queryset):
        """Unsubscribe selected users"""
        count = queryset.update(subscribed=False, unsubscribed_at=timezone.now())
        self.message_user(request, f'{count} subscriber(s) unsubscribed.')
    unsubscribe_users.short_description = 'Unsubscribe selected users'
    
    def export_subscribers(self, request, queryset):
        """Export selected subscribers as CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="subscribers.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Email', 'Name', 'Subscribed', 'Subscribed At', 
            'Opened Count', 'Clicked Count'
        ])
        
        for subscriber in queryset:
            writer.writerow([
                subscriber.email,
                subscriber.name or '',
                'Yes' if subscriber.subscribed else 'No',
                subscriber.subscribed_at.strftime('%Y-%m-%d %H:%M'),
                subscriber.opened_count,
                subscriber.clicked_count
            ])
        
        return response
    export_subscribers.short_description = 'Export selected subscribers as CSV'
    
    def add_to_group(self, request, queryset):
        """Add selected subscribers to a group"""
        group = request.POST.get('group', '')
        if group:
            for subscriber in queryset:
                if group not in subscriber.groups:
                    subscriber.groups.append(group)
                    subscriber.save()
            self.message_user(request, f'Added {queryset.count()} subscriber(s) to group "{group}".')
        else:
            self.message_user(request, 'Please specify a group name.', level='ERROR')
    add_to_group.short_description = 'Add to group'
    
    def remove_from_group(self, request, queryset):
        """Remove selected subscribers from a group"""
        group = request.POST.get('group', '')
        if group:
            for subscriber in queryset:
                if group in subscriber.groups:
                    subscriber.groups.remove(group)
                    subscriber.save()
            self.message_user(request, f'Removed {queryset.count()} subscriber(s) from group "{group}".')
        else:
            self.message_user(request, 'Please specify a group name.', level='ERROR')
    remove_from_group.short_description = 'Remove from group'


@admin.register(NewsletterOpen)
class NewsletterOpenAdmin(admin.ModelAdmin):
    """Admin configuration for Newsletter Opens"""
    
    list_display = (
        'id',
        'newsletter',
        'subscriber',
        'user',
        'location',
        'opened_at',
    )
    
    list_filter = (
        'opened_at',
        'location',
    )
    
    search_fields = (
        'subscriber__email',
        'user__email',
        'user__username',
        'ip_address',
    )
    
    readonly_fields = (
        'opened_at',
        'ip_address',
        'user_agent',
        'location',
    )
    
    fieldsets = (
        ('Open Information', {
            'fields': (
                'newsletter',
                'subscriber',
                'user',
            )
        }),
        ('Technical Details', {
            'fields': (
                'ip_address',
                'user_agent',
                'location',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': (
                'opened_at',
            )
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(NewsletterClick)
class NewsletterClickAdmin(admin.ModelAdmin):
    """Admin configuration for Newsletter Clicks"""
    
    list_display = (
        'id',
        'newsletter',
        'subscriber',
        'url_short',
        'user',
        'location',
        'clicked_at',
    )
    
    list_filter = (
        'clicked_at',
        'location',
    )
    
    search_fields = (
        'subscriber__email',
        'user__email',
        'user__username',
        'url',
        'link_text',
        'ip_address',
    )
    
    readonly_fields = (
        'clicked_at',
        'ip_address',
        'user_agent',
        'location',
    )
    
    fieldsets = (
        ('Click Information', {
            'fields': (
                'newsletter',
                'subscriber',
                'user',
            )
        }),
        ('URL Details', {
            'fields': (
                'url',
                'link_text',
            )
        }),
        ('Technical Details', {
            'fields': (
                'ip_address',
                'user_agent',
                'location',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': (
                'clicked_at',
            )
        }),
    )
    
    def url_short(self, obj):
        """Display shortened URL"""
        return obj.url[:60] + '...' if len(obj.url) > 60 else obj.url
    url_short.short_description = 'URL'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# Register the models with custom admin
admin.site.site_header = 'KMPN Newsletters Administration'
admin.site.site_title = 'KMPN Newsletters Admin'
admin.site.index_title = 'Newsletters Administration'