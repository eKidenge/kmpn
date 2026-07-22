from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Avg, Sum, OuterRef, Subquery
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import send_mail
import json
import logging
from datetime import datetime, timedelta

from .models import (
    Profile, ResearchInterest, Publication, PublicationAuthor
)
from .forms import (
    ProfileForm, ResearchInterestForm, PublicationForm,
    ProfileVisibilityForm, PublicationAuthorForm
)
from accounts.models import User, UserActivityLog
from accounts.decorators import user_activity_log, user_type_required
from members.models import Member, MemberActivity
from notifications.models import Notification

logger = logging.getLogger(__name__)


# ============================================================
# PROFILE VIEWS
# ============================================================

def profile_view(request, username=None):
    """View user profile"""
    if username:
        user = get_object_or_404(User, username=username, is_active=True)
    else:
        if request.user.is_authenticated:
            user = request.user
        else:
            messages.warning(request, 'Please login to view your profile.')
            return redirect('accounts:login')
    
    # Get or create profile
    profile, created = Profile.objects.get_or_create(user=user)
    
    # Check visibility
    if profile.profile_visibility == 'private' and user != request.user:
        if not request.user.is_authenticated:
            messages.warning(request, 'This profile is private. Please login to view.')
            return redirect('accounts:login')
        
        if request.user != user and not request.user.is_staff:
            messages.warning(request, 'This profile is private.')
            return redirect('home')
    
    # Get member information
    try:
        member = Member.objects.get(user=user)
    except Member.DoesNotExist:
        member = None
    
    # Get publications
    publications = Publication.objects.filter(
        members=user,
        status='published'
    ).order_by('-publication_date', '-created_at')
    
    # Get publication statistics
    total_publications = publications.count()
    total_citations = publications.aggregate(Sum('citation_count'))['citation_count__sum'] or 0
    
    # Get research interests
    if user.research_interests:
        interests = [interest.strip() for interest in user.research_interests.split(',') if interest.strip()]
    else:
        interests = []
    
    # Get profile completion
    profile_completion = profile.calculate_completion()
    
    # Log profile view
    if request.user.is_authenticated and request.user != user:
        UserActivityLog.objects.create(
            user=request.user,
            action_type='profile_view',
            action_description=f'Viewed profile of {user.get_full_name()}',
            ip_address=get_client_ip(request),
            metadata={'target_user': user.id}
        )
        
        if member:
            MemberActivity.objects.create(
                member=member,
                activity_type='profile_view',
                activity_description=f'Profile viewed by {request.user.get_full_name()}',
                ip_address=get_client_ip(request),
                metadata={'viewer_id': request.user.id}
            )
    
    context = {
        'profile_user': user,
        'profile': profile,
        'member': member,
        'publications': publications[:10],
        'total_publications': total_publications,
        'total_citations': total_citations,
        'interests': interests,
        'profile_completion': profile_completion,
        'is_own_profile': user == request.user,
        'page_title': f'{user.get_full_name()} - Profile',
    }
    return render(request, 'profiles/view.html', context)


@login_required
def profile_edit(request):
    """Edit profile"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save()
            
            # Update user fields
            user = request.user
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.bio = form.cleaned_data.get('bio')
            user.institution = form.cleaned_data.get('institution')
            user.department = form.cleaned_data.get('department')
            user.degree_level = form.cleaned_data.get('degree_level')
            user.research_interests = form.cleaned_data.get('research_interests')
            
            if 'profile_picture' in request.FILES:
                user.profile_picture = request.FILES['profile_picture']
            
            user.save()
            
            # Update member if exists
            try:
                member = Member.objects.get(user=user)
                member.skills = form.cleaned_data.get('skills', '').split(',') if form.cleaned_data.get('skills') else []
                member.expertise_areas = form.cleaned_data.get('expertise_areas', '').split(',') if form.cleaned_data.get('expertise_areas') else []
                member.save()
            except Member.DoesNotExist:
                pass
            
            # Calculate profile completion
            profile.calculate_completion()
            
            # Log activity
            UserActivityLog.objects.create(
                user=request.user,
                action_type='profile_update',
                action_description='Updated profile',
                ip_address=get_client_ip(request),
            )
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('profiles:view', username=request.user.username)
    else:
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'bio': request.user.bio,
            'institution': request.user.institution,
            'department': request.user.department,
            'degree_level': request.user.degree_level,
            'research_interests': request.user.research_interests,
        }
        
        # Get member skills
        try:
            member = Member.objects.get(user=request.user)
            initial_data['skills'] = ', '.join(member.skills) if member.skills else ''
            initial_data['expertise_areas'] = ', '.join(member.expertise_areas) if member.expertise_areas else ''
        except Member.DoesNotExist:
            pass
        
        form = ProfileForm(instance=profile, initial=initial_data)
    
    context = {
        'form': form,
        'profile': profile,
        'page_title': 'Edit Profile - KMPN',
    }
    return render(request, 'profiles/edit.html', context)


@login_required
def edit_basic_info(request):
    """Edit basic information"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save()
            
            # Update user
            user = request.user
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.bio = form.cleaned_data.get('bio')
            user.save()
            
            # Update member
            try:
                member = Member.objects.get(user=user)
                member.membership_type = form.cleaned_data.get('membership_type')
                member.save()
            except Member.DoesNotExist:
                pass
            
            profile.calculate_completion()
            
            messages.success(request, 'Basic information updated successfully!')
            return redirect('profiles:view', username=request.user.username)
    else:
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'bio': request.user.bio,
        }
        
        try:
            member = Member.objects.get(user=request.user)
            initial_data['membership_type'] = member.membership_type
        except Member.DoesNotExist:
            pass
        
        form = ProfileForm(instance=profile, initial=initial_data)
    
    context = {
        'form': form,
        'profile': profile,
        'page_title': 'Edit Basic Information - KMPN',
    }
    return render(request, 'profiles/edit_basic.html', context)


@login_required
def edit_academic(request):
    """Edit academic information"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save()
            
            # Update user
            user = request.user
            user.institution = form.cleaned_data.get('institution')
            user.department = form.cleaned_data.get('department')
            user.degree_level = form.cleaned_data.get('degree_level')
            user.save()
            
            # Update member
            try:
                member = Member.objects.get(user=user)
                member.student_id_number = form.cleaned_data.get('student_id_number')
                member.registration_number = form.cleaned_data.get('registration_number')
                member.year_of_study = form.cleaned_data.get('year_of_study')
                member.expected_graduation_year = form.cleaned_data.get('expected_graduation_year')
                member.thesis_title = form.cleaned_data.get('thesis_title')
                member.thesis_abstract = form.cleaned_data.get('thesis_abstract')
                member.supervisor_name = form.cleaned_data.get('supervisor_name')
                member.supervisor_email = form.cleaned_data.get('supervisor_email')
                member.save()
            except Member.DoesNotExist:
                pass
            
            profile.calculate_completion()
            
            messages.success(request, 'Academic information updated successfully!')
            return redirect('profiles:view', username=request.user.username)
    else:
        initial_data = {
            'institution': request.user.institution,
            'department': request.user.department,
            'degree_level': request.user.degree_level,
        }
        
        try:
            member = Member.objects.get(user=request.user)
            initial_data['student_id_number'] = member.student_id_number
            initial_data['registration_number'] = member.registration_number
            initial_data['year_of_study'] = member.year_of_study
            initial_data['expected_graduation_year'] = member.expected_graduation_year
            initial_data['thesis_title'] = member.thesis_title
            initial_data['thesis_abstract'] = member.thesis_abstract
            initial_data['supervisor_name'] = member.supervisor_name
            initial_data['supervisor_email'] = member.supervisor_email
        except Member.DoesNotExist:
            pass
        
        form = ProfileForm(instance=profile, initial=initial_data)
    
    context = {
        'form': form,
        'profile': profile,
        'page_title': 'Edit Academic Information - KMPN',
    }
    return render(request, 'profiles/edit_academic.html', context)


@login_required
def edit_research(request):
    """Edit research information"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save()
            
            # Update user
            user = request.user
            user.research_interests = form.cleaned_data.get('research_interests')
            user.save()
            
            # Update member
            try:
                member = Member.objects.get(user=user)
                member.research_methodologies = form.cleaned_data.get('research_methodologies', '').split(',') if form.cleaned_data.get('research_methodologies') else []
                member.collaboration_interests = form.cleaned_data.get('collaboration_interests', '').split(',') if form.cleaned_data.get('collaboration_interests') else []
                member.mentoring_interests = form.cleaned_data.get('mentoring_interests', '').split(',') if form.cleaned_data.get('mentoring_interests') else []
                member.save()
            except Member.DoesNotExist:
                pass
            
            profile.calculate_completion()
            
            messages.success(request, 'Research information updated successfully!')
            return redirect('profiles:view', username=request.user.username)
    else:
        initial_data = {
            'research_interests': request.user.research_interests,
            'primary_research_area': profile.primary_research_area,
        }
        
        try:
            member = Member.objects.get(user=request.user)
            initial_data['research_methodologies'] = ', '.join(member.research_methodologies) if member.research_methodologies else ''
            initial_data['collaboration_interests'] = ', '.join(member.collaboration_interests) if member.collaboration_interests else ''
            initial_data['mentoring_interests'] = ', '.join(member.mentoring_interests) if member.mentoring_interests else ''
        except Member.DoesNotExist:
            pass
        
        form = ProfileForm(instance=profile, initial=initial_data)
    
    context = {
        'form': form,
        'profile': profile,
        'page_title': 'Edit Research Information - KMPN',
    }
    return render(request, 'profiles/edit_research.html', context)


