from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from .models import (
    Community, CommunityMember, CommunityPost, 
    Comment, CommunityLike
)
from .forms import (
    CommunityForm, CommunityPostForm, CommentForm,
    CommunitySettingsForm, CommunityMemberRoleForm
)
from accounts.decorators import user_activity_log, user_type_required
from accounts.models import User
from notifications.models import Notification

logger = logging.getLogger(__name__)


# ============================================================
# COMMUNITY LIST AND BROWSE VIEWS
# ============================================================

def community_list(request):
    """List all communities with filters and search"""
    communities = Community.objects.filter(is_active=True)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        communities = communities.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Filters
    community_type = request.GET.get('type', '')
    if community_type:
        communities = communities.filter(community_type=community_type)
    
    access_type = request.GET.get('access', '')
    if access_type:
        communities = communities.filter(access_type=access_type)
    
    # Sorting
    sort_by = request.GET.get('sort', '-member_count')
    communities = communities.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(communities, 12)
    page = request.GET.get('page', 1)
    
    try:
        communities = paginator.page(page)
    except PageNotAnInteger:
        communities = paginator.page(1)
    except EmptyPage:
        communities = paginator.page(paginator.num_pages)
    
    # Get user's communities
    user_communities = []
    if request.user.is_authenticated:
        user_communities = CommunityMember.objects.filter(
            user=request.user
        ).values_list('community_id', flat=True)
    
    context = {
        'communities': communities,
        'user_communities': user_communities,
        'search_query': search_query,
        'community_types': Community.COMMUNITY_TYPES,
        'access_types': Community.ACCESS_TYPES,
        'current_type': community_type,
        'current_access': access_type,
        'current_sort': sort_by,
        'page_title': 'Communities - KMPN',
    }
    return render(request, 'communities/list.html', context)


def community_browse(request):
    """Browse communities with advanced filtering"""
    communities = Community.objects.filter(is_active=True)
    
    # Get all unique tags
    all_tags = set()
    for community in communities:
        if community.tags:
            all_tags.update(community.tags)
    
    # Filter by tags
    tags_filter = request.GET.getlist('tags', [])
    if tags_filter:
        for tag in tags_filter:
            communities = communities.filter(tags__icontains=tag)
    
    # Filter by category
    category = request.GET.get('category', '')
    if category:
        communities = communities.filter(categories__icontains=category)
    
    # Get popular communities
    popular_communities = Community.objects.filter(
        is_active=True
    ).order_by('-member_count')[:5]
    
    # Get featured communities
    featured_communities = communities.filter(
        is_active=True
    ).order_by('-member_count', '-post_count')[:3]
    
    context = {
        'communities': communities,
        'popular_communities': popular_communities,
        'featured_communities': featured_communities,
        'all_tags': sorted(all_tags),
        'selected_tags': tags_filter,
        'page_title': 'Browse Communities - KMPN',
    }
    return render(request, 'communities/browse.html', context)


# ============================================================
# COMMUNITY CRUD OPERATIONS
# ============================================================

@login_required
@user_activity_log('community_create', 'Created a new community')
def community_create(request):
    """Create a new community"""
    if request.method == 'POST':
        form = CommunityForm(request.POST, request.FILES)
        if form.is_valid():
            community = form.save(commit=False)
            community.created_by = request.user
            
            # Set default access type if not specified
            if not community.access_type:
                community.access_type = 'members_only'
            
            community.save()
            
            # Add creator as admin
            CommunityMember.objects.create(
                community=community,
                user=request.user,
                role='admin'
            )
            
            # Update community statistics
            community.member_count = 1
            community.save()
            
            messages.success(request, f'Community "{community.name}" created successfully!')
            return redirect('communities:detail', slug=community.slug)
    else:
        form = CommunityForm()
    
    context = {
        'form': form,
        'page_title': 'Create Community - KMPN',
    }
    return render(request, 'communities/create.html', context)


