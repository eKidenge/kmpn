from django import forms
from django.forms import ModelForm, TextInput, Textarea, Select, FileInput, CheckboxInput, NumberInput, EmailInput
from django.contrib.auth import get_user_model
from .models import Member, MemberVerificationRequest, MemberActivity

User = get_user_model()


class MemberRegistrationForm(forms.Form):
    """Form for member registration"""
    
    # User fields
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True)
    
    # User profile fields
    bio = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False)
    institution = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    department = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    degree_level = forms.ChoiceField(
        choices=[('', 'Select Degree Level')] + [
            ('bachelors', 'Bachelor\'s'),
            ('masters', 'Master\'s'),
            ('phd', 'PhD'),
            ('postdoc', 'Postdoctoral'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    research_interests = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    phone_number = forms.CharField(max_length=17, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    # Member fields
    membership_type = forms.ChoiceField(
        choices=[('', 'Select Membership Type')] + list(Member.MEMBERSHIP_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data


class MemberVerificationForm(forms.ModelForm):
    """Form for member verification"""
    
    # Additional fields for Member model
    student_id_number = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    registration_number = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    year_of_study = forms.IntegerField(min_value=1, max_value=10, required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    expected_graduation_year = forms.IntegerField(min_value=2024, max_value=2030, required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    thesis_title = forms.CharField(max_length=500, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    thesis_abstract = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False)
    supervisor_name = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    supervisor_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = MemberVerificationRequest
        fields = ['request_notes']
        widgets = {
            'request_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Any additional notes about your verification request...'}),
        }


class MemberProfileForm(forms.ModelForm):
    """Form for member profile"""
    
    # User fields
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    bio = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), required=False)
    institution = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    department = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    degree_level = forms.ChoiceField(
        choices=[('', 'Select Degree Level')] + [
            ('bachelors', 'Bachelor\'s'),
            ('masters', 'Master\'s'),
            ('phd', 'PhD'),
            ('postdoc', 'Postdoctoral'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    research_interests = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    profile_picture = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Member
        fields = [
            'membership_type', 'skills', 'expertise_areas',
            'programming_languages', 'research_methodologies',
            'collaboration_interests', 'mentoring_interests',
            'student_id_number', 'registration_number',
            'year_of_study', 'expected_graduation_year',
            'thesis_title', 'thesis_abstract',
            'supervisor_name', 'supervisor_email'
        ]
        widgets = {
            'membership_type': forms.Select(attrs={'class': 'form-control'}),
            'skills': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, R, SPSS, Machine Learning'}),
            'expertise_areas': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. NLP, Computer Vision, Statistics'}),
            'programming_languages': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, R, Java, C++'}),
            'research_methodologies': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Quantitative, Qualitative, Mixed Methods'}),
            'collaboration_interests': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Research, Funding, Mentorship'}),
            'mentoring_interests': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Undergraduate, Graduate, Postdoctoral'}),
            'student_id_number': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'year_of_study': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'expected_graduation_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2024, 'max': 2030}),
            'thesis_title': forms.TextInput(attrs={'class': 'form-control'}),
            'thesis_abstract': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'supervisor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'supervisor_email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class MemberSearchForm(forms.Form):
    """Form for searching members"""
    
    search = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search members...'}))
    institution = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Filter by institution'}))
    degree_level = forms.ChoiceField(
        choices=[('', 'All Degrees')] + [
            ('bachelors', 'Bachelor\'s'),
            ('masters', 'Master\'s'),
            ('phd', 'PhD'),
            ('postdoc', 'Postdoctoral'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    research_area = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Research area'}))
    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', 'Recent'),
            ('user__first_name', 'Name A-Z'),
            ('-publication_count', 'Most Publications'),
            ('-citation_count', 'Most Cited'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class MemberSettingsForm(forms.ModelForm):
    """Form for member settings"""
    
    class Meta:
        model = Member
        fields = ['membership_type', 'card_expires_at']
        widgets = {
            'membership_type': forms.Select(attrs={'class': 'form-control'}),
            'card_expires_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class MemberActivityFilterForm(forms.Form):
    """Form for filtering member activities"""
    
    activity_type = forms.ChoiceField(
        choices=[('', 'All Activities')] + list(MemberActivity.ACTIVITY_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )