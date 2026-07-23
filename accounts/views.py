# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Sum
from django.core.exceptions import PermissionDenied
import json
import logging

# Models
from .models import (
    User, 
    UserActivityLog, 
    UserDevice, 
    RegistrationApplication, 
    RoleChangeRequest
)

# Forms
from .forms import (
    UserRegistrationForm, 
    UserLoginForm, 
    UserUpdateForm,
    PasswordResetRequestForm, 
    PasswordResetConfirmForm,
    RoleBasedRegistrationForm, 
    RoleChangeRequestForm
)

# Decorators
from .decorators import (
    user_activity_log, 
    role_required, 
    allowed_roles,
    admin_required,
    staff_required,
    member_required,
    verified_member_required,
    approved_registration_required,
    email_verified_required,
    active_member_required,
    login_required_with_message,
    RoleRequiredMixin,
    AdminRequiredMixin,
    StaffRequiredMixin,
    MemberRequiredMixin,
    VerifiedMemberRequiredMixin,
)

# Utils
from .utils import (
    send_verification_email, 
    generate_verification_token,
    send_approval_email,
    send_rejection_email,
    send_info_request_email
)

logger = logging.getLogger(__name__)


# ============================================================
# HOMEPAGE & PUBLIC VIEWS
# ============================================================

def home(request):
    """Homepage view"""
    context = {
        'page_title': 'KPSN - Kenya Postgraduate Scholars Network',
    }
    return render(request, 'home.html', context)


# ============================================================
# REGISTRATION (ROLE-BASED)
# ============================================================

