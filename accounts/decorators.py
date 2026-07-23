# accounts/decorators.py

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseForbidden, JsonResponse
from functools import wraps
from .models import User


# ============================================================
# ROLE-BASED DECORATORS
# ============================================================

def role_required(*allowed_roles):
    """
    Decorator to check if user has one of the allowed roles.
    Usage: @role_required('admin', 'super_admin')
    
    Also supports role hierarchy (e.g., super_admin can access admin pages)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Please login to access this page.')
                return redirect('login')
            
            # Check if user's role is directly in allowed roles
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            # Check role hierarchy
            role_hierarchy = {
                'super_admin': 10,
                'admin': 9,
                'executive': 8,
                'moderator': 7,
                'verified_member': 6,
                'basic_member': 5,
                'prospective_member': 4,
                'researcher': 3,
                'alumni': 3,
                'partner': 3,
                'guest': 1,
            }
            
            user_level = role_hierarchy.get(request.user.role, 0)
            
            # Check if user has sufficient level for any allowed role
            for role in allowed_roles:
                if role_hierarchy.get(role, 0) <= user_level:
                    return view_func(request, *args, **kwargs)
            
            messages.error(request, f'Access denied. Required roles: {", ".join(allowed_roles)}')
            return redirect('home')
        
        return wrapper
    return decorator


def allowed_roles(*allowed_roles):
    """Alias for role_required"""
    return role_required(*allowed_roles)


def user_type_required(*user_types):
    """
    Decorator to check if user has one of the allowed user types.
    (Legacy - use role_required instead)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Please login to access this page.')
                return redirect('login')
            
            if request.user.role in user_types:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, f'Access denied. Required roles: {", ".join(user_types)}')
            return redirect('home')
        
        return wrapper
    return decorator


# ============================================================
# ACTIVITY LOG DECORATOR
# ============================================================

def user_activity_log(action_type=None, description=None):
    """
    Decorator to log user activity with optional custom action type and description.
    Usage: @user_activity_log('login', 'User logged in')
    Usage: @user_activity_log()  # Uses defaults
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            
            if request.user.is_authenticated:
                from .models import UserActivityLog
                try:
                    UserActivityLog.objects.create(
                        user=request.user,
                        action_type=action_type or 'page_view',
                        action_description=description or f'Accessed {view_func.__name__}',
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        referer_url=request.META.get('HTTP_REFERER', ''),
                        metadata={
                            'view_name': view_func.__name__,
                            'method': request.method,
                            'path': request.path,
                            'args': str(args),
                            'kwargs': str(kwargs),
                        }
                    )
                except Exception as e:
                    # Don't fail if logging fails
                    pass
            
            return response
        return wrapper
    return decorator


# ============================================================
# AUTHENTICATION DECORATORS
# ============================================================

def login_required_with_message(view_func):
    """
    Login required decorator with custom message
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """
    Decorator to check if user is admin or super_admin
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
        
        if request.user.role in ['admin', 'super_admin']:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    return wrapper


def staff_required(view_func):
    """
    Decorator to check if user is staff (admin, super_admin, executive, moderator)
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
        
        if request.user.role in ['admin', 'super_admin', 'executive', 'moderator']:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'Access denied. Staff privileges required.')
        return redirect('home')
    
    return wrapper


def member_required(view_func):
    """
    Decorator to check if user is a member (verified or basic)
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
        
        if request.user.role in ['verified_member', 'basic_member']:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'Access denied. Member privileges required.')
        return redirect('home')
    
    return wrapper


def verified_member_required(view_func):
    """
    Decorator to check if user is a verified member
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
        
        if request.user.role == 'verified_member':
            return view_func(request, *args, **kwargs)
        
        if request.user.role == 'basic_member':
            messages.warning(request, 'Please upgrade to verified member to access this feature.')
            return redirect('dashboard_redirect')
        
        messages.error(request, 'Access denied. Verified member privileges required.')
        return redirect('home')
    
    return wrapper


def approved_registration_required(view_func):
    """
    Decorator to check if user's registration has been approved
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
        
        if request.user.registration_status == 'approved':
            return view_func(request, *args, **kwargs)
        
        if request.user.registration_status == 'pending':
            messages.warning(request, 'Your registration is pending approval. Please wait for admin review.')
            return redirect('dashboard_redirect')
        
        if request.user.registration_status == 'rejected':
            messages.error(request, 'Your registration was rejected. Please contact support.')
            return redirect('home')
        
        if request.user.registration_status == 'banned':
            messages.error(request, 'Your account has been banned. Please contact support.')
            return redirect('home')
        
        if request.user.registration_status == 'suspended':
            messages.error(request, 'Your account has been suspended. Please contact support.')
            return redirect('home')
        
        messages.error(request, 'Access denied. Registration required.')
        return redirect('home')
    
    return wrapper


def email_verified_required(view_func):
    """
    Decorator to check if user's email has been verified
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
        
        if request.user.email_verified:
            return view_func(request, *args, **kwargs)
        
        messages.warning(request, 'Please verify your email before accessing this page.')
        return redirect('resend_verification')
    
    return wrapper


def active_member_required(view_func):
    """
    Decorator to check if user is an active member
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
        
        if request.user.is_active_member:
            return view_func(request, *args, **kwargs)
        
        messages.warning(request, 'Active membership required to access this page.')
        return redirect('dashboard_redirect')
    
    return wrapper


# ============================================================
# PERMISSION DECORATORS
# ============================================================

def permission_required(perm, login_url=None, raise_exception=False):
    """
    Decorator to check if user has a specific permission.
    Usage: @permission_required('can_manage_users')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if login_url:
                    return redirect(login_url)
                messages.warning(request, 'Please login to access this page.')
                return redirect('login')
            
            if hasattr(request.user, 'has_perm') and request.user.has_perm(perm):
                return view_func(request, *args, **kwargs)
            
            if raise_exception:
                raise PermissionDenied()
            
            messages.error(request, f'You do not have permission: {perm}')
            return redirect('home')
        
        return wrapper
    return decorator


def super_admin_required(view_func):
    """Decorator to check if user is super_admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
        
        if request.user.role == 'super_admin':
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'Access denied. Super Administrator privileges required.')
        return redirect('home')
    
    return wrapper


# ============================================================
# AJAX DECORATORS
# ============================================================

def ajax_required(view_func):
    """
    Decorator to ensure the request is AJAX
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'AJAX request required'}, status=400)
        return view_func(request, *args, **kwargs)
    return wrapper


def post_required(view_func):
    """
    Decorator to ensure the request is POST
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method != 'POST':
            messages.error(request, 'Invalid request method.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


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


# ============================================================
# CLASS-BASED VIEW DECORATORS (Mixins)
# ============================================================

class RoleRequiredMixin:
    """
    Mixin for class-based views to require specific roles
    Usage: 
    class MyView(RoleRequiredMixin, View):
        allowed_roles = ['admin', 'super_admin']
        permission_denied_message = 'Access denied.'
        permission_denied_redirect = 'home'
    """
    allowed_roles = []
    permission_denied_message = 'Access denied. Required role not found.'
    permission_denied_redirect = 'home'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
        
        # Check direct role match
        if self.allowed_roles and request.user.role in self.allowed_roles:
            return super().dispatch(request, *args, **kwargs)
        
        # Check role hierarchy
        role_hierarchy = {
            'super_admin': 10,
            'admin': 9,
            'executive': 8,
            'moderator': 7,
            'verified_member': 6,
            'basic_member': 5,
            'prospective_member': 4,
            'researcher': 3,
            'alumni': 3,
            'partner': 3,
            'guest': 1,
        }
        
        user_level = role_hierarchy.get(request.user.role, 0)
        for role in self.allowed_roles:
            if role_hierarchy.get(role, 0) <= user_level:
                return super().dispatch(request, *args, **kwargs)
        
        messages.error(request, self.permission_denied_message)
        return redirect(self.permission_denied_redirect)


class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin for admin-only views"""
    allowed_roles = ['admin', 'super_admin']
    permission_denied_message = 'Access denied. Admin privileges required.'


