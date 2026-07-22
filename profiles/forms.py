from django import forms
from django.forms import ModelForm, TextInput, Textarea, Select, FileInput, CheckboxInput, NumberInput, DateInput, EmailInput
from .models import Profile, ResearchInterest, Publication, PublicationAuthor
from members.models import Member


class ProfileForm(forms.ModelForm):
    """Form for editing profile"""
    
    # User fields
    first_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
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
    
    # Member fields - FIXED: Convert tuple to list
    membership_type = forms.ChoiceField(
        choices=[('', 'Select Membership Type')] + list(Member.MEMBERSHIP_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    skills = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, R, SPSS, Machine Learning'}),
        required=False
    )
    expertise_areas = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. NLP, Computer Vision, Statistics'}),
        required=False
    )
    programming_languages = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, R, Java, C++'}),
        required=False
    )
    research_methodologies = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Quantitative, Qualitative, Mixed Methods'}),
        required=False
    )
    collaboration_interests = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Research, Funding, Mentorship'}),
        required=False
    )
    mentoring_interests = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Undergraduate, Graduate, Postdoctoral'}),
        required=False
    )
    
    # Member academic fields
    student_id_number = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    registration_number = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    year_of_study = forms.IntegerField(min_value=1, max_value=10, required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    expected_graduation_year = forms.IntegerField(min_value=2024, max_value=2030, required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    thesis_title = forms.CharField(max_length=500, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    thesis_abstract = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False)
    supervisor_name = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    supervisor_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Profile
        fields = [
            'academic_bio', 'research_statement', 'teaching_interests',
            'current_position', 'current_employer', 'years_of_experience',
            'primary_research_area', 'profile_visibility',
            'show_email', 'show_phone'
        ]
        widgets = {
            'academic_bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'research_statement': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'teaching_interests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'current_position': forms.TextInput(attrs={'class': 'form-control'}),
            'current_employer': forms.TextInput(attrs={'class': 'form-control'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'primary_research_area': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_visibility': forms.Select(attrs={'class': 'form-control'}),
            'show_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_phone': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ResearchInterestForm(forms.ModelForm):
    """Form for research interests"""
    
    class Meta:
        model = ResearchInterest
        fields = ['name', 'description', 'category', 'sub_category', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'sub_category': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
        }


class PublicationForm(forms.ModelForm):
    """Form for publications"""
    
    class Meta:
        model = Publication
        fields = [
            'title', 'abstract', 'publication_type', 'status',
            'journal_name', 'journal_volume', 'journal_issue',
            'pages', 'doi', 'isbn', 'issn',
            'publication_date', 'acceptance_date', 'submission_date',
            'url', 'pdf_file', 'keywords'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'abstract': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'publication_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'journal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'journal_volume': forms.TextInput(attrs={'class': 'form-control'}),
            'journal_issue': forms.TextInput(attrs={'class': 'form-control'}),
            'pages': forms.TextInput(attrs={'class': 'form-control'}),
            'doi': forms.TextInput(attrs={'class': 'form-control'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'issn': forms.TextInput(attrs={'class': 'form-control'}),
            'publication_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'acceptance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'submission_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'url': forms.TextInput(attrs={'class': 'form-control'}),
            'pdf_file': forms.FileInput(attrs={'class': 'form-control'}),
            'keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. machine learning, AI, education'}),
        }


class PublicationAuthorForm(forms.ModelForm):
    """Form for publication authors"""
    
    class Meta:
        model = PublicationAuthor
        fields = ['author', 'order', 'corresponding_author', 'affiliation']
        widgets = {
            'author': forms.Select(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'corresponding_author': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'affiliation': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ProfileVisibilityForm(forms.ModelForm):
    """Form for profile visibility settings"""
    
    class Meta:
        model = Profile
        fields = ['profile_visibility', 'show_email', 'show_phone']
        widgets = {
            'profile_visibility': forms.Select(attrs={'class': 'form-control'}),
            'show_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_phone': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }