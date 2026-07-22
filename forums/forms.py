from django import forms
from django.forms import ModelForm, TextInput, Textarea, Select, FileInput, CheckboxInput
from .models import ForumCategory, ForumThread, ForumReply, ForumReport


class ForumThreadForm(forms.ModelForm):
    """Form for creating/editing forum threads"""
    
    class Meta:
        model = ForumThread
        fields = ['title', 'content', 'category', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter thread title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Write your thread content here...'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. research, AI, machine-learning'}),
        }


class ForumReplyForm(forms.ModelForm):
    """Form for creating/editing forum replies"""
    
    class Meta:
        model = ForumReply
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Write your reply here...'}),
        }


class ForumReportForm(forms.ModelForm):
    """Form for reporting inappropriate content"""
    
    class Meta:
        model = ForumReport
        fields = ['report_type', 'description']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Please describe the issue in detail...'}),
        }


class ForumCategoryForm(forms.ModelForm):
    """Form for creating/editing forum categories (admin only)"""
    
    class Meta:
        model = ForumCategory
        fields = ['name', 'description', 'order', 'requires_moderation']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'requires_moderation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ForumSearchForm(forms.Form):
    """Form for searching forums"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search forums...'})
    )
    category = forms.ModelChoiceField(
        queryset=ForumCategory.objects.filter(is_active=True),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    sort_by = forms.ChoiceField(
        choices=[
            ('-last_activity', 'Latest Activity'),
            ('-created_at', 'Newest'),
            ('-reply_count', 'Most Replies'),
            ('-view_count', 'Most Views'),
            ('-like_count', 'Most Liked'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )