from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.utils.decorators import method_decorator
from django.db.models import Sum, Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, date, timedelta
from decimal import Decimal

from accounts.decorators import family_required
from accounts.models import Family, FamilyMember
from .models import (
    Account, AccountHistory, WeeklyPeriod, BudgetTemplate,
    Allocation, Transaction, AccountLoan, LoanPayment, FamilySettings
)
from .forms import (
    AccountForm, AllocationForm, TransactionForm, 
    BudgetTemplateForm, FamilySettingsForm
)
from .utilities import (
    get_current_week, get_available_money, transfer_money,
    get_account_balance, get_account_tree
)


def app_permission_required(app_name):
    """Temporary decorator for app permissions - just checks family membership for now"""
    def decorator(view_func):
        return family_required(view_func)
    return decorator


def get_user_family(user):
    """Helper function to get user's family"""
    try:
        family_member = FamilyMember.objects.get(user=user)
        return family_member.family
    except FamilyMember.DoesNotExist:
        return None


def get_family_queryset(request, model_class):
    """Get queryset filtered by user's family"""
    family = get_user_family(request.user)
    if not family:
        return model_class.objects.none()
    return model_class.objects.filter(family=family)


# Dashboard View
@login_required
@family_required
@app_permission_required('budget_allocation')
def dashboard(request):
    """Main Budget Allocation Dashboard"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access budget allocation.")
        return redirect('accounts:dashboard')
    
    # Get current week
    today = date.today()
    # Find Monday of current week
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    current_week, created = WeeklyPeriod.objects.get_or_create(
        start_date=week_start,
        end_date=week_end,
        family=family,
        defaults={'is_active': True}
    )
    
    # Get account tree (root accounts only for display)
    root_accounts = Account.objects.filter(
        family=family, 
        parent__isnull=True,
        is_active=True
    ).order_by('account_type', 'sort_order', 'name')
    
    # Weekly summary
    week_allocations = Allocation.objects.filter(week=current_week)
    week_transactions = Transaction.objects.filter(week=current_week)
    total_allocated = week_allocations.aggregate(total=Sum('amount'))['total'] or 0
    total_income = week_transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = week_transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
    
    # Active loans
    active_loans = AccountLoan.objects.filter(family=family, is_active=True)
    
    context = {
        'title': 'Budget Allocation Dashboard',
        'family': family,
        'current_week': current_week,
        'root_accounts': root_accounts,
        'week_summary': {
            'total_allocated': total_allocated,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_flow': total_income - total_expenses,
        },
        'active_loans': active_loans,
        'recent_transactions': week_transactions.order_by('-transaction_date', '-created_at')[:5],
    }
    return render(request, 'budget_allocation/dashboard_clean.html', context)


# Account Views
@login_required
@family_required
@app_permission_required('budget_allocation')
def account_list(request):
    """List all accounts in hierarchical structure"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access accounts.")
        return redirect('accounts:dashboard')
    
    # Get all accounts for the family
    accounts = Account.objects.filter(family=family).order_by(
        'account_type', 'sort_order', 'name'
    )
    
    # Group by account type
    accounts_by_type = {}
    for account in accounts:
        if account.account_type not in accounts_by_type:
            accounts_by_type[account.account_type] = []
        accounts_by_type[account.account_type].append(account)
    
    context = {
        'title': 'Account Management',
        'family': family,
        'accounts_by_type': accounts_by_type,
        'account_types': Account.ACCOUNT_TYPE_CHOICES,
    }
    return render(request, 'budget_allocation/account/list.html', context)


@login_required
@family_required
@app_permission_required('budget_allocation')
def account_create(request):
    """Create a new account"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to create accounts.")
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = AccountForm(request.POST, family=family)
        if form.is_valid():
            account = form.save(commit=False)
            account.family = family
            account.save()
            
            # Create history entry
            AccountHistory.objects.create(
                account=account,
                family=family,
                action='created',
                new_value=account.name,
                notes=f'Account created by {request.user.get_full_name() or request.user.username}'
            )
            
            messages.success(request, f'Account "{account.name}" created successfully.')
            return redirect('budget_allocation:account_list')
        else:
            # Debug: print form errors
            print("Form validation failed:")
            for field, errors in form.errors.items():
                print(f"  {field}: {errors}")
            if hasattr(form, 'non_field_errors'):
                print(f"  Non-field errors: {form.non_field_errors()}")
            messages.error(request, "Please correct the errors below.")
    else:
        form = AccountForm(family=family)
    
    context = {
        'title': 'Create Account',
        'form': form,
        'family': family,
    }
    return render(request, 'budget_allocation/account/form.html', context)


@login_required
@family_required
@app_permission_required('budget_allocation')
def account_detail(request, pk):
    """Account detail view with transaction history"""
    family = get_user_family(request.user)
    account = get_object_or_404(Account, pk=pk, family=family)
    
    # Get transactions for this account
    transactions = Transaction.objects.filter(
        account=account
    ).order_by('-transaction_date', '-created_at')
    
    # Pagination
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Account balance (sum of income minus expenses)
    balance_data = Transaction.objects.filter(account=account).aggregate(
        income=Sum('amount', filter=Q(transaction_type='income')) or 0,
        expenses=Sum('amount', filter=Q(transaction_type='expense')) or 0
    )
    current_balance = (balance_data['income'] or 0) - (balance_data['expenses'] or 0)
    
    # Recent allocations
    recent_allocations_in = Allocation.objects.filter(
        to_account=account
    ).order_by('-created_at')[:5]
    
    recent_allocations_out = Allocation.objects.filter(
        from_account=account
    ).order_by('-created_at')[:5]
    
    # Account history
    history = AccountHistory.objects.filter(
        account=account
    ).order_by('-timestamp')[:10]
    
    context = {
        'title': f'{account.name} - Account Details',
        'account': account,
        'current_balance': current_balance,
        'transactions': page_obj,
        'recent_allocations_in': recent_allocations_in,
        'recent_allocations_out': recent_allocations_out,
        'history': history,
        'family': family,
    }
    return render(request, 'budget_allocation/account/detail.html', context)


@login_required
@family_required
@app_permission_required('budget_allocation')
def account_edit(request, pk):
    """Edit account details"""
    family = get_user_family(request.user)
    account = get_object_or_404(Account, pk=pk, family=family)
    
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account, family=family)
        if form.is_valid():
            old_name = account.name
            account = form.save()
            
            # Create history entry if name changed
            if old_name != account.name:
                AccountHistory.objects.create(
                    account=account,
                    family=family,
                    action='renamed',
                    old_value=old_name,
                    new_value=account.name,
                    notes=f'Account renamed by {request.user.get_full_name() or request.user.username}'
                )
            
            messages.success(request, f'Account "{account.name}" updated successfully.')
            return redirect('budget_allocation:account_detail', pk=account.pk)
    else:
        form = AccountForm(instance=account, family=family)
    
    context = {
        'title': f'Edit {account.name}',
        'form': form,
        'account': account,
        'family': family,
    }
    return render(request, 'budget_allocation/account/form.html', context)


# Allocation Views
@login_required
@family_required
@app_permission_required('budget_allocation')
def allocation_dashboard(request):
    """Weekly allocation interface - most important view"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access allocations.")
        return redirect('accounts:dashboard')
    
    # Get or create current week
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    current_week, created = WeeklyPeriod.objects.get_or_create(
        start_date=week_start,
        end_date=week_end,
        family=family,
        defaults={'is_active': True}
    )
    
    # Get budget templates for automatic allocation suggestions
    budget_templates = BudgetTemplate.objects.filter(
        family=family,
        is_active=True
    ).order_by('priority', 'account__name')
    
    # Get existing allocations for this week
    allocations = Allocation.objects.filter(
        week=current_week
    ).order_by('-created_at')
    
    # Get accounts for manual allocation
    accounts = Account.objects.filter(
        family=family,
        is_active=True
    ).order_by('account_type', 'sort_order', 'name')
    
    # Calculate total allocated vs available
    total_allocated = allocations.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get income accounts balance
    income_accounts = accounts.filter(account_type='income')
    available_income = 0
    for account in income_accounts:
        balance_data = Transaction.objects.filter(account=account).aggregate(
            income=Sum('amount', filter=Q(transaction_type='income')) or 0,
            expenses=Sum('amount', filter=Q(transaction_type='expense')) or 0
        )
        available_income += (balance_data['income'] or 0) - (balance_data['expenses'] or 0)
    
    context = {
        'title': 'Weekly Allocation Dashboard',
        'family': family,
        'current_week': current_week,
        'budget_templates': budget_templates,
        'allocations': allocations,
        'accounts': accounts,
        'total_allocated': total_allocated,
        'available_income': available_income,
        'remaining_to_allocate': available_income - total_allocated,
    }
    return render(request, 'budget_allocation/allocation/dashboard.html', context)


