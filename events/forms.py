# events/forms.py

from django import forms
from django.forms import ModelForm, TextInput, Textarea, Select, FileInput, CheckboxInput, NumberInput, DateTimeInput, EmailInput, URLInput
from django.core.exceptions import ValidationError
import json
from .models import Event, EventRegistration


class EventForm(forms.ModelForm):
    """Form for creating/editing events"""
    
    # Override the tags field to accept comma-separated values
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'AI, Research, Webinar, Innovation'
        }),
        help_text='Enter tags separated by commas (e.g., AI, Research, Webinar)'
    )
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type', 'status',
            'organizer_name', 'organizer_email', 'organizer_phone', 'organizer_website',
            'is_virtual', 'venue', 'address', 'city', 'country', 'virtual_link',
            'start_date', 'end_date', 'registration_deadline',
            'max_attendees', 'requires_registration', 'registration_fee',
            'currency', 'registration_link', 'agenda', 'speakers', 'program',
            'banner_image', 'poster', 'zoom_meeting_id', 'zoom_password',
            'zoom_meeting_link',  # tags is handled separately
        ]
        widgets = {
            'title': TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter event title'}),
            'description': Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Detailed description of the event...'}),
            'event_type': Select(attrs={'class': 'form-control'}),
            'status': Select(attrs={'class': 'form-control'}),
            'organizer_name': TextInput(attrs={'class': 'form-control', 'placeholder': 'Organizer name'}),
            'organizer_email': EmailInput(attrs={'class': 'form-control', 'placeholder': 'organizer@example.com'}),
            'organizer_phone': TextInput(attrs={'class': 'form-control', 'placeholder': '+254 700 000000'}),
            'organizer_website': URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'is_virtual': CheckboxInput(attrs={'class': 'form-check-input'}),
            'venue': TextInput(attrs={'class': 'form-control', 'placeholder': 'Venue name'}),
            'address': Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full address'}),
            'city': TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'country': TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'virtual_link': URLInput(attrs={'class': 'form-control', 'placeholder': 'https://zoom.us/meeting'}),
            'start_date': DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'registration_deadline': DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'max_attendees': NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Maximum attendees'}),
            'requires_registration': CheckboxInput(attrs={'class': 'form-check-input'}),
            'registration_fee': NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'currency': TextInput(attrs={'class': 'form-control', 'placeholder': 'KES, USD, EUR'}),
            'registration_link': URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/register'}),
            'agenda': Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Event agenda...'}),
            'speakers': Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Speakers information...'}),
            'program': Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Program details...'}),
            'banner_image': FileInput(attrs={'class': 'form-control'}),
            'poster': FileInput(attrs={'class': 'form-control'}),
            'zoom_meeting_id': TextInput(attrs={'class': 'form-control', 'placeholder': 'Zoom meeting ID'}),
            'zoom_password': TextInput(attrs={'class': 'form-control', 'placeholder': 'Zoom meeting password'}),
            'zoom_meeting_link': URLInput(attrs={'class': 'form-control', 'placeholder': 'https://zoom.us/j/meeting'}),
        }
        labels = {
            'is_virtual': 'Virtual Event',
            'requires_registration': 'Require Registration',
            'registration_fee': 'Registration Fee',
        }
        help_texts = {
            'max_attendees': 'Leave blank for unlimited capacity',
            'registration_deadline': 'Leave blank if no deadline',
            'registration_fee': 'Set to 0 for free events',
        }
    
    def clean_tags(self):
        """Convert comma-separated tags to JSON array"""
        tags_data = self.cleaned_data.get('tags', '')
        
        # If empty, return empty list
        if not tags_data:
            return []
        
        # If it's already a list (from JSON), return it
        if isinstance(tags_data, list):
            return tags_data
        
        # If it's a string, split by comma
        if isinstance(tags_data, str):
            # Clean up the string
            tags_data = tags_data.strip()
            
            # Try to parse as JSON first (for admin users who might enter JSON)
            if tags_data.startswith('[') and tags_data.endswith(']'):
                try:
                    parsed = json.loads(tags_data)
                    if isinstance(parsed, list):
                        return [str(tag).strip() for tag in parsed if tag]
                except json.JSONDecodeError:
                    pass
            
            # Split by comma and clean up
            tags = [tag.strip() for tag in tags_data.split(',') if tag.strip()]
            return tags
        
        # Fallback: return empty list
        return []
    
    def clean(self):
        """Validate the form"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Validate dates
        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError('End date must be after start date.')
        
        # Validate registration deadline
        registration_deadline = cleaned_data.get('registration_deadline')
        if registration_deadline and start_date:
            if registration_deadline >= start_date:
                raise ValidationError('Registration deadline must be before the event start date.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save the form, handling tags conversion"""
        instance = super().save(commit=False)
        
        # Set tags from cleaned_data
        if hasattr(self, 'cleaned_data') and 'tags' in self.cleaned_data:
            instance.tags = self.cleaned_data['tags']
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class EventRegistrationForm(forms.ModelForm):
    """Form for registering for events"""
    
    class Meta:
        model = EventRegistration
        fields = []
        # No additional fields needed as user and event are set automatically


class EventFeedbackForm(forms.Form):
    """Form for submitting event feedback"""
    
    rating = forms.ChoiceField(
        choices=[(i, f'{i} Stars') for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Rate this event'
    )
    
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Write your feedback here...'}),
        label='Your Comments'
    )


class EventFilterForm(forms.Form):
    """Form for filtering events"""
    
    event_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Event.EVENT_TYPES),
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )
    
    is_virtual = forms.ChoiceField(
        choices=[
            ('', 'All Events'),
            ('true', 'Virtual'),
            ('false', 'In-Person'),
        ],
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )
    
    time_filter = forms.ChoiceField(
        choices=[
            ('', 'All Events'),
            ('upcoming', 'Upcoming'),
            ('ongoing', 'Ongoing'),
            ('past', 'Past'),
        ],
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Search events...'})
    )


class EventSearchForm(forms.Form):
    """Form for searching events (AJAX)"""
    
    q = forms.CharField(
        max_length=255,
        required=False,
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Search events...'})
    )
    
    event_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Event.EVENT_TYPES),
        required=False,
        widget=Select(attrs={'class': 'form-control'})
    )


class CertificateGenerationForm(forms.Form):
    """Form for generating certificates"""
    
    event = forms.ModelChoiceField(
        queryset=Event.objects.filter(status='completed'),
        widget=Select(attrs={'class': 'form-control'})
    )
    
    attendees = forms.CharField(
        widget=Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Enter attendee emails (one per line)'}),
        help_text='Enter attendee email addresses, one per line'
    )
    
    certificate_type = forms.ChoiceField(
        choices=[
            ('attendance', 'Attendance Certificate'),
            ('participation', 'Participation Certificate'),
            ('presentation', 'Presentation Certificate'),
        ],
        widget=Select(attrs={'class': 'form-control'})
    )