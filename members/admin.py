from django.contrib import admin
from django.utils.html import format_html
from .models import Member, MemberVerificationRequest, MemberActivity


class MemberAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'membership_number', 'verification_status', 
        'membership_type', 'card_preview', 'is_verified_member'
    )
    list_filter = ('verification_status', 'membership_type', 'created_at')
    search_fields = ('user__email', 'user__username', 'membership_number', 'student_id_number')
    readonly_fields = ('membership_number', 'digital_card_preview', 'qr_code_preview')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'membership_number', 'membership_type', 'verification_status')
        }),
        ('Verification', {
            'fields': (
                'student_id', 'admission_letter', 'transcript',
                'verified_by', 'verified_at', 'verification_notes',
                'digital_card', 'digital_card_preview', 'qr_code', 'qr_code_preview'
            )
        }),
        ('Academic Information', {
            'fields': (
                'student_id_number', 'registration_number', 'year_of_study',
                'expected_graduation_year', 'thesis_title', 'thesis_abstract',
                'supervisor_name', 'supervisor_email'
            )
        }),
        ('Research Metrics', {
            'fields': ('publication_count', 'citation_count', 'h_index')
        }),
        ('Skills and Interests', {
            'fields': (
                'skills', 'expertise_areas', 'programming_languages',
                'research_methodologies', 'collaboration_interests',
                'mentoring_interests'
            )
        }),
        ('Card Information', {
            'fields': ('card_issued_at', 'card_expires_at')
        }),
    )
    
    def card_preview(self, obj):
        if obj.digital_card:
            return format_html(
                '<img src="{}" width="50" height="30" />',
                obj.digital_card.url
            )
        return format_html('<span style="color: gray;">No card</span>')
    card_preview.short_description = 'Card'
    
    def digital_card_preview(self, obj):
        if obj.digital_card:
            return format_html(
                '<img src="{}" width="200" height="125" />',
                obj.digital_card.url
            )
        return format_html('<span style="color: gray;">No card generated</span>')
    digital_card_preview.short_description = 'Digital Card'
    
    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" width="100" height="100" />',
                obj.qr_code.url
            )
        return format_html('<span style="color: gray;">No QR code</span>')
    qr_code_preview.short_description = 'QR Code'
    
    def is_verified_member(self, obj):
        return obj.verification_status == 'verified'
    is_verified_member.boolean = True
    is_verified_member.short_description = 'Verified'


class MemberVerificationRequestAdmin(admin.ModelAdmin):
    list_display = ('member', 'review_decision', 'reviewed_by', 'created_at')
    list_filter = ('review_decision', 'created_at')
    search_fields = ('member__user__email', 'review_notes')
    readonly_fields = ('member', 'request_type', 'documents', 'created_at')
    
    fieldsets = (
        ('Request Information', {
            'fields': ('member', 'request_type', 'request_notes', 'documents')
        }),
        ('Review Information', {
            'fields': ('reviewed_by', 'reviewed_at', 'review_notes', 'review_decision')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk or 'review_decision' in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


class MemberActivityAdmin(admin.ModelAdmin):
    list_display = ('member', 'activity_type', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('member__user__email', 'activity_description')
    readonly_fields = ('member', 'activity_type', 'activity_description', 'ip_address', 'metadata')
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False


admin.site.register(Member, MemberAdmin)
admin.site.register(MemberVerificationRequest, MemberVerificationRequestAdmin)
admin.site.register(MemberActivity, MemberActivityAdmin)