@login_required
@family_required
@app_permission_required('budget_allocation')
def create_allocation(request):
    """Create manual allocation"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to create allocations.")
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = AllocationForm(request.POST, family=family)
        if form.is_valid():
            allocation = form.save(commit=False)
            allocation.family = family
            
            # Auto-assign to current week if not specified
            if not allocation.week:
                today = date.today()
                week_start = today - timedelta(days=today.weekday())
                week_end = week_start + timedelta(days=6)
                
                current_week, created = WeeklyPeriod.objects.get_or_create(
                    start_date=week_start,
                    end_date=week_end,
                    family=family,
                    defaults={'is_active': True}
                )
                allocation.week = current_week
            
            allocation.save()
            
            messages.success(request, f'Allocation of ${allocation.amount} created successfully.')
            return redirect('budget_allocation:allocation_dashboard')
    else:
        form = AllocationForm(family=family)
    
    context = {
        'title': 'Create Allocation',
        'form': form,
        'family': family,
    }
    return render(request, 'budget_allocation/allocation/create.html', context)


# Transaction Views
@login_required
@family_required
@app_permission_required('budget_allocation')
def transaction_list(request):
    """List transactions with filtering"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access transactions.")
        return redirect('accounts:dashboard')
    
    transactions = Transaction.objects.filter(family=family)
    
    # Filtering
    account_filter = request.GET.get('account')
    transaction_type = request.GET.get('type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if account_filter:
        transactions = transactions.filter(account_id=account_filter)
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    if start_date:
        transactions = transactions.filter(transaction_date__gte=start_date)
    if end_date:
        transactions = transactions.filter(transaction_date__lte=end_date)
    
    transactions = transactions.order_by('-transaction_date', '-created_at')
    
    # Pagination
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get accounts for filter dropdown
    accounts = Account.objects.filter(family=family, is_active=True).order_by('name')
    
    context = {
        'title': 'Transaction History',
        'transactions': page_obj,
        'accounts': accounts,
        'family': family,
        'filters': {
            'account': account_filter,
            'type': transaction_type,
            'start_date': start_date,
            'end_date': end_date,
        }
    }
    return render(request, 'budget_allocation/transaction/list.html', context)


@login_required
@family_required
@app_permission_required('budget_allocation')
def transaction_create(request):
    """Create new transaction"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to create transactions.")
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, family=family)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.family = family
            
            # Auto-assign to current week if not specified
            if transaction.week_id is None:
                today = date.today()
                week_start = today - timedelta(days=today.weekday())
                week_end = week_start + timedelta(days=6)
                
                current_week, created = WeeklyPeriod.objects.get_or_create(
                    start_date=week_start,
                    end_date=week_end,
                    family=family,
                    defaults={'is_active': True}
                )
                transaction.week = current_week
            
            transaction.save()
            
            messages.success(request, f'Transaction "{transaction.description}" recorded successfully.')
            return redirect('budget_allocation:transaction_list')
    else:
        form = TransactionForm(family=family)
    
    context = {
        'title': 'Record Transaction',
        'form': form,
        'family': family,
    }
    return render(request, 'budget_allocation/transaction/create.html', context)


# Budget Template Views
@login_required
@family_required
@app_permission_required('budget_allocation')
def budget_template_list(request):
    """List and manage budget templates"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access budget templates.")
        return redirect('accounts:dashboard')
    
    templates = BudgetTemplate.objects.filter(
        family=family
    ).order_by('priority', 'account__name')
    
    context = {
        'title': 'Budget Templates',
        'templates': templates,
        'family': family,
    }
    return render(request, 'budget_allocation/budget_template/list.html', context)


@login_required
@family_required
@app_permission_required('budget_allocation')
def budget_template_create(request):
    """Create budget template"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to create budget templates.")
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = BudgetTemplateForm(request.POST, family=family)
        if form.is_valid():
            template = form.save(commit=False)
            template.family = family
            template.save()
            
            messages.success(request, f'Budget template for "{template.account.name}" created successfully.')
            return redirect('budget_allocation:budget_template_list')
    else:
        form = BudgetTemplateForm(family=family)
    
    context = {
        'title': 'Create Budget Template',
        'form': form,
        'family': family,
    }
    return render(request, 'budget_allocation/budget_template/create.html', context)


# Loan Views
@login_required
@family_required
@app_permission_required('budget_allocation')
def loan_list(request):
    """List active loans between accounts"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access loans.")
        return redirect('accounts:dashboard')
    
    active_loans = AccountLoan.objects.filter(
        family=family,
        is_active=True
    ).order_by('-loan_date')
    
    paid_loans = AccountLoan.objects.filter(
        family=family,
        is_active=False
    ).order_by('-loan_date')[:10]  # Show last 10 paid loans
    
    context = {
        'title': 'Account Loans',
        'active_loans': active_loans,
        'paid_loans': paid_loans,
        'family': family,
    }
    return render(request, 'budget_allocation/loan/list.html', context)


