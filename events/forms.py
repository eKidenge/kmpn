from django import forms
from django.forms import ModelForm, TextInput, Textarea, Select, FileInput, CheckboxInput, NumberInput, DateInput, DateTimeInput, EmailInput, URLInput
from .models import Event, EventRegistration


class EventForm(forms.ModelForm):
    """Form for creating/editing events"""
    
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
            'zoom_meeting_link', 'tags'
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
            'tags': TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. conference, workshop, AI'}),
        }


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