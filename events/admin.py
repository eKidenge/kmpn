# events/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count
from .models import Event, EventRegistration


class EventRegistrationInline(admin.TabularInline):
    """Inline for event registrations"""
    model = EventRegistration
    fields = ('user', 'attendance_status', 'payment_status', 'registration_date')
    readonly_fields = ('registration_date',)
    extra = 0
    can_delete = True
    show_change_link = True


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin configuration for Event model"""
    
    list_display = (
        'id',
        'title',
        'event_type',
        'status',
        'organizer_name',
        'start_date',
        'registration_count_display',
        'view_count',
        'status_badge',
        'days_remaining'
    )
    
    list_filter = (
        'event_type',
        'status',
        'is_virtual',
        'requires_registration',
        'created_at',
        'start_date',
    )
    
    search_fields = (
        'title',
        'description',
        'organizer_name',
        'organizer_email',
        'venue',
        'city',
        'country',
        'tags',
    )
    
    readonly_fields = (
        'slug',
        'view_count',
        'registration_count',
        'attendance_count',
        'created_at',
        'updated_at',
        'qr_code_display',
        'registrations_count_display',
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title',
                'slug',
                'description',
                'event_type',
                'status',
            )
        }),
        ('Organizer Information', {
            'fields': (
                'organizer_name',
                'organizer_email',
                'organizer_phone',
                'organizer_website',
            )
        }),
        ('Location & Venue', {
            'fields': (
                'is_virtual',
                'venue',
                'address',
                'city',
                'country',
                'virtual_link',
            )
        }),
        ('Date & Time', {
            'fields': (
                'start_date',
                'end_date',
                'registration_deadline',
            )
        }),
        ('Registration & Capacity', {
            'fields': (
                'requires_registration',
                'max_attendees',
                'current_attendees',
                'registration_fee',
                'currency',
                'registration_link',
            )
        }),
        ('Content', {
            'fields': (
                'agenda',
                'speakers',
                'program',
            )
        }),
        ('Media', {
            'fields': (
                'banner_image',
                'poster',
            ),
            'classes': ('collapse',)
        }),
        ('Zoom Integration', {
            'fields': (
                'zoom_meeting_id',
                'zoom_password',
                'zoom_meeting_link',
            ),
            'classes': ('collapse',)
        }),
        ('Recordings', {
            'fields': (
                'recording_url',
                'recording_file',
            ),
            'classes': ('collapse',)
        }),
        ('Tags & Metadata', {
            'fields': (
                'tags',
                'created_by',
                'view_count',
                'registration_count',
                'attendance_count',
                'qr_code_display',
                'registrations_count_display',
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
    
    filter_horizontal = ()
    
    actions = [
        'publish_events',
        'unpublish_events',
        'mark_as_ongoing',
        'mark_as_completed',
        'cancel_events',
        'duplicate_events',
        'delete_selected',
    ]
    
    inlines = [EventRegistrationInline]
    
    def get_queryset(self, request):
        """Annotate queryset with registration count"""
        return super().get_queryset(request).annotate(
            reg_count=Count('registrations')
        )
    
    def registration_count_display(self, obj):
        """Display registration count"""
        count = getattr(obj, 'reg_count', obj.registrations.count())
        url = reverse('admin:events_eventregistration_changelist') + f'?event__id={obj.id}'
        return format_html(
            '<a href="{}" style="font-weight: bold; color: #c9a84c;">{}</a>',
            url,
            count
        )
    registration_count_display.short_description = 'Registrations'
    
    def registrations_count_display(self, obj):
        """Display registration count in detail view"""
        count = obj.registrations.count()
        url = reverse('admin:events_eventregistration_changelist') + f'?event__id={obj.id}'
        return format_html(
            '<a href="{}" style="font-weight: bold; color: #c9a84c;">{} registrations</a>',
            url,
            count
        )
    registrations_count_display.short_description = 'Total Registrations'
    
    def qr_code_display(self, obj):
        """Display QR code if available"""
        return format_html(
            '<span style="color: #6c757d;">QR code placeholder</span>'
        )
    qr_code_display.short_description = 'QR Code'
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        status_colors = {
            'draft': '#6c757d',
            'published': '#28a745',
            'ongoing': '#17a2b8',
            'completed': '#6c757d',
            'cancelled': '#dc3545',
            'postponed': '#ffc107',
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def days_remaining(self, obj):
        """Display days remaining until event"""
        if obj.status in ['completed', 'cancelled']:
            return format_html('<span style="color: #6c757d;">N/A</span>')
        
        now = timezone.now()
        if obj.start_date < now:
            return format_html('<span style="color: #dc3545;">Past</span>')
        
        days = (obj.start_date - now).days
        if days == 0:
            return format_html('<span style="color: #ffc107;">Today!</span>')
        elif days < 7:
            return format_html('<span style="color: #ffc107; font-weight: bold;">{} days</span>', days)
        else:
            return format_html('<span style="color: #28a745;">{} days</span>', days)
    days_remaining.short_description = 'Days Left'
    
    # Actions
    def publish_events(self, request, queryset):
        """Publish selected events"""
        count = queryset.update(status='published')
        self.message_user(request, f'{count} event(s) published successfully.')
    publish_events.short_description = 'Publish selected events'
    
    def unpublish_events(self, request, queryset):
        """Unpublish selected events"""
        count = queryset.update(status='draft')
        self.message_user(request, f'{count} event(s) unpublished successfully.')
    unpublish_events.short_description = 'Unpublish selected events'
    
    def mark_as_ongoing(self, request, queryset):
        """Mark selected events as ongoing"""
        count = queryset.update(status='ongoing')
        self.message_user(request, f'{count} event(s) marked as ongoing.')
    mark_as_ongoing.short_description = 'Mark as ongoing'
    
    def mark_as_completed(self, request, queryset):
        """Mark selected events as completed"""
        count = queryset.update(status='completed')
        self.message_user(request, f'{count} event(s) marked as completed.')
    mark_as_completed.short_description = 'Mark as completed'
    
    def cancel_events(self, request, queryset):
        """Cancel selected events"""
        count = queryset.update(status='cancelled')
        self.message_user(request, f'{count} event(s) cancelled.')
    cancel_events.short_description = 'Cancel selected events'
    
    def duplicate_events(self, request, queryset):
        """Duplicate selected events"""
        for event in queryset:
            event.pk = None
            event.title = f"{event.title} (Copy)"
            event.slug = None
            event.view_count = 0
            event.registration_count = 0
            event.attendance_count = 0
            event.status = 'draft'
            event.created_at = timezone.now()
            event.updated_at = timezone.now()
            event.save()
        self.message_user(request, f'{queryset.count()} event(s) duplicated successfully.')
    duplicate_events.short_description = 'Duplicate selected events'
    
    def delete_selected(self, request, queryset):
        """Delete selected events with confirmation"""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} event(s) deleted successfully.')
    delete_selected.short_description = 'Delete selected events'
    
    def save_model(self, request, obj, form, change):
        """Set created_by when creating new event"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    """Admin configuration for EventRegistration model"""
    
    list_display = (
        'id',
        'event_title',
        'user_email',
        'attendance_status',
        'payment_status',
        'registration_date',
        'certificate_issued',
        'feedback_submitted',
    )
    
    list_filter = (
        'attendance_status',
        'payment_status',
        'certificate_issued',
        'feedback_submitted',
        'registration_date',
    )
    
    search_fields = (
        'event__title',
        'user__email',
        'user__username',
        'user__first_name',
        'user__last_name',
    )
    
    readonly_fields = (
        'registration_date',
        'created_at',
        'updated_at',
    )
    
    fieldsets = (
        ('Event & User', {
            'fields': (
                'event',
                'user',
            )
        }),
        ('Registration Details', {
            'fields': (
                'attendance_status',
                'registration_date',
            )
        }),
        ('Payment', {
            'fields': (
                'amount_paid',
                'payment_status',
                'payment_transaction_id',
            )
        }),
        ('Zoom Details', {
            'fields': (
                'zoom_join_url',
                'zoom_meeting_id',
                'zoom_password',
            ),
            'classes': ('collapse',)
        }),
        ('Certificate', {
            'fields': (
                'certificate_issued',
                'certificate_file',
                'certificate_issued_at',
            ),
            'classes': ('collapse',)
        }),
        ('Feedback', {
            'fields': (
                'feedback_submitted',
                'feedback_rating',
                'feedback_comment',
                'feedback_submitted_at',
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
        'mark_as_confirmed',
        'mark_as_attended',
        'mark_as_absent',
        'cancel_registrations',
        'issue_certificates',
    ]
    
    def event_title(self, obj):
        """Display event title"""
        return obj.event.title[:50]
    event_title.short_description = 'Event'
    
    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User'
    
    def mark_as_confirmed(self, request, queryset):
        """Mark selected registrations as confirmed"""
        count = queryset.update(attendance_status='confirmed')
        self.message_user(request, f'{count} registration(s) confirmed.')
    mark_as_confirmed.short_description = 'Mark as confirmed'
    
    def mark_as_attended(self, request, queryset):
        """Mark selected registrations as attended"""
        count = queryset.update(attendance_status='attended')
        self.message_user(request, f'{count} registration(s) marked as attended.')
    mark_as_attended.short_description = 'Mark as attended'
    
    def mark_as_absent(self, request, queryset):
        """Mark selected registrations as absent"""
        count = queryset.update(attendance_status='absent')
        self.message_user(request, f'{count} registration(s) marked as absent.')
    mark_as_absent.short_description = 'Mark as absent'
    
    def cancel_registrations(self, request, queryset):
        """Cancel selected registrations"""
        count = queryset.update(attendance_status='cancelled')
        self.message_user(request, f'{count} registration(s) cancelled.')
    cancel_registrations.short_description = 'Cancel registrations'
    
    def issue_certificates(self, request, queryset):
        """Issue certificates for selected registrations"""
        count = 0
        for registration in queryset:
            if registration.attendance_status in ['confirmed', 'attended']:
                registration.generate_certificate()
                count += 1
        self.message_user(request, f'{count} certificate(s) issued.')
    issue_certificates.short_description = 'Issue certificates for selected'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('event', 'user')


# Custom admin site configuration
admin.site.site_header = 'KMPN Event Management'
admin.site.site_title = 'KMPN Admin'
admin.site.index_title = 'KMPN Administration'