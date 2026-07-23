# accounts/utils.py

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
import uuid


def generate_verification_token():
    """Generate a unique verification token"""
    return str(uuid.uuid4())


def send_verification_email(request, user):
    """Send email verification link to user"""
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
    )


def send_approval_email(request, user):
    """Send registration approval email"""
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
        fail_silently=True,
    )


def send_rejection_email(request, user, notes=None):
    """Send registration rejection email"""
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
        fail_silently=True,
    )


def send_info_request_email(request, user, notes=None):
    """Send request for more information email"""
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
        fail_silently=True,
    )


def send_password_reset_email(request, user, token, uid):
    """Send password reset email"""
    current_site = get_current_site(request)
    subject = 'Password Reset - KPSN'
    message = render_to_string('emails/password_reset.html', {
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
    )