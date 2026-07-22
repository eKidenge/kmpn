from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.db.models import Q, Count, Sum, Avg
from rest_framework import status, viewsets, generics, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.authtoken.models import Token
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from accounts.models import User, UserActivityLog
from members.models import Member, MemberActivity
from profiles.models import Profile, Publication
from communities.models import Community, CommunityMember, CommunityPost, Comment, CommunityLike
from opportunities.models import Opportunity, OpportunityApplication, OpportunitySave
from events.models import Event, EventRegistration
from resources.models import Resource, ResourceRating, ResourceDownload
from notifications.models import Notification
from collaborations.models import CollaborationRequest

from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    MemberSerializer, MemberDetailSerializer, MemberListSerializer,
    ProfileSerializer, PublicationSerializer,
    CommunitySerializer, CommunityDetailSerializer, CommunityMemberSerializer,
    CommunityPostSerializer, CommentSerializer,
    OpportunitySerializer, OpportunityDetailSerializer, OpportunityApplicationSerializer,
    EventSerializer, EventDetailSerializer, EventRegistrationSerializer,
    ResourceSerializer, ResourceDetailSerializer,
    NotificationSerializer,
    ActivitySerializer, DashboardSerializer,
    CollaborationSerializer, CollaborationDetailSerializer,
    PasswordResetSerializer, PasswordResetConfirmSerializer,
    VerifyEmailSerializer, ResendVerificationSerializer
)
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly, IsMemberOrReadOnly

import logging
logger = logging.getLogger(__name__)


# ============================================================
# AUTHENTICATION VIEWS
# ============================================================

class RegisterView(APIView):
    """User registration API endpoint"""
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create member profile
            member = Member.objects.create(
                user=user,
                membership_type=serializer.validated_data.get('membership_type', 'student')
            )
            
            # Create user profile
            Profile.objects.create(user=user)
            
            # Log activity
            UserActivityLog.objects.create(
                user=user,
                action_type='registration',
                action_description='User registered via API',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Send verification email
            self.send_verification_email(request, user)
            
            return Response({
                'success': True,
                'message': 'Registration successful. Please check your email for verification.',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def send_verification_email(self, request, user):
        current_site = request.get_host()
        token = user.email_verification_token
        
        subject = 'Verify Your Email - KMPN'
        message = render_to_string('accounts/verification_email.html', {
            'user': user,
            'domain': current_site,
            'token': token,
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )


class LoginView(APIView):
    """User login API endpoint"""
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            user = authenticate(request, username=email, password=password)
            
            if user is None:
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if not user.is_active:
                return Response({
                    'error': 'Account is inactive. Please verify your email.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if user.is_locked():
                return Response({
                    'error': 'Account is locked due to too many failed attempts. Please try again later.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Login user
            login(request, user)
            
            # Create or get token
            token, created = Token.objects.get_or_create(user=user)
            
            # Log activity
            UserActivityLog.objects.create(
                user=user,
                action_type='login',
                action_description='User logged in via API',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Reset login attempts
            user.reset_login_attempts()
            user.last_login_ip = self.get_client_ip(request)
            user.save()
            
            return Response({
                'success': True,
                'token': token.key,
                'user': UserSerializer(user).data,
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    """User logout API endpoint"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Delete token
        try:
            request.user.auth_token.delete()
        except:
            pass
        
        logout(request)
        
        # Log activity
        UserActivityLog.objects.create(
            user=request.user,
            action_type='logout',
            action_description='User logged out via API',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PasswordResetView(APIView):
    """Password reset request API endpoint"""
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Send reset email
                self.send_reset_email(request, user, uid, token)
                
                return Response({
                    'success': True,
                    'message': 'Password reset email sent'
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                # Don't reveal that user doesn't exist
                return Response({
                    'success': True,
                    'message': 'If an account exists with this email, a reset link will be sent.'
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_reset_email(self, request, user, uid, token):
        current_site = request.get_host()
        
        subject = 'Password Reset - KMPN'
        message = render_to_string('accounts/password_reset_email.html', {
            'user': user,
            'domain': current_site,
            'uid': uid,
            'token': token,
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )


class PasswordResetConfirmView(APIView):
    """Password reset confirm API endpoint"""
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            uid = serializer.validated_data['uid']
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            try:
                uid = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response({
                    'error': 'Invalid reset link'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not default_token_generator.check_token(user, token):
                return Response({
                    'error': 'Invalid or expired reset link'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.save()
            
            # Log activity
            UserActivityLog.objects.create(
                user=user,
                action_type='profile_update',
                action_description='User reset password via API',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'success': True,
                'message': 'Password reset successful'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class VerifyEmailView(APIView):
    """Verify email API endpoint"""
    permission_classes = [AllowAny]
    serializer_class = VerifyEmailSerializer
    
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            
            try:
                user = User.objects.get(email_verification_token=token)
                
                if user.email_verified:
                    return Response({
                        'error': 'Email already verified'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                user.email_verified = True
                user.is_active = True
                user.save()
                
                # Generate membership number
                self.generate_membership_number(user)
                
                return Response({
                    'success': True,
                    'message': 'Email verified successfully'
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({
                    'error': 'Invalid verification token'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def generate_membership_number(self, user):
        import random
        import string
        
        year = timezone.now().year
        sequence = Member.objects.filter(
            membership_start_date__year=year
        ).count() + 1
        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        membership_number = f"KMPN/{year}/{str(sequence).zfill(4)}/{random_chars}"
        
        try:
            member = Member.objects.get(user=user)
            member.membership_number = membership_number
            member.membership_start_date = timezone.now()
            member.membership_expiry_date = timezone.now() + timezone.timedelta(days=365)
            member.is_active_member = True
            member.is_verified = True
            member.save()
        except Member.DoesNotExist:
            pass
        
        return membership_number


class ResendVerificationView(APIView):
    """Resend verification email API endpoint"""
    permission_classes = [AllowAny]
    serializer_class = ResendVerificationSerializer
    
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                if user.email_verified:
                    return Response({
                        'error': 'Email already verified'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Send verification email
                self.send_verification_email(request, user)
                
                return Response({
                    'success': True,
                    'message': 'Verification email sent'
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_verification_email(self, request, user):
        current_site = request.get_host()
        token = user.email_verification_token
        
        subject = 'Verify Your Email - KMPN'
        message = render_to_string('accounts/verification_email.html', {
            'user': user,
            'domain': current_site,
            'token': token,
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )


# ============================================================
# PROFILE VIEWS
# ============================================================

class ProfileView(APIView):
    """Get user profile"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        profile, created = Profile.objects.get_or_create(user=user)
        
        try:
            member = Member.objects.get(user=user)
        except Member.DoesNotExist:
            member = None
        
        return Response({
            'user': UserSerializer(user).data,
            'profile': ProfileSerializer(profile).data,
            'member': MemberSerializer(member).data if member else None,
        })


class ProfileUpdateView(APIView):
    """Update user profile"""
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        user = request.user
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Update user fields
        user_fields = ['first_name', 'last_name', 'bio', 'phone_number', 
                       'institution', 'department', 'degree_level', 'research_interests']
        
        for field in user_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()
        
        # Update profile fields
        profile_fields = ['academic_bio', 'research_statement', 'teaching_interests',
                         'current_position', 'current_employer', 'years_of_experience',
                         'primary_research_area', 'profile_visibility']
        
        for field in profile_fields:
            if field in request.data:
                setattr(profile, field, request.data[field])
        profile.save()
        
        # Update member fields
        try:
            member = Member.objects.get(user=user)
            member_fields = ['membership_type', 'skills', 'expertise_areas',
                           'programming_languages', 'research_methodologies',
                           'collaboration_interests', 'mentoring_interests']
            
            for field in member_fields:
                if field in request.data:
                    if field in ['skills', 'expertise_areas', 'programming_languages',
                                'research_methodologies', 'collaboration_interests',
                                'mentoring_interests']:
                        # Handle list fields
                        value = request.data[field]
                        if isinstance(value, str):
                            setattr(member, field, [v.strip() for v in value.split(',') if v.strip()])
                        else:
                            setattr(member, field, value)
                    else:
                        setattr(member, field, request.data[field])
            member.save()
        except Member.DoesNotExist:
            pass
        
        # Log activity
        UserActivityLog.objects.create(
            user=user,
            action_type='profile_update',
            action_description='User updated profile via API',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'user': UserSerializer(user).data,
            'profile': ProfileSerializer(profile).data,
        })
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# ============================================================
# DASHBOARD VIEWS
# ============================================================

class DashboardView(APIView):
    """Get dashboard data"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        try:
            member = Member.objects.get(user=user)
        except Member.DoesNotExist:
            member = None
        
        # Get recent activities
        activities = UserActivityLog.objects.filter(
            user=user
        ).order_by('-created_at')[:10]
        
        # Get notifications
        notifications = Notification.objects.filter(
            user=user,
            is_deleted=False
        ).order_by('-created_at')[:10]
        
        # Get upcoming events
        registrations = EventRegistration.objects.filter(
            user=user,
            event__start_date__gte=timezone.now()
        ).select_related('event').order_by('event__start_date')[:5]
        
        # Get communities
        community_memberships = CommunityMember.objects.filter(
            user=user
        ).select_related('community')[:5]
        
        return Response({
            'user': UserSerializer(user).data,
            'member': MemberSerializer(member).data if member else None,
            'recent_activities': ActivitySerializer(activities, many=True).data,
            'notifications': NotificationSerializer(notifications, many=True).data,
            'upcoming_events': EventRegistrationSerializer(registrations, many=True).data,
            'communities': CommunityMemberSerializer(community_memberships, many=True).data,
        })


class DashboardStatsView(APIView):
    """Get dashboard statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Member stats
        member_stats = {}
        try:
            member = Member.objects.get(user=user)
            member_stats = {
                'is_verified': member.verification_status == 'verified',
                'is_active': member.is_membership_active(),
                'membership_number': member.membership_number,
                'verification_status': member.verification_status,
                'joined_days': member.get_membership_duration(),
            }
        except Member.DoesNotExist:
            member_stats = {
                'is_verified': False,
                'is_active': False,
                'membership_number': None,
                'verification_status': 'pending',
                'joined_days': 0,
            }
        
        # Content stats
        content_stats = {
            'publications': Publication.objects.filter(members=user).count(),
            'communities': CommunityMember.objects.filter(user=user).count(),
            'events_attended': EventRegistration.objects.filter(
                user=user,
                attendance_status='attended'
            ).count(),
            'opportunities_applied': OpportunityApplication.objects.filter(
                applicant=user
            ).count(),
            'resources_downloaded': ResourceDownload.objects.filter(
                user=user
            ).count(),
        }
        
        # Notification stats
        notification_stats = {
            'unread': Notification.objects.filter(
                user=user,
                is_read=False,
                is_deleted=False
            ).count(),
            'total': Notification.objects.filter(
                user=user,
                is_deleted=False
            ).count(),
        }
        
        return Response({
            'member_stats': member_stats,
            'content_stats': content_stats,
            'notification_stats': notification_stats,
        })


# ============================================================
# ACTIVITY VIEWS
# ============================================================

class ActivityListView(generics.ListAPIView):
    """List user activities"""
    permission_classes = [IsAuthenticated]
    serializer_class = ActivitySerializer
    
    def get_queryset(self):
        return UserActivityLog.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


# ============================================================
# SEARCH VIEW
# ============================================================

class SearchView(APIView):
    """Search across all content"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        query = request.GET.get('q', '')
        if len(query) < 2:
            return Response({
                'error': 'Search query must be at least 2 characters'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Search members - FIXED: Removed the [:5] from here
        members = Member.objects.filter(
            verification_status='verified'
        ).filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__institution__icontains=query) |
            Q(user__research_interests__icontains=query)
        )[:5]  # Moved [:5] to the end
        
        # Search communities - FIXED: Removed the [:5] from here
        communities = Community.objects.filter(
            is_active=True
        ).filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        )[:5]  # Moved [:5] to the end
        
        # Search opportunities - FIXED: Removed the [:5] from here
        opportunities = Opportunity.objects.filter(
            status='published'
        ).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(organization_name__icontains=query)
        )[:5]  # Moved [:5] to the end
        
        # Search events - FIXED: Removed the [:5] from here
        events = Event.objects.filter(
            status__in=['published', 'ongoing']
        ).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(organizer_name__icontains=query)
        )[:5]  # Moved [:5] to the end
        
        # Search resources - FIXED: Removed the [:5] from here
        resources = Resource.objects.filter(
            is_published=True
        ).filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(keywords__icontains=query)
        )[:5]  # Moved [:5] to the end
        
        return Response({
            'query': query,
            'members': MemberListSerializer(members, many=True).data,
            'communities': CommunitySerializer(communities, many=True).data,
            'opportunities': OpportunitySerializer(opportunities, many=True).data,
            'events': EventSerializer(events, many=True).data,
            'resources': ResourceSerializer(resources, many=True).data,
        })


# ============================================================
# VIEWSETS
# ============================================================

class MemberViewSet(viewsets.ModelViewSet):
    """Member API endpoints"""
    queryset = Member.objects.filter(verification_status='verified')
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['verification_status', 'membership_type', 'user__degree_level']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'user__institution']
    ordering_fields = ['created_at', 'publication_count', 'citation_count']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MemberDetailSerializer
        elif self.action == 'list':
            return MemberListSerializer
        return MemberSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by institution
        institution = self.request.query_params.get('institution')
        if institution:
            queryset = queryset.filter(user__institution__icontains=institution)
        
        # Filter by research area
        research = self.request.query_params.get('research')
        if research:
            queryset = queryset.filter(
                Q(user__research_interests__icontains=research) |
                Q(expertise_areas__icontains=research)
            )
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def publications(self, request, pk=None):
        """Get member's publications"""
        member = self.get_object()
        publications = Publication.objects.filter(
            members=member.user,
            status='published'
        )
        serializer = PublicationSerializer(publications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """Follow a member"""
        member = self.get_object()
        
        if request.user == member.user:
            return Response({
                'error': 'You cannot follow yourself'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Implement follow logic here
        # This would use a Follow model
        
        return Response({
            'success': True,
            'message': f'Followed {member.user.get_full_name()}'
        })


class CommunityViewSet(viewsets.ModelViewSet):
    """Community API endpoints"""
    queryset = Community.objects.filter(is_active=True)
    serializer_class = CommunitySerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['community_type', 'access_type']
    search_fields = ['name', 'description', 'tags']
    ordering_fields = ['created_at', 'member_count', 'post_count']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CommunityDetailSerializer
        return CommunitySerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by member status
        member = self.request.query_params.get('member')
        if member == 'true':
            queryset = queryset.filter(
                members__user=self.request.user
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a community"""
        community = self.get_object()
        
        # Check if already a member
        if CommunityMember.objects.filter(community=community, user=request.user).exists():
            return Response({
                'error': 'Already a member of this community'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Join community
        CommunityMember.objects.create(
            community=community,
            user=request.user,
            role='member'
        )
        
        community.member_count += 1
        community.save()
        
        return Response({
            'success': True,
            'message': f'Joined {community.name}'
        })
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a community"""
        community = self.get_object()
        
        member = CommunityMember.objects.filter(
            community=community,
            user=request.user
        ).first()
        
        if not member:
            return Response({
                'error': 'Not a member of this community'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        member.delete()
        community.member_count -= 1
        community.save()
        
        return Response({
            'success': True,
            'message': f'Left {community.name}'
        })
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get community members"""
        community = self.get_object()
        members = CommunityMember.objects.filter(community=community)
        serializer = CommunityMemberSerializer(members, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        """Get community posts"""
        community = self.get_object()
        posts = CommunityPost.objects.filter(
            community=community,
            status__in=['published', 'pinned']
        ).order_by('-created_at')
        
        # Paginate
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 10)
        
        paginator = Paginator(posts, page_size)
        try:
            posts_page = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            posts_page = paginator.page(1)
        
        serializer = CommunityPostSerializer(posts_page, many=True)
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'page': int(page),
            'total_pages': paginator.num_pages
        })


class OpportunityViewSet(viewsets.ModelViewSet):
    """Opportunity API endpoints"""
    queryset = Opportunity.objects.filter(status='published')
    serializer_class = OpportunitySerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['opportunity_type', 'country', 'has_funding']
    search_fields = ['title', 'description', 'organization_name', 'tags']
    ordering_fields = ['created_at', 'application_deadline', 'view_count', 'application_count']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OpportunityDetailSerializer
        return OpportunitySerializer
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply to an opportunity"""
        opportunity = self.get_object()
        
        # Check if already applied
        if OpportunityApplication.objects.filter(opportunity=opportunity, applicant=request.user).exists():
            return Response({
                'error': 'Already applied to this opportunity'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check deadline
        if opportunity.application_deadline and timezone.now() > opportunity.application_deadline:
            return Response({
                'error': 'Application deadline has passed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create application
        application = OpportunityApplication.objects.create(
            opportunity=opportunity,
            applicant=request.user,
            cover_letter=request.data.get('cover_letter', ''),
            message=request.data.get('message', '')
        )
        
        opportunity.application_count += 1
        opportunity.save()
        
        return Response({
            'success': True,
            'message': 'Application submitted successfully',
            'application_id': application.id
        })
    
    @action(detail=True, methods=['post'])
    def save(self, request, pk=None):
        """Save an opportunity"""
        opportunity = self.get_object()
        
        # Check if already saved
        save, created = OpportunitySave.objects.get_or_create(
            opportunity=opportunity,
            user=request.user
        )
        
        if created:
            opportunity.save_count += 1
            opportunity.save()
            return Response({
                'success': True,
                'saved': True,
                'message': 'Opportunity saved'
            })
        else:
            save.delete()
            opportunity.save_count -= 1
            opportunity.save()
            return Response({
                'success': True,
                'saved': False,
                'message': 'Opportunity unsaved'
            })


class EventViewSet(viewsets.ModelViewSet):
    """Event API endpoints"""
    queryset = Event.objects.filter(status__in=['published', 'ongoing'])
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event_type', 'is_virtual', 'country']
    search_fields = ['title', 'description', 'organizer_name', 'venue']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EventDetailSerializer
        return EventSerializer
    
    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        """Register for an event"""
        event = self.get_object()
        
        # Check if already registered
        if EventRegistration.objects.filter(event=event, user=request.user).exists():
            return Response({
                'error': 'Already registered for this event'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check capacity
        if event.max_attendees and event.current_attendees >= event.max_attendees:
            return Response({
                'error': 'Event is fully booked'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check registration deadline
        if event.registration_deadline and timezone.now() > event.registration_deadline:
            return Response({
                'error': 'Registration deadline has passed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Register
        registration = EventRegistration.objects.create(
            event=event,
            user=request.user
        )
        
        event.current_attendees += 1
        event.registration_count += 1
        event.save()
        
        return Response({
            'success': True,
            'message': 'Registration successful',
            'registration_id': registration.id
        })
    
    @action(detail=True, methods=['post'])
    def cancel_registration(self, request, pk=None):
        """Cancel event registration"""
        event = self.get_object()
        
        registration = EventRegistration.objects.filter(
            event=event,
            user=request.user
        ).first()
        
        if not registration:
            return Response({
                'error': 'Not registered for this event'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        registration.attendance_status = 'cancelled'
        registration.save()
        
        event.current_attendees -= 1
        event.save()
        
        return Response({
            'success': True,
            'message': 'Registration cancelled'
        })
    
    @action(detail=True, methods=['get'])
    def attendees(self, request, pk=None):
        """Get event attendees"""
        event = self.get_object()
        registrations = EventRegistration.objects.filter(
            event=event,
            attendance_status__in=['confirmed', 'attended']
        ).select_related('user')
        
        serializer = EventRegistrationSerializer(registrations, many=True)
        return Response(serializer.data)


class ResourceViewSet(viewsets.ModelViewSet):
    """Resource API endpoints"""
    queryset = Resource.objects.filter(is_published=True)
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['resource_type', 'access_type']
    search_fields = ['title', 'description', 'keywords', 'author']
    ordering_fields = ['created_at', 'download_count', 'view_count', 'average_rating']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ResourceDetailSerializer
        return ResourceSerializer
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """Download a resource"""
        resource = self.get_object()
        
        # Check access
        if resource.access_type == 'members_only':
            try:
                member = Member.objects.get(user=request.user)
                if member.verification_status != 'verified':
                    return Response({
                        'error': 'You need to be a verified member to download this resource'
                    }, status=status.HTTP_403_FORBIDDEN)
            except Member.DoesNotExist:
                return Response({
                    'error': 'Please complete your member profile first'
                }, status=status.HTTP_403_FORBIDDEN)
        
        if resource.access_type == 'premium':
            try:
                member = Member.objects.get(user=request.user)
                if not member.is_active_member():
                    return Response({
                        'error': 'Premium membership required to download this resource'
                    }, status=status.HTTP_403_FORBIDDEN)
            except Member.DoesNotExist:
                return Response({
                    'error': 'Please complete your member profile first'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Track download
        ResourceDownload.objects.create(
            resource=resource,
            user=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        resource.increment_download_count()
        
        return Response({
            'success': True,
            'message': 'Resource download tracked',
            'download_url': resource.file.url if resource.file else resource.external_url
        })
    
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """Rate a resource"""
        resource = self.get_object()
        
        rating_value = request.data.get('rating')
        review = request.data.get('review', '')
        
        if not rating_value or int(rating_value) < 1 or int(rating_value) > 5:
            return Response({
                'error': 'Rating must be between 1 and 5'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        rating, created = ResourceRating.objects.update_or_create(
            resource=resource,
            user=request.user,
            defaults={
                'rating': int(rating_value),
                'review': review
            }
        )
        
        # Update average rating
        avg_rating = resource.ratings.aggregate(Avg('rating'))['rating__avg']
        resource.average_rating = avg_rating or 0
        resource.rating_count = resource.ratings.count()
        resource.save()
        
        return Response({
            'success': True,
            'message': 'Rating submitted successfully',
            'average_rating': resource.average_rating,
            'rating_count': resource.rating_count
        })
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class NotificationViewSet(viewsets.ModelViewSet):
    """Notification API endpoints"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        
        return Response({
            'success': True,
            'message': 'Notification marked as read'
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False,
            is_deleted=False
        ).update(is_read=True, read_at=timezone.now())
        
        return Response({
            'success': True,
            'message': f'{count} notifications marked as read',
            'count': count
        })
    
    @action(detail=True, methods=['post'])
    def delete(self, request, pk=None):
        """Delete notification"""
        notification = self.get_object()
        notification.is_deleted = True
        notification.deleted_at = timezone.now()
        notification.save()
        
        return Response({
            'success': True,
            'message': 'Notification deleted'
        })