@login_required
def community_detail(request, slug):
    """View community details"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    
    # Check if user has access
    if community.access_type == 'private':
        if not request.user.is_authenticated:
            messages.warning(request, 'This community is private. Please login to access.')
            return redirect('accounts:login')
        
        is_member = CommunityMember.objects.filter(
            community=community,
            user=request.user
        ).exists()
        
        if not is_member and community.created_by != request.user:
            messages.warning(request, 'This is a private community. Request access to join.')
            return redirect('communities:detail_public', slug=community.slug)
    
    # Get member status
    member_status = None
    if request.user.is_authenticated:
        try:
            member = CommunityMember.objects.get(
                community=community,
                user=request.user
            )
            member_status = member.role
        except CommunityMember.DoesNotExist:
            member_status = None
    
    # Get posts
    posts = CommunityPost.objects.filter(
        community=community,
        status__in=['published', 'pinned']
    ).select_related('author')
    
    # Filter posts
    post_type = request.GET.get('type', '')
    if post_type:
        posts = posts.filter(post_type=post_type)
    
    # Sort posts
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by == 'popular':
        posts = posts.order_by('-like_count', '-comment_count', '-created_at')
    elif sort_by == 'latest':
        posts = posts.order_by('-created_at')
    elif sort_by == 'oldest':
        posts = posts.order_by('created_at')
    else:
        posts = posts.order_by('-pinned', '-created_at')
    
    # Pagination
    paginator = Paginator(posts, 10)
    page = request.GET.get('page', 1)
    
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    
    # Get moderators
    moderators = CommunityMember.objects.filter(
        community=community,
        role__in=['admin', 'moderator']
    ).select_related('user')
    
    # Get member count
    member_count = community.members.count()
    
    # Increment view count
    community.view_count += 1
    community.save()
    
    context = {
        'community': community,
        'posts': posts,
        'moderators': moderators,
        'member_count': member_count,
        'member_status': member_status,
        'post_types': CommunityPost.POST_TYPES,
        'current_type': post_type,
        'current_sort': sort_by,
        'page_title': f'{community.name} - KMPN',
        'is_member': member_status is not None,
        'is_admin': member_status in ['admin', 'moderator'],
    }
    return render(request, 'communities/detail.html', context)


@login_required
def community_settings(request, slug):
    """Manage community settings"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    
    # Check permission
    if not community.members.filter(
        user=request.user,
        role__in=['admin']
    ).exists():
        messages.error(request, 'You do not have permission to manage this community.')
        return redirect('communities:detail', slug=community.slug)
    
    if request.method == 'POST':
        form = CommunitySettingsForm(request.POST, request.FILES, instance=community)
        if form.is_valid():
            community = form.save()
            messages.success(request, 'Community settings updated successfully!')
            return redirect('communities:settings', slug=community.slug)
    else:
        form = CommunitySettingsForm(instance=community)
    
    # Get member statistics
    member_stats = community.members.values('role').annotate(count=Count('id'))
    
    context = {
        'form': form,
        'community': community,
        'member_stats': member_stats,
        'page_title': f'Settings - {community.name}',
    }
    return render(request, 'communities/settings.html', context)


@login_required
def community_delete(request, slug):
    """Delete community"""
    community = get_object_or_404(Community, slug=slug)
    
    # Check permission
    if community.created_by != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete this community.')
        return redirect('communities:detail', slug=community.slug)
    
    if request.method == 'POST':
        community_name = community.name
        community.is_active = False
        community.save()
        
        messages.success(request, f'Community "{community_name}" has been deleted.')
        return redirect('communities:list')
    
    context = {
        'community': community,
        'page_title': f'Delete {community.name}',
    }
    return render(request, 'communities/delete.html', context)


# ============================================================
# COMMUNITY MEMBERSHIP MANAGEMENT
# ============================================================

@login_required
def community_join(request, slug):
    """Join a community"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    
    # Check if already a member
    if CommunityMember.objects.filter(community=community, user=request.user).exists():
        messages.warning(request, 'You are already a member of this community.')
        return redirect('communities:detail', slug=community.slug)
    
    # Check if community is full (if capacity is set)
    if community.max_members and community.member_count >= community.max_members:
        messages.error(request, 'This community has reached its maximum capacity.')
        return redirect('communities:detail', slug=community.slug)
    
    # Join the community
    CommunityMember.objects.create(
        community=community,
        user=request.user,
        role='member'
    )
    
    community.member_count += 1
    community.save()
    
    # Create notification
    Notification.objects.create(
        user=community.created_by,
        notification_type='community',
        title=f'New member joined {community.name}',
        message=f'{request.user.get_full_name()} has joined your community {community.name}.',
        link=f'/communities/{community.slug}/members/',
        metadata={
            'community_id': community.id,
            'user_id': request.user.id,
            'action': 'join'
        }
    )
    
    messages.success(request, f'You have successfully joined {community.name}!')
    return redirect('communities:detail', slug=community.slug)


@login_required
def community_leave(request, slug):
    """Leave a community"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    
    # Check if member
    member = CommunityMember.objects.filter(
        community=community,
        user=request.user
    ).first()
    
    if not member:
        messages.warning(request, 'You are not a member of this community.')
        return redirect('communities:detail', slug=community.slug)
    
    # Check if user is the only admin
    if member.role == 'admin':
        admin_count = CommunityMember.objects.filter(
            community=community,
            role='admin'
        ).count()
        
        if admin_count == 1:
            messages.error(
                request,
                'You are the only admin of this community. '
                'Please assign another admin before leaving.'
            )
            return redirect('communities:detail', slug=community.slug)
    
    if request.method == 'POST':
        member.delete()
        community.member_count -= 1
        community.save()
        
        messages.success(request, f'You have left {community.name}.')
        return redirect('communities:list')
    
    context = {
        'community': community,
        'page_title': f'Leave {community.name}',
    }
    return render(request, 'communities/leave.html', context)


