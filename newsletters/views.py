from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.mail import get_connection
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image

from .models import Newsletter, NewsletterSubscriber, NewsletterOpen, NewsletterClick
from .forms import (
    NewsletterForm, NewsletterSubscriberForm, NewsletterFilterForm,
    NewsletterSubscriberFilterForm, NewsletterTestForm,
    NewsletterSubscriberAdminForm
)
from accounts.decorators import user_activity_log, user_type_required
from accounts.models import User
from notifications.models import Notification

logger = logging.getLogger(__name__)


@login_required
@user_type_required(['admin', 'executive'])
def newsletter_list(request):
    """List all newsletters"""
    newsletters = Newsletter.objects.all().order_by('-created_at')
    
    # Filters
    filter_form = NewsletterFilterForm(request.GET)
    
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        if status:
            newsletters = newsletters.filter(status=status)
        
        date_from = filter_form.cleaned_data.get('date_from')
        if date_from:
            newsletters = newsletters.filter(created_at__date__gte=date_from)
        
        date_to = filter_form.cleaned_data.get('date_to')
        if date_to:
            newsletters = newsletters.filter(created_at__date__lte=date_to)
        
        search = filter_form.cleaned_data.get('search')
        if search:
            newsletters = newsletters.filter(
                Q(subject__icontains=search) |
                Q(content__icontains=search)
            )
    
    paginator = Paginator(newsletters, 20)
    page = request.GET.get('page', 1)
    
    try:
        newsletters = paginator.page(page)
    except PageNotAnInteger:
        newsletters = paginator.page(1)
    except EmptyPage:
        newsletters = paginator.page(paginator.num_pages)
    
    # Statistics
    total_newsletters = Newsletter.objects.count()
    sent_count = Newsletter.objects.filter(status='sent').count()
    scheduled_count = Newsletter.objects.filter(status='scheduled').count()
    draft_count = Newsletter.objects.filter(status='draft').count()
    
    context = {
        'newsletters': newsletters,
        'filter_form': filter_form,
        'total_newsletters': total_newsletters,
        'sent_count': sent_count,
        'scheduled_count': scheduled_count,
        'draft_count': draft_count,
        'page_title': 'Newsletters - Admin',
    }
    return render(request, 'newsletters/list.html', context)


@login_required
@user_type_required(['admin', 'executive'])
@user_activity_log('newsletter_create', 'Created newsletter')
def create_newsletter(request):
    """Create new newsletter"""
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.created_by = request.user
            
            # Generate HTML content
            newsletter.html_content = render_to_string(
                'newsletters/template.html',
                {
                    'subject': newsletter.subject,
                    'content': newsletter.content,
                    'tracking_id': newsletter.tracking_id,
                    'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
                }
            )
            
            newsletter.save()
            
            # Save target users if any
            target_users = request.POST.getlist('target_users')
            if target_users:
                newsletter.target_users.set(target_users)
                newsletter.send_to_all = False
                newsletter.save()
            
            messages.success(request, 'Newsletter created successfully!')
            return redirect('newsletters:detail', newsletter_id=newsletter.id)
    else:
        form = NewsletterForm()
    
    context = {
        'form': form,
        'page_title': 'Create Newsletter - Admin',
    }
    return render(request, 'newsletters/create.html', context)


@login_required
@user_type_required(['admin', 'executive'])
def newsletter_detail(request, newsletter_id):
    """View newsletter details"""
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    
    # Get open and click data
    opens = NewsletterOpen.objects.filter(newsletter=newsletter).order_by('-opened_at')[:50]
    clicks = NewsletterClick.objects.filter(newsletter=newsletter).order_by('-clicked_at')[:50]
    
    context = {
        'newsletter': newsletter,
        'opens': opens,
        'clicks': clicks,
        'page_title': newsletter.subject,
    }
    return render(request, 'newsletters/detail.html', context)


