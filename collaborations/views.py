from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import (
    CollaborationRequest, CollaborationApplication,
    SupervisorMatching, CollaborationMessage
)
from .forms import (
    CollaborationRequestForm, CollaborationApplicationForm,
    SupervisorMatchingForm, CollaborationMessageForm
)
from accounts.decorators import user_activity_log


@login_required
def collaboration_list(request):
    """List all collaboration requests"""
    collaborations = CollaborationRequest.objects.filter(
        Q(status='open') | Q(status='pending')
    ).exclude(
        requested_by=request.user
    )
    
    # Filters
    collab_type = request.GET.get('type')
    if collab_type:
        collaborations = collaborations.filter(collaboration_type=collab_type)
    
    status = request.GET.get('status')
    if status:
        collaborations = collaborations.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        collaborations = collaborations.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(required_skills__icontains=search)
        )
    
    paginator = Paginator(collaborations, 10)
    page = request.GET.get('page')
    collaborations = paginator.get_page(page)
    
    context = {
        'collaborations': collaborations,
        'page_title': 'Research Collaborations - KMPN',
        'collaboration_types': CollaborationRequest.COLLABORATION_TYPES,
        'status_choices': CollaborationRequest.STATUS_CHOICES,
    }
    return render(request, 'collaborations/list.html', context)


@login_required
@user_activity_log('collaboration_create', 'Created collaboration request')
def collaboration_create(request):
    """Create new collaboration request"""
    if request.method == 'POST':
        form = CollaborationRequestForm(request.POST, request.FILES)
        if form.is_valid():
            collaboration = form.save(commit=False)
            collaboration.requested_by = request.user
            collaboration.save()
            
            # Save target users if any
            target_users = request.POST.getlist('target_users')
            if target_users:
                collaboration.target_users.set(target_users)
            
            messages.success(request, 'Collaboration request created successfully!')
            return redirect('collaborations:detail', collab_id=collaboration.id)
    else:
        form = CollaborationRequestForm()
    
    context = {
        'form': form,
        'page_title': 'Create Collaboration - KMPN',
    }
    return render(request, 'collaborations/create.html', context)


@login_required
def collaboration_detail(request, collab_id):
    """View collaboration detail"""
    collaboration = get_object_or_404(
        CollaborationRequest,
        id=collab_id
    )
    
    # Increment view count
    collaboration.view_count += 1
    collaboration.save()
    
    # Check if user has applied
    has_applied = False
    if request.user.is_authenticated:
        has_applied = collaboration.applications.filter(
            applicant=request.user
        ).exists()
    
    # Get applications (if user is the requester)
    applications = None
    if collaboration.requested_by == request.user:
        applications = collaboration.applications.all()
    
    context = {
        'collaboration': collaboration,
        'has_applied': has_applied,
        'applications': applications,
        'page_title': collaboration.title,
    }
    return render(request, 'collaborations/detail.html', context)


@login_required
@user_activity_log('collaboration_apply', 'Applied to collaboration')
def collaboration_apply(request, collab_id):
    """Apply to collaboration"""
    collaboration = get_object_or_404(CollaborationRequest, id=collab_id)
    
    # Check if already applied
    if collaboration.applications.filter(applicant=request.user).exists():
        messages.warning(request, 'You have already applied to this collaboration.')
        return redirect('collaborations:detail', collab_id=collab_id)
    
    if request.method == 'POST':
        form = CollaborationApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.collaboration = collaboration
            application.applicant = request.user
            application.save()
            
            collaboration.application_count += 1
            collaboration.save()
            
            messages.success(request, 'Application submitted successfully!')
            return redirect('collaborations:detail', collab_id=collab_id)
    else:
        form = CollaborationApplicationForm()
    
    context = {
        'form': form,
        'collaboration': collaboration,
        'page_title': f'Apply to {collaboration.title}',
    }
    return render(request, 'collaborations/apply.html', context)


@login_required
def my_collaborations(request):
    """View user's collaborations"""
    my_requests = CollaborationRequest.objects.filter(
        requested_by=request.user
    ).order_by('-created_at')
    
    my_applications = CollaborationApplication.objects.filter(
        applicant=request.user
    ).select_related('collaboration').order_by('-created_at')
    
    context = {
        'my_requests': my_requests,
        'my_applications': my_applications,
        'page_title': 'My Collaborations - KMPN',
    }
    return render(request, 'collaborations/my_collaborations.html', context)


@login_required
def collaboration_application_action(request, app_id, action):
    """Accept or reject collaboration application"""
    application = get_object_or_404(CollaborationApplication, id=app_id)
    
    # Check permission
    if application.collaboration.requested_by != request.user:
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('collaborations:detail', collab_id=application.collaboration.id)
    
    if action == 'accept':
        application.status = 'accepted'
        application.collaboration.status = 'accepted'
        application.collaboration.save()
        messages.success(request, 'Application accepted!')
    elif action == 'reject':
        application.status = 'rejected'
        messages.info(request, 'Application rejected.')
    
    application.reviewed_by = request.user
    application.reviewed_at = timezone.now()
    application.save()
    
    return redirect('collaborations:detail', collab_id=application.collaboration.id)


@login_required
def supervisor_matching(request):
    """Supervisor matching view"""
    # Student matches
    if request.user.user_type == 'member':
        student_matches = SupervisorMatching.objects.filter(
            student=request.user
        ).order_by('-match_score')
    else:
        student_matches = []
    
    # Supervisor matches (if user is a supervisor)
    supervisor_matches = SupervisorMatching.objects.filter(
        supervisor=request.user
    ).order_by('-match_score')
    
    # Create new match request
    if request.method == 'POST':
        form = SupervisorMatchingForm(request.POST)
        if form.is_valid():
            match = form.save(commit=False)
            if request.user.user_type == 'member':
                match.student = request.user
                match.matching_type = 'student'
            else:
                match.supervisor = request.user
                match.matching_type = 'supervisor'
            match.save()
            
            # AI matching logic would go here
            # Calculate match score based on research interests, etc.
            match.match_score = calculate_match_score(match)
            match.save()
            
            messages.success(request, 'Supervisor matching request created!')
            return redirect('collaborations:supervisor_matching')
    else:
        form = SupervisorMatchingForm()
    
    context = {
        'student_matches': student_matches,
        'supervisor_matches': supervisor_matches,
        'form': form,
        'page_title': 'Supervisor Matching - KMPN',
        'is_supervisor': request.user.user_type != 'member',
    }
    return render(request, 'collaborations/supervisor_matching.html', context)


@login_required
def supervisor_match_action(request, match_id, action):
    """Accept or reject supervisor match"""
    match = get_object_or_404(SupervisorMatching, id=match_id)
    
    # Check permission
    if match.supervisor != request.user and match.student != request.user:
        messages.error(request, 'You do not have permission.')
        return redirect('collaborations:supervisor_matching')
    
    if action == 'accept':
        match.status = 'accepted'
        match.matched_at = timezone.now()
        messages.success(request, 'Match accepted!')
    elif action == 'reject':
        match.status = 'rejected'
        messages.info(request, 'Match rejected.')
    
    match.save()
    return redirect('collaborations:supervisor_matching')


@login_required
def collaboration_message(request, collab_id):
    """Send message in collaboration"""
    collaboration = get_object_or_404(CollaborationRequest, id=collab_id)
    
    # Check if user is part of this collaboration
    if (collaboration.requested_by != request.user and 
        not collaboration.applications.filter(
            applicant=request.user,
            status='accepted'
        ).exists()):
        messages.error(request, 'You are not part of this collaboration.')
        return redirect('collaborations:detail', collab_id=collab_id)
    
    if request.method == 'POST':
        form = CollaborationMessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.collaboration = collaboration
            message.sender = request.user
            
            # Determine receiver
            if collaboration.requested_by == request.user:
                # Send to first accepted applicant
                first_applicant = collaboration.applications.filter(
                    status='accepted'
                ).first()
                if first_applicant:
                    message.receiver = first_applicant.applicant
            else:
                message.receiver = collaboration.requested_by
            
            message.save()
            messages.success(request, 'Message sent!')
            return redirect('collaborations:detail', collab_id=collab_id)
    else:
        form = CollaborationMessageForm()
    
    # Get messages
    messages_list = CollaborationMessage.objects.filter(
        collaboration=collaboration
    ).order_by('created_at')
    
    # Mark messages as read
    messages_list.filter(receiver=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    context = {
        'form': form,
        'collaboration': collaboration,
        'messages': messages_list,
        'page_title': f'Messages - {collaboration.title}',
    }
    return render(request, 'collaborations/messages.html', context)


# Helper function
def calculate_match_score(match):
    """Calculate match score based on various factors"""
    # This would be a complex AI/ML algorithm in production
    # Simplified version for demonstration
    score = 0.5  # Base score
    
    # Add points for research area match
    if match.research_area:
        score += 0.2
    
    # Add points for specific topic match
    if match.specific_topic:
        score += 0.15
    
    # Add points for institution preference
    if match.preferred_institution:
        score += 0.15
    
    return round(score, 2)