@login_required
def edit_skills(request):
    """Edit skills and expertise"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save()
            
            # Update member
            try:
                member = Member.objects.get(user=request.user)
                member.skills = form.cleaned_data.get('skills', '').split(',') if form.cleaned_data.get('skills') else []
                member.expertise_areas = form.cleaned_data.get('expertise_areas', '').split(',') if form.cleaned_data.get('expertise_areas') else []
                member.programming_languages = form.cleaned_data.get('programming_languages', '').split(',') if form.cleaned_data.get('programming_languages') else []
                member.save()
            except Member.DoesNotExist:
                pass
            
            profile.calculate_completion()
            
            messages.success(request, 'Skills updated successfully!')
            return redirect('profiles:view', username=request.user.username)
    else:
        initial_data = {}
        
        try:
            member = Member.objects.get(user=request.user)
            initial_data['skills'] = ', '.join(member.skills) if member.skills else ''
            initial_data['expertise_areas'] = ', '.join(member.expertise_areas) if member.expertise_areas else ''
            initial_data['programming_languages'] = ', '.join(member.programming_languages) if member.programming_languages else ''
        except Member.DoesNotExist:
            pass
        
        form = ProfileForm(instance=profile, initial=initial_data)
    
    context = {
        'form': form,
        'profile': profile,
        'page_title': 'Edit Skills - KMPN',
    }
    return render(request, 'profiles/edit_skills.html', context)


# ============================================================
# PUBLICATION VIEWS
# ============================================================

@login_required
def edit_publications(request):
    """Edit publications"""
    publications = Publication.objects.filter(
        members=request.user
    ).order_by('-publication_date', '-created_at')
    
    context = {
        'publications': publications,
        'page_title': 'My Publications - KMPN',
    }
    return render(request, 'profiles/edit_publications.html', context)


@login_required
@user_activity_log('publication_add', 'Added publication')
def add_publication(request):
    """Add a new publication"""
    if request.method == 'POST':
        form = PublicationForm(request.POST, request.FILES)
        if form.is_valid():
            publication = form.save(commit=False)
            publication.save()
            
            # Add authors
            author_emails = request.POST.get('author_emails', '').split(',')
            for idx, email in enumerate(author_emails):
                email = email.strip()
                if email:
                    try:
                        author_user = User.objects.get(email=email)
                        PublicationAuthor.objects.create(
                            publication=publication,
                            author=author_user,
                            order=idx + 1,
                            corresponding_author=idx == 0
                        )
                    except User.DoesNotExist:
                        pass
            
            # Add current user as author if not already
            if not PublicationAuthor.objects.filter(
                publication=publication,
                author=request.user
            ).exists():
                PublicationAuthor.objects.create(
                    publication=publication,
                    author=request.user,
                    order=len(author_emails) + 1
                )
            
            # Update member publication count
            try:
                member = Member.objects.get(user=request.user)
                member.publication_count = Publication.objects.filter(
                    members=request.user,
                    status='published'
                ).count()
                member.save()
            except Member.DoesNotExist:
                pass
            
            messages.success(request, 'Publication added successfully!')
            return redirect('profiles:edit_publications')
    else:
        form = PublicationForm()
    
    context = {
        'form': form,
        'page_title': 'Add Publication - KMPN',
        'publication_types': Publication.PUBLICATION_TYPES,
        'status_choices': Publication.STATUS_CHOICES,
    }
    return render(request, 'profiles/add_publication.html', context)


@login_required
def edit_publication(request, pub_id):
    """Edit publication"""
    publication = get_object_or_404(
        Publication,
        id=pub_id,
        members=request.user
    )
    
    if request.method == 'POST':
        form = PublicationForm(request.POST, request.FILES, instance=publication)
        if form.is_valid():
            form.save()
            messages.success(request, 'Publication updated successfully!')
            return redirect('profiles:edit_publications')
    else:
        form = PublicationForm(instance=publication)
    
    context = {
        'form': form,
        'publication': publication,
        'page_title': f'Edit {publication.title[:50]}',
    }
    return render(request, 'profiles/edit_publication.html', context)


@login_required
def delete_publication(request, pub_id):
    """Delete publication"""
    publication = get_object_or_404(
        Publication,
        id=pub_id,
        members=request.user
    )
    
    if request.method == 'POST':
        publication.delete()
        messages.success(request, 'Publication deleted successfully!')
        return redirect('profiles:edit_publications')
    
    context = {
        'publication': publication,
        'page_title': f'Delete Publication',
    }
    return render(request, 'profiles/delete_publication.html', context)


@login_required
def get_citation(request, pub_id):
    """Get citation for publication"""
    publication = get_object_or_404(Publication, id=pub_id)
    
    citation_format = request.GET.get('format', 'apa')
    citation = publication.get_citation(citation_format)
    
    return JsonResponse({
        'citation': citation,
        'format': citation_format
    })


# ============================================================
# RESEARCH INTERESTS VIEWS
# ============================================================

def research_interests(request):
    """View research interests"""
    interests = ResearchInterest.objects.filter(is_active=True)
    
    # Filter by category
    category = request.GET.get('category')
    if category:
        interests = interests.filter(category=category)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        interests = interests.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    paginator = Paginator(interests, 20)
    page = request.GET.get('page', 1)
    
    try:
        interests = paginator.page(page)
    except PageNotAnInteger:
        interests = paginator.page(1)
    except EmptyPage:
        interests = paginator.page(paginator.num_pages)
    
    # Get categories
    categories = ResearchInterest.objects.filter(
        is_active=True
    ).values_list('category', flat=True).distinct()
    
    context = {
        'interests': interests,
        'categories': [cat for cat in categories if cat],
        'page_title': 'Research Interests - KMPN',
    }
    return render(request, 'profiles/research_interests.html', context)


@login_required
def add_interest(request):
    """Add research interest to user profile"""
    if request.method == 'POST':
        interest_id = request.POST.get('interest_id')
        
        try:
            interest = ResearchInterest.objects.get(id=interest_id, is_active=True)
            
            # Add to user's research interests
            user = request.user
            if user.research_interests:
                interests = [i.strip() for i in user.research_interests.split(',') if i.strip()]
            else:
                interests = []
            
            if interest.name not in interests:
                interests.append(interest.name)
                user.research_interests = ', '.join(interests)
                user.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Added {interest.name} to your interests.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Interest already added.'
                })
        except ResearchInterest.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Interest not found.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'})


@login_required
def remove_interest(request):
    """Remove research interest from user profile"""
    if request.method == 'POST':
        interest_name = request.POST.get('interest_name')
        
        user = request.user
        if user.research_interests:
            interests = [i.strip() for i in user.research_interests.split(',') if i.strip()]
            
            if interest_name in interests:
                interests.remove(interest_name)
                user.research_interests = ', '.join(interests) if interests else ''
                user.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Removed {interest_name} from your interests.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Interest not found in your profile.'
                })
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'})


# ============================================================
# PROFILE VISIBILITY
# ============================================================

@login_required
def profile_visibility(request):
    """Manage profile visibility settings"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileVisibilityForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile visibility updated successfully!')
            return redirect('profiles:view', username=request.user.username)
    else:
        form = ProfileVisibilityForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
        'page_title': 'Profile Visibility - KMPN',
    }
    return render(request, 'profiles/visibility.html', context)


