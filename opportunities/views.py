from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone
from .models import Opportunity, OpportunityApplication, OpportunitySave
from .forms import OpportunityForm, OpportunityApplicationForm, OpportunityFilterForm
from accounts.decorators import user_activity_log, user_type_required
from notifications.models import Notification


def opportunity_list(request):
    """List all opportunities"""
    opportunities = Opportunity.objects.filter(
        status='published',
        application_deadline__gte=timezone.now()
    ).order_by('-created_at')
    
    # Filters
    filter_form = OpportunityFilterForm(request.GET)
    
    if filter_form.is_valid():
        opp_type = filter_form.cleaned_data.get('opportunity_type')
        if opp_type:
            opportunities = opportunities.filter(opportunity_type=opp_type)
        
        country = filter_form.cleaned_data.get('country')
        if country:
            opportunities = opportunities.filter(country__icontains=country)
        
        has_funding = filter_form.cleaned_data.get('has_funding')
        if has_funding == 'true':
            opportunities = opportunities.filter(has_funding=True)
        elif has_funding == 'false':
            opportunities = opportunities.filter(has_funding=False)
        
        search = filter_form.cleaned_data.get('search')
        if search:
            opportunities = opportunities.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(organization_name__icontains=search) |
                Q(tags__icontains=search)
            )
        
        sort_by = filter_form.cleaned_data.get('sort_by')
        if sort_by:
            opportunities = opportunities.order_by(sort_by)
    
    paginator = Paginator(opportunities, 10)
    page = request.GET.get('page', 1)
    
    try:
        opportunities = paginator.page(page)
    except PageNotAnInteger:
        opportunities = paginator.page(1)
    except EmptyPage:
        opportunities = paginator.page(paginator.num_pages)
    
    context = {
        'opportunities': opportunities,
        'filter_form': filter_form,
        'page_title': 'Opportunities - KMPN',
    }
    return render(request, 'opportunities/list.html', context)


@login_required
@user_activity_log('opportunity_create', 'Created opportunity')
def opportunity_create(request):
    """Create new opportunity"""
    if request.method == 'POST':
        form = OpportunityForm(request.POST, request.FILES)
        if form.is_valid():
            opportunity = form.save(commit=False)
            opportunity.created_by = request.user
            
            # Auto-verify for admins/moderators
            if request.user.user_type in ['admin', 'moderator']:
                opportunity.is_verified = True
                opportunity.verified_by = request.user
                opportunity.verified_at = timezone.now()
                opportunity.status = 'published'
            
            opportunity.save()
            
            messages.success(request, 'Opportunity created successfully!')
            return redirect('opportunities:detail', opp_id=opportunity.id)
    else:
        form = OpportunityForm()
    
    context = {
        'form': form,
        'page_title': 'Create Opportunity - KMPN',
    }
    return render(request, 'opportunities/create.html', context)


@login_required
def opportunity_detail(request, opp_id):
    """View opportunity detail"""
    opportunity = get_object_or_404(Opportunity, id=opp_id)
    
    # Increment view count
    opportunity.increment_view_count()
    
    # Check if user has applied
    has_applied = False
    is_saved = False
    if request.user.is_authenticated:
        has_applied = opportunity.applications.filter(
            applicant=request.user
        ).exists()
        is_saved = opportunity.saves.filter(
            user=request.user
        ).exists()
    
    context = {
        'opportunity': opportunity,
        'has_applied': has_applied,
        'is_saved': is_saved,
        'page_title': opportunity.title,
    }
    return render(request, 'opportunities/detail.html', context)