@login_required
@user_type_required(['admin', 'executive'])
@user_activity_log('newsletter_edit', 'Edited newsletter')
def edit_newsletter(request, newsletter_id):
    """Edit newsletter"""
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    
    # Check if newsletter can be edited
    if newsletter.status in ['sent', 'sending']:
        messages.error(request, 'Cannot edit a newsletter that has been sent or is being sent.')
        return redirect('newsletters:detail', newsletter_id=newsletter.id)
    
    if request.method == 'POST':
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            newsletter = form.save()
            
            # Update HTML content
            newsletter.html_content = render_to_string(
                'newsletters/template.html',
                {
                    'subject': newsletter.subject,
                    'content': newsletter.content,
                    'tracking_id': newsletter.tracking_id,
                    'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
                }
            )
            newsletter.save()
            
            messages.success(request, 'Newsletter updated successfully!')
            return redirect('newsletters:detail', newsletter_id=newsletter.id)
    else:
        form = NewsletterForm(instance=newsletter)
    
    context = {
        'form': form,
        'newsletter': newsletter,
        'page_title': f'Edit {newsletter.subject}',
    }
    return render(request, 'newsletters/edit.html', context)


@login_required
@user_type_required(['admin', 'executive'])
@user_activity_log('newsletter_send', 'Sent newsletter')
def send_newsletter(request, newsletter_id):
    """Send newsletter"""
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    
    if newsletter.status not in ['draft', 'scheduled']:
        messages.warning(request, 'This newsletter has already been sent or is in progress.')
        return redirect('newsletters:detail', newsletter_id=newsletter.id)
    
    # Check if scheduled
    if newsletter.scheduled_at and newsletter.scheduled_at > timezone.now():
        messages.info(request, f'This newsletter is scheduled for {newsletter.scheduled_at.strftime("%Y-%m-%d %H:%M")}.')
        return redirect('newsletters:detail', newsletter_id=newsletter.id)
    
    if request.method == 'POST':
        # Get subscribers
        if newsletter.send_to_all:
            subscribers = NewsletterSubscriber.objects.filter(subscribed=True)
        else:
            subscribers = NewsletterSubscriber.objects.filter(
                subscribed=True,
                groups__overlap=newsletter.target_groups
            )
        
        total = subscribers.count()
        newsletter.total_recipients = total
        newsletter.status = 'sending'
        newsletter.save()
        
        # Send emails in batches
        batch_size = 50
        sent = 0
        errors = 0
        
        for i in range(0, total, batch_size):
            batch = subscribers[i:i+batch_size]
            for subscriber in batch:
                try:
                    # Send email
                    email = EmailMultiAlternatives(
                        subject=newsletter.subject,
                        body=newsletter.content,
                        from_email=newsletter.from_email,
                        to=[subscriber.email],
                        reply_to=[newsletter.reply_to] if newsletter.reply_to else None
                    )
                    
                    # HTML version with tracking
                    html_content = newsletter.html_content
                    # Add tracking pixel
                    tracking_pixel = f'<img src="{getattr(settings, "SITE_URL", "http://localhost:8000")}/newsletters/track/open/{newsletter.tracking_id}/{subscriber.id}/" width="1" height="1" />'
                    html_content += tracking_pixel
                    
                    email.attach_alternative(html_content, "text/html")
                    email.send()
                    
                    newsletter.delivered_count += 1
                    sent += 1
                    
                except Exception as e:
                    logger.error(f"Failed to send to {subscriber.email}: {str(e)}")
                    newsletter.bounced_count += 1
                    errors += 1
            
            # Update progress
            newsletter.save()
        
        # Mark as sent
        newsletter.status = 'sent'
        newsletter.sent_at = timezone.now()
        newsletter.save()
        
        messages.success(request, f'Newsletter sent to {sent} subscribers successfully! {errors} failed.')
        return redirect('newsletters:detail', newsletter_id=newsletter.id)
    
    # Get subscriber count
    if newsletter.send_to_all:
        subscriber_count = NewsletterSubscriber.objects.filter(subscribed=True).count()
    else:
        subscriber_count = NewsletterSubscriber.objects.filter(
            subscribed=True,
            groups__overlap=newsletter.target_groups
        ).count()
    
    context = {
        'newsletter': newsletter,
        'subscriber_count': subscriber_count,
        'page_title': f'Send {newsletter.subject}',
    }
    return render(request, 'newsletters/send.html', context)


@login_required
@user_type_required(['admin', 'executive'])
@user_activity_log('newsletter_test', 'Sent test newsletter')
def send_test_newsletter(request, newsletter_id):
    """Send test newsletter"""
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    
    if request.method == 'POST':
        form = NewsletterTestForm(request.POST)
        if form.is_valid():
            test_email = form.cleaned_data['test_email']
            
            try:
                # Send test email
                email = EmailMultiAlternatives(
                    subject=f'[TEST] {newsletter.subject}',
                    body=newsletter.content,
                    from_email=newsletter.from_email,
                    to=[test_email],
                    reply_to=[newsletter.reply_to] if newsletter.reply_to else None
                )
                
                email.attach_alternative(newsletter.html_content, "text/html")
                email.send()
                
                messages.success(request, f'Test email sent to {test_email} successfully!')
                return redirect('newsletters:detail', newsletter_id=newsletter.id)
                
            except Exception as e:
                logger.error(f"Failed to send test email: {str(e)}")
                messages.error(request, f'Failed to send test email: {str(e)}')
    else:
        form = NewsletterTestForm()
    
    context = {
        'form': form,
        'newsletter': newsletter,
        'page_title': f'Send Test - {newsletter.subject}',
    }
    return render(request, 'newsletters/send_test.html', context)


@login_required
@user_type_required(['admin', 'executive'])
def delete_newsletter(request, newsletter_id):
    """Delete newsletter"""
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    
    if newsletter.status in ['sent', 'sending']:
        messages.error(request, 'Cannot delete a newsletter that has been sent or is being sent.')
        return redirect('newsletters:detail', newsletter_id=newsletter.id)
    
    if request.method == 'POST':
        newsletter.delete()
        messages.success(request, 'Newsletter deleted successfully!')
        return redirect('newsletters:list')
    
    context = {
        'newsletter': newsletter,
        'page_title': f'Delete {newsletter.subject}',
    }
    return render(request, 'newsletters/delete.html', context)


def track_open(request, tracking_id, subscriber_id):
    """Track newsletter open"""
    try:
        newsletter = Newsletter.objects.get(tracking_id=tracking_id)
        subscriber = NewsletterSubscriber.objects.get(id=subscriber_id)
        
        # Record open
        NewsletterOpen.objects.create(
            newsletter=newsletter,
            subscriber=subscriber,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            location=request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        )
        
        newsletter.opened_count += 1
        subscriber.opened_count += 1
        newsletter.save()
        subscriber.save()
        
    except (Newsletter.DoesNotExist, NewsletterSubscriber.DoesNotExist):
        pass
    
    # Return 1x1 transparent GIF
    img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    response = HttpResponse(content_type='image/png')
    img.save(response, 'PNG')
    return response


def track_click(request, tracking_id, subscriber_id, url):
    """Track newsletter click"""
    try:
        newsletter = Newsletter.objects.get(tracking_id=tracking_id)
        subscriber = NewsletterSubscriber.objects.get(id=subscriber_id)
        
        # Record click
        NewsletterClick.objects.create(
            newsletter=newsletter,
            subscriber=subscriber,
            url=url,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            location=request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        )
        
        newsletter.clicked_count += 1
        subscriber.clicked_count += 1
        newsletter.save()
        subscriber.save()
        
    except (Newsletter.DoesNotExist, NewsletterSubscriber.DoesNotExist):
        pass
    
    # Redirect to the actual URL
    from urllib.parse import unquote
    actual_url = unquote(url)
    return redirect(actual_url)


def subscribe_newsletter(request):
    """Subscribe to newsletter"""
    if request.method == 'POST':
        form = NewsletterSubscriberForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Check if already subscribed
            subscriber, created = NewsletterSubscriber.objects.get_or_create(
                email=email,
                defaults={
                    'name': form.cleaned_data.get('name', ''),
                    'user': request.user if request.user.is_authenticated else None,
                    'ip_address': get_client_ip(request)
                }
            )
            
            if not subscriber.subscribed:
                subscriber.subscribed = True
                subscriber.unsubscribed_at = None
                subscriber.save()
                messages.success(request, 'You have been subscribed to our newsletter!')
            elif created:
                messages.success(request, 'You have been subscribed to our newsletter!')
            else:
                messages.info(request, 'You are already subscribed to our newsletter.')
            
            return redirect('home')
    else:
        form = NewsletterSubscriberForm()
    
    context = {
        'form': form,
        'page_title': 'Subscribe to Newsletter',
    }
    return render(request, 'newsletters/subscribe.html', context)


