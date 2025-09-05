"""
Subscription Tracker Views

Comprehensive views for subscription management with family scoping,
analytics, and integration with other apps.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, Count, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from django.urls import reverse
from datetime import date, datetime, timedelta
from decimal import Decimal
import json
import csv

from accounts.decorators import family_required
from accounts.models import Family, FamilyMember
from .models import (
    SubscriptionService, SubscriptionCategory, PaymentRecord,
    SubscriptionAlert, SubscriptionUsageLog
)
from .forms import (
    SubscriptionServiceForm, SubscriptionCategoryForm, QuickSubscriptionForm,
    SubscriptionFilterForm, BulkActionForm
)


def get_user_family(user):
    """Helper function to get user's family"""
    try:
        family_member = FamilyMember.objects.get(user=user)
        return family_member.family
    except FamilyMember.DoesNotExist:
        return None


@login_required
@family_required
def dashboard(request):
    """Main subscription dashboard with overview and analytics"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access subscriptions.")
        return redirect('accounts:family_join')
    
    # Get all subscriptions for this family
    subscriptions = SubscriptionService.objects.filter(family=family)
    
    # Quick statistics
    total_subscriptions = subscriptions.count()
    active_subscriptions = subscriptions.filter(status='active').count()
    
    # Calculate total monthly cost
    monthly_cost = Decimal('0.00')
    for sub in subscriptions.filter(status='active'):
        monthly_cost += sub.monthly_cost()
    
    # Get upcoming renewals (next 30 days)
    today = date.today()
    upcoming_renewals = []
    for sub in subscriptions.filter(status='active'):
        next_billing = sub.next_billing_date
        if next_billing and next_billing <= today + timedelta(days=30):
            upcoming_renewals.append(sub)
    
    # Recent activity
    recent_payments = PaymentRecord.objects.filter(
        subscription__family=family
    ).order_by('-payment_date')[:5]
    
    # Active alerts
    alerts = SubscriptionAlert.objects.filter(
        subscription__family=family,
        is_read=False
    ).order_by('-created_at')[:5]
    
    # Handle quick subscription form
    if request.method == 'POST':
        form = QuickSubscriptionForm(request.POST, family=family)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.family = family
            subscription.save()
            messages.success(request, f"Subscription '{subscription.name}' added successfully!")
            return redirect('subscription_tracker:dashboard')
    else:
        form = QuickSubscriptionForm(family=family)
    
    context = {
        'total_subscriptions': total_subscriptions,
        'active_subscriptions': active_subscriptions,
        'monthly_cost': monthly_cost,
        'annual_cost': monthly_cost * 12,
        'upcoming_renewals': upcoming_renewals[:5],
        'recent_payments': recent_payments,
        'alerts': alerts,
        'form': form,
        'subscriptions': subscriptions.filter(status='active')[:10],
    }
    
    return render(request, 'subscription_tracker/dashboard.html', context)


@login_required
@family_required  
def subscription_list(request):
    """List all subscriptions with filtering and pagination"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access subscriptions.")
        return redirect('accounts:family_join')
    
    subscriptions = SubscriptionService.objects.filter(family=family)
    
    # Apply filters
    filter_form = SubscriptionFilterForm(request.GET, family=family)
    if filter_form.is_valid():
        if filter_form.cleaned_data['category']:
            subscriptions = subscriptions.filter(category=filter_form.cleaned_data['category'])
        if filter_form.cleaned_data['status']:
            subscriptions = subscriptions.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data['search']:
            search = filter_form.cleaned_data['search']
            subscriptions = subscriptions.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search) |
                Q(website__icontains=search)
            )
    
    # Pagination
    paginator = Paginator(subscriptions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_count': subscriptions.count(),
    }
    
    return render(request, 'subscription_tracker/subscription_list.html', context)


@login_required
@family_required
def subscription_create(request):
    """Create a new subscription"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access subscriptions.")
        return redirect('accounts:family_join')
    
    if request.method == 'POST':
        form = SubscriptionServiceForm(request.POST, family=family)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.family = family
            subscription.save()
            messages.success(request, f"Subscription '{subscription.name}' created successfully!")
            return redirect('subscription_tracker:subscription_detail', pk=subscription.pk)
    else:
        form = SubscriptionServiceForm(family=family)
    
    context = {
        'form': form,
        'title': 'Add New Subscription',
    }
    
    return render(request, 'subscription_tracker/subscription_form.html', context)


@login_required
@family_required
def subscription_detail(request, pk):
    """View subscription details and payment history"""
    family = get_user_family(request.user)
    subscription = get_object_or_404(
        SubscriptionService, 
        pk=pk, 
        family=family
    )
    
    # Get payment history
    payments = PaymentRecord.objects.filter(
        subscription=subscription
    ).order_by('-payment_date')
    
    # Get alerts for this subscription
    alerts = SubscriptionAlert.objects.filter(
        subscription=subscription
    ).order_by('-created_at')
    
    # Calculate payment statistics
    total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    
    context = {
        'subscription': subscription,
        'payments': payments,
        'alerts': alerts,
        'total_paid': total_paid,
        'payment_count': payments.count(),
    }
    
    return render(request, 'subscription_tracker/subscription_detail.html', context)


@login_required
@family_required
def subscription_update(request, pk):
    """Update subscription details"""
    family = get_user_family(request.user)
    subscription = get_object_or_404(
        SubscriptionService, 
        pk=pk, 
        family=family
    )
    
    if request.method == 'POST':
        form = SubscriptionServiceForm(request.POST, instance=subscription, family=family)
        if form.is_valid():
            form.save()
            messages.success(request, f"Subscription '{subscription.name}' updated successfully!")
            return redirect('subscription_tracker:subscription_detail', pk=subscription.pk)
    else:
        form = SubscriptionServiceForm(instance=subscription, family=family)
    
    context = {
        'form': form,
        'subscription': subscription,
        'title': f'Edit {subscription.name}',
    }
    
    return render(request, 'subscription_tracker/subscription_form.html', context)


@login_required
@family_required
def subscription_delete(request, pk):
    """Delete a subscription"""
    family = get_user_family(request.user)
    subscription = get_object_or_404(
        SubscriptionService, 
        pk=pk, 
        family=family
    )
    
    if request.method == 'POST':
        subscription_name = subscription.name
        subscription.delete()
        messages.success(request, f"Subscription '{subscription_name}' deleted successfully!")
        return redirect('subscription_tracker:subscription_list')
    
    context = {
        'subscription': subscription,
    }
    
    return render(request, 'subscription_tracker/subscription_confirm_delete.html', context)


@login_required
@family_required
def category_list(request):
    """Manage subscription categories"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access subscriptions.")
        return redirect('accounts:family_join')
    
    categories = SubscriptionCategory.objects.filter(family=family)
    
    if request.method == 'POST':
        form = SubscriptionCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.family = family
            category.save()
            messages.success(request, f"Category '{category.name}' created successfully!")
            return redirect('subscription_tracker:category_list')
    else:
        form = SubscriptionCategoryForm()
    
    context = {
        'categories': categories,
        'form': form,
    }
    
    return render(request, 'subscription_tracker/category_list.html', context)


@login_required
@family_required
def cost_analysis(request):
    """Detailed cost analysis and reporting"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access subscriptions.")
        return redirect('accounts:family_join')
    
    subscriptions = SubscriptionService.objects.filter(family=family, status='active')
    
    # Calculate costs by period
    monthly_total = Decimal('0.00')
    
    # Category breakdown
    category_costs = {}
    
    for sub in subscriptions:
        monthly_cost = sub.monthly_cost()
        monthly_total += monthly_cost
        
        # Add to category totals
        category_name = sub.category.name if sub.category else 'Uncategorized'
        if category_name not in category_costs:
            category_costs[category_name] = Decimal('0.00')
        category_costs[category_name] += monthly_cost
    
    quarterly_total = monthly_total * 3
    annual_total = monthly_total * 12
    
    context = {
        'monthly_total': monthly_total,
        'quarterly_total': quarterly_total,
        'annual_total': annual_total,
        'category_costs': category_costs,
        'subscription_count': subscriptions.count(),
        'subscriptions': subscriptions,
    }
    
    return render(request, 'subscription_tracker/cost_analysis.html', context)


# AJAX Views
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def mark_payment_ajax(request):
    """Mark a payment as made via AJAX"""
    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'success': False, 'error': 'No family access'})
    
    try:
        subscription_id = request.POST.get('subscription_id')
        subscription = get_object_or_404(
            SubscriptionService, 
            pk=subscription_id, 
            family=family
        )
        
        # Create payment record
        payment = PaymentRecord.objects.create(
            subscription=subscription,
            amount=subscription.cost,
            payment_date=date.today(),
            payment_method='manual'
        )
        
        # Update next billing date
        subscription.mark_payment_made()
        
        return JsonResponse({
            'success': True,
            'message': f'Payment recorded for {subscription.name}',
            'next_billing_date': subscription.next_billing_date.isoformat() if subscription.next_billing_date else None
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def quick_add_subscription_ajax(request):
    """Quick add subscription via AJAX"""
    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'success': False, 'error': 'No family access'})
    
    try:
        form = QuickSubscriptionForm(request.POST, family=family)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.family = family
            subscription.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Subscription "{subscription.name}" added successfully!',
                'subscription': {
                    'id': subscription.id,
                    'name': subscription.name,
                    'cost': str(subscription.cost),
                    'monthly_cost': str(subscription.monthly_cost()),
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid form data',
                'errors': form.errors
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def bulk_actions(request):
    """Handle bulk actions on subscriptions"""
    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'success': False, 'error': 'No family access'})
    
    try:
        subscription_ids = request.POST.getlist('subscription_ids')
        action = request.POST.get('action')
        
        if subscription_ids and action:
            selected_subs = SubscriptionService.objects.filter(
                id__in=subscription_ids, 
                family=family
            )
            
            if action == 'cancel':
                selected_subs.update(status='cancelled')
                message = f"Cancelled {len(subscription_ids)} subscriptions."
            elif action == 'pause':
                selected_subs.update(status='paused')
                message = f"Paused {len(subscription_ids)} subscriptions."
            elif action == 'activate':
                selected_subs.update(status='active')
                message = f"Activated {len(subscription_ids)} subscriptions."
            else:
                return JsonResponse({'success': False, 'error': 'Invalid action'})
            
            return JsonResponse({'success': True, 'message': message})
        else:
            return JsonResponse({'success': False, 'error': 'No subscriptions or action specified'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def export_subscriptions_csv(request):
    """Export subscriptions to CSV"""
    family = get_user_family(request.user)
    if not family:
        return HttpResponse("No family access", status=403)
    
    subscriptions = SubscriptionService.objects.filter(family=family)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="subscriptions.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Name', 'Category', 'Cost', 'Billing Cycle', 'Status', 
        'Start Date', 'Next Billing', 'Website', 'Description'
    ])
    
    for sub in subscriptions:
        writer.writerow([
            sub.name,
            sub.category.name if sub.category else '',
            str(sub.cost),
            sub.billing_cycle,
            sub.status,
            sub.start_date.isoformat() if sub.start_date else '',
            sub.next_billing_date.isoformat() if sub.next_billing_date else '',
            sub.website_url,
            sub.description,
        ])
    
    return response


# Additional view aliases for URL compatibility
export_csv = export_subscriptions_csv
quick_add_subscription = quick_add_subscription_ajax
mark_payment = mark_payment_ajax
