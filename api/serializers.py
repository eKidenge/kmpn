from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import User, UserActivityLog
from members.models import Member, MemberActivity
from profiles.models import Profile, Publication, ResearchInterest
from communities.models import Community, CommunityMember, CommunityPost, Comment
from opportunities.models import Opportunity, OpportunityApplication
from events.models import Event, EventRegistration
from resources.models import Resource, ResourceRating, ResourceCategory
from notifications.models import Notification
from collaborations.models import CollaborationRequest, CollaborationApplication

User = get_user_model()


# ============================================================
# AUTHENTICATION SERIALIZERS
# ============================================================

class RegisterSerializer(serializers.Serializer):
    """User registration serializer"""
    
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    institution = serializers.CharField(required=False, allow_blank=True)
    department = serializers.CharField(required=False, allow_blank=True)
    degree_level = serializers.CharField(required=False, allow_blank=True)
    research_interests = serializers.CharField(required=False, allow_blank=True)
    membership_type = serializers.ChoiceField(
        choices=['student', 'researcher', 'professional', 'alumni'],
        required=False,
        default='student'
    )
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "A user with this username already exists."})
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        membership_type = validated_data.pop('membership_type', 'student')
        
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            institution=validated_data.get('institution', ''),
            department=validated_data.get('department', ''),
            degree_level=validated_data.get('degree_level', ''),
            research_interests=validated_data.get('research_interests', '')
        )
        
        # Create member profile
        Member.objects.create(
            user=user,
            membership_type=membership_type
        )
        
        # Create user profile
        Profile.objects.create(user=user)
        
        return user


class LoginSerializer(serializers.Serializer):
    """User login serializer"""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        
        if user is None:
            raise serializers.ValidationError("Invalid credentials.")
        
        if not user.is_active:
            raise serializers.ValidationError("Account is inactive.")
        
        if user.is_locked():
            raise serializers.ValidationError("Account is locked due to too many failed attempts.")
        
        data['user'] = user
        return data


class PasswordResetSerializer(serializers.Serializer):
    """Password reset serializer"""
    
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Password reset confirm serializer"""
    
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data


class VerifyEmailSerializer(serializers.Serializer):
    """Email verification serializer"""
    
    token = serializers.UUIDField(required=True)


class ResendVerificationSerializer(serializers.Serializer):
    """Resend verification email serializer"""
    
    email = serializers.EmailField(required=True)


# ============================================================
# USER SERIALIZERS
# ============================================================

class UserSerializer(serializers.ModelSerializer):
    """User serializer"""
    
    full_name = serializers.SerializerMethodField()
    member_status = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'uid', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'phone_number', 'user_type', 'profile_picture',
            'bio', 'institution', 'department', 'degree_level',
            'research_interests', 'is_verified', 'is_active_member',
            'membership_number', 'member_status', 'linkedin_url',
            'researchgate_url', 'google_scholar_url', 'orcid_id',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['uid', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_member_status(self, obj):
        if hasattr(obj, 'member_profile'):
            return obj.member_profile.verification_status
        return None


# ============================================================
# MEMBER SERIALIZERS
# ============================================================

class MemberSerializer(serializers.ModelSerializer):
    """Member serializer"""
    
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = [
            'id', 'user', 'full_name', 'membership_number', 'membership_type',
            'verification_status', 'is_active_member', 'student_id_number',
            'registration_number', 'year_of_study', 'expected_graduation_year',
            'thesis_title', 'thesis_abstract', 'supervisor_name', 'supervisor_email',
            'skills', 'expertise_areas', 'programming_languages',
            'research_methodologies', 'collaboration_interests', 'mentoring_interests',
            'publication_count', 'citation_count', 'h_index',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()


class MemberListSerializer(serializers.ModelSerializer):
    """Member list serializer (lightweight)"""
    
    full_name = serializers.SerializerMethodField()
    institution = serializers.SerializerMethodField()
    degree_level = serializers.SerializerMethodField()
    research_interests = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = [
            'id', 'full_name', 'email', 'institution', 'degree_level',
            'research_interests', 'profile_picture', 'membership_number',
            'verification_status', 'publication_count', 'citation_count'
        ]
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    
    def get_institution(self, obj):
        return obj.user.institution
    
    def get_degree_level(self, obj):
        return obj.user.degree_level
    
    def get_research_interests(self, obj):
        return obj.user.research_interests
    
    def get_profile_picture(self, obj):
        if obj.user.profile_picture:
            return obj.user.profile_picture.url
        return None


class MemberDetailSerializer(serializers.ModelSerializer):
    """Member detail serializer"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Member
        fields = '__all__'


