from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import User, RegistrationApplication, RoleChangeRequest
import re


# ============================================================
# ROLE-BASED REGISTRATION FORM
# ============================================================

class RoleBasedRegistrationForm(UserCreationForm):
    """Role-based registration form with dynamic fields"""
    
    # Personal Information
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter your email address'
        })
    )
    first_name = forms.CharField(
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter your last name'
        })
    )
    title = forms.ChoiceField(
        required=False,
        choices=[('', 'Select Title')] + [
            ('Dr.', 'Dr.'),
            ('Prof.', 'Prof.'),
            ('Mr.', 'Mr.'),
            ('Ms.', 'Ms.'),
            ('Mrs.', 'Mrs.'),
            ('Mx.', 'Mx.'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '+254 700 000 000'
        })
    )
    
    # Academic Information
    academic_level = forms.ChoiceField(
        required=False,
        choices=[('', 'Select Academic Level')] + [
            ('masters', "Master's Student"),
            ('phd', 'PhD Candidate'),
            ('postdoc', 'Postdoctoral Researcher'),
            ('early_career', 'Early Career Researcher'),
            ('senior_researcher', 'Senior Researcher'),
            ('professor', 'Professor'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    institution = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter your institution/university'
        })
    )
    department = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter your department'
        })
    )
    research_interests = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'List your research interests (separated by commas)',
            'rows': 3
        })
    )
    research_keywords = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., machine learning, public health, climate change'
        }),
        help_text="Enter research keywords separated by commas"
    )
    
    # Role Selection
    role = forms.ChoiceField(
        choices=User.Roles.choices,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        help_text="Select the role that best describes your current status"
    )
    
    # Registration Application
    motivation = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Why do you want to join the Kenya Postgraduate Scholars Network?',
            'rows': 5
        }),
        help_text="Please explain your motivation for joining KPSN and how you plan to contribute"
    )
    experience = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'List your relevant academic and professional experience',
            'rows': 3
        }),
        help_text="Include any research, teaching, or professional experience"
    )
    publications = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'List your publications (if any)',
            'rows': 3
        }),
        help_text="Include journal articles, conference papers, books, etc."
    )
    
    # Documents
    cv = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text="Upload your CV (PDF, DOC, or DOCX)"
    )
    recommendation_letter = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text="Upload a recommendation letter (optional)"
    )
    id_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text="Upload your national ID or passport (for verification)"
    )
    
    # Terms & Conditions
    agree_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': 'You must agree to the terms and conditions'}
    )
    agree_privacy = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': 'You must agree to the privacy policy'}
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'title',
            'phone_number', 'academic_level', 'institution', 'department',
            'research_interests', 'research_keywords',
            'password1', 'password2'
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
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise ValidationError('Username must be at least 3 characters long.')
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError('Username contains invalid characters.')
        if User.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken.')
        return username
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            if not re.match(r'^\+?1?\d{9,15}$', phone):
                raise ValidationError('Invalid phone number format. Use format: +254700000000')
        return phone
    
    def clean_research_keywords(self):
        keywords = self.cleaned_data.get('research_keywords', '')
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            return keyword_list
        return []
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.title = self.cleaned_data.get('title', '')
        user.phone_number = self.cleaned_data.get('phone_number')
        user.academic_level = self.cleaned_data.get('academic_level')
        user.institution = self.cleaned_data.get('institution')
        user.department = self.cleaned_data.get('department')
        user.research_interests = self.cleaned_data.get('research_interests')
        user.research_keywords = self.cleaned_data.get('research_keywords', [])
        
        user.role = 'prospective_member'
        user.registration_status = 'pending'
        user.is_active = False
        
        user.notification_preferences = {
            'email_notifications': True,
            'event_reminders': True,
            'opportunity_alerts': True,
            'community_updates': True,
            'research_matching': True,
            'mentorship_alerts': True,
        }
        
        if commit:
            user.save()
            
            RegistrationApplication.objects.create(
                user=user,
                requested_role=self.cleaned_data['role'],
                motivation=self.cleaned_data['motivation'],
                experience=self.cleaned_data.get('experience', ''),
                publications=self.cleaned_data.get('publications', ''),
                cv=self.cleaned_data.get('cv'),
                recommendation_letter=self.cleaned_data.get('recommendation_letter'),
                additional_documents=self.cleaned_data.get('id_document'),
                status=RegistrationApplication.ApplicationStatus.PENDING
            )
        
        return user


