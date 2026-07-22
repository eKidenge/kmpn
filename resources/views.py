from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Avg
from django.utils import timezone
from .models import Resource, ResourceCategory, ResourceRating, ResourceDownload
from .forms import ResourceForm, ResourceRatingForm, ResourceFilterForm, ResourceSearchForm
from accounts.decorators import user_activity_log, user_type_required
from notifications.models import Notification


def resource_list(request):
    """List all resources"""
    resources = Resource.objects.filter(
        is_published=True
    ).order_by('-created_at')
    
    # Filters
    filter_form = ResourceFilterForm(request.GET)
    
    if filter_form.is_valid():
        resource_type = filter_form.cleaned_data.get('resource_type')
        if resource_type:
            resources = resources.filter(resource_type=resource_type)
        
        access_type = filter_form.cleaned_data.get('access_type')
        if access_type:
            resources = resources.filter(access_type=access_type)
        
        category = filter_form.cleaned_data.get('category')
        if category:
            resources = resources.filter(categories=category)
        
        search = filter_form.cleaned_data.get('search')
        if search:
            resources = resources.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(keywords__icontains=search) |
                Q(author__icontains=search)
            )
        
        sort_by = filter_form.cleaned_data.get('sort_by')
        if sort_by:
            resources = resources.order_by(sort_by)
    
    # Get featured resources
    featured_resources = resources.filter(is_featured=True)[:5]
    
    # Get categories
    categories = ResourceCategory.objects.filter(is_active=True)
    
    paginator = Paginator(resources, 12)
    page = request.GET.get('page', 1)
    
    try:
        resources = paginator.page(page)
    except PageNotAnInteger:
        resources = paginator.page(1)
    except EmptyPage:
        resources = paginator.page(paginator.num_pages)
    
    context = {
        'resources': resources,
        'featured_resources': featured_resources,
        'categories': categories,
        'filter_form': filter_form,
        'page_title': 'Resources - KMPN',
    }
    return render(request, 'resources/list.html', context)


def resource_detail(request, slug):
    """View resource detail"""
    resource = get_object_or_404(Resource, slug=slug, is_published=True)
    
    # Increment view count
    resource.increment_view_count()
    
    # Get ratings
    ratings = resource.ratings.all().order_by('-created_at')
    average_rating = resource.ratings.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Check if user has rated
    user_rating = None
    if request.user.is_authenticated:
        user_rating = resource.ratings.filter(user=request.user).first()
    
    # Get related resources
    related_resources = Resource.objects.filter(
        is_published=True,
        categories__in=resource.categories.all()
    ).exclude(id=resource.id).distinct()[:5]
    
    context = {
        'resource': resource,
        'ratings': ratings[:10],
        'average_rating': average_rating,
        'user_rating': user_rating,
        'related_resources': related_resources,
        'rating_form': ResourceRatingForm() if request.user.is_authenticated else None,
        'page_title': resource.title,
    }
    return render(request, 'resources/detail.html', context)


