from django import forms
from django.forms import ModelForm, TextInput, Textarea, Select, FileInput, CheckboxInput, NumberInput, DateInput, URLInput, EmailInput
from .models import Resource, ResourceCategory, ResourceRating


class ResourceForm(forms.ModelForm):
    """Form for creating/editing resources"""
    
    class Meta:
        model = Resource
        fields = [
            'title', 'description', 'resource_type', 'access_type',
            'categories', 'file', 'cover_image', 'external_url',
            'content', 'author', 'author_email', 'publisher',
            'publication_date', 'version', 'keywords',
            'is_published', 'is_featured'
        ]
        widgets = {
            'title': TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter resource title'}),
            'description': Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Brief description of the resource...'}),
            'resource_type': Select(attrs={'class': 'form-control'}),
            'access_type': Select(attrs={'class': 'form-control'}),
            'categories': Select(attrs={'class': 'form-control', 'multiple': True}),
            'file': FileInput(attrs={'class': 'form-control'}),
            'cover_image': FileInput(attrs={'class': 'form-control'}),
            'external_url': URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/resource'}),
            'content': Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Full content of the resource...'}),
            'author': TextInput(attrs={'class': 'form-control', 'placeholder': 'Author name'}),
            'author_email': EmailInput(attrs={'class': 'form-control', 'placeholder': 'author@example.com'}),
            'publisher': TextInput(attrs={'class': 'form-control', 'placeholder': 'Publisher name'}),
            'publication_date': DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'version': TextInput(attrs={'class': 'form-control', 'placeholder': '1.0'}),
            'keywords': TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, Django, Machine Learning'}),
            'is_published': CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ResourceRatingForm(forms.ModelForm):
    """Form for rating resources"""
    
    class Meta:
        model = ResourceRating
        fields = ['rating', 'review']
        widgets = {
            'rating': Select(attrs={'class': 'form-control'}),
            'review': Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write your review here...'}),
        }


class ResourceCategoryForm(forms.ModelForm):
    """Form for creating/editing resource categories"""
    
    class Meta:
        model = ResourceCategory
        fields = ['name', 'description', 'icon', 'order', 'parent', 'is_active']
        widgets = {
            'name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Category name'}),
            'description': Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Category description...'}),
            'icon': TextInput(attrs={'class': 'form-control', 'placeholder': 'Font awesome icon class'}),
            'order': NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'parent': Select(attrs={'class': 'form-control'}),
            'is_active': CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ResourceFilterForm(forms.Form):
    """Form for filtering resources"""
    
    resource_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Resource.RESOURCE_TYPES),
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )
    
    access_type = forms.ChoiceField(
        choices=[('', 'All Access')] + list(Resource.ACCESS_TYPES),
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )
    
    category = forms.ModelChoiceField(
        queryset=ResourceCategory.objects.filter(is_active=True),
        required=False,
        empty_label='All Categories',
        widget=Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Search resources...'})
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', 'Newest'),
            ('-download_count', 'Most Downloaded'),
            ('-view_count', 'Most Viewed'),
            ('-average_rating', 'Highest Rated'),
        ],
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )


class ResourceSearchForm(forms.Form):
    """Form for searching resources (AJAX)"""
    
    q = forms.CharField(
        max_length=255,
        required=False,
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Search resources...'})
    )
    
    resource_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Resource.RESOURCE_TYPES),
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )