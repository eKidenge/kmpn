"""
KMPN Database Population Script
================================
This script populates the KMPN database with realistic test data including:
- Users (with different roles and profiles)
- Members (with verification status)
- Communities (with different types)
- Community Posts and Comments
- Opportunities (scholarships, jobs, grants)
- Events (conferences, webinars, workshops)
- Resources (guides, templates, tutorials)
- Forums and Forum Threads
- Research Collaborations
- Notifications
- Payments and Subscriptions

Usage:
    python manage.py shell < load_data.py
    or
    python manage.py runscript load_data (if django-extensions is installed)
"""

import os
import sys
import django
import random
import uuid
from datetime import datetime, timedelta, date
from decimal import Decimal
from faker import Faker
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.base import ContentFile
from django.db import transaction

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kmpn.settings')
django.setup()

# Initialize Faker
fake = Faker(['en_US', 'en_GB'])

# Import models
from accounts.models import User, UserActivityLog, UserDevice
from members.models import Member, MemberVerificationRequest, MemberActivity
from profiles.models import Profile, ResearchInterest, Publication, PublicationAuthor
from communities.models import Community, CommunityMember, CommunityPost, Comment, CommunityLike
from collaborations.models import CollaborationRequest, CollaborationApplication, SupervisorMatching
from forums.models import ForumCategory, ForumThread, ForumReply, ForumLike, ForumReport
from opportunities.models import Opportunity, OpportunityApplication, OpportunitySave
from resources.models import Resource, ResourceCategory, ResourceRating, ResourceDownload
from events.models import Event, EventRegistration
from notifications.models import Notification, NotificationPreference
from payments.models import Payment, Subscription
from newsletters.models import Newsletter, NewsletterSubscriber, NewsletterOpen, NewsletterClick
from analytics.models import PageView, UserActivityAnalytics
from admin_panel.models import SystemLog, Announcement

User = get_user_model()

# ============================================================
# CONFIGURATION
# ============================================================

NUM_USERS = 50
NUM_MEMBERS = 40
NUM_COMMUNITIES = 10
NUM_POSTS_PER_COMMUNITY = 8
NUM_COMMENTS_PER_POST = 5
NUM_OPPORTUNITIES = 20
NUM_EVENTS = 15
NUM_RESOURCES = 25
NUM_FORUM_CATEGORIES = 5
NUM_THREADS_PER_CATEGORY = 6
NUM_COLLABORATIONS = 10
NUM_NOTIFICATIONS = 100

# Kenya universities
KENYAN_UNIVERSITIES = [
    'University of Nairobi', 'Kenyatta University', 'Egerton University',
    'Jomo Kenyatta University of Agriculture and Technology', 'Moi University',
    'Strathmore University', 'University of Eastern Africa, Baraton',
    'Maseno University', 'Kisii University', 'Masinde Muliro University',
    'Dedan Kimathi University of Technology', 'Murang\'a University',
    'Chuka University', 'Laikipia University', 'South Eastern Kenya University',
    'Karatina University', 'Turkana University', 'Tharaka University',
    'Rongo University', 'Alupe University', 'Kirinyaga University',
    'Meru University of Science and Technology', 'Technical University of Kenya',
    'Multimedia University of Kenya', 'Co-operative University of Kenya'
]

# Research disciplines
RESEARCH_DISCIPLINES = [
    'Artificial Intelligence', 'Machine Learning', 'Computer Vision',
    'Natural Language Processing', 'Data Science', 'Cybersecurity',
    'Public Health', 'Epidemiology', 'Health Policy', 'Global Health',
    'Sustainable Agriculture', 'Food Security', 'Climate Change',
    'Environmental Science', 'Renewable Energy', 'Water Resources',
    'Economic Development', 'Public Policy', 'International Relations',
    'Conflict Resolution', 'Governance', 'Democracy Studies',
    'Education Technology', 'Curriculum Development', 'Educational Leadership',
    'Clinical Medicine', 'Pharmacology', 'Medical Education',
    'Molecular Biology', 'Genetics', 'Biotechnology', 'Bioinformatics',
    'Physics', 'Quantum Computing', 'Astrophysics', 'Materials Science',
    'Chemical Engineering', 'Petroleum Engineering', 'Civil Engineering',
    'Electrical Engineering', 'Mechanical Engineering'
]

# Opportunity types
OPPORTUNITY_TYPES = ['scholarship', 'phd_position', 'masters_position', 
                      'postdoc', 'grant', 'job', 'internship', 'training']

# Event types
EVENT_TYPES = ['conference', 'webinar', 'workshop', 'seminar', 'symposium', 
               'training', 'networking']

# Resource types
RESOURCE_TYPES = ['guide', 'template', 'tutorial', 'tool', 'ebook', 
                  'presentation', 'video']

# Forum categories
FORUM_CATEGORIES = [
    'Research Methods', 'Thesis Writing', 'Academic Publishing',
    'Career Development', 'Technology in Education'
]

# Community types
COMMUNITY_TYPES = ['academic', 'professional', 'research', 'special_interest', 'regional']

# User types
USER_TYPES = ['member', 'moderator', 'executive', 'admin']

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_random_item(items):
    """Get random item from list"""
    return random.choice(items)

def get_random_items(items, count=None):
    """Get random items from list"""
    if count is None:
        count = random.randint(1, min(5, len(items)))
    return random.sample(items, min(count, len(items)))

def random_date(start_date, end_date):
    """Generate random date between two dates"""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def random_datetime(start_date, end_date):
    """Generate random datetime between two datetimes"""
    delta = end_date - start_date
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start_date + timedelta(seconds=random_seconds)

def generate_username(email):
    """Generate username from email"""
    return email.split('@')[0][:30]

def get_client_ip():
    """Generate random IP address"""
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

# ============================================================
# 1. CREATE USERS
# ============================================================

@transaction.atomic
def create_users():
    """Create users with different roles"""
    print("Creating users...")
    users = []
    
    # Create superuser
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@kmpn.org',
            password='admin123',
            first_name='System',
            last_name='Administrator',
            user_type='admin',
            is_verified=True,
            email_verified=True,
            is_active=True,
            institution='KMPN Headquarters',
            bio='System administrator for the Kenya Masters and PhD Network.'
        )
        users.append(admin)
        print(f"  Created superuser: {admin.email}")
    
    # Create executives
    for i in range(5):
        email = f"executive{i+1}@kmpn.org"
        if not User.objects.filter(email=email).exists():
            user = User.objects.create_user(
                username=f"executive_{i+1}",
                email=email,
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                user_type='executive',
                is_verified=True,
                email_verified=True,
                is_active=True,
                institution=get_random_item(KENYAN_UNIVERSITIES),
                department=fake.job(),
                bio=fake.paragraph(nb_sentences=3),
                research_interests=', '.join(get_random_items(RESEARCH_DISCIPLINES, 3)),
                phone_number=fake.phone_number(),
                linkedin_url=fake.url(),
                google_scholar_url=fake.url()
            )
            users.append(user)
            print(f"  Created executive: {user.email}")
    
    # Create moderators
    for i in range(10):
        email = f"moderator{i+1}@kmpn.org"
        if not User.objects.filter(email=email).exists():
            user = User.objects.create_user(
                username=f"moderator_{i+1}",
                email=email,
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                user_type='moderator',
                is_verified=True,
                email_verified=True,
                is_active=True,
                institution=get_random_item(KENYAN_UNIVERSITIES),
                department=fake.job(),
                bio=fake.paragraph(nb_sentences=3),
                research_interests=', '.join(get_random_items(RESEARCH_DISCIPLINES, 3)),
                phone_number=fake.phone_number()
            )
            users.append(user)
            print(f"  Created moderator: {user.email}")
    
    # Create members
    for i in range(NUM_MEMBERS):
        email = f"member{i+1}@example.com"
        if not User.objects.filter(email=email).exists():
            user = User.objects.create_user(
                username=f"member_{i+1}",
                email=email,
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                user_type='member',
                is_verified=random.choice([True, False]),
                email_verified=True,
                is_active=True,
                institution=get_random_item(KENYAN_UNIVERSITIES),
                department=fake.job(),
                bio=fake.paragraph(nb_sentences=3),
                research_interests=', '.join(get_random_items(RESEARCH_DISCIPLINES, 3)),
                phone_number=fake.phone_number(),
                linkedin_url=fake.url() if random.choice([True, False]) else '',
                google_scholar_url=fake.url() if random.choice([True, False]) else '',
                orcid_id=f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}" if random.choice([True, False]) else ''
            )
            users.append(user)
            
            # Make some members verified
            if random.choice([True, False]):
                user.is_verified = True
                user.save()
            
            print(f"  Created member: {user.email}")
    
    print(f"Total users created: {len(users)}")
    return users

# ============================================================
# 2. CREATE MEMBER PROFILES
# ============================================================

@transaction.atomic
def create_member_profiles(users):
    """Create member profiles for all users"""
    print("\nCreating member profiles...")
    
    for user in users:
        if user.user_type == 'admin':
            continue
            
        member, created = Member.objects.get_or_create(
            user=user,
            defaults={
                'membership_type': get_random_item(['student', 'researcher', 'professional', 'alumni']),
                'membership_number': f"KMPN/{date.today().year}/{str(random.randint(1000, 9999))}/{uuid.uuid4().hex[:6].upper()}",
                'verification_status': get_random_item(['pending', 'verified', 'rejected']),
                'student_id_number': f"STU{random.randint(100000, 999999)}",
                'registration_number': f"REG{random.randint(100000, 999999)}",
                'year_of_study': random.randint(1, 6) if user.degree_level == 'masters' else random.randint(1, 8) if user.degree_level == 'phd' else None,
                'expected_graduation_year': random.randint(2025, 2030),
                'thesis_title': fake.sentence(nb_words=8) if random.choice([True, False]) else '',
                'thesis_abstract': fake.paragraph(nb_sentences=5) if random.choice([True, False]) else '',
                'supervisor_name': f"Prof. {fake.last_name()}" if random.choice([True, False]) else '',
                'supervisor_email': f"{fake.first_name().lower()}@university.ac.ke" if random.choice([True, False]) else '',
                'skills': get_random_items(['Python', 'R', 'SPSS', 'Stata', 'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision', 'Data Analysis', 'Statistics', 'Qualitative Research', 'Mixed Methods', 'Survey Design'], 4),
                'expertise_areas': get_random_items(RESEARCH_DISCIPLINES, 3),
                'programming_languages': get_random_items(['Python', 'R', 'Java', 'C++', 'JavaScript', 'MATLAB', 'SQL'], 2),
                'research_methodologies': get_random_items(['Quantitative', 'Qualitative', 'Mixed Methods', 'Case Study', 'Action Research', 'Experimental Design'], 2),
                'collaboration_interests': get_random_items(['Research', 'Funding', 'Mentorship', 'Publishing', 'Data Sharing'], 2),
                'mentoring_interests': get_random_items(['Undergraduate', 'Graduate', 'Postdoctoral', 'Early Career'], 2),
                'publication_count': random.randint(0, 20),
                'citation_count': random.randint(0, 100),
                'h_index': random.randint(0, 15),
                'card_issued_at': timezone.now() if random.choice([True, False]) else None,
                'card_expires_at': timezone.now() + timedelta(days=365) if random.choice([True, False]) else None
            }
        )
        
        if created:
            # Generate digital card if verified
            if member.verification_status == 'verified':
                member.generate_digital_card()
                member.generate_qr_code()
                member.save()
            
            print(f"  Created member profile for: {user.email}")
    
    print(f"Member profiles created")

# ============================================================
# 3. CREATE PROFILES
# ============================================================

@transaction.atomic
def create_profiles(users):
    """Create user profiles"""
    print("\nCreating user profiles...")
    
    for user in users:
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={
                'academic_bio': fake.paragraph(nb_sentences=5) if random.choice([True, False]) else '',
                'research_statement': fake.paragraph(nb_sentences=6) if random.choice([True, False]) else '',
                'teaching_interests': ', '.join(get_random_items(RESEARCH_DISCIPLINES, 3)) if random.choice([True, False]) else '',
                'current_position': fake.job() if random.choice([True, False]) else '',
                'current_employer': get_random_item(KENYAN_UNIVERSITIES) if random.choice([True, False]) else '',
                'years_of_experience': random.randint(1, 20) if random.choice([True, False]) else 0,
                'primary_research_area': get_random_item(RESEARCH_DISCIPLINES) if random.choice([True, False]) else '',
                'profile_visibility': get_random_item(['public', 'members_only', 'private']),
                'show_email': random.choice([True, False]),
                'show_phone': random.choice([True, False])
            }
        )
        profile.calculate_completion()
        print(f"  Created profile for: {user.email}")
    
    print(f"Profiles created")

# ============================================================
# 4. CREATE RESEARCH INTERESTS
# ============================================================

@transaction.atomic
def create_research_interests():
    """Create research interests"""
    print("\nCreating research interests...")
    
    categories = {
        'Computer Science': ['Artificial Intelligence', 'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision', 'Data Science', 'Cybersecurity', 'Cloud Computing'],
        'Engineering': ['Electrical Engineering', 'Mechanical Engineering', 'Civil Engineering', 'Chemical Engineering', 'Petroleum Engineering', 'Materials Science'],
        'Medical Sciences': ['Public Health', 'Epidemiology', 'Clinical Medicine', 'Pharmacology', 'Molecular Biology', 'Genetics', 'Biotechnology'],
        'Natural Sciences': ['Physics', 'Astrophysics', 'Chemistry', 'Biology', 'Environmental Science', 'Climate Science'],
        'Social Sciences': ['Economics', 'Political Science', 'Sociology', 'Psychology', 'Anthropology', 'Geography'],
        'Agriculture': ['Sustainable Agriculture', 'Food Security', 'Agronomy', 'Animal Science', 'Veterinary Medicine'],
        'Education': ['Education Technology', 'Curriculum Development', 'Educational Leadership', 'Special Education']
    }
    
    for category, interests in categories.items():
        for interest in interests:
            obj, created = ResearchInterest.objects.get_or_create(
                name=interest,
                defaults={
                    'description': fake.paragraph(nb_sentences=2),
                    'category': category,
                    'is_active': True
                }
            )
            if created:
                print(f"  Created research interest: {interest}")
    
    print(f"Research interests created")

# ============================================================
# 5. CREATE COMMUNITIES
# ============================================================

@transaction.atomic
def create_communities(users):
    """Create communities"""
    print("\nCreating communities...")
    
    community_names = [
        'AI Research Network', 'Public Health Forum', 'Data Science Hub',
        'Environmental Research Group', 'Education Innovation Lab',
        'Engineering Research Community', 'Medical Research Network',
        'Entrepreneurship & Innovation', 'Physics Research Group',
        'Social Sciences Forum', 'Climate Action Network',
        'Food Security Research', 'Cybersecurity Alliance',
        'Bioinformatics Community', 'Neuroscience Network'
    ]
    
    admin_users = [u for u in users if u.user_type in ['admin', 'executive', 'moderator']]
    
    for i, name in enumerate(community_names[:NUM_COMMUNITIES]):
        description = fake.paragraph(nb_sentences=5)
        community_type = get_random_item(COMMUNITY_TYPES)
        access_type = get_random_item(['public', 'members_only', 'private'])
        
        community, created = Community.objects.get_or_create(
            name=name,
            defaults={
                'description': description,
                'community_type': community_type,
                'access_type': access_type,
                'created_by': get_random_item(admin_users),
                'allow_member_posts': random.choice([True, False]),
                'require_moderation': random.choice([True, False]),
                'allow_attachments': random.choice([True, False]),
                'allow_discussions': random.choice([True, False]),
                'tags': get_random_items(['research', 'academic', 'collaboration', 'networking', 'innovation'], 3),
                'categories': get_random_items(['technology', 'science', 'humanities', 'health', 'education'], 2),
                'is_active': True
            }
        )
        
        if created:
            print(f"  Created community: {community.name}")
    
    print(f"Communities created")

# ============================================================
# 6. ADD MEMBERS TO COMMUNITIES
# ============================================================

@transaction.atomic
def add_community_members(users):
    """Add members to communities"""
    print("\nAdding members to communities...")
    
    communities = Community.objects.all()
    member_users = [u for u in users if u.user_type == 'member']
    
    for community in communities:
        # Add creator as admin
        CommunityMember.objects.get_or_create(
            community=community,
            user=community.created_by,
            defaults={'role': 'admin'}
        )
        
        # Add moderators
        moderators = [u for u in users if u.user_type == 'moderator']
        for mod in random.sample(moderators, min(2, len(moderators))):
            CommunityMember.objects.get_or_create(
                community=community,
                user=mod,
                defaults={'role': 'moderator'}
            )
        
        # Add regular members
        num_members = random.randint(10, 30)
        for user in random.sample(member_users, min(num_members, len(member_users))):
            member, created = CommunityMember.objects.get_or_create(
                community=community,
                user=user,
                defaults={
                    'role': 'member',
                    'joined_at': random_datetime(timezone.now() - timedelta(days=180), timezone.now())
                }
            )
            if created:
                community.member_count += 1
        
        community.save()
        print(f"  Added members to: {community.name} (Total: {community.member_count})")

# ============================================================
# 7. CREATE COMMUNITY POSTS
# ============================================================

@transaction.atomic
def create_community_posts():
    """Create posts in communities"""
    print("\nCreating community posts...")
    
    communities = Community.objects.all()
    post_types = ['discussion', 'question', 'announcement', 'resource', 'event', 'poll']
    
    for community in communities:
        members = CommunityMember.objects.filter(community=community).select_related('user')
        
        for i in range(random.randint(5, NUM_POSTS_PER_COMMUNITY)):
            author = random.choice(members).user if members.exists() else community.created_by
            
            post = CommunityPost.objects.create(
                community=community,
                author=author,
                title=fake.sentence(nb_words=8),
                content=fake.paragraph(nb_sentences=10),
                post_type=get_random_item(post_types),
                status=get_random_item(['published', 'pinned', 'archived']),
                view_count=random.randint(0, 500),
                comment_count=random.randint(0, 20),
                like_count=random.randint(0, 50),
                share_count=random.randint(0, 10),
                tags=get_random_items(['research', 'discussion', 'help', 'resource'], 2),
                created_at=random_datetime(timezone.now() - timedelta(days=90), timezone.now()),
                published_at=random_datetime(timezone.now() - timedelta(days=90), timezone.now())
            )
            
            community.post_count += 1
            
            # Create comments for this post
            for j in range(random.randint(0, NUM_COMMENTS_PER_POST)):
                if members.exists():
                    comment_author = random.choice(members).user
                    Comment.objects.create(
                        post=post,
                        author=comment_author,
                        content=fake.paragraph(nb_sentences=3),
                        like_count=random.randint(0, 10),
                        created_at=random_datetime(post.created_at, timezone.now())
                    )
            
            # Create some likes
            for _ in range(random.randint(0, 10)):
                if members.exists():
                    like_user = random.choice(members).user
                    if not CommunityLike.objects.filter(post=post, user=like_user).exists():
                        CommunityLike.objects.create(post=post, user=like_user)
        
        community.save()
        print(f"  Created posts for: {community.name} ({community.post_count} posts)")

# ============================================================
# 8. CREATE FORUM CATEGORIES AND THREADS
# ============================================================

@transaction.atomic
def create_forums(users):
    """Create forum categories and threads"""
    print("\nCreating forums...")
    
    member_users = [u for u in users if u.user_type in ['member', 'moderator']]
    
    for category_name in FORUM_CATEGORIES:
        category, created = ForumCategory.objects.get_or_create(
            name=category_name,
            defaults={
                'description': fake.paragraph(nb_sentences=2),
                'is_active': True,
                'requires_moderation': random.choice([True, False])
            }
        )
        
        if created:
            print(f"  Created forum category: {category_name}")
        
        # Create threads
        for i in range(NUM_THREADS_PER_CATEGORY):
            author = random.choice(member_users)
            thread = ForumThread.objects.create(
                title=fake.sentence(nb_words=8),
                content=fake.paragraph(nb_sentences=8),
                category=category,
                author=author,
                status=get_random_item(['open', 'closed', 'pinned']),
                is_sticky=random.choice([True, False]),
                is_locked=random.choice([True, False]),
                view_count=random.randint(0, 300),
                reply_count=random.randint(0, 15),
                like_count=random.randint(0, 20),
                tags=get_random_items(['help', 'discussion', 'resource', 'question'], 2),
                created_at=random_datetime(timezone.now() - timedelta(days=180), timezone.now()),
                last_activity=random_datetime(timezone.now() - timedelta(days=180), timezone.now())
            )
            
            category.thread_count += 1
            
            # Create replies
            for j in range(random.randint(0, 8)):
                reply_author = random.choice(member_users)
                ForumReply.objects.create(
                    thread=thread,
                    author=reply_author,
                    content=fake.paragraph(nb_sentences=4),
                    like_count=random.randint(0, 5),
                    created_at=random_datetime(thread.created_at, timezone.now())
                )
            
            category.save()
            
        print(f"  Created threads for: {category_name} ({category.thread_count} threads)")

# ============================================================
# 9. CREATE OPPORTUNITIES
# ============================================================

