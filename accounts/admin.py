from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, UserActivityLog, UserDevice


class UserAdminConfig(UserAdmin):
    """Custom User Admin"""
    
    list_display = (
        'email', 'username', 'first_name', 'last_name', 'user_type',
        'is_active', 'is_verified', 'is_active_member', 'member_status_badge'
    )
    list_filter = ('user_type', 'is_active', 'is_verified', 'is_active_member')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'membership_number')
    ordering = ('-date_joined',)
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'username', 'email', 'first_name', 'last_name', 'phone_number',
                'profile_picture', 'bio'
            )
        }),
        ('Academic Information', {
            'fields': ('institution', 'department', 'degree_level', 'research_interests')
        }),
        ('Membership Information', {
            'fields': (
                'user_type', 'is_verified', 'is_active_member',
                'membership_number', 'membership_start_date', 'membership_expiry_date'
            )
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
        ('Social Links', {
            'fields': ('linkedin_url', 'researchgate_url', 'google_scholar_url', 'orcid_id')
        }),
        ('Preferences', {
            'fields': ('newsletter_subscribed', 'notification_preferences')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'user_type')
        }),
    )
    
    def member_status_badge(self, obj):
        """Display member status badge"""
        if obj.is_active_member and obj.membership_expiry_date:
            from django.utils import timezone
            if timezone.now() > obj.membership_expiry_date:
                return format_html('<span style="color: red;">Expired</span>')
            return format_html('<span style="color: green;">Active</span>')
        return format_html('<span style="color: gray;">Inactive</span>')
    
    member_status_badge.short_description = 'Membership Status'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related()


class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'action_description', 'created_at')
    list_filter = ('action_type', 'created_at')
    search_fields = ('user__email', 'action_description')
    readonly_fields = ('user', 'action_type', 'action_description', 'ip_address', 'user_agent', 'metadata')
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False


class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_name', 'device_type', 'is_trusted', 'last_login')
    list_filter = ('device_type', 'is_trusted')
    search_fields = ('user__email', 'device_name', 'device_id')
    readonly_fields = ('user', 'device_id', 'device_type', 'device_name', 'ip_address', 'user_agent')


admin.site.register(User, UserAdminConfig)
admin.site.register(UserActivityLog, UserActivityLogAdmin)
admin.site.register(UserDevice, UserDeviceAdmin)
