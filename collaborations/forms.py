from django import forms
from django.contrib.auth import get_user_model
from .models import (
    CollaborationRequest, CollaborationApplication,
    SupervisorMatching, CollaborationMessage
)

User = get_user_model()


class CollaborationRequestForm(forms.ModelForm):
    """Form for creating collaboration requests"""
    
    target_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'})
    )
    
    class Meta:
        model = CollaborationRequest
        fields = [
            'title', 'description', 'collaboration_type',
            'is_open', 'required_skills', 'required_expertise',
            'start_date', 'end_date', 'is_remote', 'location',
            'country', 'has_funding', 'funding_details',
            'attachments', 'expires_at'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'collaboration_type': forms.Select(attrs={'class': 'form-control'}),
            'required_skills': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, R, SPSS'}),
            'required_expertise': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Machine Learning, Statistics'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_remote': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'has_funding': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'funding_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'expires_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class CollaborationApplicationForm(forms.ModelForm):
    """Form for applying to collaborations"""
    
    class Meta:
        model = CollaborationApplication
        fields = ['cover_letter', 'skills', 'experience', 'availability', 'attachments']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'skills': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, R, SPSS'}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'availability': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SupervisorMatchingForm(forms.ModelForm):
    """Form for supervisor matching"""
    
    class Meta:
        model = SupervisorMatching
        fields = [
            'research_area', 'research_interest', 'specific_topic',
            'preferred_institution', 'preferred_location',
            'availability_start', 'supervisor_availability'
        ]
        widgets = {
            'research_area': forms.TextInput(attrs={'class': 'form-control'}),
            'research_interest': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'specific_topic': forms.TextInput(attrs={'class': 'form-control'}),
            'preferred_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'preferred_location': forms.TextInput(attrs={'class': 'form-control'}),
            'availability_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'supervisor_availability': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CollaborationMessageForm(forms.ModelForm):
    """Form for sending collaboration messages"""
    
    class Meta:
        model = CollaborationMessage
        fields = ['message', 'attachments']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