@login_required
@user_activity_log('opportunity_apply', 'Applied to opportunity')
def opportunity_apply(request, opp_id):
    """Apply to opportunity"""
    opportunity = get_object_or_404(Opportunity, id=opp_id)
    
    # Check if already applied
    if opportunity.applications.filter(applicant=request.user).exists():
        messages.warning(request, 'You have already applied to this opportunity.')
        return redirect('opportunities:detail', opp_id=opp_id)
    
    # Check deadline
    if opportunity.application_deadline and timezone.now() > opportunity.application_deadline:
        messages.error(request, 'The application deadline has passed.')
        return redirect('opportunities:detail', opp_id=opp_id)
    
    if request.method == 'POST':
        form = OpportunityApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.opportunity = opportunity
            application.applicant = request.user
            application.save()
            
            opportunity.application_count += 1
            opportunity.save()
            
            # Notify opportunity creator
            if opportunity.created_by != request.user:
                Notification.objects.create(
                    user=opportunity.created_by,
                    notification_type='opportunity',
                    title=f'New application for {opportunity.title[:50]}',
                    message=f'{request.user.get_full_name()} applied to your opportunity.',
                    link=f'/opportunities/{opportunity.id}/',
                    metadata={
                        'opportunity_id': opportunity.id,
                        'application_id': application.id
                    }
                )
            
            messages.success(request, 'Application submitted successfully!')
            return redirect('opportunities:detail', opp_id=opp_id)
    else:
        form = OpportunityApplicationForm()
    
    context = {
        'form': form,
        'opportunity': opportunity,
        'page_title': f'Apply to {opportunity.title}',
    }
    return render(request, 'opportunities/apply.html', context)


@login_required
def save_opportunity(request, opp_id):
    """Save or unsave opportunity"""
    opportunity = get_object_or_404(Opportunity, id=opp_id)
    
    # Check if already saved
    save, created = OpportunitySave.objects.get_or_create(
        opportunity=opportunity,
        user=request.user
    )
    
    if not created:
        save.delete()
        opportunity.save_count -= 1
        opportunity.save()
        saved = False
        message = 'Opportunity removed from saved list.'
    else:
        opportunity.save_count += 1
        opportunity.save()
        saved = True
        message = 'Opportunity saved successfully!'
    
    return JsonResponse({
        'saved': saved,
        'save_count': opportunity.save_count,
        'message': message
    })


@login_required
def my_applications(request):
    """View user's applications"""
    applications = OpportunityApplication.objects.filter(
        applicant=request.user
    ).select_related('opportunity').order_by('-created_at')
    
    context = {
        'applications': applications,
        'page_title': 'My Applications - KMPN',
    }
    return render(request, 'opportunities/my_applications.html', context)


@login_required
def saved_opportunities(request):
    """View saved opportunities"""
    saved = OpportunitySave.objects.filter(
        user=request.user
    ).select_related('opportunity').order_by('-created_at')
    
    context = {
        'saved': saved,
        'page_title': 'Saved Opportunities - KMPN',
    }
    return render(request, 'opportunities/saved.html', context)


@login_required
@user_type_required(['admin', 'moderator'])
def moderate_opportunities(request):
    """Moderate opportunities (admin only)"""
    opportunities = Opportunity.objects.filter(
        status='draft',
        is_verified=False
    ).order_by('-created_at')
    
    if request.method == 'POST':
        opp_id = request.POST.get('opportunity_id')
        action = request.POST.get('action')
        review_notes = request.POST.get('review_notes', '')
        
        opportunity = get_object_or_404(Opportunity, id=opp_id)
        
        if action == 'verify':
            opportunity.is_verified = True
            opportunity.verified_by = request.user
            opportunity.verified_at = timezone.now()
            opportunity.status = 'published'
            opportunity.save()
            
            # Notify creator
            if opportunity.created_by != request.user:
                Notification.objects.create(
                    user=opportunity.created_by,
                    notification_type='opportunity',
                    title=f'Your opportunity has been approved: {opportunity.title[:50]}',
                    message='Your opportunity has been approved and is now published.',
                    link=f'/opportunities/{opportunity.id}/',
                    metadata={
                        'opportunity_id': opportunity.id,
                        'action': 'approve'
                    }
                )
            
            messages.success(request, 'Opportunity verified and published!')
            
        elif action == 'reject':
            opportunity.status = 'archived'
            opportunity.save()
            
            # Notify creator
            if opportunity.created_by != request.user:
                Notification.objects.create(
                    user=opportunity.created_by,
                    notification_type='opportunity',
                    title=f'Your opportunity was not approved: {opportunity.title[:50]}',
                    message=f'Your opportunity was not approved. Reason: {review_notes}',
                    link=f'/opportunities/',
                    metadata={
                        'opportunity_id': opportunity.id,
                        'action': 'reject',
                        'notes': review_notes
                    }
                )
            
            messages.warning(request, 'Opportunity rejected.')
        
        return redirect('opportunities:moderate')
    
    context = {
        'opportunities': opportunities,
        'page_title': 'Moderate Opportunities - Admin',
    }
    return render(request, 'opportunities/moderate.html', context)