def register(request):
    """Role-based user registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    
    if request.method == 'POST':
        form = RoleBasedRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                
                # Log registration activity
                UserActivityLog.objects.create(
                    user=user,
                    action_type='registration',
                    action_description=f'User registered with requested role: {form.cleaned_data["role"]}',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    metadata={
                        'requested_role': form.cleaned_data['role'],
                        'academic_level': user.academic_level,
                        'institution': user.institution
                    }
                )
                
                # Send verification email
                send_verification_email(request, user)
                
                messages.success(
                    request, 
                    f'Registration successful! Your application for {dict(User.Roles.choices).get(form.cleaned_data["role"], "Member")} is pending review. '
                    'Please check your email to verify your account.'
                )
                return redirect('login')
            
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                messages.error(request, 'An error occurred during registration. Please try again.')
    else:
        form = RoleBasedRegistrationForm()
    
    context = {
        'form': form,
        'page_title': 'Register - KPSN',
    }
    return render(request, 'accounts/register.html', context)


# ============================================================
# AUTHENTICATION (LOGIN/LOGOUT)
# ============================================================

def user_login(request):
    """User login view with role handling"""
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                # Check if account is locked
                if user.is_locked():
                    messages.error(request, 'Your account is temporarily locked. Please try again later.')
                    return render(request, 'accounts/login.html', {'form': form})
                
                # Check registration status
                if user.registration_status == 'rejected':
                    messages.error(request, 'Your registration application was rejected. Please contact support.')
                    return render(request, 'accounts/login.html', {'form': form})
                
                if user.registration_status == 'pending':
                    messages.warning(
                        request, 
                        'Your registration is pending review. You will receive an email once approved.'
                    )
                    return render(request, 'accounts/login.html', {'form': form})
                
                # Check if email is verified
                if not user.email_verified:
                    messages.warning(
                        request,
                        'Please verify your email before logging in. Check your inbox for the verification link.'
                    )
                    # Resend verification
                    send_verification_email(request, user)
                    return render(request, 'accounts/login.html', {'form': form})
                
                # Login successful
                login(request, user)
                
                # Log user activity
                UserActivityLog.objects.create(
                    user=user,
                    action_type='login',
                    action_description=f'User logged in as {user.get_role_display()}',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    referer_url=request.META.get('HTTP_REFERER', ''),
                )
                
                # Record device
                record_user_device(request, user)
                
                # Reset login attempts
                user.reset_login_attempts()
                
                # Update last login IP
                user.last_login_ip = get_client_ip(request)
                user.last_activity = timezone.now()
                user.save()
                
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                
                # Redirect to dashboard based on role
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard_redirect')
            else:
                try:
                    user = User.objects.get(email=email)
                    if user.is_locked():
                        messages.error(request, 'Your account is temporarily locked. Please try again later.')
                    else:
                        user.increment_login_attempts()
                        messages.error(request, 'Invalid email or password.')
                except User.DoesNotExist:
                    messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserLoginForm()
    
    context = {
        'form': form,
        'page_title': 'Login - KPSN',
    }
    return render(request, 'accounts/login.html', context)


@login_required
def user_logout(request):
    """User logout view"""
    UserActivityLog.objects.create(
        user=request.user,
        action_type='logout',
        action_description='User logged out',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


# ============================================================
# DASHBOARD REDIRECT
# ============================================================

@login_required
def dashboard_redirect(request):
    """Redirect users to their appropriate dashboard based on role"""
    
    role_dashboards = {
        'super_admin': 'super_admin_dashboard',
        'admin': 'admin_dashboard',
        'executive': 'executive_dashboard',
        'moderator': 'moderator_dashboard',
        'verified_member': 'member_dashboard',
        'basic_member': 'basic_member_dashboard',
        'alumni': 'alumni_dashboard',
        'researcher': 'researcher_dashboard',
        'partner': 'partner_dashboard',
        'guest': 'guest_dashboard',
        'prospective_member': 'prospective_member_dashboard',
    }
    
    user_role = request.user.role
    
    # Check if user is locked or banned
    if request.user.registration_status == 'banned':
        messages.error(request, 'Your account has been banned. Please contact support.')
        return redirect('home')
    
    if user_role in role_dashboards:
        return redirect(role_dashboards[user_role])
    
    # Fallback to home
    return redirect('home')


# ============================================================
# ROLE-SPECIFIC DASHBOARDS
# ============================================================

@login_required
@role_required('super_admin')
def super_admin_dashboard(request):
    """Super Administrator Dashboard - Full system control"""
    
    # Get statistics
    total_users = User.objects.count()
    pending_applications = RegistrationApplication.objects.filter(status='pending').count()
    pending_verifications = User.objects.filter(email_verified=False).count()
    active_members = User.objects.filter(is_active_member=True).count()
    locked_accounts = User.objects.filter(locked_until__gt=timezone.now()).count()
    
    # Get role counts
    role_counts = User.objects.values('role').annotate(count=Count('id'))
    
    # Get recent data
    recent_applications = RegistrationApplication.objects.select_related('user').order_by('-created_at')[:10]
    recent_activity = UserActivityLog.objects.select_related('user').order_by('-created_at')[:20]
    
    context = {
        'page_title': 'Super Admin Dashboard - KPSN',
        'total_users': total_users,
        'pending_applications': pending_applications,
        'pending_verifications': pending_verifications,
        'active_members': active_members,
        'locked_accounts': locked_accounts,
        'role_counts': role_counts,
        'recent_applications': recent_applications,
        'recent_activity': recent_activity,
    }
    return render(request, 'dashboard/super_admin.html', context)


@login_required
@role_required('admin')
def admin_dashboard(request):
    """Administrator Dashboard - Manage members and content"""
    
    total_members = User.objects.filter(is_active_member=True).count()
    pending_applications = RegistrationApplication.objects.filter(status='pending').count()
    pending_reviews = RegistrationApplication.objects.filter(status='needs_info').count()
    
    recent_verifications = RegistrationApplication.objects.filter(
        status='approved'
    ).select_related('user').order_by('-reviewed_at')[:10]
    
    role_counts = User.objects.values('role').annotate(count=Count('id'))
    recent_members = User.objects.order_by('-created_at')[:10]
    
    context = {
        'page_title': 'Admin Dashboard - KPSN',
        'total_members': total_members,
        'pending_applications': pending_applications,
        'pending_reviews': pending_reviews,
        'recent_verifications': recent_verifications,
        'role_counts': role_counts,
        'recent_members': recent_members,
        'active_members': User.objects.filter(is_active=True).count(),
    }
    return render(request, 'dashboard/admin.html', context)


@login_required
@role_required('executive')
def executive_dashboard(request):
    """Executive Dashboard - Manage events, newsletter, mentorship"""
    
    context = {
        'page_title': 'Executive Dashboard - KPSN',
    }
    return render(request, 'dashboard/executive.html', context)


@login_required
@role_required('moderator')
def moderator_dashboard(request):
    """Moderator Dashboard - Forum and content moderation"""
    
    context = {
        'page_title': 'Moderator Dashboard - KPSN',
    }
    return render(request, 'dashboard/moderator.html', context)


@login_required
def member_dashboard(request):
    """Member Dashboard - Full member features"""
    
    # Only verified members can access this specific dashboard
    if request.user.role != 'verified_member':
        if request.user.role == 'basic_member':
            return redirect('basic_member_dashboard')
        messages.error(request, 'Access Denied')
        return redirect('home')
    
    context = {
        'page_title': 'Member Dashboard - KPSN',
        'user': request.user,
        'membership_status': request.user.get_membership_status(),
    }
    return render(request, 'dashboard/member.html', context)


@login_required
def basic_member_dashboard(request):
    """Basic Member Dashboard - Limited member features"""
    
    if request.user.role != 'basic_member':
        messages.error(request, 'Access Denied')
        return redirect('home')
    
    context = {
        'page_title': 'Basic Member Dashboard - KPSN',
        'user': request.user,
        'membership_status': request.user.get_membership_status(),
    }
    return render(request, 'dashboard/basic_member.html', context)


@login_required
def alumni_dashboard(request):
    """Alumni Dashboard"""
    
    if request.user.role != 'alumni':
        messages.error(request, 'Access Denied')
        return redirect('home')
    
    context = {
        'page_title': 'Alumni Dashboard - KPSN',
        'user': request.user,
    }
    return render(request, 'dashboard/alumni.html', context)


@login_required
def researcher_dashboard(request):
    """Researcher Dashboard"""
    
    if request.user.role != 'researcher':
        messages.error(request, 'Access Denied')
        return redirect('home')
    
    context = {
        'page_title': 'Researcher Dashboard - KPSN',
        'user': request.user,
    }
    return render(request, 'dashboard/researcher.html', context)


@login_required
def partner_dashboard(request):
    """Partner Dashboard"""
    
    if request.user.role != 'partner':
        messages.error(request, 'Access Denied')
        return redirect('home')
    
    context = {
        'page_title': 'Partner Dashboard - KPSN',
        'user': request.user,
    }
    return render(request, 'dashboard/partner.html', context)


@login_required
def prospective_member_dashboard(request):
    """Prospective Member Dashboard - Pending approval"""
    
    if request.user.role != 'prospective_member':
        messages.error(request, 'Access Denied')
        return redirect('home')
    
    # Get application status
    try:
        application = RegistrationApplication.objects.get(user=request.user)
        context = {
            'page_title': 'Application Status - KPSN',
            'application': application,
        }
    except RegistrationApplication.DoesNotExist:
        context = {
            'page_title': 'Application Status - KPSN',
            'application': None,
        }
    
    return render(request, 'dashboard/prospective_member.html', context)


@login_required
def guest_dashboard(request):
    """Guest Dashboard - Limited access"""
    
    if request.user.role != 'guest':
        messages.error(request, 'Access Denied')
        return redirect('home')
    
    context = {
        'page_title': 'Guest Dashboard - KPSN',
    }
    return render(request, 'dashboard/guest.html', context)


# ============================================================
# USER PROFILE
# ============================================================

@login_required
def profile_view(request, username=None):
    """User profile view"""
    if username:
        profile_user = get_object_or_404(User, username=username, is_active=True)
    else:
        profile_user = request.user
    
    # Check if user can view this profile
    if profile_user != request.user and request.user.role not in ['super_admin', 'admin']:
        messages.error(request, 'You do not have permission to view this profile.')
        return redirect('home')
    
    # Log profile view
    if profile_user != request.user:
        UserActivityLog.objects.create(
            user=request.user,
            action_type='profile_view',
            action_description=f'Viewed profile of {profile_user.username}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
    
    context = {
        'profile_user': profile_user,
        'page_title': f'{profile_user.get_full_name()} - Profile',
        'is_own_profile': profile_user == request.user,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_update(request):
    """Update user profile"""
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()
            
            UserActivityLog.objects.create(
                user=request.user,
                action_type='profile_update',
                action_description='User updated profile',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    'updated_fields': list(form.changed_data)
                }
            )
            
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile', username=request.user.username)
    else:
        form = UserUpdateForm(instance=request.user)
    
    context = {
        'form': form,
        'page_title': 'Update Profile - KPSN',
    }
    return render(request, 'accounts/profile_update.html', context)


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('change_password')
        
        if new_password1 != new_password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('change_password')
        
        if len(new_password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('change_password')
        
        request.user.set_password(new_password1)
        request.user.save()
        
        update_session_auth_hash(request, request.user)
        
        UserActivityLog.objects.create(
            user=request.user,
            action_type='profile_update',
            action_description='User changed password',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        messages.success(request, 'Your password has been changed successfully!')
        return redirect('profile', username=request.user.username)
    
    context = {
        'page_title': 'Change Password - KPSN',
    }
    return render(request, 'accounts/change_password.html', context)


# ============================================================
# ROLE CHANGE REQUEST
# ============================================================

@login_required
def request_role_change(request):
    """Request to change user role"""
    
    if request.method == 'POST':
        form = RoleChangeRequestForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            role_change = form.save(commit=False)
            role_change.user = request.user
            role_change.current_role = request.user.role
            role_change.save()
            
            UserActivityLog.objects.create(
                user=request.user,
                action_type='role_change',
                action_description=f'Requested role change from {request.user.role} to {role_change.requested_role}',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            
            messages.success(request, 'Your role change request has been submitted for review.')
            return redirect('dashboard_redirect')
    else:
        form = RoleChangeRequestForm(user=request.user)
    
    context = {
        'form': form,
        'page_title': 'Request Role Change - KPSN',
        'current_role': request.user.get_role_display(),
    }
    return render(request, 'accounts/role_change_request.html', context)


# ============================================================
# ADMIN REGISTRATION MANAGEMENT
# ============================================================

@login_required
@role_required('admin', 'super_admin')
def manage_applications(request):
    """Admin view to manage registration applications"""
    
    applications = RegistrationApplication.objects.select_related('user').all()
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # Filter by role
    role_filter = request.GET.get('role')
    if role_filter:
        applications = applications.filter(requested_role=role_filter)
    
    # Search by email or name
    search_query = request.GET.get('search')
    if search_query:
        applications = applications.filter(
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(applications, 20)
    page = request.GET.get('page')
    try:
        applications = paginator.page(page)
    except PageNotAnInteger:
        applications = paginator.page(1)
    except EmptyPage:
        applications = paginator.page(paginator.num_pages)
    
    context = {
        'page_title': 'Manage Applications - KPSN',
        'applications': applications,
        'status_filter': status_filter,
        'role_filter': role_filter,
        'search_query': search_query,
        'status_choices': RegistrationApplication.ApplicationStatus.choices,
        'role_choices': User.Roles.choices,
        'total_pending': RegistrationApplication.objects.filter(status='pending').count(),
        'total_approved': RegistrationApplication.objects.filter(status='approved').count(),
        'total_rejected': RegistrationApplication.objects.filter(status='rejected').count(),
        'total_needs_info': RegistrationApplication.objects.filter(status='needs_info').count(),
    }
    return render(request, 'admin/manage_applications.html', context)


@login_required
@role_required('admin', 'super_admin')
def review_application(request, application_id):
    """Admin view to review a specific application"""
    
    application = get_object_or_404(RegistrationApplication, id=application_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'approve':
            application.status = 'approved'
            application.reviewed_by = request.user
            application.review_notes = notes
            application.reviewed_at = timezone.now()
            application.save()
            
            # Update user
            user = application.user
            user.role = application.requested_role
            user.registration_status = 'approved'
            user.is_verified = True
            user.is_active_member = True
            user.membership_start_date = timezone.now()
            user.membership_expiry_date = timezone.now() + timezone.timedelta(days=365)
            user.save()
            
            # Generate membership number
            generate_membership_number(user)
            
            # Send approval email
            send_approval_email(request, user)
            
            messages.success(request, f'Application for {user.get_full_name()} has been approved.')
            
        elif action == 'reject':
            application.status = 'rejected'
            application.reviewed_by = request.user
            application.review_notes = notes
            application.reviewed_at = timezone.now()
            application.save()
            
            user = application.user
            user.registration_status = 'rejected'
            user.save()
            
            # Send rejection email
            send_rejection_email(request, user, notes)
            
            messages.success(request, f'Application for {user.get_full_name()} has been rejected.')
            
        elif action == 'needs_info':
            application.status = 'needs_info'
            application.reviewed_by = request.user
            application.review_notes = notes
            application.reviewed_at = timezone.now()
            application.save()
            
            # Send email requesting more info
            send_info_request_email(request, application.user, notes)
            
            messages.success(request, f'Request for more information sent to {application.user.get_full_name()}.')
        
        UserActivityLog.objects.create(
            user=request.user,
            action_type='member_verification',
            action_description=f'Reviewed application for {application.user.email}: {action}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'application_id': application.id,
                'action': action,
                'notes': notes
            }
        )
        
        return redirect('manage_applications')
    
    context = {
        'page_title': 'Review Application - KPSN',
        'application': application,
    }
    return render(request, 'admin/review_application.html', context)


@login_required
@role_required('admin', 'super_admin')
def manage_users(request):
    """Admin view to manage all users"""
    
    users = User.objects.all()
    
    # Filter by role
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        users = users.filter(registration_status=status_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(membership_number__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 25)
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    
    context = {
        'page_title': 'Manage Users - KPSN',
        'users': users,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search_query': search_query,
        'role_choices': User.Roles.choices,
        'status_choices': User.RegistrationStatus.choices,
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
    }
    return render(request, 'admin/manage_users.html', context)


@login_required
@role_required('admin', 'super_admin')
def toggle_user_status(request, user_id):
    """Toggle user active status"""
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'activate':
            user.is_active = True
            user.registration_status = 'approved'
            messages.success(request, f'{user.get_full_name()} has been activated.')
        elif action == 'suspend':
            user.is_active = False
            user.registration_status = 'suspended'
            messages.success(request, f'{user.get_full_name()} has been suspended.')
        elif action == 'ban':
            user.is_active = False
            user.registration_status = 'banned'
            messages.success(request, f'{user.get_full_name()} has been banned.')
        elif action == 'delete':
            # Soft delete
            user.is_deleted = True
            user.deleted_at = timezone.now()
            user.is_active = False
            messages.success(request, f'{user.get_full_name()} has been deleted.')
        
        user.save()
        
        UserActivityLog.objects.create(
            user=request.user,
            action_type='profile_update',
            action_description=f'{action} user: {user.email}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        return redirect('manage_users')
    
    return redirect('manage_users')


# ============================================================
# ROLE CHANGE REQUESTS MANAGEMENT
# ============================================================

@login_required
@role_required('admin', 'super_admin')
def manage_role_requests(request):
    """Admin view to manage role change requests"""
    
    role_requests = RoleChangeRequest.objects.select_related('user', 'reviewed_by').all()
    
    status_filter = request.GET.get('status')
    if status_filter:
        role_requests = role_requests.filter(status=status_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        role_requests = role_requests.filter(
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    paginator = Paginator(role_requests, 20)
    page = request.GET.get('page')
    try:
        role_requests = paginator.page(page)
    except PageNotAnInteger:
        role_requests = paginator.page(1)
    except EmptyPage:
        role_requests = paginator.page(paginator.num_pages)
    
    context = {
        'page_title': 'Manage Role Requests - KPSN',
        'requests': role_requests,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': RoleChangeRequest.RequestStatus.choices,
    }
    return render(request, 'admin/manage_role_requests.html', context)


@login_required
@role_required('admin', 'super_admin')
def review_role_request(request, request_id):
    """Admin view to review role change request"""
    
    role_request = get_object_or_404(RoleChangeRequest, id=request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'approve':
            role_request.status = 'approved'
            role_request.reviewed_by = request.user
            role_request.review_notes = notes
            role_request.reviewed_at = timezone.now()
            role_request.save()
            
            # Update user role
            user = role_request.user
            old_role = user.role
            user.role = role_request.requested_role
            user.save()
            
            messages.success(request, f'Role change approved for {user.get_full_name()}.')
            
            # Log the change
            UserActivityLog.objects.create(
                user=request.user,
                action_type='role_change',
                action_description=f'Approved role change for {user.email}: {old_role} -> {user.role}',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            
        elif action == 'reject':
            role_request.status = 'rejected'
            role_request.reviewed_by = request.user
            role_request.review_notes = notes
            role_request.reviewed_at = timezone.now()
            role_request.save()
            
            messages.success(request, f'Role change rejected for {role_request.user.get_full_name()}.')
        
        return redirect('manage_role_requests')
    
    context = {
        'page_title': 'Review Role Request - KPSN',
        'role_request': role_request,
    }
    return render(request, 'admin/review_role_request.html', context)


# ============================================================
# ACTIVITY LOGS
# ============================================================

@login_required
@role_required('super_admin', 'admin')
def activity_logs(request):
    """View user activity logs"""
    
    logs = UserActivityLog.objects.select_related('user').all()
    
    # Filter by user
    user_filter = request.GET.get('user')
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    # Filter by action type
    action_filter = request.GET.get('action')
    if action_filter:
        logs = logs.filter(action_type=action_filter)
    
    # Date range filter
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    if from_date:
        logs = logs.filter(created_at__gte=from_date)
    if to_date:
        logs = logs.filter(created_at__lte=to_date + ' 23:59:59')
    
    # Pagination
    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        logs = paginator.page(1)
    except EmptyPage:
        logs = paginator.page(paginator.num_pages)
    
    context = {
        'page_title': 'Activity Logs - KPSN',
        'logs': logs,
        'action_types': UserActivityLog.ACTION_TYPES,
        'user_filter': user_filter,
        'action_filter': action_filter,
        'from_date': from_date,
        'to_date': to_date,
    }
    return render(request, 'admin/activity_logs.html', context)


# ============================================================
# VERIFICATION
# ============================================================

def verify_email(request, token):
    """Verify user email"""
    try:
        user = User.objects.get(email_verification_token=token)
        if user.email_verified:
            messages.info(request, 'Your email is already verified.')
            return redirect('login')
        
        user.email_verified = True
        user.is_active = True
        user.save()
        
        messages.success(request, 'Your email has been verified successfully! You can now login.')
        return redirect('login')
    
    except User.DoesNotExist:
        messages.error(request, 'Invalid verification token.')
        return redirect('home')


def resend_verification(request):
    """Resend verification email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if user.email_verified:
                messages.info(request, 'Your email is already verified.')
                return redirect('login')
            
            send_verification_email(request, user)
            messages.success(request, 'Verification email has been resent. Please check your inbox.')
            return redirect('login')
        
        except User.DoesNotExist:
            messages.error(request, 'No user found with this email address.')
    
    return render(request, 'accounts/resend_verification.html')