# ============================================================
# PROFILE SERIALIZERS
# ============================================================

class ProfileSerializer(serializers.ModelSerializer):
    """Profile serializer"""
    
    class Meta:
        model = Profile
        fields = [
            'id', 'title', 'academic_bio', 'research_statement',
            'teaching_interests', 'current_position', 'current_employer',
            'years_of_experience', 'education', 'certifications',
            'primary_research_area', 'secondary_research_areas',
            'research_keywords', 'grants_awarded', 'funding_sources',
            'awards', 'honors', 'professional_memberships',
            'profile_visibility', 'profile_completion'
        ]
        read_only_fields = ['profile_completion']


class PublicationSerializer(serializers.ModelSerializer):
    """Publication serializer"""
    
    authors = serializers.SerializerMethodField()
    
    class Meta:
        model = Publication
        fields = [
            'id', 'title', 'abstract', 'publication_type', 'status',
            'journal_name', 'journal_volume', 'journal_issue',
            'pages', 'doi', 'isbn', 'issn', 'publication_date',
            'acceptance_date', 'submission_date', 'url', 'pdf_file',
            'citation_count', 'view_count', 'download_count',
            'keywords', 'authors', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_authors(self, obj):
        authors = obj.publicationauthor_set.order_by('order')
        return [{
            'name': author.author.get_full_name(),
            'email': author.author.email,
            'order': author.order,
            'corresponding': author.corresponding_author,
            'affiliation': author.affiliation
        } for author in authors]


# ============================================================
# COMMUNITY SERIALIZERS
# ============================================================

class CommunitySerializer(serializers.ModelSerializer):
    """Community serializer"""
    
    created_by = UserSerializer(read_only=True)
    is_member = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    
    class Meta:
        model = Community
        fields = [
            'id', 'name', 'slug', 'description', 'community_type',
            'access_type', 'created_by', 'member_count', 'post_count',
            'view_count', 'logo', 'banner', 'tags', 'categories',
            'is_member', 'user_role', 'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at', 'view_count']
    
    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CommunityMember.objects.filter(
                community=obj,
                user=request.user
            ).exists()
        return False
    
    def get_user_role(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            member = CommunityMember.objects.filter(
                community=obj,
                user=request.user
            ).first()
            if member:
                return member.role
        return None


class CommunityDetailSerializer(CommunitySerializer):
    """Community detail serializer"""
    
    moderators = serializers.SerializerMethodField()
    
    class Meta(CommunitySerializer.Meta):
        fields = CommunitySerializer.Meta.fields + ['moderators']
    
    def get_moderators(self, obj):
        moderators = CommunityMember.objects.filter(
            community=obj,
            role__in=['admin', 'moderator']
        ).select_related('user')
        return [{
            'id': member.user.id,
            'name': member.user.get_full_name(),
            'email': member.user.email,
            'role': member.role
        } for member in moderators]


class CommunityMemberSerializer(serializers.ModelSerializer):
    """Community member serializer"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = CommunityMember
        fields = ['id', 'user', 'role', 'joined_at', 'last_active']


class CommunityPostSerializer(serializers.ModelSerializer):
    """Community post serializer"""
    
    author = UserSerializer(read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    user_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = CommunityPost
        fields = [
            'id', 'title', 'content', 'post_type', 'status',
            'author', 'view_count', 'like_count', 'comment_count',
            'user_liked', 'tags', 'cover_image', 'created_at',
            'updated_at', 'published_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'view_count']
    
    def get_user_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CommunityLike.objects.filter(
                post=obj,
                user=request.user
            ).exists()
        return False


class CommentSerializer(serializers.ModelSerializer):
    """Comment serializer"""
    
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'author', 'parent', 'replies',
            'like_count', 'created_at', 'updated_at'
        ]
    
    def get_replies(self, obj):
        replies = obj.replies.filter(is_approved=True, is_deleted=False)
        return CommentSerializer(replies, many=True).data


# ============================================================
# OPPORTUNITY SERIALIZERS
# ============================================================

class OpportunitySerializer(serializers.ModelSerializer):
    """Opportunity serializer"""
    
    created_by = UserSerializer(read_only=True)
    days_remaining = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    has_applied = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    
    class Meta:
        model = Opportunity
        fields = [
            'id', 'title', 'description', 'opportunity_type',
            'organization_name', 'organization_website', 'location',
            'country', 'is_remote', 'application_deadline',
            'start_date', 'end_date', 'has_funding', 'funding_amount',
            'currency', 'funding_details', 'eligibility_criteria',
            'required_qualifications', 'preferred_qualifications',
            'application_url', 'application_email', 'contact_person',
            'contact_email', 'contact_phone', 'tags', 'disciplines',
            'view_count', 'application_count', 'save_count',
            'days_remaining', 'is_expired', 'has_applied', 'is_saved',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'view_count']
    
    def get_days_remaining(self, obj):
        return obj.get_days_remaining()
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_has_applied(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.applications.filter(
                applicant=request.user
            ).exists()
        return False
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.saves.filter(
                user=request.user
            ).exists()
        return False


class OpportunityDetailSerializer(OpportunitySerializer):
    """Opportunity detail serializer"""
    
    class Meta(OpportunitySerializer.Meta):
        fields = OpportunitySerializer.Meta.fields + [
            'application_instructions', 'application_requirements',
            'required_documents'
        ]


class OpportunityApplicationSerializer(serializers.ModelSerializer):
    """Opportunity application serializer"""
    
    applicant = UserSerializer(read_only=True)
    opportunity = OpportunitySerializer(read_only=True)
    
    class Meta:
        model = OpportunityApplication
        fields = [
            'id', 'opportunity', 'applicant', 'cover_letter',
            'message', 'status', 'review_notes', 'created_at',
            'updated_at', 'reviewed_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'reviewed_at']


# ============================================================
# EVENT SERIALIZERS
# ============================================================

class EventSerializer(serializers.ModelSerializer):
    """Event serializer"""
    
    created_by = UserSerializer(read_only=True)
    is_registered = serializers.SerializerMethodField()
    registration_status = serializers.SerializerMethodField()
    has_capacity = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'description', 'event_type',
            'status', 'organizer_name', 'organizer_email',
            'organizer_phone', 'organizer_website', 'is_virtual',
            'venue', 'address', 'city', 'country', 'virtual_link',
            'start_date', 'end_date', 'registration_deadline',
            'max_attendees', 'current_attendees', 'requires_registration',
            'registration_fee', 'currency', 'registration_link',
            'agenda', 'speakers', 'program', 'banner_image',
            'poster', 'tags', 'view_count', 'registration_count',
            'is_registered', 'registration_status', 'has_capacity',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'view_count']
    
    def get_is_registered(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.registrations.filter(
                user=request.user
            ).exists()
        return False
    
    def get_registration_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            registration = obj.registrations.filter(
                user=request.user
            ).first()
            if registration:
                return registration.attendance_status
        return None
    
    def get_has_capacity(self, obj):
        return obj.has_capacity()


class EventDetailSerializer(EventSerializer):
    """Event detail serializer"""
    
    class Meta(EventSerializer.Meta):
        fields = EventSerializer.Meta.fields + [
            'zoom_meeting_id', 'zoom_password', 'zoom_meeting_link',
            'recording_url', 'recording_file'
        ]


class EventRegistrationSerializer(serializers.ModelSerializer):
    """Event registration serializer"""
    
    user = UserSerializer(read_only=True)
    event = EventSerializer(read_only=True)
    
    class Meta:
        model = EventRegistration
        fields = [
            'id', 'event', 'user', 'attendance_status',
            'registration_date', 'payment_status', 'amount_paid',
            'certificate_issued', 'certificate_file', 'feedback_submitted',
            'feedback_rating', 'feedback_comment', 'created_at'
        ]


# ============================================================
# RESOURCE SERIALIZERS
# ============================================================

class ResourceSerializer(serializers.ModelSerializer):
    """Resource serializer"""
    
    created_by = UserSerializer(read_only=True)
    categories = serializers.SerializerMethodField()
    
    class Meta:
        model = Resource
        fields = [
            'id', 'title', 'slug', 'description', 'resource_type',
            'access_type', 'categories', 'cover_image', 'file',
            'file_size', 'file_type', 'external_url', 'author',
            'author_email', 'publisher', 'publication_date',
            'version', 'keywords', 'view_count', 'download_count',
            'like_count', 'average_rating', 'rating_count',
            'is_featured', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'view_count']
    
    def get_categories(self, obj):
        return [cat.name for cat in obj.categories.all()]


class ResourceDetailSerializer(ResourceSerializer):
    """Resource detail serializer"""
    
    content = serializers.CharField(read_only=True)
    
    class Meta(ResourceSerializer.Meta):
        fields = ResourceSerializer.Meta.fields + ['content']


# ============================================================
# NOTIFICATION SERIALIZERS
# ============================================================

class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type',
            'priority', 'link', 'is_read', 'read_at',
            'created_at', 'metadata'
        ]
        read_only_fields = ['created_at']


# ============================================================
# ACTIVITY SERIALIZERS
# ============================================================

class ActivitySerializer(serializers.ModelSerializer):
    """Activity serializer"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserActivityLog
        fields = [
            'id', 'user', 'action_type', 'action_description',
            'ip_address', 'created_at', 'metadata'
        ]
        read_only_fields = ['created_at']


# ============================================================
# DASHBOARD SERIALIZERS
# ============================================================

class DashboardSerializer(serializers.Serializer):
    """Dashboard data serializer"""
    
    user = UserSerializer()
    member = MemberSerializer()
    recent_activities = ActivitySerializer(many=True)
    notifications = NotificationSerializer(many=True)
    upcoming_events = EventRegistrationSerializer(many=True)
    communities = CommunityMemberSerializer(many=True)


# ============================================================
# COLLABORATION SERIALIZERS
# ============================================================

class CollaborationSerializer(serializers.ModelSerializer):
    """Collaboration serializer"""
    
    requested_by = UserSerializer(read_only=True)
    
    class Meta:
        model = CollaborationRequest
        fields = [
            'id', 'title', 'description', 'collaboration_type',
            'status', 'requested_by', 'is_open', 'target_users',
            'required_skills', 'required_expertise', 'required_institutions',
            'start_date', 'end_date', 'duration_weeks', 'is_remote',
            'location', 'country', 'has_funding', 'funding_details',
            'attachments', 'view_count', 'application_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'view_count']


class CollaborationDetailSerializer(CollaborationSerializer):
    """Collaboration detail serializer"""
    
    applications = OpportunityApplicationSerializer(many=True, read_only=True)
    
    class Meta(CollaborationSerializer.Meta):
        fields = CollaborationSerializer.Meta.fields + ['applications']