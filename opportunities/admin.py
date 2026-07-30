# opportunities/admin.py

from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.utils import timezone
from .models import Opportunity, OpportunityApplication, OpportunitySave


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    """Admin configuration for Opportunities"""
    
    # List display fields - use methods only
    list_display = [
        'id',
        'title_preview',
        'opportunity_type_badge',
        'organization_name',
        'status_badge',
        'verified_display',
        'application_deadline',
        'days_remaining',
        'view_count',
        'application_count',
        'created_at',
    ]
    
    # List filters
    list_filter = [
        'opportunity_type',
        'status',
        'is_verified',
        'is_remote',
        'has_funding',
        'created_at',
        'application_deadline',
        'country',
    ]
    
    # Search fields
    search_fields = [
        'title',
        'description',
        'organization_name',
        'location',
        'country',
        'tags',
        'disciplines',
        'contact_person',
        'contact_email',
    ]
    
    # Default ordering
    ordering = ['-created_at']
    
    # Fieldsets for detail view
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title',
                'description',
                'opportunity_type',
                'status',
                'is_verified',
                'verified_at',
                'verified_by',
            )
        }),
        ('Organization', {
            'fields': (
                'organization_name',
                'organization_website',
                'organization_logo',
                'created_by',
            )
        }),
        ('Location', {
            'fields': (
                'location',
                'country',
                'is_remote',
            )
        }),
        ('Dates', {
            'fields': (
                'posted_date',
                'application_deadline',
                'start_date',
                'end_date',
            )
        }),
        ('Financial Information', {
            'fields': (
                'has_funding',
                'funding_amount',
                'currency',
                'funding_details',
            )
        }),
        ('Eligibility & Qualifications', {
            'fields': (
                'eligibility_criteria',
                'required_qualifications',
                'preferred_qualifications',
            )
        }),
        ('Application', {
            'fields': (
                'application_requirements',
                'required_documents',
                'application_url',
                'application_email',
                'application_instructions',
            )
        }),
        ('Contact', {
            'fields': (
                'contact_person',
                'contact_email',
                'contact_phone',
            )
        }),
        ('Tags & Metadata', {
            'fields': (
                'tags',
                'disciplines',
            )
        }),
        ('Statistics', {
            'fields': (
                'view_count',
                'application_count',
                'save_count',
                'share_count',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )
    
    # Read-only fields
    readonly_fields = [
        'posted_date',
        'created_at',
        'updated_at',
        'view_count',
        'application_count',
        'save_count',
        'share_count',
        'verified_at',
    ]
    
    # Actions
    actions = [
        'make_published',
        'make_draft',
        'make_archived',
        'mark_verified',
        'mark_unverified',
    ]
    
    def get_queryset(self, request):
        """Prefetch related data for performance"""
        return super().get_queryset(request).select_related('created_by', 'verified_by')
    
    # ============================================================
    # LIST DISPLAY METHODS - FIXED format_html
    # ============================================================
    
    def title_preview(self, obj):
        """Display truncated title"""
        return obj.title[:60] + '...' if len(obj.title) > 60 else obj.title
    title_preview.short_description = 'Title'
    
    def opportunity_type_badge(self, obj):
        """Display opportunity type as a colored badge"""
        colors = {
            'scholarship': '#2e7d32',
            'phd_position': '#1565c0',
            'masters_position': '#1565c0',
            'postdoc': '#6a1b9a',
            'conference': '#e65100',
            'call_for_papers': '#e65100',
            'grant': '#1a7a4a',
            'job': '#c62828',
            'internship': '#0d47a1',
            'training': '#f57f17',
            'other': '#616161',
        }
        color = colors.get(obj.opportunity_type, '#616161')
        # Fixed: Added a space as the second argument to format_html
        return format_html(
            '<span style="background:{};color:white;padding:2px 12px;border-radius:12px;font-size:0.7rem;font-weight:600;text-transform:uppercase;display:inline-block;">{}</span>',
            color,
            obj.get_opportunity_type_display()
        )
    opportunity_type_badge.short_description = 'Type'
    
    def status_badge(self, obj):
        """Display status as a colored badge"""
        colors = {
            'draft': '#9e9e9e',
            'published': '#2e7d32',
            'expired': '#c62828',
            'archived': '#616161',
        }
        color = colors.get(obj.status, '#9e9e9e')
        return format_html(
            '<span style="background:{};color:white;padding:2px 12px;border-radius:12px;font-size:0.7rem;font-weight:600;text-transform:uppercase;display:inline-block;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def verified_display(self, obj):
        """Display verification status - FIXED: removed format_html for simple strings"""
        if obj.is_verified:
            return mark_safe('<span style="color:#2e7d32;font-weight:700;">✅ Verified</span>')
        return mark_safe('<span style="color:#c62828;font-weight:700;">❌ Not Verified</span>')
    verified_display.short_description = 'Verified'
    
    def days_remaining(self, obj):
        """Display days remaining until deadline"""
        if obj.application_deadline:
            days = (obj.application_deadline - timezone.now()).days
            if days < 0:
                return mark_safe('<span style="color:#c62828;font-weight:700;">Expired</span>')
            elif days < 7:
                return mark_safe(f'<span style="color:#e65100;font-weight:700;">{days} days</span>')
            return mark_safe(f'<span style="color:#2e7d32;">{days} days</span>')
        return '-'
    days_remaining.short_description = 'Days Left'
    
    # ============================================================
    # ADMIN ACTIONS
    # ============================================================
    
    def make_published(self, request, queryset):
        """Publish selected opportunities"""
        count = queryset.update(status='published')
        self.message_user(request, f'{count} opportunities published.')
    make_published.short_description = "📢 Publish selected opportunities"
    
    def make_draft(self, request, queryset):
        """Move selected opportunities to draft"""
        count = queryset.update(status='draft')
        self.message_user(request, f'{count} opportunities moved to draft.')
    make_draft.short_description = "📝 Move to draft"
    
    def make_archived(self, request, queryset):
        """Archive selected opportunities"""
        count = queryset.update(status='archived')
        self.message_user(request, f'{count} opportunities archived.')
    make_archived.short_description = "📦 Archive selected opportunities"
    
    def mark_verified(self, request, queryset):
        """Mark selected opportunities as verified"""
        count = queryset.update(
            is_verified=True,
            verified_by=request.user,
            verified_at=timezone.now()
        )
        self.message_user(request, f'{count} opportunities verified.')
    mark_verified.short_description = "✅ Mark as verified"
    
    def mark_unverified(self, request, queryset):
        """Mark selected opportunities as unverified"""
        count = queryset.update(
            is_verified=False,
            verified_by=None,
            verified_at=None
        )
        self.message_user(request, f'{count} opportunities marked as unverified.')
    mark_unverified.short_description = "❌ Mark as unverified"
    
    # ============================================================
    # SAVE METHODS
    # ============================================================
    
    def save_model(self, request, obj, form, change):
        """Set created_by on create"""
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(OpportunityApplication)
class OpportunityApplicationAdmin(admin.ModelAdmin):
    """Admin configuration for Opportunity Applications"""
    
    list_display = [
        'id',
        'opportunity_title',
        'applicant_name',
        'applicant_email',
        'status_badge',
        'created_at',
        'reviewed_at',
    ]
    
    list_filter = [
        'status',
        'created_at',
        'opportunity__opportunity_type',
    ]
    
    search_fields = [
        'opportunity__title',
        'applicant__email',
        'applicant__first_name',
        'applicant__last_name',
        'cover_letter',
    ]
    
    ordering = ['-created_at']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Application Details', {
            'fields': (
                'opportunity',
                'applicant',
                'cover_letter',
                'message',
            )
        }),
        ('Documents', {
            'fields': ('documents',)
        }),
        ('Status', {
            'fields': (
                'status',
                'review_notes',
                'reviewed_by',
                'reviewed_at',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )
    
    actions = [
        'mark_pending',
        'mark_reviewing',
        'mark_shortlisted',
        'mark_accepted',
        'mark_rejected',
    ]
    
    # ============================================================
    # LIST DISPLAY METHODS
    # ============================================================
    
    def opportunity_title(self, obj):
        """Display opportunity title"""
        return obj.opportunity.title[:50] + '...' if len(obj.opportunity.title) > 50 else obj.opportunity.title
    opportunity_title.short_description = 'Opportunity'
    
    def applicant_name(self, obj):
        """Display applicant full name"""
        return obj.applicant.get_full_name() or obj.applicant.username
    applicant_name.short_description = 'Applicant'
    
    def applicant_email(self, obj):
        """Display applicant email"""
        return obj.applicant.email
    applicant_email.short_description = 'Email'
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'pending': '#f57f17',
            'reviewing': '#1565c0',
            'shortlisted': '#6a1b9a',
            'accepted': '#2e7d32',
            'rejected': '#c62828',
            'withdrawn': '#616161',
        }
        color = colors.get(obj.status, '#9e9e9e')
        return format_html(
            '<span style="background:{};color:white;padding:2px 12px;border-radius:12px;font-size:0.7rem;font-weight:600;text-transform:uppercase;display:inline-block;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    # ============================================================
    # ADMIN ACTIONS
    # ============================================================
    
    def mark_pending(self, request, queryset):
        count = queryset.update(status='pending')
        self.message_user(request, f'{count} applications marked as pending.')
    mark_pending.short_description = "⏳ Mark as pending"
    
    def mark_reviewing(self, request, queryset):
        count = queryset.update(status='reviewing')
        self.message_user(request, f'{count} applications marked as reviewing.')
    mark_reviewing.short_description = "📋 Mark as reviewing"
    
    def mark_shortlisted(self, request, queryset):
        count = queryset.update(status='shortlisted')
        self.message_user(request, f'{count} applications shortlisted.')
    mark_shortlisted.short_description = "⭐ Mark as shortlisted"
    
    def mark_accepted(self, request, queryset):
        count = queryset.update(status='accepted')
        self.message_user(request, f'{count} applications accepted.')
    mark_accepted.short_description = "✅ Mark as accepted"
    
    def mark_rejected(self, request, queryset):
        count = queryset.update(status='rejected')
        self.message_user(request, f'{count} applications rejected.')
    mark_rejected.short_description = "❌ Mark as rejected"
    
    # ============================================================
    # SAVE METHODS
    # ============================================================
    
    def save_model(self, request, obj, form, change):
        """Set reviewed_by on status change"""
        if change and 'status' in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(OpportunitySave)
class OpportunitySaveAdmin(admin.ModelAdmin):
    """Admin configuration for Opportunity Saves"""
    
    list_display = [
        'id',
        'opportunity_title',
        'user_name',
        'user_email',
        'created_at',
    ]
    
    list_filter = ['created_at']
    
    search_fields = [
        'opportunity__title',
        'user__email',
        'user__first_name',
        'user__last_name',
    ]
    
    ordering = ['-created_at']
    
    readonly_fields = ['created_at']
    
    # ============================================================
    # LIST DISPLAY METHODS
    # ============================================================
    
    def opportunity_title(self, obj):
        """Display opportunity title"""
        return obj.opportunity.title[:50] + '...' if len(obj.opportunity.title) > 50 else obj.opportunity.title
    opportunity_title.short_description = 'Opportunity'
    
    def user_name(self, obj):
        """Display user full name"""
        return obj.user.get_full_name() or obj.user.username
    user_name.short_description = 'User'
    
    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'Email'