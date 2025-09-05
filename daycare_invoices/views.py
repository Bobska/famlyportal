"""
Daycare Invoice Tracker Views

Comprehensive views for daycare provider, child, invoice and payment management
with family scoping, financial reporting, and integration capabilities.
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
from calendar import monthrange

from accounts.decorators import family_required
from accounts.models import Family, FamilyMember
from core.models import PaymentStatusChoices, PaymentMethodChoices
from .models import DaycareProvider, Child, Invoice, Payment
from .forms import (
    DaycareProviderForm, ChildForm, InvoiceForm, PaymentForm,
    QuickInvoiceForm, InvoiceFilterForm, ProviderFilterForm, PaymentFilterForm
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
    """Main daycare dashboard with financial overview and quick actions"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access daycare invoices.")
        return redirect('accounts:family_join')
    
    # Get all family data
    providers = DaycareProvider.objects.filter(family=family)
    children = Child.objects.filter(family=family)
    invoices = Invoice.objects.filter(family=family)
    payments = Payment.objects.filter(family=family)
    
    # Financial calculations
    total_outstanding = invoices.filter(
        status__in=[PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL, PaymentStatusChoices.OVERDUE]
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    
    total_paid_payments = invoices.filter(
        status__in=[PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL, PaymentStatusChoices.OVERDUE]
    ).aggregate(
        total_paid=Sum('payment__amount')
    )['total_paid'] or Decimal('0.00')
    
    actual_outstanding = total_outstanding - total_paid_payments
    
    # This month's costs
    today = date.today()
    month_start = date(today.year, today.month, 1)
    this_month_invoices = invoices.filter(invoice_date__gte=month_start)
    this_month_total = this_month_invoices.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    
    # Upcoming due dates
    next_7_days = today + timedelta(days=7)
    next_14_days = today + timedelta(days=14)
    next_30_days = today + timedelta(days=30)
    
    due_next_7 = invoices.filter(
        due_date__range=[today, next_7_days],
        status__in=[PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL]
    ).order_by('due_date')
    
    due_next_14 = invoices.filter(
        due_date__range=[next_7_days + timedelta(days=1), next_14_days],
        status__in=[PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL]
    ).order_by('due_date')
    
    due_next_30 = invoices.filter(
        due_date__range=[next_14_days + timedelta(days=1), next_30_days],
        status__in=[PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL]
    ).order_by('due_date')
    
    # Overdue invoices
    overdue_invoices = invoices.filter(
        due_date__lt=today,
        status__in=[PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL]
    ).order_by('due_date')
    
    # Recent payments
    recent_payments = payments.order_by('-payment_date')[:5]
    
    # Provider breakdown
    provider_stats = []
    for provider in providers.filter(is_active=True):
        provider_invoices = invoices.filter(provider=provider)
        outstanding = provider_invoices.filter(
            status__in=[PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL, PaymentStatusChoices.OVERDUE]
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        paid_amount = provider_invoices.filter(
            status__in=[PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL, PaymentStatusChoices.OVERDUE]
        ).aggregate(total_paid=Sum('payment__amount'))['total_paid'] or Decimal('0.00')
        
        actual_outstanding = outstanding - paid_amount
        
        provider_stats.append({
            'provider': provider,
            'outstanding': actual_outstanding,
            'children_count': children.filter(provider=provider, is_enrolled=True).count()
        })
    
    # Children enrollment overview
    children_stats = []
    for child in children.filter(is_enrolled=True):
        child_invoices = invoices.filter(child=child)
        total_cost = child_invoices.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        outstanding = child_invoices.filter(
            status__in=[PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL, PaymentStatusChoices.OVERDUE]
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        paid_amount = child_invoices.filter(
            status__in=[PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL, PaymentStatusChoices.OVERDUE]
        ).aggregate(total_paid=Sum('payment__amount'))['total_paid'] or Decimal('0.00')
        
        actual_outstanding = outstanding - paid_amount
        
        children_stats.append({
            'child': child,
            'total_cost': total_cost,
            'outstanding': actual_outstanding
        })
    
    # Calculate average monthly cost (last 6 months)
    six_months_ago = date(today.year, today.month, 1) - timedelta(days=180)
    monthly_costs = []
    
    current_date = six_months_ago
    while current_date <= today:
        month_invoices = invoices.filter(
            invoice_date__year=current_date.year,
            invoice_date__month=current_date.month
        )
        month_total = month_invoices.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        monthly_costs.append(month_total)
        
        # Move to next month
        if current_date.month == 12:
            current_date = date(current_date.year + 1, 1, 1)
        else:
            current_date = date(current_date.year, current_date.month + 1, 1)
    
    average_monthly = sum(monthly_costs) / len(monthly_costs) if monthly_costs else Decimal('0.00')
    
    # Handle quick invoice form
    if request.method == 'POST' and 'quick_invoice' in request.POST:
        quick_form = QuickInvoiceForm(request.POST, family=family)
        if quick_form.is_valid():
            invoice = quick_form.save(commit=False)
            invoice.family = family
            invoice.save()
            messages.success(request, f"Quick invoice created for {invoice.child.full_name}!")
            return redirect('daycare_invoices:dashboard')
    else:
        quick_form = QuickInvoiceForm(family=family)
    
    context = {
        'total_outstanding': actual_outstanding,
        'this_month_total': this_month_total,
        'average_monthly': average_monthly,
        'due_next_7': due_next_7,
        'due_next_14': due_next_14,
        'due_next_30': due_next_30,
        'overdue_invoices': overdue_invoices,
        'recent_payments': recent_payments,
        'provider_stats': provider_stats,
        'children_stats': children_stats,
        'quick_form': quick_form,
        'active_providers': providers.filter(is_active=True).count(),
        'enrolled_children': children.filter(is_enrolled=True).count(),
        'total_invoices': invoices.count(),
        'total_payments': payments.count(),
    }
    
    return render(request, 'daycare_invoices/dashboard.html', context)


# Provider Management Views
@login_required
@family_required
def provider_list(request):
    """List all daycare providers with filtering"""
    family = get_user_family(request.user)
    if not family:
        return redirect('accounts:family_join')
    
    providers = DaycareProvider.objects.filter(family=family)
    
    # Apply filters
    filter_form = ProviderFilterForm(request.GET)
    if filter_form.is_valid():
        if filter_form.cleaned_data['search']:
            search = filter_form.cleaned_data['search']
            providers = providers.filter(
                Q(name__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(email__icontains=search)
            )
        if filter_form.cleaned_data['active_only']:
            providers = providers.filter(is_active=True)
    
    # Add statistics to each provider
    provider_stats = []
    for provider in providers:
        invoices = Invoice.objects.filter(provider=provider)
        outstanding = invoices.filter(
            status__in=[PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL, PaymentStatusChoices.OVERDUE]
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        paid_amount = invoices.filter(
            status__in=[PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL, PaymentStatusChoices.OVERDUE]
        ).aggregate(total_paid=Sum('payment__amount'))['total_paid'] or Decimal('0.00')
        
        actual_outstanding = outstanding - paid_amount
        children_count = Child.objects.filter(provider=provider, is_enrolled=True).count()
        
        provider_stats.append({
            'provider': provider,
            'outstanding': actual_outstanding,
            'children_count': children_count,
            'total_invoices': invoices.count()
        })
    
    context = {
        'provider_stats': provider_stats,
        'filter_form': filter_form,
    }
    
    return render(request, 'daycare_invoices/provider_list.html', context)


@login_required
@family_required
def provider_create(request):
    """Create a new daycare provider"""
    family = get_user_family(request.user)
    if not family:
        return redirect('accounts:family_join')
    
    if request.method == 'POST':
        form = DaycareProviderForm(request.POST, family=family)
        if form.is_valid():
            provider = form.save(commit=False)
            provider.family = family
            provider.save()
            messages.success(request, f"Provider '{provider.name}' created successfully!")
            return redirect('daycare_invoices:provider_detail', pk=provider.pk)
    else:
        form = DaycareProviderForm(family=family)
    
    context = {
        'form': form,
        'title': 'Add New Daycare Provider'
    }
    
    return render(request, 'daycare_invoices/provider_form.html', context)


@login_required
@family_required
def provider_detail(request, pk):
    """View provider details with invoice history"""
    family = get_user_family(request.user)
    provider = get_object_or_404(DaycareProvider, pk=pk, family=family)
    
    # Get provider statistics
    invoices = Invoice.objects.filter(provider=provider).order_by('-invoice_date')
    payments = Payment.objects.filter(invoice__provider=provider).order_by('-payment_date')
    children = Child.objects.filter(provider=provider)
    
    # Financial summary
    total_invoiced = invoices.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    
    outstanding = invoices.filter(
        status__in=[PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL, PaymentStatusChoices.OVERDUE]
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    
    paid_partial = invoices.filter(
        status__in=[PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL, PaymentStatusChoices.OVERDUE]
    ).aggregate(total_paid=Sum('payment__amount'))['total_paid'] or Decimal('0.00')
    
    actual_outstanding = outstanding - paid_partial
    
    # Recent activity
    recent_invoices = invoices[:5]
    recent_payments = payments[:5]
    
    context = {
        'provider': provider,
        'invoices': recent_invoices,
        'payments': recent_payments,
        'children': children,
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'outstanding': actual_outstanding,
        'invoice_count': invoices.count(),
        'payment_count': payments.count(),
        'children_count': children.filter(is_enrolled=True).count(),
    }
    
    return render(request, 'daycare_invoices/provider_detail.html', context)


@login_required
@family_required
def provider_update(request, pk):
    """Update provider details"""
    family = get_user_family(request.user)
    provider = get_object_or_404(DaycareProvider, pk=pk, family=family)
    
    if request.method == 'POST':
        form = DaycareProviderForm(request.POST, instance=provider, family=family)
        if form.is_valid():
            form.save()
            messages.success(request, f"Provider '{provider.name}' updated successfully!")
            return redirect('daycare_invoices:provider_detail', pk=provider.pk)
    else:
        form = DaycareProviderForm(instance=provider, family=family)
    
    context = {
        'form': form,
        'provider': provider,
        'title': f'Edit {provider.name}'
    }
    
    return render(request, 'daycare_invoices/provider_form.html', context)


# Invoice Management Views
@login_required
@family_required
def invoice_list(request):
    """List all invoices with filtering and pagination"""
    family = get_user_family(request.user)
    if not family:
        return redirect('accounts:family_join')
    
    invoices = Invoice.objects.filter(family=family).order_by('-invoice_date')
    
    # Apply filters
    filter_form = InvoiceFilterForm(request.GET, family=family)
    if filter_form.is_valid():
        if filter_form.cleaned_data['provider']:
            invoices = invoices.filter(provider=filter_form.cleaned_data['provider'])
        if filter_form.cleaned_data['child']:
            invoices = invoices.filter(child=filter_form.cleaned_data['child'])
        if filter_form.cleaned_data['status']:
            invoices = invoices.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data['date_range_start']:
            invoices = invoices.filter(invoice_date__gte=filter_form.cleaned_data['date_range_start'])
        if filter_form.cleaned_data['date_range_end']:
            invoices = invoices.filter(invoice_date__lte=filter_form.cleaned_data['date_range_end'])
        if filter_form.cleaned_data['amount_min']:
            invoices = invoices.filter(amount__gte=filter_form.cleaned_data['amount_min'])
        if filter_form.cleaned_data['amount_max']:
            invoices = invoices.filter(amount__lte=filter_form.cleaned_data['amount_max'])
        if filter_form.cleaned_data['overdue_only']:
            invoices = invoices.filter(
                due_date__lt=timezone.now().date(),
                status__in=[PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL]
            )
    
    # Pagination
    paginator = Paginator(invoices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_count': invoices.count(),
    }
    
    return render(request, 'daycare_invoices/invoice_list.html', context)


@login_required
@family_required
def invoice_create(request):
    """Create a new invoice"""
    family = get_user_family(request.user)
    if not family:
        return redirect('accounts:family_join')
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, family=family)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.family = family
            invoice.save()
            messages.success(request, f"Invoice created for {invoice.child.full_name}!")
            return redirect('daycare_invoices:invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(family=family)
    
    context = {
        'form': form,
        'title': 'Create New Invoice'
    }
    
    return render(request, 'daycare_invoices/invoice_form.html', context)


@login_required
@family_required
def invoice_detail(request, pk):
    """View detailed invoice with payment history"""
    family = get_user_family(request.user)
    invoice = get_object_or_404(Invoice, pk=pk, family=family)
    
    # Get payment history
    payments = Payment.objects.filter(invoice=invoice).order_by('-payment_date')
    
    # Calculate totals
    total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    remaining_balance = invoice.amount - total_paid
    
    context = {
        'invoice': invoice,
        'payments': payments,
        'total_paid': total_paid,
        'remaining_balance': remaining_balance,
        'payment_count': payments.count(),
        'is_overdue': invoice.is_overdue,
    }
    
    return render(request, 'daycare_invoices/invoice_detail.html', context)


@login_required
@family_required
def invoice_update(request, pk):
    """Update invoice details"""
    family = get_user_family(request.user)
    invoice = get_object_or_404(Invoice, pk=pk, family=family)
    
    # Prevent editing paid invoices
    if invoice.status == PaymentStatusChoices.PAID:
        messages.error(request, "Cannot edit paid invoices.")
        return redirect('daycare_invoices:invoice_detail', pk=invoice.pk)
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice, family=family)
        if form.is_valid():
            form.save()
            messages.success(request, f"Invoice updated successfully!")
            return redirect('daycare_invoices:invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice, family=family)
    
    context = {
        'form': form,
        'invoice': invoice,
        'title': f'Edit Invoice for {invoice.child.full_name}'
    }
    
    return render(request, 'daycare_invoices/invoice_form.html', context)


# Payment Management Views
@login_required
@family_required
def payment_list(request):
    """List all payments with filtering"""
    family = get_user_family(request.user)
    if not family:
        return redirect('accounts:family_join')
    
    payments = Payment.objects.filter(family=family).order_by('-payment_date')
    
    # Apply filters
    filter_form = PaymentFilterForm(request.GET, family=family)
    if filter_form.is_valid():
        if filter_form.cleaned_data['provider']:
            payments = payments.filter(invoice__provider=filter_form.cleaned_data['provider'])
        if filter_form.cleaned_data['child']:
            payments = payments.filter(invoice__child=filter_form.cleaned_data['child'])
        if filter_form.cleaned_data['method']:
            payments = payments.filter(method=filter_form.cleaned_data['method'])
        if filter_form.cleaned_data['date_range_start']:
            payments = payments.filter(payment_date__gte=filter_form.cleaned_data['date_range_start'])
        if filter_form.cleaned_data['date_range_end']:
            payments = payments.filter(payment_date__lte=filter_form.cleaned_data['date_range_end'])
    
    # Pagination
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_count': payments.count(),
    }
    
    return render(request, 'daycare_invoices/payment_list.html', context)


@login_required
@family_required
def payment_create(request, invoice_pk=None):
    """Record a new payment"""
    family = get_user_family(request.user)
    if not family:
        return redirect('accounts:family_join')
    
    invoice = None
    if invoice_pk:
        invoice = get_object_or_404(Invoice, pk=invoice_pk, family=family)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, family=family, invoice=invoice)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.family = family
            payment.save()
            messages.success(request, f"Payment of ${payment.amount} recorded successfully!")
            return redirect('daycare_invoices:payment_detail', pk=payment.pk)
    else:
        form = PaymentForm(family=family, invoice=invoice)
    
    context = {
        'form': form,
        'invoice': invoice,
        'title': 'Record Payment'
    }
    
    return render(request, 'daycare_invoices/payment_form.html', context)


@login_required
@family_required
def payment_detail(request, pk):
    """View payment details and generate receipt"""
    family = get_user_family(request.user)
    payment = get_object_or_404(Payment, pk=pk, family=family)
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'daycare_invoices/payment_detail.html', context)


# Reporting Views
@login_required
@family_required
def financial_report(request):
    """Financial summary and reporting"""
    family = get_user_family(request.user)
    if not family:
        return redirect('accounts:family_join')
    
    # Get date range from request
    year = int(request.GET.get('year', timezone.now().year))
    month = request.GET.get('month')
    
    invoices = Invoice.objects.filter(family=family)
    payments = Payment.objects.filter(family=family)
    
    if month:
        month = int(month)
        invoices = invoices.filter(invoice_date__year=year, invoice_date__month=month)
        payments = payments.filter(payment_date__year=year, payment_date__month=month)
    else:
        invoices = invoices.filter(invoice_date__year=year)
        payments = payments.filter(payment_date__year=year)
    
    # Calculate totals
    total_invoiced = invoices.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    
    context = {
        'year': year,
        'month': month,
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'invoice_count': invoices.count(),
        'payment_count': payments.count(),
    }
    
    return render(request, 'daycare_invoices/financial_report.html', context)


# AJAX Views
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def quick_invoice_ajax(request):
    """Create invoice via AJAX"""
    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'success': False, 'error': 'No family access'})
    
    try:
        form = QuickInvoiceForm(request.POST, family=family)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.family = family
            invoice.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Invoice created for {invoice.child.full_name}!',
                'invoice': {
                    'id': invoice.id,
                    'child': invoice.child.full_name,
                    'amount': str(invoice.amount),
                    'due_date': invoice.due_date.isoformat()
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
def mark_as_paid_ajax(request, pk):
    """Mark invoice as paid via AJAX"""
    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'success': False, 'error': 'No family access'})
    
    try:
        invoice = get_object_or_404(Invoice, pk=pk, family=family)
        
        if invoice.status == PaymentStatusChoices.PAID:
            return JsonResponse({'success': False, 'error': 'Invoice already paid'})
        
        # Create payment for full remaining amount
        remaining = invoice.remaining_balance
        if remaining <= 0:
            return JsonResponse({'success': False, 'error': 'No amount remaining'})
        
        payment = Payment.objects.create(
            invoice=invoice,
            family=family,
            amount=remaining,
            payment_date=timezone.now().date(),
            method=PaymentMethodChoices.CASH,
            notes='Marked as paid via quick action'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Payment of ${remaining} recorded for {invoice.child.full_name}',
            'payment_id': payment.pk,
            'new_status': invoice.status
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# URL aliases
quick_invoice = quick_invoice_ajax
mark_as_paid = mark_as_paid_ajax
