from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
import uuid


def generate_verification_token():
    """Generate unique verification token"""
    return uuid.uuid4()


def send_verification_email(request, user):
    """Send email verification link"""
    current_site = get_current_site(request)
    token = user.email_verification_token
    
    mail_subject = 'Verify Your Email - KMPN'
    message = render_to_string('accounts/verification_email.html', {
        'user': user,
        'domain': current_site.domain,
        'token': token,
    })
    
    send_mail(
        mail_subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def generate_membership_number(user):
    """Generate unique membership number"""
    import random
    import string
    from django.utils import timezone
    
    year = timezone.now().year
    sequence = User.objects.filter(membership_start_date__year=year).count() + 1
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    return f"KMPN/{year}/{str(sequence).zfill(4)}/{random_chars}"