@login_required
def resource_download(request, slug):
    """Download resource file"""
    resource = get_object_or_404(Resource, slug=slug, is_published=True)
    
    # Check access
    if resource.access_type == 'members_only' and not request.user.is_authenticated:
        messages.error(request, 'Please login to download this resource.')
        return redirect('accounts:login')
    
    if resource.access_type == 'premium':
        try:
            member = Member.objects.get(user=request.user)
            if not member.is_active_member():
                messages.error(request, 'Premium membership required to download this resource.')
                return redirect('members:upgrade')
        except Member.DoesNotExist:
            messages.error(request, 'Please complete your member profile to download this resource.')
            return redirect('members:edit_profile')
    
    # Track download
    ResourceDownload.objects.create(
        resource=resource,
        user=request.user,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    resource.increment_download_count()
    
    # Return file or redirect
    if resource.file:
        response = FileResponse(
            resource.file.open('rb'),
            as_attachment=True,
            filename=resource.file.name.split('/')[-1]
        )
        return response
    elif resource.external_url:
        return redirect(resource.external_url)
    else:
        messages.error(request, 'File not available for download.')
        return redirect('resources:detail', slug=resource.slug)


@login_required
@user_activity_log('resource_rate', 'Rated resource')
def rate_resource(request, slug):
    """Rate a resource"""
    resource = get_object_or_404(Resource, slug=slug, is_published=True)
    
    if request.method == 'POST':
        form = ResourceRatingForm(request.POST)
        if form.is_valid():
            rating, created = ResourceRating.objects.update_or_create(
                resource=resource,
                user=request.user,
                defaults={
                    'rating': form.cleaned_data['rating'],
                    'review': form.cleaned_data.get('review', '')
                }
            )
            
            # Update average rating
            avg_rating = resource.ratings.aggregate(Avg('rating'))['rating__avg']
            resource.average_rating = avg_rating or 0
            resource.rating_count = resource.ratings.count()
            resource.save()
            
            messages.success(request, 'Rating submitted successfully!')
            return redirect('resources:detail', slug=resource.slug)
    else:
        form = ResourceRatingForm()
    
    context = {
        'form': form,
        'resource': resource,
        'page_title': f'Rate {resource.title}',
    }
    return render(request, 'resources/rate.html', context)


@login_required
@user_activity_log('resource_create', 'Created resource')
def resource_create(request):
    """Create new resource"""
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.created_by = request.user
            
            # Auto-publish for admins/moderators
            if request.user.user_type in ['admin', 'moderator']:
                resource.is_published = True
            
            resource.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, 'Resource created successfully!')
            return redirect('resources:detail', slug=resource.slug)
    else:
        form = ResourceForm()
    
    context = {
        'form': form,
        'page_title': 'Create Resource - KMPN',
    }
    return render(request, 'resources/create.html', context)


@login_required
def edit_resource(request, slug):
    """Edit resource"""
    resource = get_object_or_404(Resource, slug=slug)
    
    # Check permission
    if resource.created_by != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this resource.')
        return redirect('resources:detail', slug=resource.slug)
    
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            resource = form.save()
            messages.success(request, 'Resource updated successfully!')
            return redirect('resources:detail', slug=resource.slug)
    else:
        form = ResourceForm(instance=resource)
    
    context = {
        'form': form,
        'resource': resource,
        'page_title': f'Edit {resource.title}',
    }
    return render(request, 'resources/edit.html', context)


@login_required
def delete_resource(request, slug):
    """Delete resource"""
    resource = get_object_or_404(Resource, slug=slug)
    
    # Check permission
    if resource.created_by != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete this resource.')
        return redirect('resources:detail', slug=resource.slug)
    
    if request.method == 'POST':
        resource_title = resource.title
        resource.delete()
        messages.success(request, f'Resource "{resource_title}" deleted successfully!')
        return redirect('resources:list')
    
    context = {
        'resource': resource,
        'page_title': f'Delete {resource.title}',
    }
    return render(request, 'resources/delete.html', context)


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# AJAX Endpoints

@login_required
def search_resources_ajax(request):
    """AJAX endpoint for searching resources"""
    form = ResourceSearchForm(request.GET)
    
    resources = Resource.objects.filter(is_published=True)
    
    if form.is_valid():
        q = form.cleaned_data.get('q')
        resource_type = form.cleaned_data.get('resource_type')
        
        if q:
            resources = resources.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(keywords__icontains=q)
            )
        
        if resource_type:
            resources = resources.filter(resource_type=resource_type)
    
    resources = resources[:20]
    
    results = []
    for resource in resources:
        results.append({
            'id': resource.id,
            'title': resource.title,
            'slug': resource.slug,
            'resource_type': resource.resource_type,
            'access_type': resource.access_type,
            'download_count': resource.download_count,
            'cover_image': resource.cover_image.url if resource.cover_image else None,
        })
    
    return JsonResponse({'results': results})


@login_required
def get_resource_stats(request, slug):
    """Get resource statistics (AJAX)"""
    resource = get_object_or_404(Resource, slug=slug)
    
    return JsonResponse({
        'view_count': resource.view_count,
        'download_count': resource.download_count,
        'like_count': resource.like_count,
        'rating_count': resource.rating_count,
        'average_rating': resource.average_rating,
    })


@login_required
def toggle_featured(request, slug):
    """Toggle featured status (admin only)"""
    if not request.user.user_type in ['admin', 'moderator']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    resource = get_object_or_404(Resource, slug=slug)
    resource.is_featured = not resource.is_featured
    resource.save()
    
    return JsonResponse({
        'is_featured': resource.is_featured,
        'message': f'Resource {"featured" if resource.is_featured else "unfeatured"} successfully!'
    })