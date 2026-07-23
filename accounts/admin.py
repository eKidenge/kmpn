# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import (
    User, 
    UserActivityLog, 
    UserDevice, 
    RegistrationApplication, 
    RoleChangeRequest
)


@admin.register(User)
class UserAdminConfig(UserAdmin):
    """Custom User Admin configuration"""
    
    # Display fields in list view
    list_display = [
        'email', 
        'username', 
        'get_full_name', 
        'role',
        'registration_status',
        'institution',
        'is_verified',
        'is_active_member',
        'is_active',
        'created_at'
    ]
    
    # Filters for sidebar
    list_filter = [
        'role',
        'registration_status',
        'academic_level',
        'is_verified',
        'is_active_member',
        'is_active',
        'email_verified',
        'created_at'
    ]
    
    # Search fields
    search_fields = [
        'email', 
        'username', 
        'first_name', 
        'last_name',
        'membership_number',
        'institution'
    ]
    
    # Ordering
    ordering = ['-created_at']
    
    # Fieldsets for detail view
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'uid', 'email', 'username', 'first_name', 'last_name', 'title',
                'phone_number', 'bio', 'profile_picture'
            )
        }),
        ('Role & Status', {
            'fields': (
                'role', 'registration_status',
                'is_verified', 'is_active_member', 'is_active'
            )
        }),
        ('Academic Information', {
            'fields': (
                'academic_level', 'institution', 'department',
                'research_interests', 'research_keywords'
            )
        }),
        ('Membership', {
            'fields': (
                'membership_number', 'membership_start_date',
                'membership_expiry_date', 'membership_fee_paid',
                'membership_fee_paid_at'
            )
        }),
        ('Role-Specific Fields', {
            'fields': (
                'executive_position', 'executive_tenure_start', 'executive_tenure_end',
                'partner_organization', 'partner_type',
                'graduation_year', 'current_position',
                'publication_count', 'citation_count', 'h_index'
            )
        }),
        ('Social Media & Links', {
            'fields': (
                'linkedin_url', 'researchgate_url',
                'google_scholar_url', 'orcid_id', 'twitter_url', 'website_url'
            )
        }),
        ('Mentorship', {
            'fields': (
                'is_mentor', 'mentor_areas', 'is_mentee', 'mentee_goals', 'mentor_id'
            )
        }),
        ('Collaboration', {
            'fields': (
                'collaboration_interests', 'available_for_collaboration',
                'collaboration_preferences'
            )
        }),
        ('Preferences', {
            'fields': (
                'newsletter_subscribed', 'notification_preferences',
                'language_preference', 'timezone'
            )
        }),
        ('Security', {
            'fields': (
                'last_login_ip', 'login_attempts', 'locked_until',
                'two_factor_enabled', 'two_factor_secret', 'security_questions'
            )
        }),
        ('Permissions', {
            'fields': (
                'is_superuser', 'is_staff', 'groups', 'user_permissions'
            )
        }),
        ('Important Dates', {
            'fields': (
                'last_login', 'last_activity', 'created_at', 'updated_at',
                'is_deleted', 'deleted_at'
            )
        }),
    )
    
    # Fields for add user form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'first_name', 'last_name',
                'password1', 'password2', 'role'
            )
        }),
    )
    
    # Read-only fields
    readonly_fields = (
        'uid', 'membership_number', 'membership_start_date',
        'created_at', 'updated_at', 'last_activity',
        'email_verification_token', 'verification_token'
    )
    
    # Actions
    actions = [
        'activate_users', 
        'suspend_users', 
        'ban_users',
        'make_verified_member',
        'make_basic_member',
        'make_researcher',
        'make_alumni'
    ]
    
    def get_queryset(self, request):
        """Prefetch related data for performance"""
        return super().get_queryset(request).select_related('mentor_id')
    
    def activate_users(self, request, queryset):
        """Activate selected users"""
        count = queryset.update(is_active=True, registration_status='approved')
        self.message_user(request, f'{count} users activated.')
    activate_users.short_description = "Activate selected users"
    
    def suspend_users(self, request, queryset):
        """Suspend selected users"""
        count = queryset.update(is_active=False, registration_status='suspended')
        self.message_user(request, f'{count} users suspended.')
    suspend_users.short_description = "Suspend selected users"
    
    def ban_users(self, request, queryset):
        """Ban selected users"""
        count = queryset.update(is_active=False, registration_status='banned')
        self.message_user(request, f'{count} users banned.')
    ban_users.short_description = "Ban selected users"
    
    def make_verified_member(self, request, queryset):
        """Make selected users verified members"""
        count = queryset.update(role='verified_member', is_verified=True)
        self.message_user(request, f'{count} users made verified members.')
    make_verified_member.short_description = "Make verified member"
    
    def make_basic_member(self, request, queryset):
        """Make selected users basic members"""
        count = queryset.update(role='basic_member')
        self.message_user(request, f'{count} users made basic members.')
    make_basic_member.short_description = "Make basic member"
    
    def make_researcher(self, request, queryset):
        """Make selected users researchers"""
        count = queryset.update(role='researcher')
        self.message_user(request, f'{count} users made researchers.')
    make_researcher.short_description = "Make researcher"
    
    def make_alumni(self, request, queryset):
        """Make selected users alumni"""
        count = queryset.update(role='alumni')
        self.message_user(request, f'{count} users made alumni.')
    make_alumni.short_description = "Make alumni"


@admin.register(RegistrationApplication)
class RegistrationApplicationAdmin(admin.ModelAdmin):
    """Admin for Registration Applications"""
    
    list_display = [
        'user', 
        'requested_role', 
        'status', 
        'created_at', 
        'reviewed_at'
    ]
    
    list_filter = [
        'status', 
        'requested_role', 
        'created_at'
    ]
    
    search_fields = [
        'user__email', 
        'user__username', 
        'user__first_name', 
        'user__last_name',
        'motivation'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Application Details', {
            'fields': ('uid', 'user', 'requested_role', 'status')
        }),
        ('Application Content', {
            'fields': ('motivation', 'experience', 'publications', 'references')
        }),
        ('Documents', {
            'fields': ('cv', 'recommendation_letter', 'additional_documents')
        }),
        ('Review', {
            'fields': ('reviewed_by', 'review_notes', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = [
        'approve_applications', 
        'reject_applications',
        'mark_needs_info'
    ]
    
    def approve_applications(self, request, queryset):
        #from .utils import send_approval_email, generate_membership_number
        from .utils import send_approval_email
        from .views import generate_membership_number
        count = 0
        for application in queryset:
            if application.status in ['pending', 'needs_info']:
                application.status = 'approved'
                application.reviewed_by = request.user
                application.reviewed_at = timezone.now()
                application.save()
                
                # Update user
                user = application.user
                user.role = application.requested_role
                user.registration_status = 'approved'
                user.is_verified = True
                user.is_active_member = True
                user.membership_start_date = timezone.now()
                user.membership_expiry_date = timezone.now() + timezone.timedelta(days=365)
                user.save()
                
                # Generate membership number
                generate_membership_number(user)
                
                # Send approval email
                try:
                    send_approval_email(request, user)
                except:
                    pass
                count += 1
        
        self.message_user(request, f'{count} applications approved.')
    approve_applications.short_description = "Approve selected applications"
    
    def reject_applications(self, request, queryset):
        from .utils import send_rejection_email
        count = 0
        for application in queryset:
            if application.status in ['pending', 'needs_info']:
                application.status = 'rejected'
                application.reviewed_by = request.user
                application.review_notes = 'Rejected via admin action'
                application.reviewed_at = timezone.now()
                application.save()
                
                user = application.user
                user.registration_status = 'rejected'
                user.save()
                
                # Send rejection email
                try:
                    send_rejection_email(request, user, 'Your application has been rejected.')
                except:
                    pass
                count += 1
        
        self.message_user(request, f'{count} applications rejected.')
    reject_applications.short_description = "Reject selected applications"
    
    def mark_needs_info(self, request, queryset):
        count = 0
        for application in queryset:
            if application.status == 'pending':
                application.status = 'needs_info'
                application.reviewed_by = request.user
                application.reviewed_at = timezone.now()
                application.save()
                count += 1
        
        self.message_user(request, f'{count} applications marked as needing more information.')
    mark_needs_info.short_description = "Mark as needs more information"


@admin.register(RoleChangeRequest)
class RoleChangeRequestAdmin(admin.ModelAdmin):
    """Admin for Role Change Requests"""
    
    list_display = [
        'user', 
        'current_role', 
        'requested_role', 
        'status', 
        'created_at'
    ]
    
    list_filter = [
        'status', 
        'current_role', 
        'requested_role'
    ]
    
    search_fields = [
        'user__email', 
        'user__username',
        'reason'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Request Details', {
            'fields': ('user', 'current_role', 'requested_role', 'reason')
        }),
        ('Documents', {
            'fields': ('supporting_documents',)
        }),
        ('Review', {
            'fields': ('status', 'reviewed_by', 'review_notes', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        from django.utils import timezone
        count = 0
        for role_request in queryset:
            if role_request.status == 'pending':
                role_request.status = 'approved'
                role_request.reviewed_by = request.user
                role_request.reviewed_at = timezone.now()
                role_request.save()
                
                # Update user role
                user = role_request.user
                user.role = role_request.requested_role
                user.save()
                count += 1
        
        self.message_user(request, f'{count} role change requests approved.')
    approve_requests.short_description = "Approve selected requests"
    
    def reject_requests(self, request, queryset):
        from django.utils import timezone
        count = 0
        for role_request in queryset:
            if role_request.status == 'pending':
                role_request.status = 'rejected'
                role_request.reviewed_by = request.user
                role_request.reviewed_at = timezone.now()
                role_request.save()
                count += 1
        
        self.message_user(request, f'{count} role change requests rejected.')
    reject_requests.short_description = "Reject selected requests"


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    """Admin for User Activity Logs"""
    
    list_display = [
        'user', 
        'action_type', 
        'action_description', 
        'ip_address',
        'created_at'
    ]
    
    list_filter = [
        'action_type', 
        'created_at'
    ]
    
    search_fields = [
        'user__email', 
        'user__username', 
        'action_description'
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Activity Details', {
            'fields': ('user', 'action_type', 'action_description')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'referer_url')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    """Admin for User Devices"""
    
    list_display = [
        'user', 
        'device_name', 
        'device_type', 
        'last_login', 
        'is_trusted'
    ]
    
    list_filter = [
        'device_type', 
        'is_trusted',
        'os'
    ]
    
    search_fields = [
        'user__email', 
        'user__username', 
        'device_name',
        'device_id'
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Device Details', {
            'fields': ('user', 'device_type', 'device_name', 'device_id')
        }),
        ('Browser & OS', {
            'fields': ('browser', 'browser_version', 'os', 'os_version')
        }),
        ('Network', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Trust Status', {
            'fields': ('is_trusted', 'last_login')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
