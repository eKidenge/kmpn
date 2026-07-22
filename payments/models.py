from django.db import models
from django.conf import settings
from django.utils import timezone


class Payment(models.Model):
    """Payment transactions"""
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_METHODS = (
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
        ('bank', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('other', 'Other'),
    )
    
    PAYMENT_TYPES = (
        ('membership', 'Membership Fee'),
        ('event', 'Event Registration'),
        ('donation', 'Donation'),
        ('service', 'Service Fee'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Amount
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='KES')
    
    # Transaction details
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    
    # M-Pesa specific
    mpesa_receipt_number = models.CharField(max_length=50, blank=True, null=True)
    mpesa_transaction_code = models.CharField(max_length=50, blank=True, null=True)
    mpesa_phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Item details
    item_name = models.CharField(max_length=255)
    item_id = models.IntegerField(blank=True, null=True)
    item_type = models.CharField(max_length=50, blank=True, null=True)
    
    # Description
    description = models.TextField(blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Completion
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True, null=True)
    
    # Refund
    refunded_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refunded_at = models.DateTimeField(null=True, blank=True)
    refund_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['payment_type']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.amount} {self.currency} - {self.status}"
    
    def complete_payment(self):
        """Complete payment transaction"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def fail_payment(self, reason=None):
        """Fail payment transaction"""
        self.status = 'failed'
        self.failed_at = timezone.now()
        if reason:
            self.failure_reason = reason
        self.save()


class Subscription(models.Model):
    """User subscriptions"""
    
    SUBSCRIPTION_STATUS = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    
    SUBSCRIPTION_TYPES = (
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPES, default='free')
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='inactive')
    
    # Plan details
    plan_name = models.CharField(max_length=255, blank=True, null=True)
    plan_description = models.TextField(blank=True, null=True)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='KES')
    billing_cycle = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
            ('one_time', 'One Time')
        ],
        default='monthly'
    )
    
    # Dates
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    last_billing_date = models.DateTimeField(null=True, blank=True)
    next_billing_date = models.DateTimeField(null=True, blank=True)
    
    # Auto-renewal
    auto_renew = models.BooleanField(default=True)
    
    # Features
    features = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'subscriptions'
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
    
    def __str__(self):
        return f"{self.user.email} - {self.subscription_type} ({self.status})"
    
    def is_active(self):
        """Check if subscription is active"""
        if self.status != 'active':
            return False
        if self.end_date and timezone.now() > self.end_date:
            self.status = 'expired'
            self.save()
            return False
        return True
    
    def days_remaining(self):
        """Get days remaining in subscription"""
        if self.end_date:
            delta = self.end_date - timezone.now()
            return delta.days if delta.days > 0 else 0
        return None
