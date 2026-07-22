from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from .models import Event, EventRegistration
from .forms import EventForm, EventRegistrationForm, EventFeedbackForm, EventFilterForm, CertificateGenerationForm
from accounts.decorators import user_activity_log, user_type_required
from accounts.models import User
from members.models import Member, MemberActivity
from notifications.models import Notification


def event_list(request):
    """List all events"""
    events = Event.objects.filter(
        status__in=['published', 'ongoing']
    ).order_by('start_date')
    
    # Filters
    filter_form = EventFilterForm(request.GET)
    
    if filter_form.is_valid():
        event_type = filter_form.cleaned_data.get('event_type')
        if event_type:
            events = events.filter(event_type=event_type)
        
        is_virtual = filter_form.cleaned_data.get('is_virtual')
        if is_virtual == 'true':
            events = events.filter(is_virtual=True)
        elif is_virtual == 'false':
            events = events.filter(is_virtual=False)
        
        time_filter = filter_form.cleaned_data.get('time_filter')
        now = timezone.now()
        if time_filter == 'upcoming':
            events = events.filter(start_date__gte=now)
        elif time_filter == 'ongoing':
            events = events.filter(start_date__lte=now, end_date__gte=now)
        elif time_filter == 'past':
            events = events.filter(end_date__lt=now)
        
        search = filter_form.cleaned_data.get('search')
        if search:
            events = events.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(organizer_name__icontains=search) |
                Q(tags__icontains=search)
            )
    
    paginator = Paginator(events, 10)
    page = request.GET.get('page', 1)
    
    try:
        events = paginator.page(page)
    except PageNotAnInteger:
        events = paginator.page(1)
    except EmptyPage:
        events = paginator.page(paginator.num_pages)
    
    context = {
        'events': events,
        'filter_form': filter_form,
        'page_title': 'Events - KMPN',
    }
    return render(request, 'events/list.html', context)


def event_detail(request, slug):
    """View event detail"""
    event = get_object_or_404(Event, slug=slug)
    event.increment_view_count()
    
    # Check if user is registered
    is_registered = False
    registration = None
    if request.user.is_authenticated:
        try:
            registration = EventRegistration.objects.get(
                event=event,
                user=request.user
            )
            is_registered = True
        except EventRegistration.DoesNotExist:
            pass
    
    # Check if registration is open
    registration_open = True
    if event.registration_deadline:
        registration_open = timezone.now() < event.registration_deadline
    
    # Get registered users count
    registration_count = event.registrations.count()
    
    # Check if event has capacity
    has_capacity = True
    if event.max_attendees:
        has_capacity = registration_count < event.max_attendees
    
    context = {
        'event': event,
        'is_registered': is_registered,
        'registration': registration,
        'registration_open': registration_open,
        'registration_count': registration_count,
        'has_capacity': has_capacity,
        'page_title': event.title,
    }
    return render(request, 'events/detail.html', context)


@login_required
@user_activity_log('event_create', 'Created event')
def event_create(request):
    """Create new event"""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            
            # Auto-publish for admins/moderators
            if request.user.user_type in ['admin', 'moderator']:
                event.status = 'published'
            
            event.save()
            messages.success(request, 'Event created successfully!')
            return redirect('events:detail', slug=event.slug)
    else:
        form = EventForm()
    
    context = {
        'form': form,
        'page_title': 'Create Event - KMPN',
    }
    return render(request, 'events/create.html', context)


@login_required
def edit_event(request, slug):
    """Edit event"""
    event = get_object_or_404(Event, slug=slug)
    
    # Check permission
    if event.created_by != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this event.')
        return redirect('events:detail', slug=event.slug)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            event = form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('events:detail', slug=event.slug)
    else:
        form = EventForm(instance=event)
    
    context = {
        'form': form,
        'event': event,
        'page_title': f'Edit {event.title}',
    }
    return render(request, 'events/edit.html', context)


@login_required
def delete_event(request, slug):
    """Delete event"""
    event = get_object_or_404(Event, slug=slug)
    
    # Check permission
    if event.created_by != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete this event.')
        return redirect('events:detail', slug=event.slug)
    
    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, f'Event "{event_title}" deleted successfully!')
        return redirect('events:list')
    
    context = {
        'event': event,
        'page_title': f'Delete {event.title}',
    }
    return render(request, 'events/delete.html', context)


@login_required
@user_activity_log('event_register', 'Registered for event')
def event_register(request, slug):
    """Register for event"""
    event = get_object_or_404(Event, slug=slug)
    
    # Check if event is published
    if event.status not in ['published', 'ongoing']:
        messages.error(request, 'This event is not open for registration.')
        return redirect('events:detail', slug=event.slug)
    
    # Check if already registered
    if event.registrations.filter(user=request.user).exists():
        messages.warning(request, 'You are already registered for this event.')
        return redirect('events:detail', slug=event.slug)
    
    # Check capacity
    if event.max_attendees and event.current_attendees >= event.max_attendees:
        messages.error(request, 'This event is fully booked.')
        return redirect('events:detail', slug=event.slug)
    
    # Check registration deadline
    if event.registration_deadline and timezone.now() > event.registration_deadline:
        messages.error(request, 'Registration deadline has passed.')
        return redirect('events:detail', slug=event.slug)
    
    # Check if registration is required
    if not event.requires_registration:
        messages.info(request, 'This event does not require registration.')
        return redirect('events:detail', slug=event.slug)
    
    if request.method == 'POST':
        form = EventRegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.event = event
            registration.user = request.user
            registration.save()
            
            # Update event attendees
            event.current_attendees += 1
            event.registration_count += 1
            event.save()
            
            # Log activity
            try:
                member = Member.objects.get(user=request.user)
                MemberActivity.objects.create(
                    member=member,
                    activity_type='event_registration',
                    activity_description=f'Registered for {event.title}',
                    metadata={'event_id': event.id}
                )
            except Member.DoesNotExist:
                pass
            
            # Notify event organizer
            if event.created_by != request.user:
                Notification.objects.create(
                    user=event.created_by,
                    notification_type='event',
                    title=f'New registration for {event.title}',
                    message=f'{request.user.get_full_name()} registered for your event.',
                    link=f'/events/{event.slug}/',
                    metadata={'event_id': event.id}
                )
            
            messages.success(request, 'Registration successful! You will receive a confirmation email.')
            return redirect('events:detail', slug=event.slug)
    else:
        form = EventRegistrationForm()
    
    context = {
        'form': form,
        'event': event,
        'page_title': f'Register for {event.title}',
    }
    return render(request, 'events/register.html', context)


@login_required
def cancel_registration(request, slug):
    """Cancel event registration"""
    event = get_object_or_404(Event, slug=slug)
    
    registration = get_object_or_404(
        EventRegistration,
        event=event,
        user=request.user
    )
    
    if request.method == 'POST':
        registration.attendance_status = 'cancelled'
        registration.save()
        
        # Update event attendees
        event.current_attendees -= 1
        event.save()
        
        messages.success(request, 'Registration cancelled successfully.')
        return redirect('events:detail', slug=event.slug)
    
    context = {
        'event': event,
        'registration': registration,
        'page_title': f'Cancel Registration - {event.title}',
    }
    return render(request, 'events/cancel_registration.html', context)


@login_required
def my_events(request):
    """View user's events"""
    registrations = EventRegistration.objects.filter(
        user=request.user
    ).select_related('event').order_by('-registration_date')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        if status == 'upcoming':
            registrations = registrations.filter(event__start_date__gte=timezone.now())
        elif status == 'past':
            registrations = registrations.filter(event__end_date__lt=timezone.now())
        elif status == 'ongoing':
            registrations = registrations.filter(
                event__start_date__lte=timezone.now(),
                event__end_date__gte=timezone.now()
            )
    
    paginator = Paginator(registrations, 10)
    page = request.GET.get('page', 1)
    
    try:
        registrations = paginator.page(page)
    except PageNotAnInteger:
        registrations = paginator.page(1)
    except EmptyPage:
        registrations = paginator.page(paginator.num_pages)
    
    context = {
        'registrations': registrations,
        'page_title': 'My Events - KMPN',
    }
    return render(request, 'events/my_events.html', context)


@login_required
def event_feedback(request, slug):
    """Submit feedback for event"""
    event = get_object_or_404(Event, slug=slug)
    
    registration = get_object_or_404(
        EventRegistration,
        event=event,
        user=request.user
    )
    
    if registration.feedback_submitted:
        messages.warning(request, 'You have already submitted feedback for this event.')
        return redirect('events:detail', slug=event.slug)
    
    if request.method == 'POST':
        form = EventFeedbackForm(request.POST)
        if form.is_valid():
            registration.feedback_submitted = True
            registration.feedback_rating = form.cleaned_data['rating']
            registration.feedback_comment = form.cleaned_data['comment']
            registration.feedback_submitted_at = timezone.now()
            registration.save()
            
            messages.success(request, 'Feedback submitted successfully! Thank you!')
            return redirect('events:detail', slug=event.slug)
    else:
        form = EventFeedbackForm()
    
    context = {
        'form': form,
        'event': event,
        'page_title': f'Feedback for {event.title}',
    }
    return render(request, 'events/feedback.html', context)


