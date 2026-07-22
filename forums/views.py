from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone
from .models import ForumCategory, ForumThread, ForumReply, ForumLike, ForumReport
from .forms import ForumThreadForm, ForumReplyForm, ForumReportForm, ForumSearchForm
from accounts.decorators import user_activity_log, user_type_required
from notifications.models import Notification


def forum_list(request):
    """List all forum categories and threads"""
    categories = ForumCategory.objects.filter(is_active=True)
    
    # Get recent threads across all categories
    recent_threads = ForumThread.objects.filter(
        status__in=['open', 'pinned']
    ).order_by('-is_sticky', '-last_activity')[:10]
    
    # Search form
    search_form = ForumSearchForm(request.GET)
    
    # Handle search
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        category = search_form.cleaned_data.get('category')
        sort_by = search_form.cleaned_data.get('sort_by', '-last_activity')
        
        threads = ForumThread.objects.filter(status__in=['open', 'pinned'])
        
        if search_query:
            threads = threads.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(author__username__icontains=search_query) |
                Q(author__first_name__icontains=search_query) |
                Q(author__last_name__icontains=search_query)
            )
        
        if category:
            threads = threads.filter(category=category)
        
        # FIXED: Only apply ordering if sort_by is not empty
        if sort_by:
            threads = threads.order_by(sort_by)
        else:
            threads = threads.order_by('-is_sticky', '-last_activity')
    else:
        threads = ForumThread.objects.filter(
            status__in=['open', 'pinned']
        ).order_by('-is_sticky', '-last_activity')
    
    paginator = Paginator(threads, 20)
    page = request.GET.get('page', 1)
    
    try:
        threads = paginator.page(page)
    except PageNotAnInteger:
        threads = paginator.page(1)
    except EmptyPage:
        threads = paginator.page(paginator.num_pages)
    
    context = {
        'categories': categories,
        'threads': threads,
        'recent_threads': recent_threads,
        'search_form': search_form,
        'page_title': 'Forums - KMPN',
    }
    return render(request, 'forums/list.html', context)


def forum_category(request, slug):
    """View threads in a category"""
    category = get_object_or_404(ForumCategory, slug=slug, is_active=True)
    
    threads = ForumThread.objects.filter(
        category=category,
        status__in=['open', 'pinned']
    ).order_by('-is_sticky', '-last_activity')
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        threads = threads.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(author__username__icontains=search_query)
        )
    
    paginator = Paginator(threads, 20)
    page = request.GET.get('page', 1)
    
    try:
        threads = paginator.page(page)
    except PageNotAnInteger:
        threads = paginator.page(1)
    except EmptyPage:
        threads = paginator.page(paginator.num_pages)
    
    context = {
        'category': category,
        'threads': threads,
        'search_query': search_query,
        'page_title': f'{category.name} - Forums',
    }
    return render(request, 'forums/category.html', context)


def thread_detail(request, thread_id):
    """View forum thread"""
    thread = get_object_or_404(ForumThread, id=thread_id)
    
    # Increment view count
    thread.view_count += 1
    thread.save()
    
    # Get replies
    replies = ForumReply.objects.filter(
        thread=thread,
        is_approved=True,
        is_deleted=False
    ).select_related('author')
    
    paginator = Paginator(replies, 20)
    page = request.GET.get('page', 1)
    
    try:
        replies = paginator.page(page)
    except PageNotAnInteger:
        replies = paginator.page(1)
    except EmptyPage:
        replies = paginator.page(paginator.num_pages)
    
    # Check if user can reply
    can_reply = thread.status != 'closed' and not thread.is_locked
    
    context = {
        'thread': thread,
        'replies': replies,
        'can_reply': can_reply,
        'reply_form': ForumReplyForm() if can_reply else None,
        'page_title': thread.title,
    }
    return render(request, 'forums/thread_detail.html', context)


@login_required
@user_activity_log('forum_create', 'Created forum thread')
def create_thread(request, category_slug=None):
    """Create new forum thread"""
    if category_slug:
        category = get_object_or_404(ForumCategory, slug=category_slug)
    else:
        category = None
    
    if request.method == 'POST':
        form = ForumThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.author = request.user
            if category:
                thread.category = category
            else:
                thread.category = form.cleaned_data['category']
            thread.save()
            
            # Save tags
            tags = request.POST.get('tags', '')
            if tags:
                thread.tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
                thread.save()
            
            # Update category statistics
            thread.category.thread_count += 1
            thread.category.save()
            
            messages.success(request, 'Thread created successfully!')
            return redirect('forums:thread_detail', thread_id=thread.id)
    else:
        form = ForumThreadForm(initial={'category': category})
    
    context = {
        'form': form,
        'category': category,
        'page_title': 'Create Thread - Forums',
    }
    return render(request, 'forums/create_thread.html', context)


@login_required
@user_activity_log('forum_reply', 'Replied to forum thread')
def create_reply(request, thread_id):
    """Create reply to forum thread"""
    thread = get_object_or_404(ForumThread, id=thread_id)
    
    # Check if thread is locked
    if thread.is_locked:
        messages.error(request, 'This thread is locked and cannot be replied to.')
        return redirect('forums:thread_detail', thread_id=thread.id)
    
    # Check if user is the author or if thread is open
    if thread.status == 'closed' and thread.author != request.user:
        messages.error(request, 'This thread is closed.')
        return redirect('forums:thread_detail', thread_id=thread.id)
    
    if request.method == 'POST':
        form = ForumReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.thread = thread
            reply.author = request.user
            reply.save()
            
            # Update thread statistics
            thread.reply_count += 1
            thread.last_activity = timezone.now()
            thread.save()
            
            # Notify thread author
            if thread.author != request.user:
                Notification.objects.create(
                    user=thread.author,
                    notification_type='forum',
                    title=f'New reply to your thread: {thread.title[:50]}',
                    message=f'{request.user.get_full_name()} replied to your thread "{thread.title[:50]}"',
                    link=f'/forums/thread/{thread.id}/',
                    metadata={
                        'thread_id': thread.id,
                        'reply_id': reply.id
                    }
                )
            
            messages.success(request, 'Reply posted successfully!')
            return redirect('forums:thread_detail', thread_id=thread.id)
    else:
        form = ForumReplyForm()
    
    context = {
        'form': form,
        'thread': thread,
        'page_title': f'Reply to {thread.title}',
    }
    return render(request, 'forums/create_reply.html', context)


