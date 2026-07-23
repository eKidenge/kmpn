from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, RegistrationApplication, RoleChangeRequest, UserActivityLog, UserDevice


@admin.register(User)
class UserAdminConfig(UserAdmin):
    """Custom User Admin configuration"""
    
    # Fix: Change 'user_type' to 'role'
    list_display = [
        'email', 
        'username', 
        'get_full_name', 
        'role',  # Changed from 'user_type'
        'institution',
        'is_verified',
        'is_active_member',
        'is_active',
        'created_at'
    ]
    
    # Fix: Change 'user_type' to 'role'
    list_filter = [
        'role',  # Changed from 'user_type'
        'registration_status',
        'academic_level',
        'is_verified',
        'is_active_member',
        'is_active',
        'created_at'
    ]
    
    search_fields = [
        'email', 
        'username', 
        'first_name', 
        'last_name',
        'membership_number'
    ]
    
    ordering = ['-created_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'email', 'username', 'first_name', 'last_name', 'title',
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
                'membership_expiry_date', 'membership_fee_paid'
            )
        }),
        ('Social Links', {
            'fields': (
                'linkedin_url', 'researchgate_url',
                'google_scholar_url', 'orcid_id', 'twitter_url'
            )
        }),
        ('Permissions', {
            'fields': (
                'is_superuser', 'is_staff', 'groups', 'user_permissions'
            )
        }),
        ('Important Dates', {
            'fields': (
                'last_login', 'created_at', 'updated_at'
            )
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'first_name', 'last_name',
                'password1', 'password2', 'role'
            )
        }),
    )
    
    readonly_fields = (
        'membership_number', 'membership_start_date',
        'created_at', 'updated_at'
    )


@admin.register(RegistrationApplication)
class RegistrationApplicationAdmin(admin.ModelAdmin):
    """Admin for Registration Applications"""
    
    list_display = [
        'user', 'requested_role', 'status', 'created_at', 'reviewed_at'
    ]
    list_filter = ['status', 'requested_role', 'created_at']
    search_fields = ['user__email', 'user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_applications', 'reject_applications']
    
    fieldsets = (
        ('Application Details', {
            'fields': ('user', 'requested_role', 'status')
        }),
        ('Application Content', {
            'fields': ('motivation', 'experience', 'publications')
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
    
    def approve_applications(self, request, queryset):
        from django.utils import timezone
        from .utils import send_approval_email, generate_membership_number
        
        count = 0
        for application in queryset:
            if application.status == 'pending':
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
                send_approval_email(request, user)
                count += 1
        
        self.message_user(request, f'{count} applications approved.')
    approve_applications.short_description = "Approve selected applications"
    
    def reject_applications(self, request, queryset):
        from .utils import send_rejection_email
        
        count = 0
        for application in queryset:
            if application.status == 'pending':
                application.status = 'rejected'
                application.reviewed_by = request.user
                application.review_notes = 'Rejected via admin action'
                application.reviewed_at = timezone.now()
                application.save()
                
                user = application.user
                user.registration_status = 'rejected'
                user.save()
                
                # Send rejection email
                send_rejection_email(request, user, 'Your application has been rejected.')
                count += 1
        
        self.message_user(request, f'{count} applications rejected.')
    reject_applications.short_description = "Reject selected applications"


@admin.register(RoleChangeRequest)
class RoleChangeRequestAdmin(admin.ModelAdmin):
    """Admin for Role Change Requests"""
    
    list_display = ['user', 'current_role', 'requested_role', 'status', 'created_at']
    list_filter = ['status', 'current_role', 'requested_role']
    search_fields = ['user__email', 'user__username']
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
    
    list_display = ['user', 'action_type', 'action_description', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['user__email', 'user__username', 'action_description']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    """Admin for User Devices"""
    
    list_display = ['user', 'device_name', 'device_type', 'last_login', 'is_trusted']
    list_filter = ['device_type', 'is_trusted']
    search_fields = ['user__email', 'user__username', 'device_name']
    readonly_fields = ['created_at']