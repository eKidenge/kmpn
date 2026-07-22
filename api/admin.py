from django.contrib import admin
from .models import APIAccessLog, APIToken, APIWebhook, APIWebhookLog


@admin.register(APIAccessLog)
class APIAccessLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'endpoint', 'method', 'status_code', 'created_at']
    list_filter = ['status_code', 'method', 'created_at']
    search_fields = ['endpoint', 'user__email']
    readonly_fields = ['user', 'endpoint', 'method', 'status_code', 'response_time',
                      'ip_address', 'user_agent', 'request_data', 'response_data']
    date_hierarchy = 'created_at'


@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'is_active', 'is_revoked', 'created_at']
    list_filter = ['is_active', 'is_revoked', 'created_at']
    search_fields = ['user__email', 'name', 'token']
    readonly_fields = ['token', 'created_at']


@admin.register(APIWebhook)
class APIWebhookAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'url', 'is_active', 'last_triggered']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'url', 'user__email']


@admin.register(APIWebhookLog)
class APIWebhookLogAdmin(admin.ModelAdmin):
    list_display = ['webhook', 'event', 'success', 'response_code', 'created_at']
    list_filter = ['success', 'created_at']
    search_fields = ['webhook__name', 'event']
    readonly_fields = ['webhook', 'event', 'payload', 'response_code', 
                      'response_body', 'error', 'duration', 'success', 'retry_count']
    date_hierarchy = 'created_at'