@login_required
def like_thread(request, thread_id):
    """Like or unlike a forum thread"""
    thread = get_object_or_404(ForumThread, id=thread_id)
    
    # Check if already liked
    like, created = ForumLike.objects.get_or_create(
        user=request.user,
        thread=thread,
        like_type='thread'
    )
    
    if not created:
        # Unlike
        like.delete()
        thread.like_count -= 1
        thread.save()
        liked = False
    else:
        thread.like_count += 1
        thread.save()
        liked = True
    
    # Notify thread author
    if liked and thread.author != request.user:
        Notification.objects.create(
            user=thread.author,
            notification_type='forum',
            title=f'Someone liked your thread: {thread.title[:50]}',
            message=f'{request.user.get_full_name()} liked your thread "{thread.title[:50]}"',
            link=f'/forums/thread/{thread.id}/',
            metadata={
                'thread_id': thread.id,
                'action': 'like'
            }
        )
    
    return JsonResponse({
        'liked': liked,
        'like_count': thread.like_count
    })


@login_required
def like_reply(request, reply_id):
    """Like or unlike a forum reply"""
    reply = get_object_or_404(ForumReply, id=reply_id)
    
    # Check if already liked
    like, created = ForumLike.objects.get_or_create(
        user=request.user,
        reply=reply,
        like_type='reply'
    )
    
    if not created:
        like.delete()
        reply.like_count -= 1
        reply.save()
        liked = False
    else:
        reply.like_count += 1
        reply.save()
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'like_count': reply.like_count
    })


@login_required
def edit_thread(request, thread_id):
    """Edit forum thread"""
    thread = get_object_or_404(ForumThread, id=thread_id)
    
    # Check permission
    if thread.author != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this thread.')
        return redirect('forums:thread_detail', thread_id=thread.id)
    
    if request.method == 'POST':
        form = ForumThreadForm(request.POST, instance=thread)
        if form.is_valid():
            thread = form.save()
            messages.success(request, 'Thread updated successfully!')
            return redirect('forums:thread_detail', thread_id=thread.id)
    else:
        form = ForumThreadForm(instance=thread)
    
    context = {
        'form': form,
        'thread': thread,
        'page_title': f'Edit {thread.title}',
    }
    return render(request, 'forums/edit_thread.html', context)


@login_required
def edit_reply(request, reply_id):
    """Edit forum reply"""
    reply = get_object_or_404(ForumReply, id=reply_id)
    
    # Check permission
    if reply.author != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this reply.')
        return redirect('forums:thread_detail', thread_id=reply.thread.id)
    
    if request.method == 'POST':
        form = ForumReplyForm(request.POST, instance=reply)
        if form.is_valid():
            reply = form.save()
            messages.success(request, 'Reply updated successfully!')
            return redirect('forums:thread_detail', thread_id=reply.thread.id)
    else:
        form = ForumReplyForm(instance=reply)
    
    context = {
        'form': form,
        'reply': reply,
        'page_title': 'Edit Reply',
    }
    return render(request, 'forums/edit_reply.html', context)


@login_required
def report_content(request, content_type, content_id):
    """Report inappropriate content"""
    content = None
    if content_type == 'thread':
        content = get_object_or_404(ForumThread, id=content_id)
    elif content_type == 'reply':
        content = get_object_or_404(ForumReply, id=content_id)
    
    if request.method == 'POST':
        form = ForumReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reported_by = request.user
            if content_type == 'thread':
                report.thread = content
            else:
                report.reply = content
            report.save()
            
            messages.success(request, 'Report submitted successfully! Moderators will review it.')
            return redirect('forums:thread_detail', thread_id=content.thread.id if content_type == 'reply' else content.id)
    else:
        form = ForumReportForm()
    
    context = {
        'form': form,
        'content': content,
        'content_type': content_type,
        'page_title': 'Report Content',
    }
    return render(request, 'forums/report.html', context)


@login_required
@user_type_required(['admin', 'moderator'])
def moderate_reports(request):
    """Moderate reported content (admin only)"""
    reports = ForumReport.objects.filter(status='pending').order_by('-created_at')
    
    if request.method == 'POST':
        report_id = request.POST.get('report_id')
        action = request.POST.get('action')
        review_notes = request.POST.get('review_notes', '')
        
        report = get_object_or_404(ForumReport, id=report_id)
        report.reviewed_by = request.user
        report.reviewed_at = timezone.now()
        report.review_notes = review_notes
        
        if action == 'resolve':
            report.status = 'resolved'
            
            # Take action on reported content
            if report.thread:
                report.thread.status = 'archived'
                report.thread.save()
            elif report.reply:
                report.reply.is_deleted = True
                report.reply.save()
            
            messages.success(request, 'Report resolved successfully.')
        
        elif action == 'reject':
            report.status = 'rejected'
            messages.info(request, 'Report rejected.')
        
        report.save()
        return redirect('forums:moderate_reports')
    
    context = {
        'reports': reports,
        'page_title': 'Moderate Reports - Admin',
    }
    return render(request, 'forums/moderate_reports.html', context)