# ============================================================
# PASSWORD RESET
# ============================================================

def password_reset_request(request):
    """Request password reset"""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                
                # Generate token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Send reset email
                current_site = get_current_site(request)
                mail_subject = 'Password Reset - KPSN'
                message = render_to_string('accounts/password_reset_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': uid,
                    'token': token,
                })
                
                send_mail(
                    mail_subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                
                messages.success(
                    request,
                    'Password reset email has been sent. Please check your inbox.'
                )
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'No user found with this email address.')
    else:
        form = PasswordResetRequestForm()
    
    context = {
        'form': form,
        'page_title': 'Reset Password - KPSN',
    }
    return render(request, 'accounts/password_reset_request.html', context)


def password_reset_confirm(request, uidb64, token):
    """Confirm password reset"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = PasswordResetConfirmForm(request.POST)
            if form.is_valid():
                new_password = form.cleaned_data['new_password1']
                user.set_password(new_password)
                user.save()
                
                messages.success(
                    request,
                    'Your password has been reset successfully! You can now login with your new password.'
                )
                return redirect('login')
        else:
            form = PasswordResetConfirmForm()
        
        context = {
            'form': form,
            'page_title': 'Reset Password - KPSN',
        }
        return render(request, 'accounts/password_reset_confirm.html', context)
    else:
        messages.error(request, 'Invalid password reset link.')
        return redirect('home')


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def record_user_device(request, user):
    """Record user device information"""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    device_id = f"{user.id}_{user_agent[:50]}"
    
    device, created = UserDevice.objects.get_or_create(
        user=user,
        device_id=device_id,
        defaults={
            'device_name': get_device_name(user_agent),
            'device_type': get_device_type(user_agent),
            'browser': get_browser_name(user_agent),
            'os': get_os_name(user_agent),
            'ip_address': get_client_ip(request),
            'user_agent': user_agent,
        }
    )
    
    if not created:
        device.last_login = timezone.now()
        device.ip_address = get_client_ip(request)
        device.save()


def get_device_type(user_agent):
    """Determine device type from user agent"""
    user_agent = user_agent.lower()
    if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        return 'mobile'
    elif 'tablet' in user_agent or 'ipad' in user_agent:
        return 'tablet'
    return 'desktop'


def get_device_name(user_agent):
    """Extract device name from user agent"""
    return 'Unknown Device'


def get_browser_name(user_agent):
    """Extract browser name from user agent"""
    user_agent = user_agent.lower()
    if 'chrome' in user_agent:
        return 'Chrome'
    elif 'firefox' in user_agent:
        return 'Firefox'
    elif 'safari' in user_agent:
        return 'Safari'
    elif 'edge' in user_agent:
        return 'Edge'
    elif 'opera' in user_agent:
        return 'Opera'
    return 'Unknown'


def get_os_name(user_agent):
    """Extract OS name from user agent"""
    user_agent = user_agent.lower()
    if 'windows' in user_agent:
        return 'Windows'
    elif 'mac' in user_agent:
        return 'macOS'
    elif 'linux' in user_agent:
        return 'Linux'
    elif 'android' in user_agent:
        return 'Android'
    elif 'ios' in user_agent or 'iphone' in user_agent:
        return 'iOS'
    return 'Unknown'


def generate_membership_number(user):
    """Generate unique membership number"""
    import random
    import string
    
    year = timezone.now().year
    sequence = User.objects.filter(membership_start_date__year=year).count() + 1
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    membership_number = f"KPSN/{year}/{str(sequence).zfill(4)}/{random_chars}"
    user.membership_number = membership_number
    user.membership_start_date = timezone.now()
    user.membership_expiry_date = timezone.now() + timezone.timedelta(days=365)
    user.is_active_member = True
    user.is_verified = True
    user.save()
    
    return membership_number


# ============================================================
# AJAX VIEWS
# ============================================================

@login_required
def check_username_availability(request):
    """Check if username is available"""
    username = request.GET.get('username', '')
    if username:
        exists = User.objects.filter(username__iexact=username).exists()
        return JsonResponse({'available': not exists})
    return JsonResponse({'error': 'Username required'})


@login_required
def check_email_availability(request):
    """Check if email is available"""
    email = request.GET.get('email', '')
    if email:
        exists = User.objects.filter(email__iexact=email).exists()
        return JsonResponse({'available': not exists})
    return JsonResponse({'error': 'Email required'})


@login_required
@role_required('admin', 'super_admin')
def get_user_stats(request):
    """Get user statistics for admin dashboard"""
    
    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'pending_applications': RegistrationApplication.objects.filter(status='pending').count(),
        'role_counts': list(User.objects.values('role').annotate(count=Count('id'))),
        'registration_status_counts': list(User.objects.values('registration_status').annotate(count=Count('id'))),
    }
    
    return JsonResponse(stats)