# ============================================================
# ROLE CHANGE REQUEST FORM
# ============================================================

class RoleChangeRequestForm(forms.ModelForm):
    """Form for requesting a role change"""
    
    reason = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Explain why you want to change your role',
            'rows': 5
        })
    )
    supporting_documents = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text="Upload supporting documents (if any)"
    )
    
    class Meta:
        model = RoleChangeRequest
        fields = ['requested_role', 'reason', 'supporting_documents']
        widgets = {
            'requested_role': forms.Select(attrs={'class': 'form-control'})
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            current_role = self.user.role
            available_roles = [role for role in User.Roles.choices if role[0] != current_role]
            self.fields['requested_role'].choices = available_roles


# ============================================================
# ADMIN FORMS
# ============================================================

class AdminApplicationReviewForm(forms.Form):
    """Admin form for reviewing registration applications"""
    
    ACTION_CHOICES = [
        ('approve', 'Approve Application'),
        ('reject', 'Reject Application'),
        ('needs_info', 'Request More Information'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Add notes for the applicant',
            'rows': 4
        })
    )
    role_override = forms.ChoiceField(
        required=False,
        choices=User.Roles.choices,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Override the requested role (optional)"
    )
    membership_duration = forms.IntegerField(
        required=False,
        initial=365,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 30,
            'max': 1095
        }),
        help_text="Membership duration in days (default: 365)"
    )


class AdminUserEditForm(forms.ModelForm):
    """Admin form for editing users"""
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'title',
            'phone_number', 'role', 'registration_status',
            'academic_level', 'institution', 'department',
            'research_interests', 'is_active', 'is_verified',
            'is_active_member', 'membership_number',
            'membership_start_date', 'membership_expiry_date'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'registration_status': forms.Select(attrs={'class': 'form-control'}),
            'academic_level': forms.Select(attrs={'class': 'form-control'}),
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'research_interests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active_member': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'membership_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'membership_start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'membership_expiry_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError('This email is already registered to another user.')
        return email


# ============================================================
# USER LOGIN FORM (FIXED)
# ============================================================

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
                if user.registration_status == 'rejected':
                    raise ValidationError('Your registration application was rejected. Please contact support.')
                if user.registration_status == 'pending':
                    raise ValidationError('Your registration is pending review. You will receive an email once approved.')
                if not user.email_verified:
                    raise ValidationError('Please verify your email before logging in. Check your inbox for the verification link.')
            except User.DoesNotExist:
                pass
        
        return cleaned_data


# ============================================================
# USER UPDATE FORM (FIXED)
# ============================================================

class UserUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'title', 'phone_number', 'bio',
            'institution', 'department', 'academic_level', 'research_interests',
            'profile_picture', 'linkedin_url', 'researchgate_url',
            'google_scholar_url', 'orcid_id', 'twitter_url', 'website_url',
            'newsletter_subscribed'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_level': forms.Select(attrs={'class': 'form-control'}),
            'research_interests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/your-profile'}),
            'researchgate_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://researchgate.net/profile/your-profile'}),
            'google_scholar_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://scholar.google.com/citations?user=your-id'}),
            'orcid_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000-0000-0000-0000'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://twitter.com/your-handle'}),
            'website_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://your-website.com'}),
            'newsletter_subscribed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            if not re.match(r'^\+?1?\d{9,15}$', phone):
                raise ValidationError('Invalid phone number format.')
        return phone
    
    def clean_orcid_id(self):
        orcid = self.cleaned_data.get('orcid_id')
        if orcid:
            cleaned = re.sub(r'[-\s]', '', orcid)
            if not re.match(r'^\d{16}$', cleaned):
                raise ValidationError('Invalid ORCID ID format. Use format: 0000-0000-0000-0000')
        return orcid


# ============================================================
# ORIGINAL REGISTRATION FORM (KEPT FOR COMPATIBILITY)
# ============================================================

