# members/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count
from .models import Member, MemberVerificationRequest, MemberActivity


class MemberActivityInline(admin.TabularInline):
    """Inline for member activities"""
    model = MemberActivity
    fields = ('activity_type', 'activity_description', 'created_at')
    readonly_fields = ('created_at',)
    extra = 0
    can_delete = True
    show_change_link = True


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """Admin configuration for Member model"""
    
    list_display = (
        'id',
        'user',
        'membership_number',
        'verification_status',
        'publication_count',
        'citation_count',
        'h_index',
        'card_preview',
        'verification_status_badge',
        'created_at',
    )
    
    list_filter = (
        'verification_status',
        'membership_type',
        'created_at',
    )
    
    search_fields = (
        'user__email',
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__institution',
        'membership_number',
        'expertise_areas',
        'skills',
        'thesis_title',
        'student_id_number',
        'registration_number',
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'last_activity',
        'qr_code_preview',
        'digital_card_preview',
    )
    
    fieldsets = (
        ('Member Information', {
            'fields': (
                'user',
                'membership_number',
                'membership_type',
            )
        }),
        ('Verification', {
            'fields': (
                'verification_status',
                'verified_by',
                'verified_at',
                'verification_notes',
            )
        }),
        ('Verification Documents', {
            'fields': (
                'student_id',
                'admission_letter',
                'transcript',
            ),
            'classes': ('collapse',)
        }),
        ('Academic Information', {
            'fields': (
                'student_id_number',
                'registration_number',
                'year_of_study',
                'expected_graduation_year',
            )
        }),
        ('Thesis/Research', {
            'fields': (
                'thesis_title',
                'thesis_abstract',
                'supervisor_name',
                'supervisor_email',
            ),
            'classes': ('collapse',)
        }),
        ('Research & Publications', {
            'fields': (
                'publication_count',
                'citation_count',
                'h_index',
            )
        }),
        ('Skills & Expertise', {
            'fields': (
                'skills',
                'expertise_areas',
                'programming_languages',
                'research_methodologies',
            ),
            'classes': ('collapse',)
        }),
        ('Interests', {
            'fields': (
                'collaboration_interests',
                'mentoring_interests',
            ),
            'classes': ('collapse',)
        }),
        ('Digital Card', {
            'fields': (
                'digital_card',
                'qr_code',
                'qr_code_preview',
                'digital_card_preview',
                'card_issued_at',
                'card_expires_at',
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
    
    inlines = [MemberActivityInline]
    
    actions = [
        'verify_members',
        'unverify_members',
        'export_members',
        'reset_statistics',
        'generate_cards',
    ]
    
    def card_preview(self, obj):
        """Display card preview"""
        if obj.digital_card:
            return "✅ Card exists"
        return "No card"
    card_preview.short_description = 'Digital Card'
    
    def qr_code_preview(self, obj):
        """Display QR code preview"""
        if obj.qr_code:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✅ QR Code</span>'
            )
        return format_html(
                '<span style="color: #6c757d;">No QR code</span>'
            )
    qr_code_preview.short_description = 'QR Code'
    
    def digital_card_preview(self, obj):
        """Display digital card preview"""
        if obj.digital_card:
            try:
                return format_html(
                    '<img src="{}" style="max-width: 100px; max-height: 60px; border: 1px solid #ddd;" />',
                    obj.digital_card.url
                )
            except:
                return format_html(
                    '<span style="color: #28a745; font-weight: bold;">✅ Card exists</span>'
                )
        return format_html(
                '<span style="color: #6c757d;">No card</span>'
            )
    digital_card_preview.short_description = 'Card Preview'
    
    def verification_status_badge(self, obj):
        """Display verification status as colored badge"""
        status_colors = {
            'pending': '#ffc107',
            'verified': '#28a745',
            'rejected': '#dc3545',
            'suspended': '#6c757d',
        }
        color = status_colors.get(obj.verification_status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase;">{}</span>',
            color,
            obj.get_verification_status_display()
        )
    verification_status_badge.short_description = 'Status'
    
    def verify_members(self, request, queryset):
        """Verify selected members"""
        count = 0
        for member in queryset:
            if member.verification_status != 'verified':
                member.verification_status = 'verified'
                member.verified_by = request.user
                member.verified_at = timezone.now()
                member.card_issued_at = timezone.now()
                member.card_expires_at = timezone.now() + timezone.timedelta(days=365)
                member.generate_digital_card()
                member.generate_qr_code()
                member.save()
                count += 1
        self.message_user(request, f'{count} member(s) verified successfully.')
    verify_members.short_description = 'Verify selected members'
    
    def unverify_members(self, request, queryset):
        """Unverify selected members"""
        count = queryset.update(verification_status='pending')
        self.message_user(request, f'{count} member(s) unverified successfully.')
    unverify_members.short_description = 'Unverify selected members'
    
    def reset_statistics(self, request, queryset):
        """Reset statistics for selected members"""
        count = queryset.update(publication_count=0, citation_count=0, h_index=0)
        self.message_user(request, f'Statistics reset for {count} member(s).')
    reset_statistics.short_description = 'Reset statistics'
    
    def generate_cards(self, request, queryset):
        """Generate digital cards for selected members"""
        count = 0
        for member in queryset:
            if member.verification_status == 'verified':
                member.generate_digital_card()
                member.generate_qr_code()
                member.card_issued_at = timezone.now()
                member.card_expires_at = timezone.now() + timezone.timedelta(days=365)
                member.save()
                count += 1
        self.message_user(request, f'Digital cards generated for {count} member(s).')
    generate_cards.short_description = 'Generate digital cards'
    
    def export_members(self, request, queryset):
        """Export selected members as CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="members_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Membership Number', 'Name', 'Email', 'Institution', 'Academic Level',
            'Verification Status', 'Publications', 'Citations', 'H-Index', 'Joined Date'
        ])
        
        for member in queryset:
            writer.writerow([
                member.membership_number,
                member.user.get_full_name(),
                member.user.email,
                member.user.institution or '',
                member.user.get_academic_level_display() if hasattr(member.user, 'get_academic_level_display') else '',
                member.get_verification_status_display(),
                member.publication_count,
                member.citation_count,
                member.h_index,
                member.created_at.strftime('%Y-%m-%d')
            ])
        
        return response
    export_members.short_description = 'Export selected members as CSV'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


@admin.register(MemberVerificationRequest)
class MemberVerificationRequestAdmin(admin.ModelAdmin):
    """Admin configuration for Member Verification Request"""
    
    list_display = (
        'id',
        'member',
        'review_decision',
        'status_badge',
        'created_at',
        'reviewed_at',
    )
    
    list_filter = (
        'review_decision',
        'created_at',
    )
    
    search_fields = (
        'member__user__email',
        'member__user__username',
        'member__user__first_name',
        'member__user__last_name',
        'member__membership_number',
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'documents_display',
    )
    
    fieldsets = (
        ('Member Information', {
            'fields': (
                'member',
                'request_type',
                'request_notes',
            )
        }),
        ('Documents', {
            'fields': (
                'documents_display',
                'documents',
            ),
            'classes': ('collapse',)
        }),
        ('Review', {
            'fields': (
                'review_decision',
                'reviewed_by',
                'review_notes',
                'reviewed_at',
            )
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
        'approve_requests',
        'reject_requests',
        'request_info',
    ]
    
    def documents_display(self, obj):
        """Display uploaded documents"""
        if obj.documents:
            html = '<ul style="margin: 0; padding-left: 20px;">'
            for key, value in obj.documents.items():
                html += f'<li><strong>{key.replace("_", " ").title()}:</strong> {value}</li>'
            html += '</ul>'
            return format_html(html)
        return format_html('<span style="color: #6c757d;">No documents uploaded</span>')
    documents_display.short_description = 'Documents'
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        status_colors = {
            'pending': '#ffc107',
            'reviewing': '#17a2b8',
            'approved': '#28a745',
            'rejected': '#dc3545',
            'additional_info': '#ff9800',
        }
        color = status_colors.get(obj.review_decision, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase;">{}</span>',
            color,
            obj.get_review_decision_display()
        )
    status_badge.short_description = 'Status'
    
    def approve_requests(self, request, queryset):
        """Approve selected verification requests"""
        count = 0
        for verification in queryset:
            if verification.review_decision == 'pending':
                verification.review_decision = 'approved'
                verification.reviewed_by = request.user
                verification.reviewed_at = timezone.now()
                verification.save()
                
                member = verification.member
                member.verification_status = 'verified'
                member.verified_by = request.user
                member.verified_at = timezone.now()
                member.card_issued_at = timezone.now()
                member.card_expires_at = timezone.now() + timezone.timedelta(days=365)
                member.generate_digital_card()
                member.generate_qr_code()
                member.save()
                count += 1
        self.message_user(request, f'{count} verification request(s) approved.')
    approve_requests.short_description = 'Approve selected requests'
    
    def reject_requests(self, request, queryset):
        """Reject selected verification requests"""
        count = 0
        for verification in queryset:
            if verification.review_decision == 'pending':
                verification.review_decision = 'rejected'
                verification.reviewed_by = request.user
                verification.reviewed_at = timezone.now()
                verification.save()
                
                member = verification.member
                member.verification_status = 'rejected'
                member.save()
                count += 1
        self.message_user(request, f'{count} verification request(s) rejected.')
    reject_requests.short_description = 'Reject selected requests'
    
    def request_info(self, request, queryset):
        """Request additional information"""
        count = 0
        for verification in queryset:
            if verification.review_decision == 'pending':
                verification.review_decision = 'additional_info'
                verification.reviewed_by = request.user
                verification.reviewed_at = timezone.now()
                verification.save()
                count += 1
        self.message_user(request, f'Additional information requested for {count} request(s).')
    request_info.short_description = 'Request additional information'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('member', 'member__user', 'reviewed_by')


@admin.register(MemberActivity)
class MemberActivityAdmin(admin.ModelAdmin):
    """Admin configuration for Member Activity"""
    
    list_display = (
        'id',
        'member',
        'activity_type',
        'activity_description_short',
        'ip_address',
        'created_at',
    )
    
    list_filter = (
        'activity_type',
        'created_at',
    )
    
    search_fields = (
        'member__user__email',
        'member__user__username',
        'member__user__first_name',
        'member__user__last_name',
        'activity_description',
        'ip_address',
    )
    
    readonly_fields = (
        'created_at',
        'ip_address',
        'activity_description',
        'metadata',
    )
    
    fieldsets = (
        ('Activity', {
            'fields': (
                'member',
                'activity_type',
                'activity_description',
            )
        }),
        ('Metadata', {
            'fields': (
                'ip_address',
                'metadata',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    def activity_description_short(self, obj):
        """Display shortened activity description"""
        if len(obj.activity_description) > 50:
            return obj.activity_description[:50] + '...'
        return obj.activity_description
    activity_description_short.short_description = 'Description'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('member', 'member__user')