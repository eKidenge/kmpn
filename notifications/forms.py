from django import forms
from django.forms import ModelForm, TextInput, Textarea, Select, CheckboxInput, TimeInput
from .models import Notification, NotificationPreference


class NotificationPreferenceForm(forms.ModelForm):
    """Form for managing notification preferences"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled',
            'event_notifications', 'opportunity_notifications', 'community_notifications',
            'message_notifications', 'collaboration_notifications', 'membership_notifications',
            'payment_notifications', 'reminder_notifications',
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
            'digest_enabled', 'digest_frequency'
        ]
        widgets = {
            'email_enabled': CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_enabled': CheckboxInput(attrs={'class': 'form-check-input'}),
            'push_enabled': CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_enabled': CheckboxInput(attrs={'class': 'form-check-input'}),
            'event_notifications': CheckboxInput(attrs={'class': 'form-check-input'}),
            'opportunity_notifications': CheckboxInput(attrs={'class': 'form-check-input'}),
            'community_notifications': CheckboxInput(attrs={'class': 'form-check-input'}),
            'message_notifications': CheckboxInput(attrs={'class': 'form-check-input'}),
            'collaboration_notifications': CheckboxInput(attrs={'class': 'form-check-input'}),
            'membership_notifications': CheckboxInput(attrs={'class': 'form-check-input'}),
            'payment_notifications': CheckboxInput(attrs={'class': 'form-check-input'}),
            'reminder_notifications': CheckboxInput(attrs={'class': 'form-check-input'}),
            'quiet_hours_enabled': CheckboxInput(attrs={'class': 'form-check-input'}),
            'quiet_hours_start': TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'quiet_hours_end': TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'digest_enabled': CheckboxInput(attrs={'class': 'form-check-input'}),
            'digest_frequency': Select(attrs={'class': 'form-control'}),
        }


class NotificationFilterForm(forms.Form):
    """Form for filtering notifications"""
    
    notification_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Notification.NOTIFICATION_TYPES),  # Fixed: Use Notification model
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )
    
    is_read = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('true', 'Unread Only'),
            ('false', 'Read Only'),
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


class MarkAllReadForm(forms.Form):
    """Form for marking all notifications as read"""
    
    confirm = forms.BooleanField(
        required=True,
        widget=CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': 'Please confirm you want to mark all as read.'}
    )


class DeleteAllForm(forms.Form):
    """Form for deleting all notifications"""
    
    confirm = forms.BooleanField(
        required=True,
        widget=CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': 'Please confirm you want to delete all notifications.'}
    )