@transaction.atomic
def create_opportunities(users):
    """Create opportunities"""
    print("\nCreating opportunities...")
    
    admin_users = [u for u in users if u.user_type in ['admin', 'executive', 'moderator']]
    
    opportunity_titles = [
        'DAAD Masters Scholarship 2024', 'German Academic Exchange PhD Scholarship',
        'Wellcome Trust Research Fellowship', 'African Union Postdoctoral Fellowship',
        'World Bank Graduate Scholarship', 'Mastercard Foundation Scholars Program',
        'Google AI Research Internship', 'Microsoft Research PhD Fellowship',
        'UNECA Research Consultant', 'World Health Organization Internship',
        'International Development Research Centre (IDRC) Grant',
        'African Development Bank Research Grant', 'EU Horizon 2020 Research Grant',
        'National Research Fund Kenya - Call for Proposals',
        'Endeavour Scholarships and Fellowships', 'Japan Government MEXT Scholarship',
        'Commonwealth PhD Scholarships', 'Fulbright Graduate Study Program',
        'Rhodes Scholarships', 'Chevening Scholarships'
    ]
    
    for i in range(NUM_OPPORTUNITIES):
        title = random.choice(opportunity_titles) if i < len(opportunity_titles) else fake.sentence(nb_words=6)
        opportunity_type = get_random_item(OPPORTUNITY_TYPES)
        deadline = timezone.now() + timedelta(days=random.randint(7, 90))
        
        opportunity, created = Opportunity.objects.get_or_create(
            title=title,
            defaults={
                'description': fake.paragraph(nb_sentences=10),
                'opportunity_type': opportunity_type,
                'status': get_random_item(['published', 'draft', 'expired']),
                'organization_name': fake.company(),
                'organization_website': fake.url(),
                'location': fake.city(),
                'country': get_random_item(['Kenya', 'USA', 'UK', 'Germany', 'Canada', 'Australia', 'Netherlands']),
                'is_remote': random.choice([True, False]),
                'application_deadline': deadline,
                'start_date': deadline + timedelta(days=random.randint(30, 90)),
                'end_date': deadline + timedelta(days=random.randint(120, 200)),
                'has_funding': random.choice([True, False]),
                'funding_amount': Decimal(random.randint(1000, 50000)) if random.choice([True, False]) else None,
                'currency': get_random_item(['KES', 'USD', 'EUR']),
                'funding_details': fake.paragraph(nb_sentences=3) if random.choice([True, False]) else '',
                'eligibility_criteria': fake.paragraph(nb_sentences=5),
                'required_qualifications': fake.paragraph(nb_sentences=4),
                'preferred_qualifications': fake.paragraph(nb_sentences=3),
                'application_requirements': fake.paragraph(nb_sentences=4),
                'required_documents': get_random_items(['CV', 'Cover Letter', 'Transcripts', 'Research Proposal', 'Recommendation Letters', 'Publication List'], 4),
                'application_url': fake.url() if random.choice([True, False]) else '',
                'application_email': fake.email() if random.choice([True, False]) else '',
                'application_instructions': fake.paragraph(nb_sentences=3),
                'contact_person': fake.name(),
                'contact_email': fake.email(),
                'contact_phone': fake.phone_number(),
                'tags': get_random_items(['scholarship', 'research', 'funding', 'career', 'international'], 3),
                'disciplines': get_random_items(RESEARCH_DISCIPLINES, 3),
                'view_count': random.randint(0, 300),
                'application_count': random.randint(0, 50),
                'save_count': random.randint(0, 20),
                'created_by': get_random_item(admin_users),
                'is_verified': random.choice([True, False]),
                'verified_at': timezone.now() if random.choice([True, False]) else None
            }
        )
        
        if created:
            # Create some applications
            member_users = [u for u in users if u.user_type == 'member']
            for applicant in random.sample(member_users, min(random.randint(0, 10), len(member_users))):
                OpportunityApplication.objects.create(
                    opportunity=opportunity,
                    applicant=applicant,
                    cover_letter=fake.paragraph(nb_sentences=5),
                    message=fake.paragraph(nb_sentences=3),
                    status=get_random_item(['pending', 'reviewing', 'shortlisted', 'accepted', 'rejected']),
                    created_at=random_datetime(opportunity.created_at, timezone.now())
                )
            
            # Create some saves
            for user in random.sample(member_users, min(random.randint(0, 5), len(member_users))):
                OpportunitySave.objects.create(
                    opportunity=opportunity,
                    user=user
                )
            
            print(f"  Created opportunity: {opportunity.title[:50]}...")

# ============================================================
# 10. CREATE EVENTS
# ============================================================

@transaction.atomic
def create_events(users):
    """Create events"""
    print("\nCreating events...")
    
    admin_users = [u for u in users if u.user_type in ['admin', 'executive', 'moderator']]
    
    event_titles = [
        'East African Postgraduate Conference 2024',
        'KMPN Annual Research Symposium',
        'AI and Machine Learning in Africa - Webinar Series',
        'Public Health Research Workshop',
        'Data Science for Social Good - Conference',
        'Climate Change Research Forum',
        'Entrepreneurship in Academia - Seminar',
        'Research Methodology Training Program',
        'Academic Publishing Workshop',
        'Career Development in Research - Panel Discussion',
        'Sustainable Agriculture Conference',
        'Digital Health Innovation Summit',
        'Women in STEM Conference',
        'Policy Research and Advocacy Workshop',
        'International Development Research Symposium'
    ]
    
    for i in range(NUM_EVENTS):
        title = random.choice(event_titles) if i < len(event_titles) else fake.sentence(nb_words=6)
        start_date = timezone.now() + timedelta(days=random.randint(7, 120))
        end_date = start_date + timedelta(days=random.randint(1, 3))
        
        event, created = Event.objects.get_or_create(
            title=title,
            defaults={
                'slug': f"{title.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}",
                'description': fake.paragraph(nb_sentences=8),
                'event_type': get_random_item(EVENT_TYPES),
                'status': get_random_item(['published', 'ongoing', 'completed']),
                'organizer_name': fake.name(),
                'organizer_email': fake.email(),
                'organizer_phone': fake.phone_number(),
                'organizer_website': fake.url() if random.choice([True, False]) else '',
                'is_virtual': random.choice([True, False]),
                'venue': fake.street_address() if random.choice([True, False]) else '',
                'address': fake.street_address() if random.choice([True, False]) else '',
                'city': fake.city(),
                'country': 'Kenya',
                'virtual_link': fake.url() if random.choice([True, False]) else '',
                'start_date': start_date,
                'end_date': end_date,
                'registration_deadline': start_date - timedelta(days=random.randint(1, 14)),
                'max_attendees': random.randint(50, 500) if random.choice([True, False]) else None,
                'current_attendees': random.randint(0, 100),
                'requires_registration': random.choice([True, False]),
                'registration_fee': Decimal(random.randint(0, 5000)),
                'currency': 'KES',
                'registration_link': fake.url() if random.choice([True, False]) else '',
                'agenda': fake.paragraph(nb_sentences=5),
                'speakers': fake.paragraph(nb_sentences=4),
                'program': fake.paragraph(nb_sentences=6),
                'tags': get_random_items(['conference', 'workshop', 'research', 'networking'], 3),
                'view_count': random.randint(0, 200),
                'registration_count': random.randint(0, 50),
                'created_by': get_random_item(admin_users),
                'created_at': random_datetime(timezone.now() - timedelta(days=60), timezone.now())
            }
        )
        
        if created:
            # Create registrations
            member_users = [u for u in users if u.user_type == 'member']
            for attendee in random.sample(member_users, min(random.randint(0, 30), len(member_users))):
                EventRegistration.objects.create(
                    event=event,
                    user=attendee,
                    attendance_status=get_random_item(['pending', 'confirmed', 'attended', 'absent']),
                    created_at=random_datetime(event.created_at, timezone.now())
                )
            
            print(f"  Created event: {event.title[:50]}...")

# ============================================================
# 11. CREATE RESOURCES
# ============================================================