@login_required
def community_members(request, slug):
    """View community members"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    
    # Check access for private communities
    if community.access_type == 'private':
        is_member = CommunityMember.objects.filter(
            community=community,
            user=request.user
        ).exists()
        
        if not is_member and community.created_by != request.user:
            messages.warning(request, 'This is a private community. Members only.')
            return redirect('communities:detail', slug=community.slug)
    
    members = CommunityMember.objects.filter(
        community=community
    ).select_related('user').order_by('-role', '-joined_at')
    
    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        members = members.filter(role=role_filter)
    
    # Search members
    search_query = request.GET.get('search', '')
    if search_query:
        members = members.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    paginator = Paginator(members, 20)
    page = request.GET.get('page', 1)
    
    try:
        members = paginator.page(page)
    except PageNotAnInteger:
        members = paginator.page(1)
    except EmptyPage:
        members = paginator.page(paginator.num_pages)
    
    context = {
        'community': community,
        'members': members,
        'role_choices': CommunityMember.ROLE_CHOICES,
        'current_role': role_filter,
        'search_query': search_query,
        'page_title': f'Members - {community.name}',
    }
    return render(request, 'communities/members.html', context)


@login_required
def community_member_role(request, slug, user_id):
    """Change member role"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    
    # Check permission
    if not community.members.filter(
        user=request.user,
        role='admin'
    ).exists():
        messages.error(request, 'You do not have permission to manage members.')
        return redirect('communities:detail', slug=community.slug)
    
    target_member = get_object_or_404(
        CommunityMember,
        community=community,
        user_id=user_id
    )
    
    # Prevent changing own role
    if target_member.user == request.user:
        messages.error(request, 'You cannot change your own role.')
        return redirect('communities:members', slug=community.slug)
    
    if request.method == 'POST':
        form = CommunityMemberRoleForm(request.POST, instance=target_member)
        if form.is_valid():
            old_role = target_member.role
            target_member = form.save()
            
            Notification.objects.create(
                user=target_member.user,
                notification_type='community',
                title=f'Role changed in {community.name}',
                message=f'Your role has been changed from {old_role} to {target_member.role}.',
                link=f'/communities/{community.slug}/',
                metadata={
                    'community_id': community.id,
                    'old_role': old_role,
                    'new_role': target_member.role
                }
            )
            
            messages.success(request, f'Role updated for {target_member.user.get_full_name()}.')
            return redirect('communities:members', slug=community.slug)
    else:
        form = CommunityMemberRoleForm(instance=target_member)
    
    context = {
        'form': form,
        'community': community,
        'target_member': target_member,
        'page_title': f'Change Role - {community.name}',
    }
    return render(request, 'communities/member_role.html', context)


@login_required
def community_remove_member(request, slug, user_id):
    """Remove member from community"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    
    # Check permission
    if not community.members.filter(
        user=request.user,
        role='admin'
    ).exists():
        messages.error(request, 'You do not have permission to remove members.')
        return redirect('communities:detail', slug=community.slug)
    
    target_member = get_object_or_404(
        CommunityMember,
        community=community,
        user_id=user_id
    )
    
    # Prevent removing self
    if target_member.user == request.user:
        messages.error(request, 'You cannot remove yourself. Use the Leave option.')
        return redirect('communities:members', slug=community.slug)
    
    if request.method == 'POST':
        user_name = target_member.user.get_full_name()
        target_member.delete()
        community.member_count -= 1
        community.save()
        
        messages.success(request, f'{user_name} has been removed from the community.')
        return redirect('communities:members', slug=community.slug)
    
    context = {
        'community': community,
        'target_member': target_member,
        'page_title': f'Remove Member - {community.name}',
    }
    return render(request, 'communities/remove_member.html', context)


# ============================================================
# COMMUNITY POSTS CRUD OPERATIONS
# ============================================================

@login_required
@user_activity_log('community_post_create', 'Created a post in community')
def create_post(request, slug):
    """Create a new post in community"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    
    # Check if user is a member (for non-public communities)
    if community.access_type != 'public':
        is_member = CommunityMember.objects.filter(
            community=community,
            user=request.user
        ).exists()
        
        if not is_member:
            messages.warning(request, 'You must be a member to post in this community.')
            return redirect('communities:detail', slug=community.slug)
    
    # Check if members can post
    if not community.allow_member_posts:
        is_moderator = community.members.filter(
            user=request.user,
            role__in=['admin', 'moderator']
        ).exists()
        
        if not is_moderator:
            messages.warning(request, 'Posting is currently restricted in this community.')
            return redirect('communities:detail', slug=community.slug)
    
    if request.method == 'POST':
        form = CommunityPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.community = community
            post.author = request.user
            
            # Auto-publish if user is moderator or if no moderation required
            if not community.require_moderation:
                post.status = 'published'
            else:
                post.status = 'draft'
            
            # Handle poll data
            if post.post_type == 'poll':
                poll_options = request.POST.get('poll_options', '')
                if poll_options:
                    options = [opt.strip() for opt in poll_options.split(',') if opt.strip()]
                    post.poll_data = {'options': options, 'votes': {}}
            
            post.save()
            
            # Handle tags
            tags = request.POST.get('tags', '')
            if tags:
                post.tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
                post.save()
            
            # Update community statistics
            community.post_count += 1
            community.save()
            
            # Create notifications for community members
            if post.status == 'published':
                self._notify_members_about_post(community, post)
            
            messages.success(request, 'Post created successfully!')
            return redirect('communities:post_detail', slug=community.slug, post_id=post.id)
    else:
        initial_data = {'community': community}
        form = CommunityPostForm(initial=initial_data)
    
    context = {
        'form': form,
        'community': community,
        'page_title': f'Create Post - {community.name}',
        'post_types': CommunityPost.POST_TYPES,
    }
    return render(request, 'communities/create_post.html', context)


def post_detail(request, slug, post_id):
    """View a single post"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    post = get_object_or_404(CommunityPost, id=post_id, community=community)
    
    # Check if post is accessible
    if post.status == 'draft' and post.author != request.user:
        if not request.user.is_staff:
            messages.warning(request, 'This post is not yet published.')
            return redirect('communities:detail', slug=community.slug)
    
    # Increment view count
    post.increment_view_count()
    
    # Get comments
    comments = Comment.objects.filter(
        post=post,
        is_approved=True,
        is_deleted=False
    ).select_related('author')
    
    # Get nested comments
    top_comments = comments.filter(parent=None)
    
    paginator = Paginator(top_comments, 20)
    page = request.GET.get('page', 1)
    
    try:
        top_comments = paginator.page(page)
    except PageNotAnInteger:
        top_comments = paginator.page(1)
    except EmptyPage:
        top_comments = paginator.page(paginator.num_pages)
    
    # Check if user has liked the post
    user_liked = False
    if request.user.is_authenticated:
        user_liked = CommunityLike.objects.filter(
            user=request.user,
            post=post
        ).exists()
    
    # Check if user is a moderator
    is_moderator = False
    if request.user.is_authenticated:
        is_moderator = community.members.filter(
            user=request.user,
            role__in=['admin', 'moderator']
        ).exists()
    
    context = {
        'post': post,
        'community': community,
        'comments': top_comments,
        'user_liked': user_liked,
        'is_moderator': is_moderator,
        'page_title': f'{post.title} - {community.name}',
        'comment_form': CommentForm(),
    }
    return render(request, 'communities/post_detail.html', context)


@login_required
def edit_post(request, slug, post_id):
    """Edit a post"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    post = get_object_or_404(CommunityPost, id=post_id, community=community)
    
    # Check permission
    if post.author != request.user:
        is_moderator = community.members.filter(
            user=request.user,
            role__in=['admin', 'moderator']
        ).exists()
        
        if not is_moderator and not request.user.is_staff:
            messages.error(request, 'You do not have permission to edit this post.')
            return redirect('communities:post_detail', slug=community.slug, post_id=post.id)
    
    if request.method == 'POST':
        form = CommunityPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save()
            
            # Update tags
            tags = request.POST.get('tags', '')
            if tags:
                post.tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
                post.save()
            
            messages.success(request, 'Post updated successfully!')
            return redirect('communities:post_detail', slug=community.slug, post_id=post.id)
    else:
        # Pre-fill tags
        initial_data = {}
        if post.tags:
            initial_data['tags'] = ', '.join(post.tags)
        form = CommunityPostForm(instance=post, initial=initial_data)
    
    context = {
        'form': form,
        'post': post,
        'community': community,
        'page_title': f'Edit Post - {community.name}',
    }
    return render(request, 'communities/edit_post.html', context)


