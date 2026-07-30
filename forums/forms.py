# forums/forms.py

from django import forms
from .models import ForumCategory, ForumThread, ForumReply, ForumReport


class ForumThreadForm(forms.ModelForm):
    """Form for creating/editing forum threads"""
    
    # Handle tags as comma-separated input
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-government',
            'placeholder': 'AI, Research, Webinar, Innovation'
        }),
        help_text='Enter tags separated by commas (e.g., AI, Research, Webinar)'
    )
    
    class Meta:
        model = ForumThread
        fields = ['title', 'content', 'category']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-government',
                'placeholder': 'Enter thread title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control form-control-government',
                'rows': 10,
                'placeholder': 'Write your thread content here...'
            }),
            'category': forms.Select(attrs={'class': 'form-control form-control-government'}),
        }
    
    def clean_tags(self):
        """Convert comma-separated tags to list"""
        tags_data = self.cleaned_data.get('tags', '')
        if not tags_data:
            return []
        if isinstance(tags_data, str):
            return [tag.strip() for tag in tags_data.split(',') if tag.strip()]
        return tags_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if 'tags' in self.cleaned_data:
            instance.tags = self.cleaned_data['tags']
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ForumReplyForm(forms.ModelForm):
    class Meta:
        model = ForumReply
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control form-control-government',
                'rows': 5,
                'placeholder': 'Write your reply here...'
            }),
        }


class ForumReportForm(forms.ModelForm):
    class Meta:
        model = ForumReport
        fields = ['report_type', 'description']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-control form-control-government'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control form-control-government',
                'rows': 4,
                'placeholder': 'Please describe the issue in detail...'
            }),
        }


class ForumSearchForm(forms.Form):
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
            ('', 'Latest Activity'),
            ('-created_at', 'Newest'),
            ('-reply_count', 'Most Replies'),
            ('-view_count', 'Most Views'),
            ('-like_count', 'Most Liked'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )