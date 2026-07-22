from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
import json
import logging
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

from .models import (
    Member, MemberVerificationRequest, MemberActivity
)
from .forms import (
    MemberRegistrationForm, MemberVerificationForm,
    MemberProfileForm, MemberSearchForm, MemberSettingsForm
)
from accounts.models import User, UserActivityLog
from accounts.decorators import user_activity_log, user_type_required
from notifications.models import Notification
from profiles.models import Profile, Publication

logger = logging.getLogger(__name__)


# ============================================================
# MEMBER DASHBOARD
# ============================================================

@login_required
def member_dashboard(request):
    """Member dashboard with overview and statistics"""
    try:
        member = Member.objects.get(user=request.user)
    except Member.DoesNotExist:
        # Create member profile if it doesn't exist
        member = Member.objects.create(user=request.user)
    
    # Get recent activities
    recent_activities = MemberActivity.objects.filter(
        member=member
    ).order_by('-created_at')[:10]
    
    # Get member statistics
    total_publications = Publication.objects.filter(
        members=request.user
    ).count()
    
    total_citations = Publication.objects.filter(
        members=request.user
    ).aggregate(Sum('citation_count'))['citation_count__sum'] or 0
    
    # Get communities count
    from communities.models import CommunityMember
    communities_count = CommunityMember.objects.filter(
        user=request.user
    ).count()
    
    # Get upcoming events
    from events.models import EventRegistration
    upcoming_events = EventRegistration.objects.filter(
        user=request.user,
        event__start_date__gte=timezone.now()
    ).select_related('event').order_by('event__start_date')[:5]
    
    # Get pending verification status
    verification_status = member.verification_status
    pending_verification = MemberVerificationRequest.objects.filter(
        member=member,
        review_decision='pending'
    ).exists()
    
    # Calculate profile completion
    profile_completion = calculate_profile_completion(request.user)
    
    # Get membership duration
    membership_duration = None
    if member.created_at:
        duration = timezone.now() - member.created_at
        membership_duration = duration.days
    
    context = {
        'member': member,
        'recent_activities': recent_activities,
        'total_publications': total_publications,
        'total_citations': total_citations,
        'communities_count': communities_count,
        'upcoming_events': upcoming_events,
        'verification_status': verification_status,
        'pending_verification': pending_verification,
        'profile_completion': profile_completion,
        'membership_duration': membership_duration,
        'page_title': 'Member Dashboard - KMPN',
    }
    return render(request, 'members/dashboard.html', context)


# ============================================================
# MEMBER VERIFICATION
# ============================================================

@login_required
@user_activity_log('verification_request', 'Requested member verification')
def member_verification_request(request):
    """Request member verification"""
    try:
        member = Member.objects.get(user=request.user)
    except Member.DoesNotExist:
        member = Member.objects.create(user=request.user)
    
    # Check if already verified
    if member.verification_status == 'verified':
        messages.warning(request, 'You are already a verified member.')
        return redirect('members:dashboard')
    
    # Check if already has pending request
    if MemberVerificationRequest.objects.filter(
        member=member,
        review_decision='pending'
    ).exists():
        messages.warning(request, 'You already have a pending verification request.')
        return redirect('members:dashboard')
    
    if request.method == 'POST':
        form = MemberVerificationForm(request.POST, request.FILES)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.member = member
            
            # Collect uploaded documents
            documents = {}
            if 'student_id' in request.FILES:
                documents['student_id'] = request.FILES['student_id'].name
                member.student_id = request.FILES['student_id']
            if 'admission_letter' in request.FILES:
                documents['admission_letter'] = request.FILES['admission_letter'].name
                member.admission_letter = request.FILES['admission_letter']
            if 'transcript' in request.FILES:
                documents['transcript'] = request.FILES['transcript'].name
                member.transcript = request.FILES['transcript']
            
            verification.documents = documents
            verification.save()
            
            # Update member details from form
            member.student_id_number = form.cleaned_data.get('student_id_number')
            member.registration_number = form.cleaned_data.get('registration_number')
            member.year_of_study = form.cleaned_data.get('year_of_study')
            member.expected_graduation_year = form.cleaned_data.get('expected_graduation_year')
            member.thesis_title = form.cleaned_data.get('thesis_title')
            member.thesis_abstract = form.cleaned_data.get('thesis_abstract')
            member.supervisor_name = form.cleaned_data.get('supervisor_name')
            member.supervisor_email = form.cleaned_data.get('supervisor_email')
            member.save()
            
            # Notify admins
            self._notify_admins_about_verification(member)
            
            messages.success(
                request,
                'Verification request submitted successfully! '
                'You will receive a confirmation once verified.'
            )
            return redirect('members:verification_status')
    else:
        initial_data = {
            'student_id_number': member.student_id_number,
            'registration_number': member.registration_number,
            'year_of_study': member.year_of_study,
            'expected_graduation_year': member.expected_graduation_year,
            'thesis_title': member.thesis_title,
            'thesis_abstract': member.thesis_abstract,
            'supervisor_name': member.supervisor_name,
            'supervisor_email': member.supervisor_email,
        }
        form = MemberVerificationForm(initial=initial_data)
    
    context = {
        'form': form,
        'member': member,
        'page_title': 'Member Verification - KMPN',
    }
    return render(request, 'members/verification_request.html', context)


@login_required
def verification_status(request):
    """View verification status"""
    try:
        member = Member.objects.get(user=request.user)
    except Member.DoesNotExist:
        messages.warning(request, 'Please complete your member profile first.')
        return redirect('members:dashboard')
    
    verification_requests = MemberVerificationRequest.objects.filter(
        member=member
    ).order_by('-created_at')
    
    latest_request = verification_requests.first()
    
    context = {
        'member': member,
        'verification_requests': verification_requests,
        'latest_request': latest_request,
        'page_title': 'Verification Status - KMPN',
    }
    return render(request, 'members/verification_status.html', context)


@login_required
@user_type_required(['admin', 'moderator'])
def manage_verifications(request):
    """Manage member verifications (admin only)"""
    pending_verifications = MemberVerificationRequest.objects.filter(
        review_decision='pending'
    ).select_related('member', 'member__user').order_by('-created_at')
    
    # Filters
    status_filter = request.GET.get('status', '')
    if status_filter:
        pending_verifications = pending_verifications.filter(
            review_decision=status_filter
        )
    
    search_query = request.GET.get('search', '')
    if search_query:
        pending_verifications = pending_verifications.filter(
            Q(member__user__email__icontains=search_query) |
            Q(member__user__username__icontains=search_query) |
            Q(member__user__first_name__icontains=search_query) |
            Q(member__user__last_name__icontains=search_query)
        )
    
    paginator = Paginator(pending_verifications, 10)
    page = request.GET.get('page', 1)
    
    try:
        pending_verifications = paginator.page(page)
    except PageNotAnInteger:
        pending_verifications = paginator.page(1)
    except EmptyPage:
        pending_verifications = paginator.page(paginator.num_pages)
    
    context = {
        'verifications': pending_verifications,
        'status_choices': MemberVerificationRequest.STATUS_CHOICES,
        'current_status': status_filter,
        'search_query': search_query,
        'page_title': 'Manage Verifications - Admin',
    }
    return render(request, 'members/manage_verifications.html', context)