@transaction.atomic
def create_resources(users):
    """Create resources"""
    print("\nCreating resources...")
    
    admin_users = [u for u in users if u.user_type in ['admin', 'executive', 'moderator']]
    
    resource_titles = [
        'Research Proposal Writing Guide',
        'Thesis Template - University Format',
        'LaTeX Thesis Template',
        'Academic CV Template',
        'Grant Writing Workshop Materials',
        'Statistical Analysis with R - Tutorial',
        'Introduction to Python for Researchers',
        'Qualitative Research Methods Guide',
        'Systematic Literature Review Guide',
        'Data Management Plan Template',
        'Research Ethics Guidelines',
        'Academic Poster Template',
        'Journal Article Writing Guide',
        'Citation Management with Zotero',
        'Research Data Analysis with SPSS',
        'Introduction to Machine Learning for Research',
        'Deep Learning Fundamentals',
        'Natural Language Processing - A Researcher\'s Guide',
        'Computer Vision for Scientific Research',
        'Advanced Statistical Methods',
        'Research Impact and Knowledge Translation',
        'Grant Proposal Writing Workshop Materials',
        'Academic Presentation Skills',
        'Research Collaboration Guide',
        'Publishing in High-Impact Journals'
    ]
    
    categories = ResourceCategory.objects.all()
    if not categories.exists():
        # Create categories
        category_names = ['Guides', 'Templates', 'Tutorials', 'Tools', 'E-Books', 'Presentations']
        for cat_name in category_names:
            ResourceCategory.objects.create(
                name=cat_name,
                description=fake.paragraph(nb_sentences=2),
                is_active=True
            )
        categories = ResourceCategory.objects.all()
    
    for i in range(NUM_RESOURCES):
        title = random.choice(resource_titles) if i < len(resource_titles) else fake.sentence(nb_sentences=4)
        
        resource, created = Resource.objects.get_or_create(
            title=title,
            defaults={
                'slug': f"{title.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}",
                'description': fake.paragraph(nb_sentences=4),
                'resource_type': get_random_item(RESOURCE_TYPES),
                'access_type': get_random_item(['public', 'members_only', 'premium']),
                'content': fake.paragraph(nb_sentences=8),
                'author': fake.name(),
                'author_email': fake.email(),
                'publisher': get_random_item(KENYAN_UNIVERSITIES),
                'publication_date': random_date(date(2020, 1, 1), date.today()),
                'version': f"{random.randint(1, 3)}.{random.randint(0, 9)}",
                'keywords': get_random_items(RESEARCH_DISCIPLINES, 4),
                'view_count': random.randint(0, 500),
                'download_count': random.randint(0, 100),
                'like_count': random.randint(0, 50),
                'rating_count': random.randint(0, 20),
                'average_rating': random.uniform(3, 5),
                'is_published': random.choice([True, False]),
                'is_featured': random.choice([True, False]),
                'created_by': get_random_item(admin_users),
                'created_at': random_datetime(timezone.now() - timedelta(days=180), timezone.now())
            }
        )
        
        if created:
            # Add categories
            for cat in random.sample(list(categories), min(random.randint(1, 3), categories.count())):
                resource.categories.add(cat)
            
            # Create ratings
            member_users = [u for u in users if u.user_type == 'member']
            for user in random.sample(member_users, min(random.randint(0, 10), len(member_users))):
                ResourceRating.objects.get_or_create(
                    resource=resource,
                    user=user,
                    defaults={
                        'rating': random.randint(1, 5),
                        'review': fake.paragraph(nb_sentences=2) if random.choice([True, False]) else ''
                    }
                )
            
            print(f"  Created resource: {resource.title[:50]}...")

# ============================================================
# 12. CREATE NOTIFICATIONS
# ============================================================

@transaction.atomic
def create_notifications(users):
    """Create notifications"""
    print("\nCreating notifications...")
    
    notification_types = ['system', 'event', 'opportunity', 'community', 'message', 
                          'collaboration', 'member', 'payment', 'reminder', 'alert', 'forum', 'resource']
    
    for user in users:
        if user.user_type == 'admin':
            continue
            
        # Create notification preference
        NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'email_enabled': random.choice([True, False]),
                'sms_enabled': random.choice([True, False]),
                'push_enabled': random.choice([True, False]),
                'in_app_enabled': random.choice([True, False]),
                'event_notifications': random.choice([True, False]),
                'opportunity_notifications': random.choice([True, False]),
                'community_notifications': random.choice([True, False]),
                'message_notifications': random.choice([True, False]),
                'collaboration_notifications': random.choice([True, False]),
                'membership_notifications': random.choice([True, False]),
                'payment_notifications': random.choice([True, False]),
                'reminder_notifications': random.choice([True, False]),
                'quiet_hours_enabled': random.choice([True, False]),
                'quiet_hours_start': datetime(2020, 1, 1, 22, 0, 0).time() if random.choice([True, False]) else None,
                'quiet_hours_end': datetime(2020, 1, 1, 6, 0, 0).time() if random.choice([True, False]) else None,
                'digest_enabled': random.choice([True, False]),
                'digest_frequency': get_random_item(['daily', 'weekly', 'monthly'])
            }
        )
        
        # Create notifications
        for i in range(random.randint(5, 15)):
            notification_type = get_random_item(notification_types)
            is_read = random.choice([True, False])
            
            Notification.objects.create(
                user=user,
                notification_type=notification_type,
                priority=get_random_item(['low', 'medium', 'high']),
                title=fake.sentence(nb_words=6),
                message=fake.paragraph(nb_sentences=2),
                link=fake.url() if random.choice([True, False]) else '',
                is_read=is_read,
                read_at=timezone.now() if is_read else None,
                created_at=random_datetime(timezone.now() - timedelta(days=30), timezone.now()),
                metadata={'source': 'load_data_script'}
            )
    
    print(f"Notifications created")

# ============================================================
# 13. CREATE COLLABORATIONS
# ============================================================

@transaction.atomic
def create_collaborations(users):
    """Create research collaborations"""
    print("\nCreating collaborations...")
    
    member_users = [u for u in users if u.user_type == 'member']
    
    collaboration_titles = [
        'AI in Healthcare Research Collaboration',
        'Climate Change Impact Study - Kenya',
        'Data Science for Public Health',
        'Sustainable Agriculture Research Network',
        'Early Childhood Education Research',
        'Renewable Energy Innovation Project',
        'Biodiversity Conservation Initiative',
        'Digital Transformation in Education',
        'Mental Health Research in Universities',
        'Food Security and Nutrition Study'
    ]
    
    for i in range(NUM_COLLABORATIONS):
        title = random.choice(collaboration_titles) if i < len(collaboration_titles) else fake.sentence(nb_words=6)
        requester = random.choice(member_users)
        
        collaboration, created = CollaborationRequest.objects.get_or_create(
            title=title,
            defaults={
                'description': fake.paragraph(nb_sentences=6),
                'collaboration_type': get_random_item(['research', 'co_authorship', 'data_collection', 'peer_review', 'mentorship']),
                'status': get_random_item(['open', 'pending', 'accepted', 'completed']),
                'requested_by': requester,
                'is_open': random.choice([True, False]),
                'required_skills': get_random_items(['Python', 'R', 'SPSS', 'Qualitative Analysis', 'Statistical Analysis'], 3),
                'required_expertise': get_random_items(RESEARCH_DISCIPLINES, 3),
                'required_institutions': get_random_items(KENYAN_UNIVERSITIES, 2),
                'start_date': date.today() + timedelta(days=random.randint(7, 30)),
                'end_date': date.today() + timedelta(days=random.randint(60, 180)),
                'duration_weeks': random.randint(4, 26),
                'is_remote': random.choice([True, False]),
                'location': fake.city() if random.choice([True, False]) else '',
                'country': 'Kenya',
                'has_funding': random.choice([True, False]),
                'funding_details': fake.paragraph(nb_sentences=3) if random.choice([True, False]) else '',
                'view_count': random.randint(0, 100),
                'application_count': random.randint(0, 10),
                'created_at': random_datetime(timezone.now() - timedelta(days=60), timezone.now())
            }
        )
        
        if created:
            # Create applications
            for applicant in random.sample(member_users, min(random.randint(0, 5), len(member_users))):
                if applicant != requester:
                    CollaborationApplication.objects.create(
                        collaboration=collaboration,
                        applicant=applicant,
                        cover_letter=fake.paragraph(nb_sentences=4),
                        skills=get_random_items(['Python', 'R', 'Research', 'Writing'], 3),
                        experience=fake.paragraph(nb_sentences=3),
                        availability=fake.paragraph(nb_sentences=2),
                        status=get_random_item(['pending', 'reviewing', 'accepted', 'rejected']),
                        created_at=random_datetime(collaboration.created_at, timezone.now())
                    )
            
            print(f"  Created collaboration: {collaboration.title[:50]}...")

# ============================================================
# 14. CREATE USER ACTIVITIES
# ============================================================

@transaction.atomic
def create_user_activities(users):
    """Create user activity logs"""
    print("\nCreating user activities...")
    
    action_types = ['login', 'logout', 'registration', 'profile_update', 'member_verification',
                    'community_join', 'event_registration', 'opportunity_apply', 'resource_download',
                    'forum_post', 'collaboration_request', 'payment']
    
    for user in users:
        for i in range(random.randint(5, 20)):
            UserActivityLog.objects.create(
                user=user,
                action_type=get_random_item(action_types),
                action_description=fake.sentence(nb_words=6),
                ip_address=get_client_ip(),
                user_agent=fake.user_agent(),
                created_at=random_datetime(timezone.now() - timedelta(days=90), timezone.now())
            )
    
    print(f"User activities created")

# ============================================================
# 15. CREATE PAYMENTS AND SUBSCRIPTIONS
# ============================================================

@transaction.atomic
def create_payments_and_subscriptions(users):
    """Create payments and subscriptions"""
    print("\nCreating payments and subscriptions...")
    
    member_users = [u for u in users if u.user_type == 'member']
    
    for user in member_users:
        # Create subscription
        subscription, created = Subscription.objects.get_or_create(
            user=user,
            defaults={
                'subscription_type': get_random_item(['free', 'basic', 'premium']),
                'status': get_random_item(['active', 'inactive', 'expired']),
                'price': Decimal(random.randint(0, 5000)),
                'currency': 'KES',
                'billing_cycle': get_random_item(['monthly', 'quarterly', 'yearly']),
                'start_date': random_datetime(timezone.now() - timedelta(days=180), timezone.now()),
                'end_date': random_datetime(timezone.now(), timezone.now() + timedelta(days=180)),
                'last_billing_date': random_datetime(timezone.now() - timedelta(days=30), timezone.now()),
                'next_billing_date': random_datetime(timezone.now(), timezone.now() + timedelta(days=30)),
                'auto_renew': random.choice([True, False]),
                'features': get_random_items(['premium_access', 'priority_support', 'exclusive_events'], 2)
            }
        )
        
        # Create payments
        for i in range(random.randint(1, 5)):
            Payment.objects.create(
                user=user,
                payment_type=get_random_item(['membership', 'event', 'donation', 'service']),
                payment_method=get_random_item(['mpesa', 'card', 'bank', 'paypal']),
                status=get_random_item(['completed', 'pending', 'failed']),
                amount=Decimal(random.randint(100, 10000)),
                currency='KES',
                transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
                reference_number=f"REF-{uuid.uuid4().hex[:8].upper()}",
                item_name=fake.sentence(nb_words=3),
                description=fake.paragraph(nb_sentences=2),
                completed_at=timezone.now() if random.choice([True, False]) else None
            )
    
    print(f"Payments and subscriptions created")

# ============================================================
# 16. CREATE NEWSLETTER SUBSCRIBERS
# ============================================================

