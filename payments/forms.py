from django import forms
from django.forms import ModelForm, TextInput, Textarea, Select, NumberInput, EmailInput, URLInput
from .models import Payment, Subscription


class PaymentForm(forms.ModelForm):
    """Form for initiating payments"""
    
    class Meta:
        model = Payment
        fields = [
            'payment_type', 'payment_method', 'amount', 'currency',
            'item_name', 'item_id', 'item_type', 'description'
        ]
        widgets = {
            'payment_type': Select(attrs={'class': 'form-control'}),
            'payment_method': Select(attrs={'class': 'form-control'}),
            'amount': NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'currency': TextInput(attrs={'class': 'form-control', 'placeholder': 'KES'}),
            'item_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Item name'}),
            'item_id': NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'item_type': TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. membership, event'}),
            'description': Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Payment description...'}),
        }


class MpesaPaymentForm(forms.Form):
    """Form for M-Pesa payment"""
    
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 254700000000',
            'help_text': 'Enter phone number in international format (e.g., 254700000000)'
        }),
        help_text='Enter phone number in international format (e.g., 254700000000)'
    )
    
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '1',
            'readonly': 'readonly'
        })
    )
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        # Remove any whitespace
        phone_number = phone_number.replace(' ', '').replace('-', '')
        
        # Validate phone number format
        import re
        if not re.match(r'^254\d{9}$', phone_number):
            raise forms.ValidationError(
                'Phone number must be in format: 254XXXXXXXXX (e.g., 254700000000)'
            )
        
        return phone_number


class SubscriptionForm(forms.ModelForm):
    """Form for managing subscriptions"""
    
    class Meta:
        model = Subscription
        fields = ['subscription_type', 'billing_cycle', 'auto_renew']
        widgets = {
            'subscription_type': Select(attrs={'class': 'form-control'}),
            'billing_cycle': Select(attrs={'class': 'form-control'}),
            'auto_renew': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PaymentFilterForm(forms.Form):
    """Form for filtering payments"""
    
    payment_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Payment.PAYMENT_TYPES),
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )
    
    payment_method = forms.ChoiceField(
        choices=[('', 'All Methods')] + list(Payment.PAYMENT_METHODS),
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(Payment.PAYMENT_STATUS),
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class RefundForm(forms.Form):
    """Form for processing refunds"""
    
    refund_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        widget=NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
    )
    
    refund_reason = forms.CharField(
        required=True,
        widget=Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for refund...'})
    )
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': 'Please confirm you want to process this refund.'}
    )
    
    def clean_refund_amount(self):
        refund_amount = self.cleaned_data.get('refund_amount')
        if refund_amount <= 0:
            raise forms.ValidationError('Refund amount must be greater than 0.')
        return refund_amount


class MpesaValidationForm(forms.Form):
    """Form for validating M-Pesa transactions"""
    
    transaction_id = forms.CharField(max_length=50, required=True)
    amount = forms.DecimalField(max_digits=10, decimal_places=2, required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    receipt_number = forms.CharField(max_length=50, required=True)
    
    def clean_transaction_id(self):
        transaction_id = self.cleaned_data.get('transaction_id')
        if not transaction_id or len(transaction_id) < 5:
            raise forms.ValidationError('Invalid transaction ID.')
        return transaction_id