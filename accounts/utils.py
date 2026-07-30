# accounts/utils.py

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.utils import timezone
import uuid
import random
import string
import logging

logger = logging.getLogger(__name__)


def generate_verification_token():
    """Generate a unique verification token"""
    return str(uuid.uuid4())


def generate_membership_number(user):
    """
    Generate unique membership number for a user
    Returns: str - The generated membership number
    """
    from .models import User
    
    try:
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
        
        logger.info(f"Generated membership number {membership_number} for user {user.email}")
        return membership_number
        
    except Exception as e:
        logger.error(f"Failed to generate membership number for {user.email}: {str(e)}")
        # Fallback: generate a simple number
        fallback_number = f"KPSN/{timezone.now().year}/{uuid.uuid4().hex[:8].upper()}"
        user.membership_number = fallback_number
        user.membership_start_date = timezone.now()
        user.membership_expiry_date = timezone.now() + timezone.timedelta(days=365)
        user.is_active_member = True
        user.is_verified = True
        user.save()
        return fallback_number


def send_verification_email(request, user):
    """
    Send email verification link to user
    Returns: bool - True if email sent successfully, False otherwise
    """
    try:
        current_site = get_current_site(request)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        subject = 'Verify Your Email - KPSN'
        message = render_to_string('emails/verify_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': uid,
            'token': token,
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=message,  # Send as HTML
        )
        logger.info(f"Verification email sent to {user.email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False


def send_approval_email(request, user):
    """
    Send registration approval email
    Returns: bool - True if email sent successfully, False otherwise
    """
    try:
        current_site = get_current_site(request)
        subject = 'Registration Approved - KPSN'
        message = render_to_string('emails/registration_approved.html', {
            'user': user,
            'domain': current_site.domain,
            'membership_number': user.membership_number,
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=message,
        )
        logger.info(f"Approval email sent to {user.email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send approval email to {user.email}: {str(e)}")
        return False


def send_rejection_email(request, user, notes=None):
    """
    Send registration rejection email
    Returns: bool - True if email sent successfully, False otherwise
    """
    try:
        current_site = get_current_site(request)
        subject = 'Registration Update - KPSN'
        message = render_to_string('emails/registration_rejected.html', {
            'user': user,
            'domain': current_site.domain,
            'notes': notes,
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=message,
        )
        logger.info(f"Rejection email sent to {user.email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send rejection email to {user.email}: {str(e)}")
        return False


def send_info_request_email(request, user, notes=None):
    """
    Send request for more information email
    Returns: bool - True if email sent successfully, False otherwise
    """
    try:
        current_site = get_current_site(request)
        subject = 'Additional Information Required - KPSN'
        message = render_to_string('emails/registration_info_request.html', {
            'user': user,
            'domain': current_site.domain,
            'notes': notes,
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=message,
        )
        logger.info(f"Info request email sent to {user.email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send info request email to {user.email}: {str(e)}")
        return False


def send_password_reset_email(request, user, token, uid):
    """
    Send password reset email
    Returns: bool - True if email sent successfully, False otherwise
    """
    try:
        current_site = get_current_site(request)
        subject = 'Password Reset - KPSN'
        message = render_to_string('accounts/password_reset_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': uid,
            'token': token,
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=message,
        )
        logger.info(f"Password reset email sent to {user.email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False


def send_welcome_email(request, user):
    """
    Send welcome email to new user
    Returns: bool - True if email sent successfully, False otherwise
    """
    try:
        current_site = get_current_site(request)
        subject = 'Welcome to KPSN!'
        message = render_to_string('emails/welcome.html', {
            'user': user,
            'domain': current_site.domain,
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=message,
        )
        logger.info(f"Welcome email sent to {user.email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False


def send_newsletter_email(request, user, subject, content):
    """
    Send newsletter email to user
    Returns: bool - True if email sent successfully, False otherwise
    """
    try:
        current_site = get_current_site(request)
        message = render_to_string('emails/newsletter.html', {
            'user': user,
            'domain': current_site.domain,
            'content': content,
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=message,
        )
        logger.info(f"Newsletter email sent to {user.email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send newsletter email to {user.email}: {str(e)}")
        return False


def send_notification_email(request, user, subject, content):
    """
    Send notification email to user
    Returns: bool - True if email sent successfully, False otherwise
    """
    try:
        current_site = get_current_site(request)
        message = render_to_string('emails/notification.html', {
            'user': user,
            'domain': current_site.domain,
            'content': content,
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=message,
        )
        logger.info(f"Notification email sent to {user.email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send notification email to {user.email}: {str(e)}")
        return False


def generate_verification_url(request, user):
    """
    Generate email verification URL for user
    Returns: str - The full verification URL
    """
    current_site = get_current_site(request)
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    protocol = 'https' if request.is_secure() else 'http'
    
    return f"{protocol}://{current_site.domain}/accounts/verify-email/{uid}/{token}/"


def generate_password_reset_url(request, user):
    """
    Generate password reset URL for user
    Returns: str - The full password reset URL
    """
    current_site = get_current_site(request)
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    protocol = 'https' if request.is_secure() else 'http'
    
    return f"{protocol}://{current_site.domain}/accounts/password-reset/{uid}/{token}/"


# Legacy aliases for backward compatibility
send_verification = send_verification_email
send_approval = send_approval_email
send_rejection = send_rejection_email
send_info_request = send_info_request_email