@login_required
def delete_post(request, slug, post_id):
    """Delete a post"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    post = get_object_or_404(CommunityPost, id=post_id, community=community)
    
    # Check permission
    if post.author != request.user:
        is_moderator = community.members.filter(
            user=request.user,
            role__in=['admin', 'moderator']
        ).exists()
        
        if not is_moderator and not request.user.is_staff:
            messages.error(request, 'You do not have permission to delete this post.')
            return redirect('communities:post_detail', slug=community.slug, post_id=post.id)
    
    if request.method == 'POST':
        post.status = 'deleted'
        post.save()
        
        # Update community statistics
        community.post_count -= 1
        community.save()
        
        messages.success(request, 'Post deleted successfully!')
        return redirect('communities:detail', slug=community.slug)
    
    context = {
        'post': post,
        'community': community,
        'page_title': f'Delete Post - {community.name}',
    }
    return render(request, 'communities/delete_post.html', context)


@login_required
def pin_post(request, slug, post_id):
    """Pin or unpin a post"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    post = get_object_or_404(CommunityPost, id=post_id, community=community)
    
    # Check permission
    is_moderator = community.members.filter(
        user=request.user,
        role__in=['admin', 'moderator']
    ).exists()
    
    if not is_moderator and not request.user.is_staff:
        messages.error(request, 'You do not have permission to pin posts.')
        return redirect('communities:post_detail', slug=community.slug, post_id=post.id)
    
    if request.method == 'POST':
        if post.status == 'pinned':
            post.status = 'published'
            messages.success(request, 'Post unpinned successfully!')
        else:
            post.status = 'pinned'
            messages.success(request, 'Post pinned successfully!')
        
        post.save()
        return redirect('communities:post_detail', slug=community.slug, post_id=post.id)
    
    context = {
        'post': post,
        'community': community,
        'page_title': f'Pin Post - {community.name}',
    }
    return render(request, 'communities/pin_post.html', context)


# ============================================================
# COMMENTS CRUD OPERATIONS
# ============================================================

