# opportunities/forms.py

from django import forms
from django.forms import ModelForm, TextInput, Textarea, Select, FileInput, CheckboxInput, NumberInput, DateInput, DateTimeInput, EmailInput, URLInput
from .models import Opportunity, OpportunityApplication


class OpportunityForm(forms.ModelForm):
    """Form for creating/editing opportunities"""
    
    # Override JSON fields to handle comma-separated input
    required_documents = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'CV, Cover Letter, Transcripts (comma separated)'
        }),
        help_text="Enter required documents separated by commas"
    )
    
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'scholarship, research, AI (comma separated)'
        }),
        help_text="Enter tags separated by commas"
    )
    
    disciplines = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Computer Science, Physics, Medicine (comma separated)'
        }),
        help_text="Enter disciplines separated by commas"
    )
    
    class Meta:
        model = Opportunity
        fields = [
            'title', 'description', 'opportunity_type', 'organization_name',
            'organization_website', 'organization_logo', 'location', 'country',
            'is_remote', 'application_deadline', 'start_date', 'end_date',
            'has_funding', 'funding_amount', 'currency', 'funding_details',
            'eligibility_criteria', 'required_qualifications', 'preferred_qualifications',
            'application_requirements', 'application_url',
            'application_email', 'application_instructions', 'contact_person',
            'contact_email', 'contact_phone',
        ]
        widgets = {
            'title': TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter opportunity title'}),
            'description': Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Detailed description of the opportunity...'}),
            'opportunity_type': Select(attrs={'class': 'form-control'}),
            'organization_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Organization name'}),
            'organization_website': URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'organization_logo': FileInput(attrs={'class': 'form-control'}),
            'location': TextInput(attrs={'class': 'form-control', 'placeholder': 'City, Country'}),
            'country': TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'is_remote': CheckboxInput(attrs={'class': 'form-check-input'}),
            'application_deadline': DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'start_date': DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'has_funding': CheckboxInput(attrs={'class': 'form-check-input'}),
            'funding_amount': NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'currency': TextInput(attrs={'class': 'form-control', 'placeholder': 'KES, USD, EUR'}),
            'funding_details': Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Details about funding...'}),
            'eligibility_criteria': Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Who is eligible to apply?'}),
            'required_qualifications': Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Required qualifications...'}),
            'preferred_qualifications': Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Preferred qualifications...'}),
            'application_requirements': Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'What is required for the application?'}),
            'application_url': URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/apply'}),
            'application_email': EmailInput(attrs={'class': 'form-control', 'placeholder': 'apply@example.com'}),
            'application_instructions': Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional application instructions...'}),
            'contact_person': TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact person name'}),
            'contact_email': EmailInput(attrs={'class': 'form-control', 'placeholder': 'contact@example.com'}),
            'contact_phone': TextInput(attrs={'class': 'form-control', 'placeholder': '+254 700 000000'}),
        }
    
    def clean_required_documents(self):
        """Convert comma-separated string to list"""
        data = self.cleaned_data.get('required_documents', '')
        if data:
            return [item.strip() for item in data.split(',') if item.strip()]
        return []
    
    def clean_tags(self):
        """Convert comma-separated string to list"""
        data = self.cleaned_data.get('tags', '')
        if data:
            return [item.strip() for item in data.split(',') if item.strip()]
        return []
    
    def clean_disciplines(self):
        """Convert comma-separated string to list"""
        data = self.cleaned_data.get('disciplines', '')
        if data:
            return [item.strip() for item in data.split(',') if item.strip()]
        return []
    
    def clean_application_deadline(self):
        """Ensure deadline is in the future"""
        deadline = self.cleaned_data.get('application_deadline')
        if deadline:
            from django.utils import timezone
            if deadline < timezone.now():
                raise forms.ValidationError("Application deadline must be in the future.")
        return deadline
    
    def clean_funding_amount(self):
        """Ensure funding amount is positive if funding is available"""
        amount = self.cleaned_data.get('funding_amount')
        has_funding = self.cleaned_data.get('has_funding')
        if has_funding and (amount is None or amount <= 0):
            raise forms.ValidationError("Please enter a valid funding amount.")
        return amount


class OpportunityApplicationForm(forms.ModelForm):
    """Form for applying to opportunities"""
    
    class Meta:
        model = OpportunityApplication
        fields = ['cover_letter', 'message']
        widgets = {
            'cover_letter': Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Write your cover letter here...'}),
            'message': Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Any additional message...'}),
        }


class OpportunityFilterForm(forms.Form):
    """Form for filtering opportunities"""
    
    opportunity_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Opportunity.OPPORTUNITY_TYPES),
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )
    
    country = forms.CharField(
        max_length=100,
        required=False,
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'})
    )
    
    has_funding = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('true', 'Has Funding'),
            ('false', 'No Funding'),
        ],
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Search opportunities...'})
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', 'Newest'),
            ('application_deadline', 'Deadline Soon'),
            ('-application_count', 'Most Popular'),
            ('-view_count', 'Most Viewed'),
        ],
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )


class OpportunityReviewForm(forms.Form):
    """Form for reviewing opportunities (admin only)"""
    
    status = forms.ChoiceField(
        choices=[
            ('draft', 'Draft'),
            ('published', 'Publish'),
            ('archived', 'Archive'),
        ],
        widget=Select(attrs={'class': 'form-control'})
    )
    
    review_notes = forms.CharField(
        required=False,
        widget=Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Review notes...'})
    )
    
    is_verified = forms.BooleanField(
        required=False,
        widget=CheckboxInput(attrs={'class': 'form-check-input'})
    )