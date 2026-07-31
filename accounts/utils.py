# accounts/utils.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.utils import timezone
import uuid
import random
import string
import logging
import os

# Try to import Brevo SDK
try:
    import sib_api_v3_sdk
    from sib_api_v3_sdk.rest import ApiException
    BREVO_AVAILABLE = True
except ImportError:
    BREVO_AVAILABLE = False
    sib_api_v3_sdk = None
    ApiException = None

logger = logging.getLogger(__name__)


def generate_verification_token():
    """Generate a unique verification token"""
    return uuid.uuid4()


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


def send_verification_email_brevo(request, user):
    """
    Send verification email using Brevo API
    Returns: bool - True if email sent successfully, False otherwise
    """
    if not BREVO_AVAILABLE:
        logger.warning("Brevo SDK not available")
        return False
    
    try:
        # Get API key from environment
        api_key = os.environ.get('BREVO_API_KEY', '')
        if not api_key:
            logger.warning("BREVO_API_KEY not set in environment")
            return False
        
        # Configure API key
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = api_key
        
        # Create API instance
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        
        # Generate token if not exists
        if not user.email_verification_token:
            user.email_verification_token = uuid.uuid4()
            user.save()
        
        # Build verification URL
        domain = request.get_host() if request else 'kmpn.onrender.com'
        protocol = 'https' if request and request.is_secure() else 'http'
        verification_url = reverse('accounts:verify_email', kwargs={'token': user.email_verification_token})
        full_url = f"{protocol}://{domain}{verification_url}"
        
        logger.info(f"Verification URL: {full_url}")
        
        # Render email template
        html_content = render_to_string('emails/verify_email.html', {
            'user': user,
            'verification_url': full_url,
            'domain': domain,
            'protocol': protocol,
            'site_name': 'KPSN',
        })
        
        # Send email via Brevo API
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{'email': user.email, 'name': user.get_full_name() or user.username}],
            sender={'email': 'noreply@kmpn.or.ke', 'name': 'KPSN'},
            subject='Verify Your Email - KPSN',
            html_content=html_content,
        )
        
        api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Verification email sent via Brevo API to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Brevo API error for {user.email}: {str(e)}")
        return False


def send_verification_email(request, user):
    """
    Send email verification link to user using UUID token
    Tries Brevo API first, falls back to SMTP if available
    Returns: bool - True if email sent successfully, False otherwise
    """
    # Try Brevo API first if available
    if BREVO_AVAILABLE and os.environ.get('BREVO_API_KEY'):
        try:
            result = send_verification_email_brevo(request, user)
            if result:
                return True
        except Exception as e:
            logger.error(f"Brevo API failed, falling back to SMTP: {str(e)}")
    
    # Fallback to SMTP
    try:
        # Generate UUID token if not exists
        if not user.email_verification_token:
            user.email_verification_token = uuid.uuid4()
            user.save()
        
        # Get the current site domain
        current_site = get_current_site(request)
        domain = current_site.domain
        
        # For local development, use the request host
        if request:
            domain = request.get_host()
        
        # Determine protocol
        protocol = 'https' if request.is_secure() else 'http'
        
        # Build verification URL using UUID
        verification_url = reverse('accounts:verify_email', kwargs={'token': user.email_verification_token})
        full_url = f"{protocol}://{domain}{verification_url}"
        
        subject = 'Verify Your Email - KPSN'
        message = render_to_string('emails/verify_email.html', {
            'user': user,
            'verification_url': full_url,
            'domain': domain,
            'protocol': protocol,
            'site_name': 'KPSN',
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=message,
        )
        logger.info(f"Verification email sent via SMTP to {user.email}")
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
        domain = current_site.domain
        if request:
            domain = request.get_host()
        
        subject = 'Registration Approved - KPSN'
        message = render_to_string('emails/registration_approved.html', {
            'user': user,
            'domain': domain,
            'membership_number': user.membership_number,
            'site_name': 'KPSN',
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
        domain = current_site.domain
        if request:
            domain = request.get_host()
        
        subject = 'Registration Update - KPSN'
        message = render_to_string('emails/registration_rejected.html', {
            'user': user,
            'domain': domain,
            'notes': notes,
            'site_name': 'KPSN',
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
        domain = current_site.domain
        if request:
            domain = request.get_host()
        
        subject = 'Additional Information Required - KPSN'
        message = render_to_string('emails/registration_info_request.html', {
            'user': user,
            'domain': domain,
            'notes': notes,
            'site_name': 'KPSN',
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
        domain = current_site.domain
        if request:
            domain = request.get_host()
        
        protocol = 'https' if request.is_secure() else 'http'
        
        subject = 'Password Reset - KPSN'
        message = render_to_string('emails/password_reset_email.html', {
            'user': user,
            'domain': domain,
            'protocol': protocol,
            'uid': uid,
            'token': token,
            'site_name': 'KPSN',
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
        domain = current_site.domain
        if request:
            domain = request.get_host()
        
        subject = 'Welcome to KPSN!'
        message = render_to_string('emails/welcome.html', {
            'user': user,
            'domain': domain,
            'site_name': 'KPSN',
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
        domain = current_site.domain
        if request:
            domain = request.get_host()
        
        message = render_to_string('emails/newsletter.html', {
            'user': user,
            'domain': domain,
            'content': content,
            'site_name': 'KPSN',
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
        domain = current_site.domain
        if request:
            domain = request.get_host()
        
        message = render_to_string('emails/notification.html', {
            'user': user,
            'domain': domain,
            'content': content,
            'site_name': 'KPSN',
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
    Generate email verification URL for user using UUID
    Returns: str - The full verification URL
    """
    if not user.email_verification_token:
        user.email_verification_token = uuid.uuid4()
        user.save()
    
    current_site = get_current_site(request)
    domain = current_site.domain
    if request:
        domain = request.get_host()
    
    protocol = 'https' if request.is_secure() else 'http'
    verification_url = reverse('accounts:verify_email', kwargs={'token': user.email_verification_token})
    
    return f"{protocol}://{domain}{verification_url}"


def generate_password_reset_url(request, user):
    """
    Generate password reset URL for user
    Returns: str - The full password reset URL
    """
    current_site = get_current_site(request)
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    protocol = 'https' if request.is_secure() else 'http'
    domain = current_site.domain
    if request:
        domain = request.get_host()
    
    return f"{protocol}://{domain}/accounts/password-reset/confirm/{uid}/{token}/"


# Legacy aliases for backward compatibility
send_verification = send_verification_email
send_approval = send_approval_email
send_rejection = send_rejection_email
send_info_request = send_info_request_email