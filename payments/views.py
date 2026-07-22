from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json
import uuid
import hashlib
import hmac
import logging
from .models import Payment, Subscription
from .forms import (
    PaymentForm, MpesaPaymentForm, SubscriptionForm, 
    PaymentFilterForm, RefundForm, MpesaValidationForm
)
from accounts.decorators import user_activity_log, user_type_required
from accounts.models import User
from notifications.models import Notification

logger = logging.getLogger(__name__)


@login_required
def payment_list(request):
    """List user payments"""
    payments = Payment.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # Filters
    filter_form = PaymentFilterForm(request.GET)
    
    if filter_form.is_valid():
        payment_type = filter_form.cleaned_data.get('payment_type')
        if payment_type:
            payments = payments.filter(payment_type=payment_type)
        
        payment_method = filter_form.cleaned_data.get('payment_method')
        if payment_method:
            payments = payments.filter(payment_method=payment_method)
        
        status = filter_form.cleaned_data.get('status')
        if status:
            payments = payments.filter(status=status)
        
        date_from = filter_form.cleaned_data.get('date_from')
        if date_from:
            payments = payments.filter(created_at__date__gte=date_from)
        
        date_to = filter_form.cleaned_data.get('date_to')
        if date_to:
            payments = payments.filter(created_at__date__lte=date_to)
    
    paginator = Paginator(payments, 10)
    page = request.GET.get('page', 1)
    
    try:
        payments = paginator.page(page)
    except PageNotAnInteger:
        payments = paginator.page(1)
    except EmptyPage:
        payments = paginator.page(paginator.num_pages)
    
    # Get total spent
    total_spent = Payment.objects.filter(
        user=request.user,
        status='completed'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'payments': payments,
        'filter_form': filter_form,
        'total_spent': total_spent,
        'page_title': 'Payments - KMPN',
    }
    return render(request, 'payments/list.html', context)


@login_required
@user_activity_log('payment_initiate', 'Initiated payment')
def initiate_payment(request):
    """Initiate a payment"""
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user
            
            # Generate transaction ID
            payment.transaction_id = f"KMPN-{uuid.uuid4().hex[:12].upper()}"
            
            payment.save()
            
            # Redirect to payment gateway based on method
            if payment.payment_method == 'mpesa':
                return redirect('payments:mpesa_pay', payment_id=payment.id)
            elif payment.payment_method == 'card':
                # Redirect to card payment (stripe, etc.)
                messages.info(request, 'Card payments coming soon.')
                return redirect('payments:detail', payment_id=payment.id)
            else:
                messages.info(request, 'Payment initiated. Please complete the payment.')
                return redirect('payments:detail', payment_id=payment.id)
    else:
        # Pre-fill from GET parameters
        initial = {}
        if request.GET.get('item_name'):
            initial['item_name'] = request.GET.get('item_name')
        if request.GET.get('amount'):
            initial['amount'] = request.GET.get('amount')
        if request.GET.get('payment_type'):
            initial['payment_type'] = request.GET.get('payment_type')
        
        form = PaymentForm(initial=initial)
    
    context = {
        'form': form,
        'page_title': 'Make Payment - KMPN',
    }
    return render(request, 'payments/initiate.html', context)


@login_required
def mpesa_payment(request, payment_id):
    """M-Pesa payment processing"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if payment.status != 'pending':
        messages.warning(request, 'This payment has already been processed.')
        return redirect('payments:list')
    
    if request.method == 'POST':
        form = MpesaPaymentForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            
            # Here you would integrate with M-Pesa Daraja API
            # For now, we'll simulate a successful payment
            
            # Simulate payment processing
            import random
            success = random.random() > 0.2  # 80% success rate
            
            if success:
                payment.status = 'completed'
                payment.mpesa_phone_number = phone_number
                payment.mpesa_receipt_number = f"REC{random.randint(100000, 999999)}"
                payment.completed_at = timezone.now()
                payment.save()
                
                # Update subscription if membership payment
                if payment.payment_type == 'membership':
                    update_membership_status(request.user)
                
                # Send notification
                Notification.objects.create(
                    user=request.user,
                    notification_type='payment',
                    title='Payment Successful',
                    message=f'Your payment of {payment.amount} {payment.currency} was successful.',
                    link='/payments/',
                    metadata={'payment_id': payment.id}
                )
                
                messages.success(request, 'Payment completed successfully!')
                return redirect('payments:receipt', payment_id=payment.id)
            else:
                payment.status = 'failed'
                payment.failed_at = timezone.now()
                payment.failure_reason = 'Payment processing failed'
                payment.save()
                
                messages.error(request, 'Payment failed. Please try again.')
                return redirect('payments:detail', payment_id=payment.id)
    else:
        form = MpesaPaymentForm(initial={'amount': payment.amount})
    
    context = {
        'form': form,
        'payment': payment,
        'page_title': 'M-Pesa Payment - KMPN',
    }
    return render(request, 'payments/mpesa_pay.html', context)


@login_required
def payment_detail(request, payment_id):
    """View payment details"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    context = {
        'payment': payment,
        'page_title': f'Payment {payment.transaction_id}',
    }
    return render(request, 'payments/detail.html', context)


