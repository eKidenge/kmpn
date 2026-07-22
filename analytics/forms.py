from django import forms
from django.forms import ModelForm, TextInput, Select, DateInput, NumberInput
from .models import CampaignAnalytics


class AnalyticsDateFilterForm(forms.Form):
    """Form for filtering analytics by date"""
    
    date_range = forms.ChoiceField(
        choices=[
            ('7', 'Last 7 Days'),
            ('30', 'Last 30 Days'),
            ('90', 'Last 90 Days'),
            ('180', 'Last 6 Months'),
            ('365', 'Last Year'),
            ('custom', 'Custom Range'),
        ],
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )
    
    start_date = forms.DateField(
        required=False,
        widget=DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    end_date = forms.DateField(
        required=False,
        widget=DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class CampaignAnalyticsForm(forms.ModelForm):
    """Form for campaign analytics"""
    
    class Meta:
        model = CampaignAnalytics
        fields = [
            'campaign_type', 'campaign_name', 'subject',
            'total_sent', 'total_delivered', 'total_opened',
            'total_clicked', 'total_bounced', 'total_unsubscribed',
            'total_spam'
        ]
        widgets = {
            'campaign_type': Select(attrs={'class': 'form-control'}),
            'campaign_name': TextInput(attrs={'class': 'form-control'}),
            'subject': TextInput(attrs={'class': 'form-control'}),
            'total_sent': NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'total_delivered': NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'total_opened': NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'total_clicked': NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'total_bounced': NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'total_unsubscribed': NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'total_spam': NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