# ============================================================
# AJAX ENDPOINTS
# ============================================================

@login_required
def get_profile_completion(request):
    """Get profile completion percentage (AJAX)"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    completion = profile.calculate_completion()
    
    return JsonResponse({
        'completion': completion,
        'sections': {
            'basic': {
                'completed': bool(profile.user.first_name and profile.user.last_name),
                'total': 1
            },
            'academic': {
                'completed': bool(profile.user.institution and profile.user.department),
                'total': 2
            },
            'research': {
                'completed': bool(profile.research_statement or profile.user.research_interests),
                'total': 2
            },
            'skills': {
                'completed': bool(profile.user.bio),
                'total': 1
            },
            'publications': {
                'completed': Publication.objects.filter(members=profile.user).exists(),
                'total': 1
            }
        }
    })


@login_required
def get_publication_citation(request, pub_id):
    """Get publication citation in different formats"""
    publication = get_object_or_404(Publication, id=pub_id)
    
    formats = ['apa', 'mla', 'chicago', 'harvard']
    citations = {}
    
    for fmt in formats:
        citations[fmt] = publication.get_citation(fmt)
    
    return JsonResponse(citations)


@login_required
def search_publications(request):
    """Search publications (AJAX)"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    publications = Publication.objects.filter(
        status='published'
    ).filter(
        Q(title__icontains=query) |
        Q(abstract__icontains=query) |
        Q(keywords__icontains=query) |
        Q(journal_name__icontains=query) |
        Q(authors__email__icontains=query)
    ).distinct()[:10]
    
    results = []
    for pub in publications:
        authors = pub.get_authors_list()
        author_names = [author.author.get_full_name() for author in authors[:5]]
        author_str = ', '.join(author_names)
        if len(authors) > 5:
            author_str += ', et al.'
        
        results.append({
            'id': pub.id,
            'title': pub.title,
            'authors': author_str,
            'journal': pub.journal_name,
            'year': pub.publication_date.year if pub.publication_date else None,
            'type': pub.publication_type,
            'citation_count': pub.citation_count,
            'url': pub.url,
            'doi': pub.doi,
        })
    
    return JsonResponse({'results': results})


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