@login_required
def add_comment(request, slug, post_id):
    """Add a comment to a post"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    post = get_object_or_404(CommunityPost, id=post_id, community=community)
    
    # Check if user can comment
    if post.status not in ['published', 'pinned']:
        messages.warning(request, 'This post is not open for comments.')
        return redirect('communities:post_detail', slug=community.slug, post_id=post.id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            
            # Handle reply
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id)
                    comment.parent = parent_comment
                except Comment.DoesNotExist:
                    pass
            
            # Auto-approve if user is moderator or community doesn't require moderation
            is_moderator = community.members.filter(
                user=request.user,
                role__in=['admin', 'moderator']
            ).exists()
            
            if is_moderator:
                comment.is_approved = True
            
            comment.save()
            
            # Update post comment count
            post.comment_count += 1
            post.save()
            
            # Notify post author
            if post.author != request.user:
                Notification.objects.create(
                    user=post.author,
                    notification_type='community',
                    title=f'New comment on your post in {community.name}',
                    message=f'{request.user.get_full_name()} commented on your post "{post.title[:50]}"',
                    link=f'/communities/{community.slug}/post/{post.id}/',
                    metadata={
                        'post_id': post.id,
                        'comment_id': comment.id,
                        'community_id': community.id
                    }
                )
            
            # Notify parent comment author if it's a reply
            if comment.parent and comment.parent.author != request.user:
                Notification.objects.create(
                    user=comment.parent.author,
                    notification_type='community',
                    title=f'New reply to your comment in {community.name}',
                    message=f'{request.user.get_full_name()} replied to your comment on "{post.title[:50]}"',
                    link=f'/communities/{community.slug}/post/{post.id}/#comment-{comment.id}',
                    metadata={
                        'post_id': post.id,
                        'comment_id': comment.id,
                        'community_id': community.id
                    }
                )
            
            messages.success(request, 'Comment added successfully!')
            return redirect('communities:post_detail', slug=community.slug, post_id=post.id)
    
    messages.error(request, 'Invalid comment.')
    return redirect('communities:post_detail', slug=community.slug, post_id=post.id)


@login_required
def edit_comment(request, slug, comment_id):
    """Edit a comment"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    comment = get_object_or_404(Comment, id=comment_id, post__community=community)
    
    # Check permission
    if comment.author != request.user:
        is_moderator = community.members.filter(
            user=request.user,
            role__in=['admin', 'moderator']
        ).exists()
        
        if not is_moderator and not request.user.is_staff:
            messages.error(request, 'You do not have permission to edit this comment.')
            return redirect('communities:post_detail', slug=community.slug, post_id=comment.post.id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment = form.save()
            messages.success(request, 'Comment updated successfully!')
            return redirect('communities:post_detail', slug=community.slug, post_id=comment.post.id)
    else:
        form = CommentForm(instance=comment)
    
    context = {
        'form': form,
        'comment': comment,
        'community': community,
        'page_title': 'Edit Comment',
    }
    return render(request, 'communities/edit_comment.html', context)


@login_required
def delete_comment(request, slug, comment_id):
    """Delete a comment"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    comment = get_object_or_404(Comment, id=comment_id, post__community=community)
    
    # Check permission
    if comment.author != request.user:
        is_moderator = community.members.filter(
            user=request.user,
            role__in=['admin', 'moderator']
        ).exists()
        
        if not is_moderator and not request.user.is_staff:
            messages.error(request, 'You do not have permission to delete this comment.')
            return redirect('communities:post_detail', slug=community.slug, post_id=comment.post.id)
    
    if request.method == 'POST':
        comment.is_deleted = True
        comment.save()
        
        # Update post comment count
        post = comment.post
        post.comment_count -= 1
        post.save()
        
        messages.success(request, 'Comment deleted successfully!')
        return redirect('communities:post_detail', slug=community.slug, post_id=post.id)
    
    context = {
        'comment': comment,
        'community': community,
        'page_title': 'Delete Comment',
    }
    return render(request, 'communities/delete_comment.html', context)


# ============================================================
# LIKES AND INTERACTIONS
# ============================================================

@login_required
def like_post(request, slug, post_id):
    """Like or unlike a post"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    post = get_object_or_404(CommunityPost, id=post_id, community=community)
    
    # Check if already liked
    like = CommunityLike.objects.filter(
        user=request.user,
        post=post
    ).first()
    
    if like:
        # Unlike
        like.delete()
        post.like_count -= 1
        post.save()
        liked = False
        message = 'Post unliked.'
    else:
        # Like
        CommunityLike.objects.create(
            user=request.user,
            post=post
        )
        post.like_count += 1
        post.save()
        liked = True
        message = 'Post liked!'
        
        # Notify post author
        if post.author != request.user:
            Notification.objects.create(
                user=post.author,
                notification_type='community',
                title=f'New like on your post in {community.name}',
                message=f'{request.user.get_full_name()} liked your post "{post.title[:50]}"',
                link=f'/communities/{community.slug}/post/{post.id}/',
                metadata={
                    'post_id': post.id,
                    'community_id': community.id
                }
            )
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'like_count': post.like_count,
            'message': message
        })
    
    messages.success(request, message)
    return redirect('communities:post_detail', slug=community.slug, post_id=post.id)