class StaffRequiredMixin(RoleRequiredMixin):
    """Mixin for staff-only views"""
    allowed_roles = ['admin', 'super_admin', 'executive', 'moderator']
    permission_denied_message = 'Access denied. Staff privileges required.'


class MemberRequiredMixin(RoleRequiredMixin):
    """Mixin for member-only views"""
    allowed_roles = ['verified_member', 'basic_member']
    permission_denied_message = 'Access denied. Member privileges required.'


class VerifiedMemberRequiredMixin(RoleRequiredMixin):
    """Mixin for verified member-only views"""
    allowed_roles = ['verified_member']
    permission_denied_message = 'Access denied. Verified member privileges required.'


class SuperAdminRequiredMixin(RoleRequiredMixin):
    """Mixin for super admin-only views"""
    allowed_roles = ['super_admin']
    permission_denied_message = 'Access denied. Super Administrator privileges required.'


# ============================================================
# CONTEXT PROCESSORS
# ============================================================

def user_role_context(request):
    """
    Context processor to add user role to templates
    Usage: Add to TEMPLATES.context_processors in settings.py
    """
    if request.user.is_authenticated:
        return {
            'user_role': request.user.role,
            'user_role_display': request.user.get_role_display(),
            'is_super_admin': request.user.role == 'super_admin',
            'is_admin': request.user.role in ['admin', 'super_admin'],
            'is_staff': request.user.role in ['admin', 'super_admin', 'executive', 'moderator'],
            'is_member': request.user.role in ['verified_member', 'basic_member'],
            'is_verified_member': request.user.role == 'verified_member',
            'is_basic_member': request.user.role == 'basic_member',
            'registration_status': request.user.registration_status,
            'registration_status_display': request.user.get_registration_status_display(),
            'is_approved': request.user.registration_status == 'approved',
            'is_pending': request.user.registration_status == 'pending',
            'is_rejected': request.user.registration_status == 'rejected',
        }
    return {
        'user_role': None,
        'user_role_display': None,
        'is_super_admin': False,
        'is_admin': False,
        'is_staff': False,
        'is_member': False,
        'is_verified_member': False,
        'is_basic_member': False,
        'registration_status': None,
        'registration_status_display': None,
        'is_approved': False,
        'is_pending': False,
        'is_rejected': False,
    }


# ============================================================
# TEMPLATE TAGS
# ============================================================

from django import template
register = template.Library()


@register.filter
def has_role(user, role):
    """Template filter to check if user has a specific role"""
    if not user or not user.is_authenticated:
        return False
    return user.role == role


@register.filter
def has_any_role(user, roles):
    """Template filter to check if user has any of the given roles"""
    if not user or not user.is_authenticated:
        return False
    roles_list = roles.split(',')
    return user.role in roles_list


@register.filter
def is_at_least(user, role):
    """Template filter to check if user is at least the given role level"""
    if not user or not user.is_authenticated:
        return False
    
    role_hierarchy = {
        'super_admin': 10,
        'admin': 9,
        'executive': 8,
        'moderator': 7,
        'verified_member': 6,
        'basic_member': 5,
        'prospective_member': 4,
        'researcher': 3,
        'alumni': 3,
        'partner': 3,
        'guest': 1,
    }
    
    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(role, 0)
    return user_level >= required_level


@register.simple_tag
def get_user_role_display(user):
    """Template tag to get user role display name"""
    if user and user.is_authenticated:
        return user.get_role_display()
    return ''