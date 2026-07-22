from django import forms
from django.forms import ModelForm, TextInput, Textarea, Select, FileInput, CheckboxInput
from .models import Community, CommunityPost, Comment, CommunityMember


class CommunityForm(ModelForm):
    """Form for creating/editing communities"""
    
    class Meta:
        model = Community
        fields = [
            'name', 'description', 'community_type', 'access_type',
            'logo', 'banner', 'tags', 'categories',
            'allow_member_posts', 'require_moderation',
            'allow_attachments', 'allow_discussions'
        ]
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'description': Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'community_type': Select(attrs={'class': 'form-control'}),
            'access_type': Select(attrs={'class': 'form-control'}),
            'logo': FileInput(attrs={'class': 'form-control'}),
            'banner': FileInput(attrs={'class': 'form-control'}),
            'tags': TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. research, AI, machine-learning'}),
            'categories': TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. technology, science, humanities'}),
            'allow_member_posts': CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_moderation': CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_attachments': CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_discussions': CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CommunitySettingsForm(ModelForm):
    """Form for community settings"""
    
    class Meta:
        model = Community
        fields = [
            'name', 'description', 'community_type', 'access_type',
            'logo', 'banner', 'tags', 'categories',
            'allow_member_posts', 'require_moderation',
            'allow_attachments', 'allow_discussions'
        ]
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'description': Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'community_type': Select(attrs={'class': 'form-control'}),
            'access_type': Select(attrs={'class': 'form-control'}),
            'logo': FileInput(attrs={'class': 'form-control'}),
            'banner': FileInput(attrs={'class': 'form-control'}),
            'tags': TextInput(attrs={'class': 'form-control'}),
            'categories': TextInput(attrs={'class': 'form-control'}),
            'allow_member_posts': CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_moderation': CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_attachments': CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_discussions': CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CommunityPostForm(ModelForm):
    """Form for creating/editing posts"""
    
    class Meta:
        model = CommunityPost
        fields = ['title', 'content', 'post_type', 'cover_image']
        widgets = {
            'title': TextInput(attrs={'class': 'form-control'}),
            'content': Textarea(attrs={'class': 'form-control', 'rows': 15}),
            'post_type': Select(attrs={'class': 'form-control'}),
            'cover_image': FileInput(attrs={'class': 'form-control'}),
        }


class CommentForm(ModelForm):
    """Form for creating/editing comments"""
    
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write your comment...'})
        }


class CommunityMemberRoleForm(ModelForm):
    """Form for changing member roles"""
    
    class Meta:
        model = CommunityMember
        fields = ['role']
        widgets = {
            'role': Select(attrs={'class': 'form-control'})
        }