@login_required
def like_comment(request, slug, comment_id):
    """Like or unlike a comment"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    comment = get_object_or_404(Comment, id=comment_id, post__community=community)
    
    # Check if already liked
    like = CommunityLike.objects.filter(
        user=request.user,
        comment=comment
    ).first()
    
    if like:
        like.delete()
        comment.like_count -= 1
        comment.save()
        liked = False
    else:
        CommunityLike.objects.create(
            user=request.user,
            comment=comment
        )
        comment.like_count += 1
        comment.save()
        liked = True
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'like_count': comment.like_count
        })
    
    return redirect('communities:post_detail', slug=community.slug, post_id=comment.post.id)


# ============================================================
# MODERATION AND ADMIN VIEWS
# ============================================================

@login_required
def moderate_community(request, slug):
    """Moderate community content"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    
    # Check permission
    is_moderator = community.members.filter(
        user=request.user,
        role__in=['admin', 'moderator']
    ).exists()
    
    if not is_moderator and not request.user.is_staff:
        messages.error(request, 'You do not have permission to moderate this community.')
        return redirect('communities:detail', slug=community.slug)
    
    # Get pending posts (draft status)
    pending_posts = CommunityPost.objects.filter(
        community=community,
        status='draft'
    ).order_by('-created_at')
    
    # Get reported comments
    reported_comments = Comment.objects.filter(
        post__community=community,
        is_deleted=False
    ).order_by('-created_at')
    
    # Filter reported comments (those with report_count > 0)
    reported_comments = reported_comments.filter(report_count__gt=0)
    
    paginator_posts = Paginator(pending_posts, 10)
    paginator_comments = Paginator(reported_comments, 10)
    
    page_posts = request.GET.get('page_posts', 1)
    page_comments = request.GET.get('page_comments', 1)
    
    try:
        pending_posts = paginator_posts.page(page_posts)
    except (PageNotAnInteger, EmptyPage):
        pending_posts = paginator_posts.page(1)
    
    try:
        reported_comments = paginator_comments.page(page_comments)
    except (PageNotAnInteger, EmptyPage):
        reported_comments = paginator_comments.page(1)
    
    context = {
        'community': community,
        'pending_posts': pending_posts,
        'reported_comments': reported_comments,
        'page_title': f'Moderate - {community.name}',
    }
    return render(request, 'communities/moderate.html', context)


@login_required
def approve_post(request, slug, post_id):
    """Approve a pending post"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    post = get_object_or_404(CommunityPost, id=post_id, community=community)
    
    # Check permission
    is_moderator = community.members.filter(
        user=request.user,
        role__in=['admin', 'moderator']
    ).exists()
    
    if not is_moderator and not request.user.is_staff:
        messages.error(request, 'You do not have permission to approve posts.')
        return redirect('communities:detail', slug=community.slug)
    
    if request.method == 'POST':
        post.status = 'published'
        post.save()
        
        # Notify author
        if post.author != request.user:
            Notification.objects.create(
                user=post.author,
                notification_type='community',
                title=f'Your post has been approved in {community.name}',
                message=f'Your post "{post.title[:50]}" has been approved and is now visible.',
                link=f'/communities/{community.slug}/post/{post.id}/',
                metadata={
                    'post_id': post.id,
                    'community_id': community.id,
                    'action': 'approve'
                }
            )
        
        messages.success(request, 'Post approved successfully!')
        return redirect('communities:moderate', slug=community.slug)
    
    context = {
        'post': post,
        'community': community,
        'page_title': f'Approve Post - {community.name}',
    }
    return render(request, 'communities/approve_post.html', context)


@login_required
def reject_post(request, slug, post_id):
    """Reject a pending post"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    post = get_object_or_404(CommunityPost, id=post_id, community=community)
    
    # Check permission
    is_moderator = community.members.filter(
        user=request.user,
        role__in=['admin', 'moderator']
    ).exists()
    
    if not is_moderator and not request.user.is_staff:
        messages.error(request, 'You do not have permission to reject posts.')
        return redirect('communities:detail', slug=community.slug)
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '')
        
        post.status = 'archived'
        post.save()
        
        # Notify author
        if post.author != request.user:
            Notification.objects.create(
                user=post.author,
                notification_type='community',
                title=f'Your post was not approved in {community.name}',
                message=f'Your post "{post.title[:50]}" was not approved. Reason: {rejection_reason}',
                link=f'/communities/{community.slug}/',
                metadata={
                    'post_id': post.id,
                    'community_id': community.id,
                    'reason': rejection_reason,
                    'action': 'reject'
                }
            )
        
        messages.success(request, 'Post rejected successfully!')
        return redirect('communities:moderate', slug=community.slug)
    
    context = {
        'post': post,
        'community': community,
        'page_title': f'Reject Post - {community.name}',
    }
    return render(request, 'communities/reject_post.html', context)