# Settings View
@login_required
@family_required
@app_permission_required('budget_allocation')
def family_settings(request):
    """Configure family budget allocation settings"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access settings.")
        return redirect('accounts:dashboard')
    
    settings_obj, created = FamilySettings.objects.get_or_create(
        family=family,
        defaults={
            'week_start_day': 1,  # Monday
            'default_interest_rate': 0.01,
            'notification_threshold': 100.00,
        }
    )
    
    if request.method == 'POST':
        form = FamilySettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Budget allocation settings updated successfully.')
            return redirect('budget_allocation:family_settings')
    else:
        form = FamilySettingsForm(instance=settings_obj)
    
    context = {
        'title': 'Budget Allocation Settings',
        'form': form,
        'settings': settings_obj,
        'family': family,
    }
    return render(request, 'budget_allocation/settings.html', context)


# Simplified API endpoints for future loan functionality
@login_required
@family_required
@app_permission_required('budget_allocation')
def accounts_api(request):
    """Get all accounts with their current balances"""
    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'error': 'Family not found'}, status=400)
    
    current_week = get_current_week(family)
    accounts = Account.objects.filter(family=family).order_by('sort_order')
    
    account_data = {}
    for account in accounts:
        balance = get_account_balance(account, current_week)
        account_data[str(account.pk)] = {
            'id': account.pk,
            'name': account.name,
            'balance': float(balance),
            'formatted_balance': f"${balance:,.2f}",
            'account_type': account.account_type
        }
    
    return JsonResponse(account_data)


@login_required
@family_required
@app_permission_required('budget_allocation')
def account_balance_api(request, account_id):
    """Get current account balance via AJAX"""
    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'error': 'Family not found'}, status=400)
    
    try:
        account = Account.objects.get(pk=account_id, family=family)
        current_week = get_current_week(family)
        balance = get_account_balance(account, current_week)
        
        return JsonResponse({
            'account_id': account.pk,
            'name': account.name,
            'balance': float(balance),
            'formatted_balance': f"${balance:,.2f}"
        })
    except Account.DoesNotExist:
        return JsonResponse({'error': 'Account not found'}, status=404)


@login_required
@family_required
@app_permission_required('budget_allocation')
def allocation_suggestions_api(request):
    """Get auto-allocation suggestions via AJAX"""
    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'error': 'Family not found'}, status=400)
    
    current_week = get_current_week(family)
    available_money = get_available_money(family, current_week)
    templates = BudgetTemplate.objects.filter(
        family=family,
        is_active=True
    ).order_by('priority')
    
    suggestions = []
    remaining_money = available_money
    
    for template in templates:
        if remaining_money <= 0:
            break
            
        if template.allocation_type == 'percentage' and template.percentage:
            suggested_amount = min(
                available_money * (template.percentage / 100),
                remaining_money
            )
        elif template.allocation_type == 'fixed' and template.weekly_amount:
            suggested_amount = min(template.weekly_amount, remaining_money)
        else:  # range or calculated
            suggested_amount = min(template.min_amount or 0, remaining_money)
        
        if suggested_amount and suggested_amount > 0:
            suggestions.append({
                'account_id': template.account.pk,
                'account_name': template.account.name,
                'amount': float(suggested_amount),
                'formatted_amount': f"${suggested_amount:,.2f}",
                'priority': template.priority,
                'allocation_type': template.allocation_type
            })
            remaining_money -= suggested_amount
    
    return JsonResponse({
        'suggestions': suggestions,
        'total_available': float(available_money),
        'remaining_after_suggestions': float(remaining_money)
    })


@login_required
@family_required
@app_permission_required('budget_allocation')
def week_summary_api(request):
    """Get current week financial summary via AJAX"""
    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'error': 'Family not found'}, status=400)
    
    current_week = get_current_week(family)
    
    # Calculate totals
    total_allocated = Allocation.objects.filter(
        week=current_week
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_income = Transaction.objects.filter(
        account__family=family,
        week=current_week,
        transaction_type='income'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_expenses = Transaction.objects.filter(
        account__family=family,
        week=current_week,
        transaction_type='expense'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    available_money = get_available_money(family, current_week)
    
    # Get account tree
    account_tree = get_account_tree(family)
    
    return JsonResponse({
        'week_start': current_week.start_date.strftime('%Y-%m-%d'),
        'week_end': current_week.end_date.strftime('%Y-%m-%d'),
        'total_allocated': float(total_allocated),
        'total_income': float(total_income),
        'total_expenses': float(total_expenses),
        'available_money': float(available_money),
        'account_tree': account_tree,
        'formatted_allocated': f"${total_allocated:,.2f}",
        'formatted_income': f"${total_income:,.2f}",
        'formatted_expenses': f"${total_expenses:,.2f}",
        'formatted_available': f"${available_money:,.2f}"
    })