@login_required
@user_type_required(['admin', 'moderator'])
def generate_certificates(request, slug):
    """Generate certificates for event attendees (admin only)"""
    event = get_object_or_404(Event, slug=slug)
    
    if event.status != 'completed':
        messages.warning(request, 'Certificates can only be generated for completed events.')
        return redirect('events:detail', slug=event.slug)
    
    if request.method == 'POST':
        form = CertificateGenerationForm(request.POST)
        if form.is_valid():
            attendee_emails = form.cleaned_data['attendees'].strip().split('\n')
            certificate_type = form.cleaned_data['certificate_type']
            
            generated = 0
            for email in attendee_emails:
                email = email.strip()
                if email:
                    try:
                        user = User.objects.get(email=email)
                        registration = EventRegistration.objects.get(
                            event=event,
                            user=user,
                            attendance_status__in=['confirmed', 'attended']
                        )
                        
                        # Generate certificate
                        registration.generate_certificate()
                        generated += 1
                    except (User.DoesNotExist, EventRegistration.DoesNotExist):
                        pass
            
            messages.success(request, f'{generated} certificates generated successfully!')
            return redirect('events:detail', slug=event.slug)
    else:
        # Get attendees for this event
        attendees = EventRegistration.objects.filter(
            event=event,
            attendance_status__in=['confirmed', 'attended']
        ).select_related('user')
        
        initial_attendees = '\n'.join([reg.user.email for reg in attendees])
        form = CertificateGenerationForm(initial={'attendees': initial_attendees, 'event': event})
    
    context = {
        'form': form,
        'event': event,
        'page_title': f'Generate Certificates - {event.title}',
    }
    return render(request, 'events/generate_certificates.html', context)


@login_required
def download_certificate(request, registration_id):
    """Download event certificate"""
    registration = get_object_or_404(
        EventRegistration,
        id=registration_id,
        user=request.user
    )
    
    if not registration.certificate_issued or not registration.certificate_file:
        messages.warning(request, 'Certificate not yet available for this event.')
        return redirect('events:detail', slug=registration.event.slug)
    
    return FileResponse(
        registration.certificate_file.open('rb'),
        as_attachment=True,
        filename=f"certificate_{registration.event.slug}_{registration.user.username}.pdf"
    )


# AJAX Endpoints

@login_required
def get_registration_status(request, slug):
    """Get registration status for an event (AJAX)"""
    event = get_object_or_404(Event, slug=slug)
    
    is_registered = False
    if request.user.is_authenticated:
        is_registered = event.registrations.filter(user=request.user).exists()
    
    return JsonResponse({
        'is_registered': is_registered,
        'current_attendees': event.current_attendees,
        'max_attendees': event.max_attendees,
        'has_capacity': not event.max_attendees or event.current_attendees < event.max_attendees,
        'registration_open': not event.registration_deadline or timezone.now() < event.registration_deadline
    })


@login_required
def get_event_stats(request, slug):
    """Get event statistics (AJAX)"""
    event = get_object_or_404(Event, slug=slug)
    
    return JsonResponse({
        'view_count': event.view_count,
        'registration_count': event.registration_count,
        'attendance_count': event.registrations.filter(attendance_status='attended').count(),
        'current_attendees': event.current_attendees,
        'max_attendees': event.max_attendees,
    })


def search_events_ajax(request):
    """Search events (AJAX)"""
    form = EventSearchForm(request.GET)
    
    events = Event.objects.filter(status__in=['published', 'ongoing'])
    
    if form.is_valid():
        q = form.cleaned_data.get('q')
        event_type = form.cleaned_data.get('event_type')
        
        if q:
            events = events.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(organizer_name__icontains=q)
            )
        
        if event_type:
            events = events.filter(event_type=event_type)
    
    events = events[:10]
    
    results = []
    for event in events:
        results.append({
            'id': event.id,
            'title': event.title,
            'slug': event.slug,
            'event_type': event.event_type,
            'start_date': event.start_date.isoformat(),
            'end_date': event.end_date.isoformat(),
            'is_virtual': event.is_virtual,
            'venue': event.venue,
            'registration_count': event.registration_count,
            'banner_image': event.banner_image.url if event.banner_image else None,
        })
    
    return JsonResponse({'results': results})