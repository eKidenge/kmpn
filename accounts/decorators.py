from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import UserActivityLog


def user_activity_log(action_type, description=None):
    """Decorator to log user activity"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            
            if request.user.is_authenticated:
                action_desc = description or f"{action_type} performed"
                UserActivityLog.objects.create(
                    user=request.user,
                    action_type=action_type,
                    action_description=action_desc,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                )
            
            return response
        return wrapper
    return decorator


def user_type_required(allowed_types):
    """Decorator to restrict access based on user type"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please login to access this page.')
                return redirect('login')
            
            if request.user.user_type not in allowed_types:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('home')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