@login_required
def payment_receipt(request, payment_id):
    """View payment receipt"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if payment.status != 'completed':
        messages.warning(request, 'Receipt not available for incomplete payments.')
        return redirect('payments:list')
    
    context = {
        'payment': payment,
        'page_title': 'Payment Receipt - KMPN',
    }
    return render(request, 'payments/receipt.html', context)


@login_required
def subscription_view(request):
    """View and manage subscription"""
    subscription, created = Subscription.objects.get_or_create(
        user=request.user,
        defaults={
            'subscription_type': 'free',
            'status': 'active'
        }
    )
    
    if request.method == 'POST':
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            subscription = form.save()
            messages.success(request, 'Subscription updated successfully!')
            return redirect('payments:subscription')
    else:
        form = SubscriptionForm(instance=subscription)
    
    # Get subscription history (payments for subscriptions)
    subscription_payments = Payment.objects.filter(
        user=request.user,
        payment_type='membership',
        status='completed'
    ).order_by('-created_at')
    
    # Available plans
    plans = [
        {
            'id': 'free',
            'name': 'Free',
            'type': 'free',
            'price': 0,
            'currency': 'KES',
            'features': [
                'Basic community access',
                'Limited opportunities',
                'Basic profile',
                'Public resources'
            ],
            'popular': False
        },
        {
            'id': 'premium',
            'name': 'Premium',
            'type': 'premium',
            'price': 1000,
            'currency': 'KES',
            'billing_cycle': 'monthly',
            'features': [
                'Full community access',
                'Premium opportunities',
                'Advanced profile',
                'All resources',
                'Priority support',
                'Networking events'
            ],
            'popular': True
        },
        {
            'id': 'enterprise',
            'name': 'Enterprise',
            'type': 'enterprise',
            'price': 5000,
            'currency': 'KES',
            'billing_cycle': 'monthly',
            'features': [
                'Everything in Premium',
                'Custom branding',
                'Dedicated support',
                'API access',
                'Custom integrations',
                'Analytics dashboard'
            ],
            'popular': False
        }
    ]
    
    context = {
        'subscription': subscription,
        'plans': plans,
        'subscription_payments': subscription_payments[:5],
        'form': form,
        'page_title': 'Subscription - KMPN',
    }
    return render(request, 'payments/subscription.html', context)


@login_required
def cancel_subscription(request):
    """Cancel user subscription"""
    subscription = get_object_or_404(Subscription, user=request.user)
    
    if subscription.status in ['expired', 'cancelled']:
        messages.warning(request, 'Your subscription is already cancelled or expired.')
        return redirect('payments:subscription')
    
    if request.method == 'POST':
        subscription.status = 'cancelled'
        subscription.cancelled_at = timezone.now()
        subscription.auto_renew = False
        subscription.save()
        
        Notification.objects.create(
            user=request.user,
            notification_type='payment',
            title='Subscription Cancelled',
            message='Your subscription has been cancelled. You will lose premium access at the end of your billing cycle.',
            link='/payments/subscription/',
            metadata={'subscription_id': subscription.id}
        )
        
        messages.success(request, 'Subscription cancelled successfully.')
        return redirect('payments:subscription')
    
    context = {
        'subscription': subscription,
        'page_title': 'Cancel Subscription - KMPN',
    }
    return render(request, 'payments/cancel_subscription.html', context)


@login_required
@user_type_required(['admin', 'moderator'])
def payment_admin(request):
    """Admin view for payments"""
    payments = Payment.objects.all().order_by('-created_at')
    
    # Filters
    status = request.GET.get('status')
    if status:
        payments = payments.filter(status=status)
    
    payment_type = request.GET.get('payment_type')
    if payment_type:
        payments = payments.filter(payment_type=payment_type)
    
    search = request.GET.get('search')
    if search:
        payments = payments.filter(
            Q(user__email__icontains=search) |
            Q(transaction_id__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)
        )
    
    paginator = Paginator(payments, 20)
    page = request.GET.get('page', 1)
    
    try:
        payments = paginator.page(page)
    except PageNotAnInteger:
        payments = paginator.page(1)
    except EmptyPage:
        payments = paginator.page(paginator.num_pages)
    
    # Summary statistics
    total_completed = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    total_pending = Payment.objects.filter(status='pending').count()
    total_failed = Payment.objects.filter(status='failed').count()
    
    context = {
        'payments': payments,
        'total_completed': total_completed,
        'total_pending': total_pending,
        'total_failed': total_failed,
        'page_title': 'Payment Management - Admin',
    }
    return render(request, 'payments/admin.html', context)


@login_required
@user_type_required(['admin', 'moderator'])
def refund_payment(request, payment_id):
    """Refund a payment (admin only)"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    if payment.status != 'completed':
        messages.error(request, 'Only completed payments can be refunded.')
        return redirect('payments:admin')
    
    if payment.refunded_amount > 0:
        messages.warning(request, 'This payment has already been partially or fully refunded.')
        return redirect('payments:admin')
    
    if request.method == 'POST':
        form = RefundForm(request.POST)
        if form.is_valid():
            refund_amount = form.cleaned_data['refund_amount']
            refund_reason = form.cleaned_data['refund_reason']
            
            if refund_amount > payment.amount:
                messages.error(request, 'Refund amount cannot exceed the payment amount.')
                return redirect('payments:refund', payment_id=payment_id)
            
            # Process refund (in production, integrate with payment gateway)
            payment.refunded_amount = refund_amount
            payment.refunded_at = timezone.now()
            payment.refund_reason = refund_reason
            
            if refund_amount == payment.amount:
                payment.status = 'refunded'
            
            payment.save()
            
            # Notify user
            Notification.objects.create(
                user=payment.user,
                notification_type='payment',
                title=f'Payment Refunded: {payment.transaction_id}',
                message=f'Your payment of {refund_amount} {payment.currency} has been refunded. Reason: {refund_reason}',
                link='/payments/',
                metadata={'payment_id': payment.id}
            )
            
            messages.success(request, f'Refund of {refund_amount} {payment.currency} processed successfully!')
            return redirect('payments:admin')
    else:
        form = RefundForm(initial={'refund_amount': payment.amount})
    
    context = {
        'form': form,
        'payment': payment,
        'page_title': f'Refund Payment - {payment.transaction_id}',
    }
    return render(request, 'payments/refund.html', context)


