from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone
from .models import Notification, NotificationPreference
from .forms import NotificationPreferenceForm, NotificationFilterForm, MarkAllReadForm, DeleteAllForm


@login_required
def notification_list(request):
    """List user notifications"""
    notifications = Notification.objects.filter(
        user=request.user,
        is_deleted=False
    ).order_by('-created_at')
    
    # Filters
    filter_form = NotificationFilterForm(request.GET)
    
    if filter_form.is_valid():
        notification_type = filter_form.cleaned_data.get('notification_type')
        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)
        
        is_read = filter_form.cleaned_data.get('is_read')
        if is_read == 'true':
            notifications = notifications.filter(is_read=False)
        elif is_read == 'false':
            notifications = notifications.filter(is_read=True)
        
        date_from = filter_form.cleaned_data.get('date_from')
        if date_from:
            notifications = notifications.filter(created_at__date__gte=date_from)
        
        date_to = filter_form.cleaned_data.get('date_to')
        if date_to:
            notifications = notifications.filter(created_at__date__lte=date_to)
    
    paginator = Paginator(notifications, 20)
    page = request.GET.get('page', 1)
    
    try:
        notifications = paginator.page(page)
    except PageNotAnInteger:
        notifications = paginator.page(1)
    except EmptyPage:
        notifications = paginator.page(paginator.num_pages)
    
    # Get unread count
    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False,
        is_deleted=False
    ).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
        'filter_form': filter_form,
        'mark_all_form': MarkAllReadForm(),
        'delete_all_form': DeleteAllForm(),
        'page_title': 'Notifications - KMPN',
    }
    return render(request, 'notifications/list.html', context)


@login_required
def mark_as_read(request, notif_id):
    """Mark notification as read"""
    notification = get_object_or_404(
        Notification,
        id=notif_id,
        user=request.user
    )
    notification.mark_as_read()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Notification marked as read.')
    return redirect('notifications:list')


@login_required
def mark_all_read(request):
    """Mark all notifications as read"""
    if request.method == 'POST':
        form = MarkAllReadForm(request.POST)
        if form.is_valid():
            count = Notification.objects.filter(
                user=request.user,
                is_read=False,
                is_deleted=False
            ).update(is_read=True, read_at=timezone.now())
            
            messages.success(request, f'{count} notifications marked as read.')
            return redirect('notifications:list')
    else:
        form = MarkAllReadForm()
    
    context = {
        'form': form,
        'page_title': 'Mark All Read - KMPN',
    }
    return render(request, 'notifications/mark_all_read.html', context)


@login_required
def delete_notification(request, notif_id):
    """Delete notification"""
    notification = get_object_or_404(
        Notification,
        id=notif_id,
        user=request.user
    )
    notification.is_deleted = True
    notification.deleted_at = timezone.now()
    notification.save()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Notification deleted.')
    return redirect('notifications:list')


@login_required
def delete_all_notifications(request):
    """Delete all notifications"""
    if request.method == 'POST':
        form = DeleteAllForm(request.POST)
        if form.is_valid():
            count = Notification.objects.filter(
                user=request.user,
                is_deleted=False
            ).update(is_deleted=True, deleted_at=timezone.now())
            
            messages.success(request, f'{count} notifications deleted.')
            return redirect('notifications:list')
    else:
        form = DeleteAllForm()
    
    context = {
        'form': form,
        'page_title': 'Delete All Notifications - KMPN',
    }
    return render(request, 'notifications/delete_all.html', context)


@login_required
def notification_preferences(request):
    """Manage notification preferences"""
    # Get or create preferences
    pref, created = NotificationPreference.objects.get_or_create(
        user=request.user
    )
    
    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST, instance=pref)
        if form.is_valid():
            form.save()
            messages.success(request, 'Preferences updated successfully!')
            return redirect('notifications:preferences')
    else:
        form = NotificationPreferenceForm(instance=pref)
    
    context = {
        'form': form,
        'page_title': 'Notification Preferences - KMPN',
    }
    return render(request, 'notifications/preferences.html', context)


@login_required
def get_notification_count(request):
    """Get unread notification count (AJAX)"""
    count = Notification.objects.filter(
        user=request.user,
        is_read=False,
        is_deleted=False
    ).count()
    
    return JsonResponse({'count': count})


@login_required
def get_notifications_ajax(request):
    """Get notifications for dropdown (AJAX)"""
    limit = int(request.GET.get('limit', 10))
    
    notifications = Notification.objects.filter(
        user=request.user,
        is_deleted=False
    ).order_by('-created_at')[:limit]
    
    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False,
        is_deleted=False
    ).count()
    
    data = {
        'unread_count': unread_count,
        'notifications': []
    }
    
    for notif in notifications:
        data['notifications'].append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message[:100],
            'link': notif.link,
            'is_read': notif.is_read,
            'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M'),
            'notification_type': notif.notification_type,
        })
    
    return JsonResponse(data)