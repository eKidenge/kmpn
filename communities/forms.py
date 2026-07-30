# communities/forms.py - COMPLETE FIXED VERSION

from django import forms
from django.forms import ModelForm, TextInput, Textarea, Select, FileInput, CheckboxInput
from .models import Community, CommunityPost, Comment, CommunityMember


class CommunityForm(ModelForm):
    """Form for creating/editing communities"""
    
    # Override tags and categories to handle comma-separated input
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-government',
            'placeholder': 'Research, AI, Data Science, Machine Learning'
        }),
        help_text='Enter tags separated by commas (e.g., Research, AI, Data Science)'
    )
    
    categories = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-government',
            'placeholder': 'Academic, Professional, Research'
        }),
        help_text='Enter categories separated by commas'
    )
    
    class Meta:
        model = Community
        fields = [
            'name', 'description', 'community_type', 'access_type',
            'logo', 'banner',
            'allow_member_posts', 'require_moderation',
            'allow_attachments', 'allow_discussions'
        ]
        widgets = {
            'name': TextInput(attrs={
                'class': 'form-control form-control-government',
                'placeholder': 'Enter community name'
            }),
            'description': Textarea(attrs={
                'class': 'form-control form-control-government',
                'rows': 10,
                'placeholder': 'Describe the purpose of this community...'
            }),
            'community_type': Select(attrs={'class': 'form-control form-control-government'}),
            'access_type': Select(attrs={'class': 'form-control form-control-government'}),
            'logo': FileInput(attrs={'class': 'form-control form-control-government'}),
            'banner': FileInput(attrs={'class': 'form-control form-control-government'}),
            'allow_member_posts': CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_moderation': CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_attachments': CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_discussions': CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Community Name',
            'description': 'Description',
            'community_type': 'Community Type',
            'access_type': 'Access Type',
            'logo': 'Logo',
            'banner': 'Banner Image',
            'allow_member_posts': 'Allow members to create posts',
            'require_moderation': 'Require post moderation',
            'allow_attachments': 'Allow attachments',
            'allow_discussions': 'Allow discussions',
        }
        help_texts = {
            'logo': 'Recommended: Square image, 512x512px',
            'banner': 'Recommended: 1200x400px',
        }
    
    def clean_tags(self):
        """Convert comma-separated tags to list"""
        tags_data = self.cleaned_data.get('tags', '')
        if not tags_data:
            return []
        if isinstance(tags_data, str):
            return [tag.strip() for tag in tags_data.split(',') if tag.strip()]
        return tags_data
    
    def clean_categories(self):
        """Convert comma-separated categories to list"""
        categories_data = self.cleaned_data.get('categories', '')
        if not categories_data:
            return []
        if isinstance(categories_data, str):
            return [cat.strip() for cat in categories_data.split(',') if cat.strip()]
        return categories_data
    
    def save(self, commit=True):
        """Save the form with tags and categories"""
        instance = super().save(commit=False)
        
        # Set tags from cleaned_data
        if 'tags' in self.cleaned_data:
            instance.tags = self.cleaned_data['tags']
        
        # Set categories from cleaned_data
        if 'categories' in self.cleaned_data:
            instance.categories = self.cleaned_data['categories']
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class CommunitySettingsForm(ModelForm):
    """Form for community settings"""
    
    # Override tags and categories to handle comma-separated input
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-government',
            'placeholder': 'Research, AI, Data Science, Machine Learning'
        }),
        help_text='Enter tags separated by commas (e.g., Research, AI, Data Science)'
    )
    
    categories = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-government',
            'placeholder': 'Academic, Professional, Research'
        }),
        help_text='Enter categories separated by commas'
    )
    
    class Meta:
        model = Community
        fields = [
            'name', 'description', 'community_type', 'access_type',
            'logo', 'banner',
            'allow_member_posts', 'require_moderation',
            'allow_attachments', 'allow_discussions'
        ]
        widgets = {
            'name': TextInput(attrs={
                'class': 'form-control form-control-government',
                'placeholder': 'Enter community name'
            }),
            'description': Textarea(attrs={
                'class': 'form-control form-control-government',
                'rows': 10,
                'placeholder': 'Describe the purpose of this community...'
            }),
            'community_type': Select(attrs={'class': 'form-control form-control-government'}),
            'access_type': Select(attrs={'class': 'form-control form-control-government'}),
            'logo': FileInput(attrs={'class': 'form-control form-control-government'}),
            'banner': FileInput(attrs={'class': 'form-control form-control-government'}),
            'allow_member_posts': CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_moderation': CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_attachments': CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_discussions': CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Community Name',
            'description': 'Description',
            'community_type': 'Community Type',
            'access_type': 'Access Type',
            'logo': 'Logo',
            'banner': 'Banner Image',
            'allow_member_posts': 'Allow members to create posts',
            'require_moderation': 'Require post moderation',
            'allow_attachments': 'Allow attachments',
            'allow_discussions': 'Allow discussions',
        }
        help_texts = {
            'logo': 'Recommended: Square image, 512x512px',
            'banner': 'Recommended: 1200x400px',
        }
    
    def clean_tags(self):
        """Convert comma-separated tags to list"""
        tags_data = self.cleaned_data.get('tags', '')
        if not tags_data:
            return []
        if isinstance(tags_data, str):
            return [tag.strip() for tag in tags_data.split(',') if tag.strip()]
        return tags_data
    
    def clean_categories(self):
        """Convert comma-separated categories to list"""
        categories_data = self.cleaned_data.get('categories', '')
        if not categories_data:
            return []
        if isinstance(categories_data, str):
            return [cat.strip() for cat in categories_data.split(',') if cat.strip()]
        return categories_data
    
    def save(self, commit=True):
        """Save the form with tags and categories"""
        instance = super().save(commit=False)
        
        # Set tags from cleaned_data
        if 'tags' in self.cleaned_data:
            instance.tags = self.cleaned_data['tags']
        
        # Set categories from cleaned_data
        if 'categories' in self.cleaned_data:
            instance.categories = self.cleaned_data['categories']
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class CommunityPostForm(ModelForm):
    """Form for creating/editing posts"""
    
    class Meta:
        model = CommunityPost
        fields = ['title', 'content', 'post_type', 'cover_image']
        widgets = {
            'title': TextInput(attrs={
                'class': 'form-control form-control-government',
                'placeholder': 'Enter post title'
            }),
            'content': Textarea(attrs={
                'class': 'form-control form-control-government',
                'rows': 15,
                'placeholder': 'Write your post content here...'
            }),
            'post_type': Select(attrs={'class': 'form-control form-control-government'}),
            'cover_image': FileInput(attrs={'class': 'form-control form-control-government'}),
        }
        labels = {
            'title': 'Post Title',
            'content': 'Content',
            'post_type': 'Post Type',
            'cover_image': 'Cover Image',
        }


class CommentForm(ModelForm):
    """Form for creating/editing comments"""
    
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': Textarea(attrs={
                'class': 'form-control form-control-government',
                'rows': 3,
                'placeholder': 'Write your comment...'
            })
        }
        labels = {
            'content': 'Comment',
        }


class CommunityMemberRoleForm(ModelForm):
    """Form for changing member roles"""
    
    class Meta:
        model = CommunityMember
        fields = ['role']
        widgets = {
            'role': Select(attrs={'class': 'form-control form-control-government'})
        }
        labels = {
            'role': 'Member Role',
        }


class CommunitySearchForm(forms.Form):
    """Form for searching communities"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-government',
            'placeholder': 'Search communities...'
        })
    )
    
    community_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Community.COMMUNITY_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-government'})
    )
    
    access_type = forms.ChoiceField(
        choices=[('', 'All Access')] + list(Community.ACCESS_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-government'})
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('-member_count', 'Most Members'),
            ('-created_at', 'Newest'),
            ('name', 'Name A-Z'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-government'})
    )