# Webhook for M-Pesa callbacks
@csrf_exempt
def mpesa_webhook(request):
    """Handle M-Pesa webhook callbacks"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Verify the webhook signature
            # signature = request.headers.get('X-Signature')
            # if not verify_signature(data, signature):
            #     return JsonResponse({'error': 'Invalid signature'}, status=400)
            
            # Process payment
            transaction_id = data.get('transaction_id')
            status = data.get('status')
            
            if transaction_id and status == 'completed':
                try:
                    payment = Payment.objects.get(transaction_id=transaction_id)
                    payment.status = 'completed'
                    payment.mpesa_receipt_number = data.get('receipt_number')
                    payment.completed_at = timezone.now()
                    payment.save()
                    
                    # Update subscription if membership payment
                    if payment.payment_type == 'membership':
                        update_membership_status(payment.user)
                    
                    return JsonResponse({'success': True})
                except Payment.DoesNotExist:
                    return JsonResponse({'error': 'Payment not found'}, status=404)
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


def verify_signature(data, signature):
    """Verify webhook signature"""
    # Implement signature verification here
    # Using your secret key
    secret = getattr(settings, 'MPESA_WEBHOOK_SECRET', '')
    if not secret:
        return True  # Skip verification in development
    
    expected = hmac.new(
        secret.encode(),
        json.dumps(data).encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# Helper functions
def update_membership_status(user):
    """Update user's membership status after payment"""
    try:
        subscription = Subscription.objects.get(user=user)
        
        # Update subscription details
        subscription.status = 'active'
        subscription.start_date = timezone.now()
        subscription.end_date = timezone.now() + timezone.timedelta(days=365)
        subscription.last_billing_date = timezone.now()
        subscription.next_billing_date = timezone.now() + timezone.timedelta(days=365)
        subscription.save()
        
        # Update member status
        try:
            member = Member.objects.get(user=user)
            member.is_active_member = True
            member.membership_start_date = timezone.now()
            member.membership_expiry_date = timezone.now() + timezone.timedelta(days=365)
            member.save()
        except Member.DoesNotExist:
            pass
        
        return True
    except Subscription.DoesNotExist:
        return False


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# AJAX Endpoints

@login_required
def check_payment_status(request, payment_id):
    """Check payment status (AJAX)"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    return JsonResponse({
        'status': payment.status,
        'transaction_id': payment.transaction_id,
        'amount': str(payment.amount),
        'currency': payment.currency,
        'completed_at': payment.completed_at.isoformat() if payment.completed_at else None
    })


@login_required
def get_subscription_status(request):
    """Get subscription status (AJAX)"""
    try:
        subscription = Subscription.objects.get(user=request.user)
        is_active = subscription.is_active()
        
        return JsonResponse({
            'subscription_type': subscription.subscription_type,
            'status': subscription.status,
            'is_active': is_active,
            'start_date': subscription.start_date.isoformat() if subscription.start_date else None,
            'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
            'days_remaining': subscription.days_remaining(),
            'auto_renew': subscription.auto_renew
        })
    except Subscription.DoesNotExist:
        return JsonResponse({
            'subscription_type': 'free',
            'status': 'inactive',
            'is_active': False,
            'start_date': None,
            'end_date': None,
            'days_remaining': 0,
            'auto_renew': False
        })