@login_required
@user_type_required(['admin', 'moderator'])
def review_verification(request, verification_id):
    """Review a verification request"""
    verification = get_object_or_404(
        MemberVerificationRequest,
        id=verification_id,
        review_decision='pending'
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        review_notes = request.POST.get('review_notes', '')
        
        if action == 'approve':
            # Approve verification
            verification.review_decision = 'approved'
            verification.reviewed_by = request.user
            verification.reviewed_at = timezone.now()
            verification.review_notes = review_notes
            verification.save()
            
            # Update member status
            member = verification.member
            member.verification_status = 'verified'
            member.verified_by = request.user
            member.verified_at = timezone.now()
            member.verification_notes = review_notes
            
            # Generate digital card
            member.generate_digital_card()
            member.generate_qr_code()
            
            member.save()
            
            # Send notification to member
            Notification.objects.create(
                user=member.user,
                notification_type='member',
                title='Member Verification Approved',
                message=f'Your membership has been verified! You can now access all features.',
                link='/members/dashboard/',
                metadata={
                    'verification_id': verification.id,
                    'action': 'approve'
                }
            )
            
            # Send email notification
            self._send_verification_email(member.user, 'approved')
            
            messages.success(
                request,
                f'Member {member.user.get_full_name()} has been verified successfully!'
            )
            
        elif action == 'reject':
            # Reject verification
            verification.review_decision = 'rejected'
            verification.reviewed_by = request.user
            verification.reviewed_at = timezone.now()
            verification.review_notes = review_notes
            verification.save()
            
            member = verification.member
            member.verification_status = 'rejected'
            member.verification_notes = review_notes
            member.save()
            
            # Send notification to member
            Notification.objects.create(
                user=member.user,
                notification_type='member',
                title='Member Verification Rejected',
                message=f'Your membership verification was rejected. Please review the notes and resubmit.',
                link='/members/verification/',
                metadata={
                    'verification_id': verification.id,
                    'action': 'reject',
                    'notes': review_notes
                }
            )
            
            # Send email notification
            self._send_verification_email(member.user, 'rejected', review_notes)
            
            messages.warning(
                request,
                f'Member {member.user.get_full_name()} verification has been rejected.'
            )
        
        elif action == 'request_info':
            # Request additional information
            verification.review_decision = 'additional_info'
            verification.reviewed_by = request.user
            verification.reviewed_at = timezone.now()
            verification.review_notes = review_notes
            verification.save()
            
            # Send notification to member
            Notification.objects.create(
                user=member.user,
                notification_type='member',
                title='Additional Information Required',
                message=f'Please provide additional information for your verification: {review_notes}',
                link='/members/verification/',
                metadata={
                    'verification_id': verification.id,
                    'action': 'request_info',
                    'notes': review_notes
                }
            )
            
            messages.info(
                request,
                f'Additional information requested from {member.user.get_full_name()}.'
            )
        
        return redirect('members:manage_verifications')
    
    context = {
        'verification': verification,
        'page_title': 'Review Verification - Admin',
    }
    return render(request, 'members/review_verification.html', context)


# ============================================================
# DIGITAL CARD
# ============================================================

@login_required
def digital_card(request):
    """View digital membership card"""
    try:
        member = Member.objects.get(user=request.user)
    except Member.DoesNotExist:
        messages.warning(request, 'Please complete your member profile first.')
        return redirect('members:dashboard')
    
    if member.verification_status != 'verified':
        messages.warning(request, 'You need to be verified to access your digital card.')
        return redirect('members:verification_status')
    
    context = {
        'member': member,
        'page_title': 'Digital Membership Card - KMPN',
    }
    return render(request, 'members/digital_card.html', context)


@login_required
def download_digital_card(request):
    """Download digital membership card as image"""
    try:
        member = Member.objects.get(user=request.user)
    except Member.DoesNotExist:
        messages.error(request, 'Member profile not found.')
        return redirect('members:dashboard')
    
    if member.verification_status != 'verified':
        messages.error(request, 'You need to be verified to download your card.')
        return redirect('members:verification_status')
    
    # Generate card image
    card_image = generate_card_image(member)
    
    # Create response
    response = HttpResponse(content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="kmpn_card_{member.membership_number}.png"'
    card_image.save(response, 'PNG')
    
    return response


@login_required
def download_qr_code(request):
    """Download QR code as image"""
    try:
        member = Member.objects.get(user=request.user)
    except Member.DoesNotExist:
        messages.error(request, 'Member profile not found.')
        return redirect('members:dashboard')
    
    if member.verification_status != 'verified':
        messages.error(request, 'You need to be verified to download your QR code.')
        return redirect('members:verification_status')
    
    if not member.qr_code:
        member.generate_qr_code()
        member.save()
    
    response = HttpResponse(content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="qrcode_{member.membership_number}.png"'
    
    # Open and return the QR code image
    with open(member.qr_code.path, 'rb') as f:
        response.write(f.read())
    
    return response


# ============================================================
# MEMBER DIRECTORY
# ============================================================

def member_directory(request):
    """Browse member directory"""
    members = Member.objects.filter(
        verification_status='verified'
    ).select_related('user')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        members = members.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__institution__icontains=search_query) |
            Q(user__research_interests__icontains=search_query) |
            Q(membership_number__icontains=search_query)
        )
    
    # Filters
    institution = request.GET.get('institution', '')
    if institution:
        members = members.filter(user__institution__icontains=institution)
    
    degree_level = request.GET.get('degree_level', '')
    if degree_level:
        members = members.filter(user__degree_level=degree_level)
    
    research_area = request.GET.get('research_area', '')
    if research_area:
        members = members.filter(
            Q(user__research_interests__icontains=research_area) |
            Q(expertise_areas__icontains=research_area)
        )
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by == 'name':
        members = members.order_by('user__first_name', 'user__last_name')
    elif sort_by == 'recent':
        members = members.order_by('-created_at')
    elif sort_by == 'publications':
        members = members.order_by('-publication_count')
    else:
        members = members.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(members, 20)
    page = request.GET.get('page', 1)
    
    try:
        members = paginator.page(page)
    except PageNotAnInteger:
        members = paginator.page(1)
    except EmptyPage:
        members = paginator.page(paginator.num_pages)
    
    # Get unique institutions for filter
    institutions = Member.objects.filter(
        verification_status='verified'
    ).exclude(user__institution__isnull=True).values_list(
        'user__institution', flat=True
    ).distinct()
    
    context = {
        'members': members,
        'search_query': search_query,
        'institutions': sorted([inst for inst in institutions if inst]),
        'degree_levels': ['bachelors', 'masters', 'phd', 'postdoc'],
        'current_institution': institution,
        'current_degree': degree_level,
        'current_sort': sort_by,
        'page_title': 'Member Directory - KMPN',
    }
    return render(request, 'members/directory.html', context)


@login_required
def member_search(request):
    """AJAX endpoint for member search"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    members = Member.objects.filter(
        Q(verification_status='verified'),
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(user__email__icontains=query) |
        Q(user__research_interests__icontains=query) |
        Q(user__institution__icontains=query)
    )[:10]
    
    results = []
    for member in members:
        results.append({
            'id': member.id,
            'name': member.user.get_full_name(),
            'email': member.user.email,
            'username': member.user.username,
            'institution': member.user.institution,
            'degree': member.user.degree_level,
            'profile_picture': member.user.profile_picture.url if member.user.profile_picture else None,
            'membership_number': member.membership_number,
            'research_interests': member.user.research_interests,
        })
    
    return JsonResponse({'results': results})


# ============================================================
# MEMBER DETAIL AND PROFILE
# ============================================================

def member_detail(request, member_id):
    """View member details"""
    member = get_object_or_404(
        Member,
        id=member_id,
        verification_status='verified'
    )
    
    # Check if member profile is public
    if hasattr(member.user, 'profile'):
        if member.user.profile.profile_visibility == 'private':
            if not request.user.is_authenticated or request.user != member.user:
                messages.warning(request, 'This member\'s profile is private.')
                return redirect('members:directory')
    
    # Log profile view
    if request.user.is_authenticated and request.user != member.user:
        MemberActivity.objects.create(
            member=member,
            activity_type='profile_view',
            activity_description=f'Profile viewed by {request.user.get_full_name()}',
            ip_address=get_client_ip(request),
            metadata={'viewer_id': request.user.id}
        )
    
    # Get member statistics
    total_publications = Publication.objects.filter(
        members=member.user
    ).count()
    
    total_citations = Publication.objects.filter(
        members=member.user
    ).aggregate(Sum('citation_count'))['citation_count__sum'] or 0
    
    # Get communities
    from communities.models import CommunityMember
    communities = CommunityMember.objects.filter(
        user=member.user
    ).select_related('community')[:5]
    
    # Check if current user can follow
    can_follow = request.user.is_authenticated and request.user != member.user
    
    context = {
        'member': member,
        'total_publications': total_publications,
        'total_citations': total_citations,
        'communities': communities,
        'can_follow': can_follow,
        'page_title': f'{member.user.get_full_name()} - Profile',
    }
    return render(request, 'members/member_detail.html', context)


@login_required
def follow_member(request, member_id):
    """Follow another member"""
    member = get_object_or_404(Member, id=member_id)
    
    if request.user == member.user:
        return JsonResponse({'error': 'You cannot follow yourself'}, status=400)
    
    # Check if already following
    # This would use a Follow model - for now we'll use a simple approach
    is_following = False
    
    if request.method == 'POST':
        # Implement follow/unfollow logic
        # For now, just toggle a JSON field or use a related model
        is_following = not is_following  # Toggle for demo
        
        return JsonResponse({
            'following': is_following,
            'message': f'{"Unfollowed" if not is_following else "Followed"} {member.user.get_full_name()}'
        })
    
    return JsonResponse({'following': is_following})


@login_required
def message_member(request, member_id):
    """Send message to another member"""
    recipient = get_object_or_404(Member, id=member_id)
    
    if request.user == recipient.user:
        messages.error(request, 'You cannot send a message to yourself.')
        return redirect('members:detail', member_id=member_id)
    
    if request.method == 'POST':
        message_content = request.POST.get('message', '').strip()
        
        if not message_content:
            messages.error(request, 'Please enter a message.')
            return redirect('members:message', member_id=member_id)
        
        # Create notification for recipient
        Notification.objects.create(
            user=recipient.user,
            notification_type='message',
            title=f'New message from {request.user.get_full_name()}',
            message=message_content[:200],
            link=f'/members/{member_id}/',
            metadata={
                'sender_id': request.user.id,
                'message_preview': message_content[:100]
            }
        )
        
        # Send email notification
        self._send_message_notification(recipient.user, request.user, message_content)
        
        messages.success(request, f'Message sent to {recipient.user.get_full_name()} successfully!')
        return redirect('members:detail', member_id=member_id)
    
    context = {
        'recipient': recipient,
        'page_title': f'Send Message to {recipient.user.get_full_name()}',
    }
    return render(request, 'members/message.html', context)


# ============================================================
# MEMBER PROFILE MANAGEMENT
# ============================================================

@login_required
def edit_profile(request):
    """Edit member profile"""
    try:
        member = Member.objects.get(user=request.user)
    except Member.DoesNotExist:
        member = Member.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = MemberProfileForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            member = form.save()
            
            # Update user fields
            user = request.user
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.bio = form.cleaned_data.get('bio')
            user.institution = form.cleaned_data.get('institution')
            user.department = form.cleaned_data.get('department')
            user.degree_level = form.cleaned_data.get('degree_level')
            user.research_interests = form.cleaned_data.get('research_interests')
            
            if 'profile_picture' in request.FILES:
                user.profile_picture = request.FILES['profile_picture']
            
            user.save()
            
            # Update skills
            skills = request.POST.get('skills', '')
            if skills:
                member.skills = [s.strip() for s in skills.split(',') if s.strip()]
            
            # Update expertise areas
            expertise = request.POST.get('expertise_areas', '')
            if expertise:
                member.expertise_areas = [e.strip() for e in expertise.split(',') if e.strip()]
            
            # Update programming languages
            programming = request.POST.get('programming_languages', '')
            if programming:
                member.programming_languages = [p.strip() for p in programming.split(',') if p.strip()]
            
            member.save()
            
            # Log activity
            MemberActivity.objects.create(
                member=member,
                activity_type='profile_update',
                activity_description='Updated profile',
                ip_address=get_client_ip(request),
            )
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('members:detail', member_id=member.id)
    else:
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'bio': request.user.bio,
            'institution': request.user.institution,
            'department': request.user.department,
            'degree_level': request.user.degree_level,
            'research_interests': request.user.research_interests,
        }
        form = MemberProfileForm(instance=member, initial=initial_data)
    
    context = {
        'form': form,
        'member': member,
        'page_title': 'Edit Profile - KMPN',
    }
    return render(request, 'members/edit_profile.html', context)


@login_required
def member_settings(request):
    """Member settings"""
    try:
        member = Member.objects.get(user=request.user)
    except Member.DoesNotExist:
        member = Member.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = MemberSettingsForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully!')
            return redirect('members:settings')
    else:
        form = MemberSettingsForm(instance=member)
    
    context = {
        'form': form,
        'member': member,
        'page_title': 'Settings - KMPN',
    }
    return render(request, 'members/settings.html', context)


# ============================================================
# MEMBER ACTIVITIES
# ============================================================

@login_required
def member_activities(request):
    """View member activities"""
    try:
        member = Member.objects.get(user=request.user)
    except Member.DoesNotExist:
        messages.warning(request, 'Please complete your profile first.')
        return redirect('members:dashboard')
    
    activities = MemberActivity.objects.filter(
        member=member
    ).order_by('-created_at')
    
    # Filters
    activity_type = request.GET.get('type', '')
    if activity_type:
        activities = activities.filter(activity_type=activity_type)
    
    date_from = request.GET.get('date_from')
    if date_from:
        activities = activities.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        activities = activities.filter(created_at__date__lte=date_to)
    
    paginator = Paginator(activities, 20)
    page = request.GET.get('page', 1)
    
    try:
        activities = paginator.page(page)
    except PageNotAnInteger:
        activities = paginator.page(1)
    except EmptyPage:
        activities = paginator.page(paginator.num_pages)
    
    context = {
        'activities': activities,
        'activity_types': MemberActivity.ACTIVITY_TYPES,
        'current_type': activity_type,
        'page_title': 'My Activities - KMPN',
    }
    return render(request, 'members/activities.html', context)


# ============================================================
# AJAX ENDPOINTS
# ============================================================

@login_required
def get_members_json(request):
    """Get members as JSON for autocomplete"""
    query = request.GET.get('q', '')
    
    members = Member.objects.filter(
        verification_status='verified'
    ).select_related('user')
    
    if query:
        members = members.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__username__icontains=query)
        )
    
    members = members[:20]
    
    results = []
    for member in members:
        results.append({
            'id': member.id,
            'name': member.user.get_full_name(),
            'email': member.user.email,
            'username': member.user.username,
            'institution': member.user.institution,
            'profile_picture': member.user.profile_picture.url if member.user.profile_picture else None,
        })
    
    return JsonResponse({'results': results})


@login_required
def verify_documents(request):
    """AJAX endpoint to verify uploaded documents"""
    if request.method == 'POST' and request.FILES:
        document = request.FILES.get('document')
        if document:
            # Validate file type
            allowed_types = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
            file_extension = document.name.split('.')[-1].lower()
            
            if file_extension not in allowed_types:
                return JsonResponse({
                    'valid': False,
                    'error': 'Invalid file type. Allowed: PDF, JPG, PNG, DOC, DOCX'
                })
            
            # Validate file size (max 10MB)
            if document.size > 10 * 1024 * 1024:
                return JsonResponse({
                    'valid': False,
                    'error': 'File size exceeds 10MB limit'
                })
            
            return JsonResponse({'valid': True})
    
    return JsonResponse({'valid': False, 'error': 'No document uploaded'})


@login_required
def check_membership(request):
    """Check membership status (AJAX)"""
    try:
        member = Member.objects.get(user=request.user)
        is_verified = member.verification_status == 'verified'
        is_active = member.is_membership_active()
        
        return JsonResponse({
            'verified': is_verified,
            'active': is_active,
            'membership_number': member.membership_number,
            'expiry_date': member.card_expires_at.isoformat() if member.card_expires_at else None,
            'days_remaining': member.get_membership_duration() if is_active else 0,
        })
    except Member.DoesNotExist:
        return JsonResponse({
            'verified': False,
            'active': False,
            'membership_number': None,
            'expiry_date': None,
            'days_remaining': 0,
        })


# ============================================================
# ADMIN VIEWS
# ============================================================

@login_required
@user_type_required(['admin', 'moderator'])
def export_members(request):
    """Export member data (admin only)"""
    import csv
    from io import StringIO
    
    members = Member.objects.filter(
        verification_status='verified'
    ).select_related('user')
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Membership Number', 'Name', 'Email', 'Institution', 'Department',
        'Degree Level', 'Research Interests', 'Verification Status',
        'Joined Date', 'Publications', 'Citations'
    ])
    
    # Write data
    for member in members:
        publications = Publication.objects.filter(members=member.user).count()
        citations = Publication.objects.filter(members=member.user).aggregate(
            Sum('citation_count')
        )['citation_count__sum'] or 0
        
        writer.writerow([
            member.membership_number,
            member.user.get_full_name(),
            member.user.email,
            member.user.institution,
            member.user.department,
            member.user.degree_level,
            member.user.research_interests,
            member.verification_status,
            member.created_at.strftime('%Y-%m-%d'),
            publications,
            citations
        ])
    
    # Create response
    response = HttpResponse(
        output.getvalue(),
        content_type='text/csv'
    )
    response['Content-Disposition'] = 'attachment; filename="members_export.csv"'
    
    return response


@login_required
@user_type_required(['admin', 'moderator'])
def member_statistics(request):
    """View member statistics (admin only)"""
    total_members = Member.objects.count()
    verified_members = Member.objects.filter(verification_status='verified').count()
    pending_members = Member.objects.filter(verification_status='pending').count()
    rejected_members = Member.objects.filter(verification_status='rejected').count()
    
    # Members by institution
    institution_stats = Member.objects.filter(
        verification_status='verified'
    ).values('user__institution').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Members by degree level
    degree_stats = Member.objects.filter(
        verification_status='verified'
    ).values('user__degree_level').annotate(
        count=Count('id')
    )
    
    # Members by month (last 12 months)
    from datetime import datetime
    month_stats = []
    for i in range(12):
        month_date = timezone.now() - timedelta(days=30*i)
        month_count = Member.objects.filter(
            created_at__year=month_date.year,
            created_at__month=month_date.month
        ).count()
        month_stats.append({
            'month': month_date.strftime('%B %Y'),
            'count': month_count
        })
    
    context = {
        'total_members': total_members,
        'verified_members': verified_members,
        'pending_members': pending_members,
        'rejected_members': rejected_members,
        'institution_stats': institution_stats,
        'degree_stats': degree_stats,
        'month_stats': month_stats,
        'page_title': 'Member Statistics - Admin',
    }
    return render(request, 'members/statistics.html', context)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def calculate_profile_completion(user):
    """Calculate profile completion percentage"""
    fields = [
        user.first_name,
        user.last_name,
        user.email,
        user.bio,
        user.institution,
        user.department,
        user.degree_level,
        user.research_interests,
        user.profile_picture,
    ]
    
    # Check if profile exists
    if hasattr(user, 'profile'):
        profile = user.profile
        fields.extend([
            profile.academic_bio,
            profile.research_statement,
            profile.primary_research_area,
            profile.current_position,
        ])
    
    # Check if member exists
    if hasattr(user, 'member_profile'):
        member = user.member_profile
        fields.extend([
            member.skills,
            member.expertise_areas,
        ])
    
    filled = sum(1 for field in fields if field)
    total = len(fields)
    
    return int((filled / total) * 100) if total > 0 else 0


def generate_card_image(member):
    """Generate digital membership card image"""
    # Create a professional-looking card
    width, height = 600, 350
    image = Image.new('RGB', (width, height), color='#1a237e')
    draw = ImageDraw.Draw(image)
    
    # Draw border
    draw.rectangle([10, 10, width-10, height-10], outline='#ffffff', width=2)
    
    # Add KMPN header
    try:
        font_title = ImageFont.truetype("arial.ttf", 28)
        font_subtitle = ImageFont.truetype("arial.ttf", 16)
        font_text = ImageFont.truetype("arial.ttf", 14)
    except:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_text = ImageFont.load_default()
    
    # Title
    draw.text((30, 20), "Kenya Masters & PhD Network", fill='#ffffff', font=font_title)
    draw.text((30, 55), "Digital Membership Card", fill='#64b5f6', font=font_subtitle)
    
    # Member details
    y_pos = 90
    draw.text((30, y_pos), f"Name: {member.user.get_full_name()}", fill='#ffffff', font=font_text)
    y_pos += 30
    draw.text((30, y_pos), f"Member ID: {member.membership_number}", fill='#ffffff', font=font_text)
    y_pos += 30
    draw.text((30, y_pos), f"Email: {member.user.email}", fill='#ffffff', font=font_text)
    y_pos += 30
    draw.text((30, y_pos), f"Institution: {member.user.institution or 'N/A'}", fill='#ffffff', font=font_text)
    y_pos += 30
    draw.text((30, y_pos), f"Degree: {member.user.degree_level or 'N/A'}", fill='#ffffff', font=font_text)
    
    # Status badge
    status_color = '#4caf50' if member.verification_status == 'verified' else '#ff9800'
    draw.rectangle([width-180, 20, width-20, 60], fill=status_color, outline='#ffffff', width=1)
    draw.text((width-160, 30), "VERIFIED", fill='#ffffff', font=font_subtitle)
    
    # Expiry date
    if member.card_expires_at:
        draw.text(
            (width-200, height-30),
            f"Valid until: {member.card_expires_at.strftime('%B %d, %Y')}",
            fill='#90caf9',
            font=font_text
        )
    
    # Footer
    draw.line([30, height-50, width-30, height-50], fill='#64b5f6', width=1)
    draw.text(
        (30, height-40),
        "This card is the property of KMPN. Please present upon request.",
        fill='#90caf9',
        font=font_subtitle
    )
    
    # Add QR code if exists
    if member.qr_code:
        try:
            qr_img = Image.open(member.qr_code.path)
            qr_img = qr_img.resize((100, 100))
            image.paste(qr_img, (width-120, height-130))
        except:
            pass
    
    return image


def _notify_admins_about_verification(member):
    """Notify admins about new verification request"""
    from accounts.models import User
    
    admins = User.objects.filter(user_type__in=['admin', 'moderator'])
    
    for admin in admins:
        if admin != member.user:
            Notification.objects.create(
                user=admin,
                notification_type='member',
                title='New Verification Request',
                message=f'{member.user.get_full_name()} has submitted a verification request.',
                link='/members/manage-verifications/',
                metadata={
                    'member_id': member.id,
                    'member_name': member.user.get_full_name()
                }
            )


def _send_verification_email(user, status, notes=None):
    """Send verification status email"""
    subject = f'Member Verification {status.capitalize()} - KMPN'
    
    context = {
        'user': user,
        'status': status,
        'notes': notes,
        'site_url': settings.SITE_URL,
    }
    
    if status == 'approved':
        template = 'members/email/verification_approved.html'
    elif status == 'rejected':
        template = 'members/email/verification_rejected.html'
    else:
        template = 'members/email/verification_status.html'
    
    html_message = render_to_string(template, context)
    plain_message = render_to_string(template.replace('.html', '.txt'), context)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )


def _send_message_notification(recipient, sender, message):
    """Send message notification email"""
    subject = f'New Message from {sender.get_full_name()} - KMPN'
    
    context = {
        'recipient': recipient,
        'sender': sender,
        'message': message,
        'site_url': settings.SITE_URL,
    }
    
    html_message = render_to_string('members/email/message_notification.html', context)
    plain_message = render_to_string('members/email/message_notification.txt', context)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient.email],
        html_message=html_message,
        fail_silently=False,
    )