def unsubscribe_newsletter(request, email=None, token=None):
    """Unsubscribe from newsletter"""
    if email and token:
        # Verify token (in production, use a proper token system)
        subscriber = get_object_or_404(NewsletterSubscriber, email=email)
        subscriber.subscribed = False
        subscriber.unsubscribed_at = timezone.now()
        subscriber.save()
        
        messages.success(request, 'You have been unsubscribed from our newsletter.')
        return redirect('home')
    elif request.method == 'POST':
        email = request.POST.get('email')
        subscriber = get_object_or_404(NewsletterSubscriber, email=email)
        subscriber.subscribed = False
        subscriber.unsubscribed_at = timezone.now()
        subscriber.save()
        
        messages.success(request, 'You have been unsubscribed from our newsletter.')
        return redirect('home')
    else:
        # Show unsubscribe form
        return render(request, 'newsletters/unsubscribe.html')


@login_required
@user_type_required(['admin', 'executive'])
def subscriber_list(request):
    """Manage subscribers (admin only)"""
    subscribers = NewsletterSubscriber.objects.all().order_by('-created_at')
    
    # Filters
    filter_form = NewsletterSubscriberFilterForm(request.GET)
    
    if filter_form.is_valid():
        subscribed = filter_form.cleaned_data.get('subscribed')
        if subscribed == 'true':
            subscribers = subscribers.filter(subscribed=True)
        elif subscribed == 'false':
            subscribers = subscribers.filter(subscribed=False)
        
        group = filter_form.cleaned_data.get('group')
        if group:
            subscribers = subscribers.filter(groups__icontains=group)
        
        search = filter_form.cleaned_data.get('search')
        if search:
            subscribers = subscribers.filter(
                Q(email__icontains=search) |
                Q(name__icontains=search)
            )
    
    paginator = Paginator(subscribers, 50)
    page = request.GET.get('page', 1)
    
    try:
        subscribers = paginator.page(page)
    except PageNotAnInteger:
        subscribers = paginator.page(1)
    except EmptyPage:
        subscribers = paginator.page(paginator.num_pages)
    
    # Statistics
    total_subscribers = NewsletterSubscriber.objects.count()
    active_subscribers = NewsletterSubscriber.objects.filter(subscribed=True).count()
    inactive_subscribers = total_subscribers - active_subscribers
    
    context = {
        'subscribers': subscribers,
        'filter_form': filter_form,
        'total_subscribers': total_subscribers,
        'active_subscribers': active_subscribers,
        'inactive_subscribers': inactive_subscribers,
        'page_title': 'Manage Subscribers - Admin',
    }
    return render(request, 'newsletters/subscribers.html', context)


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
@user_type_required(['admin', 'executive'])
def get_newsletter_stats(request, newsletter_id):
    """Get newsletter statistics (AJAX)"""
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    
    return JsonResponse({
        'total_recipients': newsletter.total_recipients,
        'delivered_count': newsletter.delivered_count,
        'opened_count': newsletter.opened_count,
        'clicked_count': newsletter.clicked_count,
        'bounced_count': newsletter.bounced_count,
        'unsubscribed_count': newsletter.unsubscribed_count,
        'open_rate': newsletter.get_open_rate(),
        'click_rate': newsletter.get_click_rate(),
        'status': newsletter.status,
        'sent_at': newsletter.sent_at.isoformat() if newsletter.sent_at else None
    })


@login_required
@user_type_required(['admin', 'executive'])
def export_subscribers(request):
    """Export subscribers as CSV (admin only)"""
    import csv
    from io import StringIO
    
    subscribers = NewsletterSubscriber.objects.filter(subscribed=True)
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Email', 'Name', 'Subscribed', 'Groups',
        'Opened Count', 'Clicked Count', 'Subscribed At'
    ])
    
    # Write data
    for subscriber in subscribers:
        writer.writerow([
            subscriber.email,
            subscriber.name or '',
            'Yes' if subscriber.subscribed else 'No',
            ', '.join(subscriber.groups) if subscriber.groups else '',
            subscriber.opened_count,
            subscriber.clicked_count,
            subscriber.subscribed_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="subscribers_export.csv"'
    return response