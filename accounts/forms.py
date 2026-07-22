from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import User
import re


class UserRegistrationForm(UserCreationForm):
    """Custom registration form"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )
    first_name = forms.CharField(
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your first name'})
    )
    last_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your last name'})
    )
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number (optional)'})
    )
    institution = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your institution'})
    )
    degree_level = forms.ChoiceField(
        required=False,
        choices=[('', 'Select Degree Level')] + [
            ('bachelors', 'Bachelor\'s'),
            ('masters', 'Master\'s'),
            ('phd', 'PhD'),
            ('postdoc', 'Postdoctoral'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    research_interests = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your research interests',
            'rows': 3
        })
    )
    agree_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': 'You must agree to the terms and conditions'}
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone_number',
            'institution', 'degree_level', 'research_interests', 'password1', 'password2'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    
    def clean_email(self):
        """Validate email is unique"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email
    
    def clean_username(self):
        """Validate username"""
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise ValidationError('Username must be at least 3 characters long.')
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError('Username contains invalid characters.')
        return username
    
    def clean_phone_number(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone_number')
        if phone:
            if not re.match(r'^\+?1?\d{9,15}$', phone):
                raise ValidationError('Invalid phone number format.')
        return phone
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number')
        user.institution = self.cleaned_data.get('institution')
        user.degree_level = self.cleaned_data.get('degree_level')
        user.research_interests = self.cleaned_data.get('research_interests')
        user.is_active = False  # Will be activated after email verification
        
        if commit:
            user.save()
            # Create default notification preferences
            user.notification_preferences = {
                'email_notifications': True,
                'event_reminders': True,
                'opportunity_alerts': True,
                'community_updates': True,
            }
            user.save()
        
        return user


class UserLoginForm(AuthenticationForm):
    """Custom login form"""
    
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            try:
                user = User.objects.get(email=username)
                if user.is_locked():
                    raise ValidationError('Your account is temporarily locked due to multiple failed login attempts. Please try again later.')
            except User.DoesNotExist:
                pass
        
        return cleaned_data


class UserUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 'bio',
            'institution', 'department', 'degree_level', 'research_interests',
            'profile_picture', 'linkedin_url', 'researchgate_url',
            'google_scholar_url', 'orcid_id', 'newsletter_subscribed'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'degree_level': forms.Select(attrs={'class': 'form-control'}),
            'research_interests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/your-profile'}),
            'researchgate_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://researchgate.net/profile/your-profile'}),
            'google_scholar_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://scholar.google.com/citations?user=your-id'}),
            'orcid_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000-0000-0000-0000'}),
            'newsletter_subscribed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PasswordResetRequestForm(forms.Form):
    """Password reset request form"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email address'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise ValidationError('No user found with this email address.')
        return email


class PasswordResetConfirmForm(forms.Form):
    """Password reset confirmation form"""
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match.')
        
        if len(password1) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        
        return password2
