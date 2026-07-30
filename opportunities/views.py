# opportunities/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone
from .models import Opportunity, OpportunityApplication
from .forms import OpportunityForm, OpportunityApplicationForm


@login_required
def opportunity_create(request):
    """Create a new opportunity"""
    
    if request.method == 'POST':
        form = OpportunityForm(request.POST, request.FILES)
        
        # Debug: Print form errors
        if not form.is_valid():
            print("=" * 60)
            print("FORM ERRORS:")
            for field, errors in form.errors.items():
                print(f"  {field}: {', '.join(errors)}")
            print("=" * 60)
            print("POST DATA:")
            print(request.POST)
            print("=" * 60)
        
        if form.is_valid():
            try:
                opportunity = form.save(commit=False)
                opportunity.created_by = request.user
                opportunity.save()
                
                # Handle tags and disciplines (they are already cleaned by the form)
                # The form's clean methods handle the conversion to lists
                
                messages.success(request, 'Opportunity created successfully!')
                return redirect('opportunities:detail', opportunity.id)
            except Exception as e:
                messages.error(request, f'Error creating opportunity: {str(e)}')
                import traceback
                traceback.print_exc()
    else:
        form = OpportunityForm()
    
    context = {
        'form': form,
        'page_title': 'Post Opportunity - KPSN',
    }
    return render(request, 'opportunities/create.html', context)


@login_required
def opportunity_detail(request, opp_id):
    """View opportunity details"""
    
    opportunity = get_object_or_404(Opportunity, id=opp_id)
    
    # Increment view count
    opportunity.increment_view_count()
    
    # Check if user has applied
    has_applied = False
    if request.user.is_authenticated:
        has_applied = OpportunityApplication.objects.filter(
            opportunity=opportunity,
            applicant=request.user
        ).exists()
    
    context = {
        'opportunity': opportunity,
        'has_applied': has_applied,
        'page_title': opportunity.title,
    }
    return render(request, 'opportunities/detail.html', context)


def opportunity_list(request):
    """List all opportunities"""
    
    opportunities = Opportunity.objects.filter(status='published')
    
    # Filter by type
    opportunity_type = request.GET.get('type')
    if opportunity_type:
        opportunities = opportunities.filter(opportunity_type=opportunity_type)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        opportunities = opportunities.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(organization_name__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Sort
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['-created_at', 'application_deadline', '-application_count', '-view_count']:
        opportunities = opportunities.order_by(sort_by)
    else:
        opportunities = opportunities.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(opportunities, 12)
    page = request.GET.get('page', 1)
    
    try:
        opportunities = paginator.page(page)
    except PageNotAnInteger:
        opportunities = paginator.page(1)
    except EmptyPage:
        opportunities = paginator.page(paginator.num_pages)
    
    context = {
        'opportunities': opportunities,
        'page_title': 'Opportunities - KPSN',
    }
    return render(request, 'opportunities/list.html', context)


@login_required
def opportunity_apply(request, opp_id):
    """Apply for an opportunity"""
    
    opportunity = get_object_or_404(Opportunity, id=opp_id)
    
    # Check if already applied
    if OpportunityApplication.objects.filter(opportunity=opportunity, applicant=request.user).exists():
        messages.warning(request, 'You have already applied for this opportunity.')
        return redirect('opportunities:detail', opp_id)
    
    # Check if deadline has passed
    if opportunity.is_expired():
        messages.error(request, 'The application deadline for this opportunity has passed.')
        return redirect('opportunities:detail', opp_id)
    
    if request.method == 'POST':
        form = OpportunityApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.opportunity = opportunity
            application.applicant = request.user
            application.save()
            
            # Increment application count
            opportunity.application_count += 1
            opportunity.save()
            
            messages.success(request, 'Application submitted successfully!')
            return redirect('opportunities:detail', opp_id)
    else:
        form = OpportunityApplicationForm()
    
    context = {
        'form': form,
        'opportunity': opportunity,
        'page_title': f'Apply for {opportunity.title}',
    }
    return render(request, 'opportunities/apply.html', context)


@login_required
def my_applications(request):
    """View user's applications"""
    
    applications = OpportunityApplication.objects.filter(
        applicant=request.user
    ).select_related('opportunity').order_by('-created_at')
    
    paginator = Paginator(applications, 20)
    page = request.GET.get('page', 1)
    
    try:
        applications = paginator.page(page)
    except PageNotAnInteger:
        applications = paginator.page(1)
    except EmptyPage:
        applications = paginator.page(paginator.num_pages)
    
    context = {
        'applications': applications,
        'page_title': 'My Applications - KPSN',
    }
    return render(request, 'opportunities/my_applications.html', context)


@login_required
def opportunity_edit(request, opp_id):
    """Edit an opportunity"""
    
    opportunity = get_object_or_404(Opportunity, id=opp_id)
    
    # Check if user is the creator or admin
    if opportunity.created_by != request.user and request.user.role not in ['admin', 'super_admin']:
        messages.error(request, 'You do not have permission to edit this opportunity.')
        return redirect('opportunities:detail', opp_id)
    
    if request.method == 'POST':
        form = OpportunityForm(request.POST, request.FILES, instance=opportunity)
        if form.is_valid():
            form.save()
            messages.success(request, 'Opportunity updated successfully!')
            return redirect('opportunities:detail', opp_id)
    else:
        form = OpportunityForm(instance=opportunity)
    
    context = {
        'form': form,
        'opportunity': opportunity,
        'page_title': f'Edit {opportunity.title}',
    }
    return render(request, 'opportunities/create.html', context)


@login_required
def opportunity_delete(request, opp_id):
    """Delete an opportunity"""
    
    opportunity = get_object_or_404(Opportunity, id=opp_id)
    
    # Check if user is the creator or admin
    if opportunity.created_by != request.user and request.user.role not in ['admin', 'super_admin']:
        messages.error(request, 'You do not have permission to delete this opportunity.')
        return redirect('opportunities:detail', opp_id)
    
    if request.method == 'POST':
        opportunity.delete()
        messages.success(request, 'Opportunity deleted successfully!')
        return redirect('opportunities:list')
    
    context = {
        'opportunity': opportunity,
        'page_title': f'Delete {opportunity.title}',
    }
    return render(request, 'opportunities/delete.html', context)


@login_required
def saved_opportunities(request):
    """View saved opportunities"""
    
    saved = Opportunity.objects.filter(saves__user=request.user).order_by('-created_at')
    
    paginator = Paginator(saved, 12)
    page = request.GET.get('page', 1)
    
    try:
        saved = paginator.page(page)
    except PageNotAnInteger:
        saved = paginator.page(1)
    except EmptyPage:
        saved = paginator.page(paginator.num_pages)
    
    context = {
        'saved': saved,
        'page_title': 'Saved Opportunities - KPSN',
    }
    return render(request, 'opportunities/saved.html', context)


@login_required
def save_opportunity(request, opp_id):
    """Save or unsave an opportunity"""
    
    opportunity = get_object_or_404(Opportunity, id=opp_id)
    
    if request.method == 'POST':
        from .models import OpportunitySave
        
        save_record = OpportunitySave.objects.filter(
            opportunity=opportunity,
            user=request.user
        )
        
        if save_record.exists():
            save_record.delete()
            messages.success(request, 'Opportunity removed from saved.')
        else:
            OpportunitySave.objects.create(
                opportunity=opportunity,
                user=request.user
            )
            opportunity.save_count += 1
            opportunity.save()
            messages.success(request, 'Opportunity saved!')
        
        return redirect('opportunities:detail', opp_id)
    
    return redirect('opportunities:detail', opp_id)


@login_required
def moderate_opportunities(request):
    """Moderate opportunities (admin only)"""
    
    if request.user.role not in ['admin', 'super_admin', 'moderator']:
        messages.error(request, 'You do not have permission to moderate opportunities.')
        return redirect('opportunities:list')
    
    opportunities = Opportunity.objects.filter(status='draft').order_by('-created_at')
    
    paginator = Paginator(opportunities, 20)
    page = request.GET.get('page', 1)
    
    try:
        opportunities = paginator.page(page)
    except PageNotAnInteger:
        opportunities = paginator.page(1)
    except EmptyPage:
        opportunities = paginator.page(paginator.num_pages)
    
    context = {
        'opportunities': opportunities,
        'page_title': 'Moderate Opportunities - KPSN',
    }
    return render(request, 'opportunities/moderate.html', context)