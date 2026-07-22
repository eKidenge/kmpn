from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
import logging
from .models import User, UserActivityLog, UserDevice
from .forms import (
    UserRegistrationForm, UserLoginForm, UserUpdateForm,
    PasswordResetRequestForm, PasswordResetConfirmForm
)
from .decorators import user_activity_log, user_type_required
from .utils import send_verification_email, generate_verification_token

logger = logging.getLogger(__name__)


def home(request):
    """Homepage view"""
    context = {
        'page_title': 'KMPN - Kenya Masters and PhD Network',
    }
    return render(request, 'home.html', context)


def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                
                # Send verification email
                send_verification_email(request, user)
                
                messages.success(
                    request, 
                    'Registration successful! Please check your email to verify your account.'
                )
                return redirect('login')
            
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                messages.error(request, 'An error occurred during registration. Please try again.')
    else:
        form = UserRegistrationForm()
    
    context = {
        'form': form,
        'page_title': 'Register - KMPN',
    }
    return render(request, 'accounts/register.html', context)


def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                if user.is_locked():
                    messages.error(request, 'Your account is temporarily locked. Please try again later.')
                    return render(request, 'accounts/login.html', {'form': form})
                
                login(request, user)
                
                # Log user activity
                UserActivityLog.objects.create(
                    user=user,
                    action_type='login',
                    action_description='User logged in',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    referer_url=request.META.get('HTTP_REFERER', ''),
                    metadata={'user_agent': request.META.get('HTTP_USER_AGENT', '')}
                )
                
                # Record device
                record_user_device(request, user)
                
                # Reset login attempts
                user.reset_login_attempts()
                
                # Update last login IP
                user.last_login_ip = get_client_ip(request)
                user.save()
                
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                
                # Redirect to next parameter or home
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('home')
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
        'page_title': 'Login - KMPN',
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


@login_required
def profile_view(request, username=None):
    """User profile view"""
    if username:
        profile_user = get_object_or_404(User, username=username, is_active=True)
    else:
        profile_user = request.user
    
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
            )
            
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile', username=request.user.username)
    else:
        form = UserUpdateForm(instance=request.user)
    
    context = {
        'form': form,
        'page_title': 'Update Profile - KMPN',
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
        
        # Update session hash to keep user logged in
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
        'page_title': 'Change Password - KMPN',
    }
    return render(request, 'accounts/change_password.html', context)


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
        
        # Generate membership number
        generate_membership_number(user)
        
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


def password_reset_request(request):
    """Request password reset"""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.get(email=email)
            
            # Generate token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Send reset email
            current_site = get_current_site(request)
            mail_subject = 'Password Reset - KMPN'
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
    else:
        form = PasswordResetRequestForm()
    
    context = {
        'form': form,
        'page_title': 'Reset Password - KMPN',
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
            'page_title': 'Reset Password - KMPN',
        }
        return render(request, 'accounts/password_reset_confirm.html', context)
    else:
        messages.error(request, 'Invalid password reset link.')
        return redirect('home')


# Helper Functions

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
    device_id = f"{user.id}_{request.META.get('HTTP_USER_AGENT', '')[:50]}"
    
    # Check if device already exists
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
    # Simplified - you can use a library like user-agents
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
    
    membership_number = f"KMPN/{year}/{str(sequence).zfill(4)}/{random_chars}"
    user.membership_number = membership_number
    user.membership_start_date = timezone.now()
    user.membership_expiry_date = timezone.now() + timezone.timedelta(days=365)
    user.is_active_member = True
    user.is_verified = True
    user.save()
    
    return membership_number


# AJAX Views

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