class UserRegistrationForm(UserCreationForm):
    """Original registration form (kept for compatibility)"""
    
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
    academic_level = forms.ChoiceField(
        required=False,
        choices=[('', 'Select Academic Level')] + [
            ('masters', "Master's Student"),
            ('phd', 'PhD Candidate'),
            ('postdoc', 'Postdoctoral Researcher'),
            ('early_career', 'Early Career Researcher'),
            ('senior_researcher', 'Senior Researcher'),
            ('professor', 'Professor'),
            ('other', 'Other'),
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
            'institution', 'academic_level', 'research_interests', 'password1', 'password2'
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
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise ValidationError('Username must be at least 3 characters long.')
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError('Username contains invalid characters.')
        return username
    
    def clean_phone_number(self):
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
        user.academic_level = self.cleaned_data.get('academic_level')
        user.research_interests = self.cleaned_data.get('research_interests')
        user.is_active = False
        
        if commit:
            user.save()
            user.notification_preferences = {
                'email_notifications': True,
                'event_reminders': True,
                'opportunity_alerts': True,
                'community_updates': True,
            }
            user.save()
        
        return user


# ============================================================
# PASSWORD RESET FORMS
# ============================================================

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
    
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter.')
        if not re.search(r'\d', password):
            raise ValidationError('Password must contain at least one number.')
        return password
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match.')
        
        return password2


# ============================================================
# MENTORSHIP FORMS
# ============================================================

class MentorshipApplicationForm(forms.Form):
    """Form for applying to be a mentor"""
    
    mentorship_areas = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'List the areas you can mentor others in',
            'rows': 4
        }),
        help_text="List your expertise areas separated by commas"
    )
    mentoring_philosophy = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Describe your mentoring philosophy and approach',
            'rows': 4
        })
    )
    availability = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Describe your availability for mentoring',
            'rows': 3
        })
    )
    max_mentees = forms.IntegerField(
        required=False,
        initial=3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 10
        }),
        help_text="Maximum number of mentees you can handle"
    )
    experience_years = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0
        }),
        help_text="Years of experience in your field"
    )
    
    def clean_mentorship_areas(self):
        areas = self.cleaned_data.get('mentorship_areas')
        if areas:
            area_list = [a.strip() for a in areas.split(',') if a.strip()]
            if len(area_list) < 2:
                raise ValidationError('Please list at least 2 mentorship areas.')
            return area_list
        return []


class MenteeApplicationForm(forms.Form):
    """Form for applying to be a mentee"""
    
    mentee_goals = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'What do you hope to achieve through mentorship?',
            'rows': 4
        })
    )
    preferred_mentorship_areas = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'List the areas you need mentorship in',
            'rows': 3
        }),
        help_text="List specific areas where you need guidance"
    )
    commitment_level = forms.ChoiceField(
        required=True,
        choices=[
            ('low', 'Low (1-2 hours/month)'),
            ('medium', 'Medium (3-5 hours/month)'),
            ('high', 'High (6+ hours/month)'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    preferred_mentor_role = forms.ChoiceField(
        required=False,
        choices=[('', 'Any')] + list(User.Roles.choices),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Preferred mentor role (optional)"
    )
    
    def clean_preferred_mentorship_areas(self):
        areas = self.cleaned_data.get('preferred_mentorship_areas')
        if areas:
            area_list = [a.strip() for a in areas.split(',') if a.strip()]
            if len(area_list) < 1:
                raise ValidationError('Please list at least 1 mentorship area.')
            return area_list
        return []


# ============================================================
# COLLABORATION FORMS
# ============================================================

class CollaborationRequestForm(forms.Form):
    """Form for requesting collaboration"""
    
    collaborator_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter collaborator\'s email'
        })
    )
    project_title = forms.CharField(
        required=True,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Project title'
        })
    )
    project_description = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Describe your project and why you want to collaborate',
            'rows': 5
        })
    )
    expected_outcomes = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'What do you expect from this collaboration?',
            'rows': 3
        })
    )
    timeline = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Estimated project timeline'
        })
    )
    
    def clean_collaborator_email(self):
        email = self.cleaned_data.get('collaborator_email')
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError('No user found with this email address.')
        return email