@transaction.atomic
def create_newsletter_subscribers(users):
    """Create newsletter subscribers"""
    print("\nCreating newsletter subscribers...")
    
    for user in users:
        if user.user_type != 'admin':
            subscriber, created = NewsletterSubscriber.objects.get_or_create(
                email=user.email,
                defaults={
                    'name': user.get_full_name() or user.username,
                    'subscribed': random.choice([True, False]),
                    'user': user,
                    'groups': get_random_items(['members', 'researchers', 'alumni'], 2),
                    'opened_count': random.randint(0, 20),
                    'clicked_count': random.randint(0, 10),
                    'subscribed_at': random_datetime(timezone.now() - timedelta(days=180), timezone.now())
                }
            )
            
            if created:
                print(f"  Created newsletter subscriber: {user.email}")

# ============================================================
# 17. CREATE ANNOUNCEMENTS
# ============================================================

@transaction.atomic
def create_announcements(users):
    """Create announcements"""
    print("\nCreating announcements...")
    
    admin_users = [u for u in users if u.user_type in ['admin', 'executive']]
    
    announcement_titles = [
        'Welcome to KMPN - Kenya Masters and PhD Network',
        'New Features and Updates on KMPN Platform',
        'Call for Papers - East African Postgraduate Conference',
        'KMPN Annual Research Symposium - Registration Open',
        'New Scholarships and Funding Opportunities',
        'KMPN Community Guidelines Update',
        'Research Collaboration Opportunities',
        'Upcoming Webinars and Workshops',
        'KMPN Member Spotlight - Meet Our Scholars',
        'KMPN Strategic Plan 2025-2030'
    ]
    
    for title in announcement_titles:
        Announcement.objects.create(
            title=title,
            content=fake.paragraph(nb_sentences=5),
            priority=get_random_item(['low', 'medium', 'high', 'critical']),
            show_on_homepage=random.choice([True, False]),
            show_on_dashboard=random.choice([True, False]),
            show_to_all=random.choice([True, False]),
            start_date=random_datetime(timezone.now() - timedelta(days=30), timezone.now()),
            end_date=random_datetime(timezone.now(), timezone.now() + timedelta(days=30)) if random.choice([True, False]) else None,
            is_active=True,
            created_by=get_random_item(admin_users),
            created_at=random_datetime(timezone.now() - timedelta(days=60), timezone.now())
        )
    
    print(f"Announcements created")

# ============================================================
# 18. CREATE SYSTEM LOGS
# ============================================================

@transaction.atomic
def create_system_logs():
    """Create system logs"""
    print("\nCreating system logs...")
    
    log_levels = ['info', 'warning', 'error', 'critical']
    log_sources = ['system', 'user', 'payment', 'email', 'cron', 'api']
    
    for i in range(50):
        SystemLog.objects.create(
            level=get_random_item(log_levels),
            source=get_random_item(log_sources),
            message=fake.sentence(nb_words=8),
            details={'timestamp': timezone.now().isoformat()},
            ip_address=get_client_ip(),
            created_at=random_datetime(timezone.now() - timedelta(days=30), timezone.now())
        )
    
    print(f"System logs created")

# ============================================================
# 19. CREATE PAGE VIEWS (Analytics)
# ============================================================

@transaction.atomic
def create_page_views(users):
    """Create page views for analytics"""
    print("\nCreating page views...")
    
    pages = [
        '/', '/members/directory/', '/communities/', '/opportunities/', 
        '/events/', '/resources/', '/forums/', '/about/', '/contact/'
    ]
    
    for user in users:
        for i in range(random.randint(5, 20)):
            PageView.objects.create(
                page_url=get_random_item(pages),
                page_title=fake.sentence(nb_words=3),
                referer_url=fake.url() if random.choice([True, False]) else '',
                user=user if random.choice([True, False]) else None,
                session_id=uuid.uuid4().hex[:16],
                ip_address=get_client_ip(),
                user_agent=fake.user_agent(),
                device_type=get_random_item(['desktop', 'mobile', 'tablet']),
                browser=get_random_item(['Chrome', 'Firefox', 'Safari', 'Edge']),
                os=get_random_item(['Windows', 'macOS', 'Linux', 'Android', 'iOS']),
                country='Kenya',
                city=fake.city(),
                time_on_page=random.randint(5, 300),
                scroll_depth=random.randint(0, 100),
                bounce=random.choice([True, False]),
                created_at=random_datetime(timezone.now() - timedelta(days=30), timezone.now())
            )
    
    print(f"Page views created")

# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    """Main execution function"""
    print("=" * 60)
    print("KMPN DATABASE POPULATION SCRIPT")
    print("=" * 60)
    print(f"Starting at: {timezone.now()}")
    print()
    
    try:
        # Create all data
        users = create_users()
        create_member_profiles(users)
        create_profiles(users)
        create_research_interests()
        create_communities(users)
        add_community_members(users)
        create_community_posts()
        create_forums(users)
        create_opportunities(users)
        create_events(users)
        create_resources(users)
        create_notifications(users)
        create_collaborations(users)
        create_user_activities(users)
        create_payments_and_subscriptions(users)
        create_newsletter_subscribers(users)
        create_announcements(users)
        create_system_logs()
        create_page_views(users)
        
        print("\n" + "=" * 60)
        print("✅ DATA POPULATION COMPLETE!")
        print("=" * 60)
        print(f"Total Users: {User.objects.count()}")
        print(f"Total Members: {Member.objects.count()}")
        print(f"Total Communities: {Community.objects.count()}")
        print(f"Total Posts: {CommunityPost.objects.count()}")
        print(f"Total Opportunities: {Opportunity.objects.count()}")
        print(f"Total Events: {Event.objects.count()}")
        print(f"Total Resources: {Resource.objects.count()}")
        print(f"Total Forum Threads: {ForumThread.objects.count()}")
        print(f"Total Notifications: {Notification.objects.count()}")
        print(f"Total Collaborations: {CollaborationRequest.objects.count()}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()