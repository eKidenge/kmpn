from django import forms
from django.forms import ModelForm, TextInput, Textarea, Select, EmailInput, CheckboxInput, DateTimeInput
from .models import Newsletter, NewsletterSubscriber


class NewsletterForm(forms.ModelForm):
    """Form for creating/editing newsletters"""
    
    class Meta:
        model = Newsletter
        fields = [
            'subject', 'content', 'from_email', 'reply_to',
            'send_to_all', 'target_groups', 'scheduled_at'
        ]
        widgets = {
            'subject': TextInput(attrs={'class': 'form-control', 'placeholder': 'Newsletter subject'}),
            'content': Textarea(attrs={'class': 'form-control', 'rows': 15, 'placeholder': 'Write your newsletter content here...'}),
            'from_email': EmailInput(attrs={'class': 'form-control', 'placeholder': 'from@example.com'}),
            'reply_to': EmailInput(attrs={'class': 'form-control', 'placeholder': 'reply@example.com'}),
            'send_to_all': CheckboxInput(attrs={'class': 'form-check-input'}),
            'target_groups': TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. members, premium, researchers'}),
            'scheduled_at': DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class NewsletterSubscriberForm(forms.ModelForm):
    """Form for subscribing to newsletter"""
    
    class Meta:
        model = NewsletterSubscriber
        fields = ['email', 'name']
        widgets = {
            'email': EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'}),
            'name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your name (optional)'}),
        }


class NewsletterSubscriberAdminForm(forms.ModelForm):
    """Form for managing subscribers (admin only)"""
    
    class Meta:
        model = NewsletterSubscriber
        fields = ['email', 'name', 'subscribed', 'groups']
        widgets = {
            'email': EmailInput(attrs={'class': 'form-control'}),
            'name': TextInput(attrs={'class': 'form-control'}),
            'subscribed': CheckboxInput(attrs={'class': 'form-check-input'}),
            'groups': TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. premium, researchers'}),
        }


class NewsletterFilterForm(forms.Form):
    """Form for filtering newsletters"""
    
    status = forms.ChoiceField(
        choices=[
            ('', 'All Status'),
            ('draft', 'Draft'),
            ('scheduled', 'Scheduled'),
            ('sent', 'Sent'),
            ('failed', 'Failed'),
        ],
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
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Search newsletters...'})
    )


class NewsletterSubscriberFilterForm(forms.Form):
    """Form for filtering subscribers"""
    
    subscribed = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('true', 'Subscribed'),
            ('false', 'Unsubscribed'),
        ],
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )
    
    group = forms.CharField(
        max_length=255,
        required=False,
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Filter by group'})
    )
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Search subscribers...'})
    )


class NewsletterTestForm(forms.Form):
    """Form for sending test newsletter"""
    
    test_email = forms.EmailField(
        required=True,
        widget=EmailInput(attrs={'class': 'form-control', 'placeholder': 'test@example.com'})
    )
    
    confirm = forms.BooleanField(
        required=True,
        widget=CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': 'Please confirm you want to send a test email.'}
    )