# resources/admin.py - FINAL FIXED VERSION

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count, Avg, Sum
from .models import ResourceCategory, Resource, ResourceRating, ResourceDownload


class ResourceCategoryInline(admin.TabularInline):
    model = ResourceCategory
    fields = ('name', 'slug', 'resource_count', 'is_active')
    readonly_fields = ('resource_count',)
    extra = 0
    show_change_link = True


@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'resource_count', 'parent', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('name', 'description', 'slug')
    readonly_fields = ('slug', 'resource_count', 'created_at', 'updated_at', 'resources_link')
    
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'slug', 'description', 'icon')}),
        ('Hierarchy', {'fields': ('parent', 'order')}),
        ('Status', {'fields': ('is_active',)}),
        ('Statistics', {'fields': ('resource_count', 'resources_link'), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    inlines = [ResourceCategoryInline]
    actions = ['activate_categories', 'deactivate_categories', 'reset_statistics']
    
    def resources_link(self, obj):
        url = reverse('admin:resources_resource_changelist') + f'?categories__id={obj.id}'
        return format_html('<a href="{}" style="font-weight: bold; color: #c9a84c;">{} resources</a>', url, obj.resource_count)
    resources_link.short_description = 'Resources'
    
    def activate_categories(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} category(ies) activated successfully.')
    activate_categories.short_description = 'Activate selected categories'
    
    def deactivate_categories(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} category(ies) deactivated successfully.')
    deactivate_categories.short_description = 'Deactivate selected categories'
    
    def reset_statistics(self, request, queryset):
        for category in queryset:
            category.resource_count = category.resources.count()
            category.save()
        self.message_user(request, f'Statistics reset for {queryset.count()} category(ies).')
    reset_statistics.short_description = 'Reset statistics'
    
    def save_model(self, request, obj, form, change):
        if not change and not obj.slug:
            from django.utils.text import slugify
            obj.slug = slugify(obj.name)
        super().save_model(request, obj, form, change)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'resource_type', 'access_type', 'is_published', 'is_featured',
        'view_count', 'download_count', 'created_by', 'created_at'
    )
    
    list_filter = ('resource_type', 'access_type', 'is_published', 'is_featured', 'created_at', 'categories')
    search_fields = ('title', 'description', 'author', 'publisher', 'keywords', 'created_by__email', 'created_by__username')
    
    readonly_fields = (
        'slug', 'view_count', 'download_count', 'like_count', 'rating_count', 'average_rating',
        'created_at', 'updated_at'
    )
    
    fieldsets = (
        ('Basic Information', {'fields': ('title', 'slug', 'description', 'resource_type', 'access_type')}),
        ('Categories', {'fields': ('categories',)}),
        ('File Information', {'fields': ('file', 'cover_image', 'external_url')}),
        ('Content', {'fields': ('content',), 'classes': ('collapse',)}),
        ('Metadata', {'fields': ('author', 'author_email', 'publisher', 'publication_date', 'version', 'is_latest_version')}),
        ('Keywords', {'fields': ('keywords',), 'classes': ('collapse',)}),
        ('Status & Featured', {'fields': ('is_published', 'is_featured')}),
        ('Statistics', {'fields': ('view_count', 'download_count', 'like_count', 'rating_count', 'average_rating'), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_by', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    filter_horizontal = ('categories',)
    
    actions = [
        'publish_resources', 'unpublish_resources', 'feature_resources', 'unfeature_resources',
        'make_public', 'make_members_only', 'make_premium', 'duplicate_resources', 'delete_resources', 'export_resources'
    ]
    
    def publish_resources(self, request, queryset):
        count = queryset.update(is_published=True)
        self.message_user(request, f'{count} resource(s) published successfully.')
    publish_resources.short_description = 'Publish selected resources'
    
    def unpublish_resources(self, request, queryset):
        count = queryset.update(is_published=False)
        self.message_user(request, f'{count} resource(s) unpublished successfully.')
    unpublish_resources.short_description = 'Unpublish selected resources'
    
    def feature_resources(self, request, queryset):
        count = queryset.update(is_featured=True)
        self.message_user(request, f'{count} resource(s) featured successfully.')
    feature_resources.short_description = 'Feature selected resources'
    
    def unfeature_resources(self, request, queryset):
        count = queryset.update(is_featured=False)
        self.message_user(request, f'{count} resource(s) unfeatured successfully.')
    unfeature_resources.short_description = 'Unfeature selected resources'
    
    def make_public(self, request, queryset):
        count = queryset.update(access_type='public')
        self.message_user(request, f'{count} resource(s) made public.')
    make_public.short_description = 'Make public'
    
    def make_members_only(self, request, queryset):
        count = queryset.update(access_type='members_only')
        self.message_user(request, f'{count} resource(s) made members only.')
    make_members_only.short_description = 'Make members only'
    
    def make_premium(self, request, queryset):
        count = queryset.update(access_type='premium')
        self.message_user(request, f'{count} resource(s) made premium.')
    make_premium.short_description = 'Make premium'
    
    def duplicate_resources(self, request, queryset):
        count = 0
        for resource in queryset:
            old_id = resource.id
            resource.pk = None
            resource.title = f"{resource.title} (Copy)"
            resource.slug = None
            resource.view_count = 0
            resource.download_count = 0
            resource.like_count = 0
            resource.rating_count = 0
            resource.average_rating = 0.0
            resource.is_published = False
            resource.created_at = timezone.now()
            resource.updated_at = timezone.now()
            resource.save()
            resource.categories.set(queryset.get(id=old_id).categories.all())
            count += 1
        self.message_user(request, f'{count} resource(s) duplicated successfully.')
    duplicate_resources.short_description = 'Duplicate selected resources'
    
    def delete_resources(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} resource(s) deleted successfully.')
    delete_resources.short_description = 'Delete selected resources'
    
    def export_resources(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="resources_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Title', 'Type', 'Access', 'Author', 'Publisher', 'Views', 'Downloads', 'Rating', 'Created At'])
        
        for resource in queryset:
            writer.writerow([
                resource.title,
                resource.get_resource_type_display(),
                resource.get_access_type_display(),
                resource.author or '',
                resource.publisher or '',
                resource.view_count,
                resource.download_count,
                resource.average_rating,
                resource.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        return response
    export_resources.short_description = 'Export selected resources as CSV'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(ResourceRating)
class ResourceRatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'resource', 'user', 'rating_display', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('resource__title', 'user__email', 'user__username', 'review')
    readonly_fields = ('created_at', 'updated_at', 'rating_display')
    
    fieldsets = (
        ('Rating Information', {'fields': ('resource', 'user', 'rating_display', 'rating')}),
        ('Review', {'fields': ('review',), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def rating_display(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: #f1c40f; font-size: 1.1rem;">{} ({})</span>', stars, obj.rating)
    rating_display.short_description = 'Rating'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('resource', 'user')


@admin.register(ResourceDownload)
class ResourceDownloadAdmin(admin.ModelAdmin):
    list_display = ('id', 'resource', 'user', 'ip_address', 'downloaded_at')
    list_filter = ('downloaded_at',)
    search_fields = ('resource__title', 'user__email', 'user__username', 'ip_address')
    readonly_fields = ('downloaded_at', 'ip_address', 'user_agent')
    
    fieldsets = (
        ('Download Information', {'fields': ('resource', 'user')}),
        ('Technical Details', {'fields': ('ip_address', 'user_agent'), 'classes': ('collapse',)}),
        ('Timestamp', {'fields': ('downloaded_at',)}),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('resource', 'user')


admin.site.site_header = 'KMPN Resources Administration'
admin.site.site_title = 'KMPN Resources Admin'
admin.site.index_title = 'Resources Administration'