@login_required
def report_comment(request, slug, comment_id):
    """Report a comment"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    comment = get_object_or_404(Comment, id=comment_id, post__community=community)
    
    if request.method == 'POST':
        report_reason = request.POST.get('report_reason', '')
        
        if report_reason:
            comment.report_count += 1
            comment.save()
            
            # Notify moderators
            moderators = CommunityMember.objects.filter(
                community=community,
                role__in=['admin', 'moderator']
            ).select_related('user')
            
            for moderator in moderators:
                if moderator.user != request.user:
                    Notification.objects.create(
                        user=moderator.user,
                        notification_type='community',
                        title=f'Comment reported in {community.name}',
                        message=f'{request.user.get_full_name()} reported a comment in {community.name}',
                        link=f'/communities/{community.slug}/moderate/',
                        metadata={
                            'comment_id': comment.id,
                            'community_id': community.id,
                            'reason': report_reason
                        }
                    )
            
            messages.success(request, 'Comment reported successfully. Our moderators will review it.')
        else:
            messages.error(request, 'Please provide a reason for reporting.')
        
        return redirect('communities:post_detail', slug=community.slug, post_id=comment.post.id)
    
    context = {
        'comment': comment,
        'community': community,
        'page_title': 'Report Comment',
    }
    return render(request, 'communities/report_comment.html', context)


# ============================================================
# AJAX ENDPOINTS
# ============================================================

def search_communities(request):
    """AJAX endpoint to search communities"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    communities = Community.objects.filter(
        Q(is_active=True),
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(tags__icontains=query)
    )[:10]
    
    results = []
    for community in communities:
        is_member = False
        if request.user.is_authenticated:
            is_member = CommunityMember.objects.filter(
                community=community,
                user=request.user
            ).exists()
        
        results.append({
            'id': community.id,
            'name': community.name,
            'slug': community.slug,
            'member_count': community.member_count,
            'is_member': is_member,
            'logo_url': community.logo.url if community.logo else None,
        })
    
    return JsonResponse({'results': results})


def get_community_data(request, slug):
    """AJAX endpoint to get community data"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    
    # Check if user is a member
    is_member = False
    user_role = None
    if request.user.is_authenticated:
        try:
            member = CommunityMember.objects.get(
                community=community,
                user=request.user
            )
            is_member = True
            user_role = member.role
        except CommunityMember.DoesNotExist:
            pass
    
    data = {
        'id': community.id,
        'name': community.name,
        'slug': community.slug,
        'description': community.description,
        'community_type': community.community_type,
        'access_type': community.access_type,
        'member_count': community.member_count,
        'post_count': community.post_count,
        'view_count': community.view_count,
        'is_member': is_member,
        'user_role': user_role,
        'created_at': community.created_at.isoformat(),
        'logo_url': community.logo.url if community.logo else None,
        'banner_url': community.banner.url if community.banner else None,
    }
    
    return JsonResponse(data)


def get_post_comments(request, slug, post_id):
    """AJAX endpoint to load more comments"""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    post = get_object_or_404(CommunityPost, id=post_id, community=community)
    
    page = request.GET.get('page', 1)
    comments = Comment.objects.filter(
        post=post,
        is_approved=True,
        is_deleted=False
    ).select_related('author')
    
    paginator = Paginator(comments, 10)
    
    try:
        comments = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        return JsonResponse({'comments': [], 'has_next': False})
    
    comments_data = []
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'author': comment.author.get_full_name() or comment.author.username,
            'author_username': comment.author.username,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p'),
            'like_count': comment.like_count,
            'is_author': comment.author == request.user if request.user.is_authenticated else False,
            'replies': [],
            'reply_count': comment.replies.filter(is_approved=True, is_deleted=False).count()
        })
    
    return JsonResponse({
        'comments': comments_data,
        'has_next': comments.has_next(),
        'page': comments.number,
        'total_pages': paginator.num_pages
    })


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _notify_members_about_post(self, community, post):
    """Notify community members about new post"""
    # Get all members except the author
    members = CommunityMember.objects.filter(
        community=community
    ).exclude(user=post.author).select_related('user')
    
    for member in members:
        # Check if member wants notifications
        if member.notification_preferences.get('new_posts', True):
            Notification.objects.create(
                user=member.user,
                notification_type='community',
                title=f'New post in {community.name}',
                message=f'{post.author.get_full_name()} posted "{post.title[:50]}" in {community.name}',
                link=f'/communities/{community.slug}/post/{post.id}/',
                metadata={
                    'post_id': post.id,
                    'community_id': community.id,
                    'author_id': post.author.id
                }
            )


# ============================================================
# ERROR HANDLING VIEWS
# ============================================================

def community_not_found(request, exception=None):
    """Handle community not found error"""
    return render(request, 'communities/not_found.html', status=404)


def community_forbidden(request, exception=None):
    """Handle community access forbidden error"""
    return render(request, 'communities/forbidden.html', status=403)
