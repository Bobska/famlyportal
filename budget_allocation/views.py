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
    get_account_balance, get_account_balance_with_children, get_account_tree
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


def calculate_overall_balance(family, current_week=None):
    """Calculate overall balance: Total Income - Total Expenses"""
    if not current_week:
        try:
            from .utilities import get_current_week
            current_week = get_current_week(family)
        except Exception:
            # Fallback if get_current_week doesn't exist
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            
            current_week, created = WeeklyPeriod.objects.get_or_create(
                start_date=week_start,
                end_date=week_end,
                family=family,
                defaults={'is_active': True}
            )
    
    total_income = Transaction.objects.filter(
        account__family=family,
        account__account_type='income',
        week=current_week
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_expenses = Transaction.objects.filter(
        account__family=family,
        account__account_type='expense',
        week=current_week
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_balance': total_income - total_expenses,
    }


# Dashboard View
@login_required
@family_required
@app_permission_required('budget_allocation')
def dashboard(request):
    """Enhanced dashboard with auto-setup and intuitive display"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access budget allocation.")
        return redirect('accounts:dashboard')
    
    # Ensure default accounts exist
    from .utils import ensure_default_accounts_exist
    setup_result = ensure_default_accounts_exist(family)
    
    # Notify user if accounts were created
    if setup_result['created_count'] > 0:
        account_names = [acc.name for acc in setup_result['created_accounts']]
        messages.success(
            request, 
            f"Welcome! Created default accounts for your family: {', '.join(account_names)}"
        )
    
    # Get user-visible accounts (exclude root)
    income_accounts = Account.objects.filter(
        family=family, 
        account_type='income',
        is_active=True
    ).select_related('parent').order_by('sort_order', 'name')
    
    expense_accounts = Account.objects.filter(
        family=family, 
        account_type='expense',
        is_active=True
    ).select_related('parent').order_by('sort_order', 'name')
    
    # Get current week
    try:
        current_week = get_current_week(family)
    except AttributeError:
        # Fallback to existing logic if get_current_week method doesn't exist
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        current_week, created = WeeklyPeriod.objects.get_or_create(
            start_date=week_start,
            end_date=week_end,
            family=family,
            defaults={'is_active': True}
        )
    
    # Calculate overall balance
    overall_balance = calculate_overall_balance(family, current_week)
    
    # Weekly summary
    week_allocations = Allocation.objects.filter(week=current_week)
    week_transactions = Transaction.objects.filter(week=current_week)
    total_allocated = week_allocations.aggregate(total=Sum('amount'))['total'] or 0
    
    # Active loans
    active_loans = AccountLoan.objects.filter(family=family, is_active=True)
    
    context = {
        'title': 'Budget Allocation Dashboard',
        'family': family,
        'current_week': current_week,
        'income_accounts': income_accounts,
        'expense_accounts': expense_accounts,
        'overall_balance': overall_balance,
        'week_summary': {
            'total_allocated': total_allocated,
            'total_income': overall_balance.get('total_income', 0),
            'total_expenses': overall_balance.get('total_expenses', 0),
            'net_flow': overall_balance.get('net_balance', 0),
        },
        'active_loans': active_loans,
        'recent_transactions': week_transactions.order_by('-transaction_date', '-created_at')[:5],
        'setup_result': setup_result,
    }
    return render(request, 'budget_allocation/dashboard_clean.html', context)


# Account Views
@login_required
@family_required
@app_permission_required('budget_allocation')
def account_list(request):
    """Account list view with same layout as dashboard"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access accounts.")
        return redirect('accounts:dashboard')
    
    # Ensure default accounts exist
    from .utils import ensure_default_accounts_exist
    ensure_default_accounts_exist(family)
    
    # Get accounts organized by type (same as dashboard)
    # Only get parent accounts (accounts with no parent)
    income_accounts = Account.objects.filter(
        family=family, 
        account_type='income',
        is_active=True,
        parent__isnull=True  # Only parent accounts
    ).select_related('parent').prefetch_related('children').order_by('sort_order', 'name')
    
    expense_accounts = Account.objects.filter(
        family=family, 
        account_type='expense',
        is_active=True,
        parent__isnull=True  # Only parent accounts
    ).select_related('parent').prefetch_related('children').order_by('sort_order', 'name')
    
    # Get current week and calculate overall balance (same as dashboard)
    current_week = get_current_week(family)
    overall_balance = calculate_overall_balance(family, current_week)
    
    context = {
        'title': 'Account Management',
        'income_accounts': income_accounts,
        'expense_accounts': expense_accounts,
        'overall_balance': overall_balance,
        'current_week': current_week,
        'show_management_tools': True,  # Differentiate from dashboard
        'family': family,
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
@login_required
@family_required
@app_permission_required('budget_allocation')
def account_detail(request, account_id):
    """Enhanced account detail view with comprehensive management features"""
    family = get_user_family(request.user)
    account = get_object_or_404(Account, id=account_id, family=family)
    
    # Get current week for balance calculations
    current_week = get_current_week(family)
    
    # Get child accounts with their balances
    child_accounts = account.children.filter(is_active=True).order_by('sort_order', 'name')
    
    # Calculate account balance including child accounts for parent display
    account_balance = get_account_balance_with_children(account, current_week)
    
    # Calculate child account balances and create enriched data structure
    child_balances = {}
    enriched_child_accounts = []
    for child in child_accounts:
        balance = get_account_balance(child, current_week)
        child_balances[child.id] = balance
        # Create enriched data with balance included
        enriched_child_accounts.append({
            'account': child,
            'balance': balance
        })
    
    # Get recent transactions with pagination
    transactions = Transaction.objects.filter(
        account=account,
        family=family
    ).order_by('-transaction_date', '-created_at')
    
    # Pagination for transactions
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Recent allocations involving this account
    recent_allocations_in = Allocation.objects.filter(
        to_account=account,
        week__family=family
    ).order_by('-created_at')[:5]
    
    recent_allocations_out = Allocation.objects.filter(
        from_account=account,
        week__family=family
    ).order_by('-created_at')[:5]
    
    # Account activity history
    history = AccountHistory.objects.filter(
        account=account
    ).order_by('-timestamp')[:10]
    
    # Weekly activity summary (last 4 weeks)
    weekly_summary = []
    for i in range(4):
        week_start = current_week.start_date - timedelta(weeks=i)
        week_end = current_week.end_date - timedelta(weeks=i)
        
        week_transactions = transactions.filter(
            transaction_date__range=[week_start, week_end]
        )
        
        income = week_transactions.filter(transaction_type='income').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        expenses = week_transactions.filter(transaction_type='expense').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        weekly_summary.append({
            'week_start': week_start,
            'week_end': week_end,
            'income': income,
            'expenses': expenses,
            'net': income - expenses
        })
    
    context = {
        'title': f'{account.name} - Account Details',
        'account': account,
        'child_accounts': child_accounts,
        'enriched_child_accounts': enriched_child_accounts,
        'child_balances': child_balances,
        'account_balance': account_balance,
        'transactions': page_obj,
        'recent_allocations_in': recent_allocations_in,
        'recent_allocations_out': recent_allocations_out,
        'can_add_children': account.can_have_children,
        'history': history,
        'weekly_summary': weekly_summary,
        'current_week': current_week,
        'family': family,
    }
    return render(request, 'budget_allocation/account/detail.html', context)


@login_required
@family_required
@app_permission_required('budget_allocation')
def account_edit(request, account_id):
    """Edit account details"""
    family = get_user_family(request.user)
    account = get_object_or_404(Account, id=account_id, family=family)
    
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
            return redirect('budget_allocation:account_detail', account_id=account.id)
    else:
        form = AccountForm(instance=account, family=family)
    
    context = {
        'title': f'Edit {account.name}',
        'form': form,
        'account': account,
        'family': family,
    }
    return render(request, 'budget_allocation/account/form.html', context)


@login_required
@family_required
@app_permission_required('budget_allocation')
def add_child_account(request, parent_id):
    """Add child account to existing account"""
    family = get_user_family(request.user)
    parent_account = get_object_or_404(
        Account, 
        id=parent_id, 
        family=family
    )
    
    # Check if parent can have children
    if not parent_account.can_have_children:
        messages.error(request, f'Account "{parent_account.name}" cannot have child accounts.')
        return redirect('budget_allocation:account_detail', account_id=parent_account.pk)
    
    if request.method == 'POST':
        # Use the new ChildAccountForm
        from .forms import ChildAccountForm
        form = ChildAccountForm(request.POST, parent=parent_account)
        if form.is_valid():
            # The form's save method now handles setting parent, family, and account_type
            child_account = form.save()
            
            # Create history entry
            AccountHistory.objects.create(
                account=child_account,
                family=family,
                action='created',
                new_value=child_account.name,
                notes=f'Child account created under "{parent_account.name}" by {request.user.get_full_name() or request.user.username}'
            )
            
            messages.success(request, f'Account "{child_account.name}" created successfully!')
            return redirect('budget_allocation:account_detail', account_id=parent_account.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Pre-populate form with parent account info
        from .forms import ChildAccountForm
        form = ChildAccountForm(parent=parent_account)
    
    context = {
        'title': f'Add Child Account to {parent_account.name}',
        'form': form,
        'parent_account': parent_account,
        'family': family,
    }
    return render(request, 'budget_allocation/account/add_child.html', context)


@login_required
@family_required  
@app_permission_required('budget_allocation')
def edit_account(request, account_id):
    """Edit account details"""
    family = get_user_family(request.user)
    account = get_object_or_404(Account, id=account_id, family=family)
    
    if request.method == 'POST':
        # Use appropriate form based on whether it's a child account
        if account.parent:
            from .forms import ChildAccountForm
            form = ChildAccountForm(request.POST, instance=account, parent=account.parent)
        else:
            from .forms import AccountForm
            form = AccountForm(request.POST, instance=account, family=family)
            
        if form.is_valid():
            # Track what changed
            changed_fields = []
            for field in form.changed_data:
                old_value = getattr(account, field)
                changed_fields.append(f"{field}: {old_value} → {form.cleaned_data[field]}")
            
            updated_account = form.save()
            
            # Create history entry if changes were made
            if changed_fields:
                AccountHistory.objects.create(
                    account=updated_account,
                    family=family,
                    action='updated',
                    old_value="; ".join(changed_fields),
                    new_value=updated_account.name,
                    notes=f'Account updated by {request.user.get_full_name() or request.user.username}'
                )
            
            messages.success(request, f'Account "{updated_account.name}" updated successfully!')
            return redirect('budget_allocation:account_detail', account_id=updated_account.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Initialize form with current account data
        if account.parent:
            from .forms import ChildAccountForm
            form = ChildAccountForm(instance=account, parent=account.parent)
        else:
            from .forms import AccountForm
            form = AccountForm(instance=account, family=family)
    
    context = {
        'title': f'Edit Account: {account.name}',
        'form': form,
        'account': account,
        'family': family,
        'is_edit': True,
    }
    
    # Add parent_account to context when editing a child account
    if account.parent:
        context['parent_account'] = account.parent
    
    template = 'budget_allocation/account/add_child.html' if account.parent else 'budget_allocation/account/edit.html'
    return render(request, template, context)


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
    
    # Get merchant/payee accounts for modal dropdown
    merchant_accounts = Account.objects.filter(
        family=family, 
        is_merchant_payee=True,
        is_active=True
    ).order_by('name')
    
    # Get parent accounts for new account creation (income and expense root accounts)
    parent_income_accounts = Account.objects.filter(
        family=family,
        account_type='income',
        parent__isnull=True,  # Root income accounts
        is_active=True
    ).order_by('name')
    
    parent_expense_accounts = Account.objects.filter(
        family=family,
        account_type='expense',
        parent__isnull=True,  # Root expense accounts
        is_active=True
    ).order_by('name')
    
    # Get complete account tree for hierarchical parent selection
    account_tree = get_account_tree(family)
    
    # Serialize account tree for JavaScript
    import json
    def serialize_tree(tree_node):
        if isinstance(tree_node, list):
            return [serialize_tree(node) for node in tree_node]
        return {
            'id': tree_node['account'].id,
            'name': tree_node['account'].name,
            'account_type': tree_node['account'].account_type,
            'level': tree_node['level'],
            'children': serialize_tree(tree_node['children']) if tree_node['children'] else []
        }
    
    account_tree_json = json.dumps(serialize_tree(account_tree))
    
    # Calculate transaction summary for sidebar
    from django.db.models import Sum
    transaction_summary = {
        'total_income': transactions.filter(transaction_type='income').aggregate(
            total=Sum('amount'))['total'] or 0,
        'total_expenses': transactions.filter(transaction_type='expense').aggregate(
            total=Sum('amount'))['total'] or 0,
    }
    transaction_summary['net_flow'] = transaction_summary['total_income'] - transaction_summary['total_expenses']
    
    context = {
        'title': 'Transaction History',
        'transactions': page_obj,
        'accounts': accounts,
        'merchant_accounts': merchant_accounts,
        'parent_income_accounts': parent_income_accounts,
        'parent_expense_accounts': parent_expense_accounts,
        'account_tree': account_tree,
        'account_tree_json': account_tree_json,
        'transaction_summary': transaction_summary,
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
    
    # Get the account parameter if passed (from account detail page)
    account_id = request.GET.get('account')
    initial_account = None
    if account_id:
        try:
            initial_account = Account.objects.get(id=account_id, family=family, is_active=True)
        except Account.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, family=family, initial_account=initial_account)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.family = family
            
            # Auto-determine transaction type if not provided and we have an account
            if not transaction.transaction_type and initial_account:
                # Default to expense for most account types, income for income accounts
                if initial_account.account_type == 'income':
                    transaction.transaction_type = 'income'
                else:
                    transaction.transaction_type = 'expense'
            
            # Auto-assign to week based on transaction date
            if not transaction.week and transaction.transaction_date:
                from datetime import timedelta
                trans_date = transaction.transaction_date
                # Find the week start (Monday)
                week_start = trans_date - timedelta(days=trans_date.weekday())
                week_end = week_start + timedelta(days=6)
                
                current_week, created = WeeklyPeriod.objects.get_or_create(
                    start_date=week_start,
                    end_date=week_end,
                    family=family,
                    defaults={
                        'is_active': True,
                        'week_number': 1 + (week_start - date(week_start.year, 1, 1)).days // 7,
                        'year': week_start.year
                    }
                )
                transaction.week = current_week
            
            transaction.save()
            
            messages.success(request, f'Transaction "{transaction.description or "Transaction"}" recorded successfully.')
            
            # Redirect back to account detail if we came from there
            if initial_account:
                return redirect('budget_allocation:account_detail', account_id=initial_account.pk)
            return redirect('budget_allocation:transaction_list')
    else:
        # Initialize form with account if specified
        initial = {}
        if initial_account:
            initial['account'] = initial_account
        form = TransactionForm(family=family, initial_account=initial_account, initial=initial)
    
    context = {
        'title': 'Record Transaction',
        'form': form,
        'family': family,
        'initial_account': initial_account,
    }
    return render(request, 'budget_allocation/transaction/create.html', context)


@login_required
@family_required
@app_permission_required('budget_allocation')
def transaction_delete(request, pk):
    """Delete a transaction"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to delete transactions.")
        return redirect('accounts:dashboard')
    
    # Get the transaction, ensuring it belongs to the user's family
    transaction_obj = get_object_or_404(Transaction, pk=pk, family=family)
    
    if request.method == 'POST':
        transaction_description = transaction_obj.description or "Transaction"
        transaction_obj.delete()
        messages.success(request, f'Transaction "{transaction_description}" has been deleted successfully.')
        
        # Check if we should redirect back to account detail
        from_account = request.GET.get('from_account')
        if from_account and transaction_obj.account:
            return redirect('budget_allocation:account_detail', account_id=transaction_obj.account.pk)
        
        # Default redirect to transaction list
        return redirect('budget_allocation:transaction_list')
    
    # For GET requests, render confirmation page
    context = {
        'title': 'Delete Transaction',
        'transaction': transaction_obj,
        'family': family,
    }
    return render(request, 'budget_allocation/transaction/delete.html', context)


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
        # Use rollup balance for parent accounts, individual balance for child accounts
        if account.parent is None:
            balance = get_account_balance_with_children(account, current_week)
        else:
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
        # Use rollup balance for parent accounts, individual balance for child accounts
        if account.parent is None:
            balance = get_account_balance_with_children(account, current_week)
        else:
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
def toggle_account_status_api(request, account_id):
    """Toggle account active status via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'}, status=405)
    
    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'success': False, 'error': 'Family not found'}, status=400)
    
    try:
        account = Account.objects.get(pk=account_id, family=family)
        
        # Toggle the status
        account.is_active = not account.is_active
        
        # Set activation/deactivation dates
        if account.is_active:
            account.date_activated = date.today()
            account.date_deactivated = None
        else:
            account.date_deactivated = date.today()
        
        account.save()
        
        # Create history entry
        AccountHistory.objects.create(
            account=account,
            family=family,
            action='activated' if account.is_active else 'deactivated',
            new_value=str(account.is_active),
            notes=f'Account {"activated" if account.is_active else "deactivated"} by {request.user.get_full_name() or request.user.username}'
        )
        
        return JsonResponse({
            'success': True,
            'is_active': account.is_active,
            'message': f'Account {"activated" if account.is_active else "deactivated"} successfully'
        })
        
    except Account.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Account not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


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


@login_required
@family_required
@app_permission_required('budget_allocation')
def create_account_ajax(request):
    """Create a new account via AJAX for use in transaction modal"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'success': False, 'error': 'Family not found'}, status=400)
    
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        account_type = request.POST.get('account_type', '').strip()
        description = request.POST.get('description', '').strip()
        parent_id = request.POST.get('parent', '').strip()
        
        # Validate required fields
        if not name:
            return JsonResponse({'success': False, 'error': 'Account name is required'}, status=400)
        
        if not account_type or account_type not in ['income', 'expense']:
            return JsonResponse({'success': False, 'error': 'Valid account type is required'}, status=400)
            
        if not parent_id:
            return JsonResponse({'success': False, 'error': 'Parent account is required'}, status=400)
        
        # Validate parent account exists and belongs to user's family
        try:
            parent_account = Account.objects.get(id=parent_id, family=family)
            # Allow any account of the same type as parent (more flexible than just matching type)
            # This allows creating child accounts under any account, not just root accounts
            if parent_account.account_type != account_type:
                return JsonResponse({
                    'success': False, 
                    'error': f'Parent account must be of type {account_type}'
                }, status=400)
        except Account.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid parent account'}, status=400)
        
        # Check if account with this name already exists under this parent
        if Account.objects.filter(family=family, name=name, parent=parent_account).exists():
            return JsonResponse({
                'success': False, 
                'error': f'An account with this name already exists under {parent_account.name}'
            }, status=400)
        
        # Create the new account
        with transaction.atomic():
            new_account = Account.objects.create(
                family=family,
                name=name,
                account_type=account_type,
                parent=parent_account,
                description=description,
                is_active=True,
                is_merchant_payee=True  # Mark as merchant/payee since it's created for transactions
            )
            
            # Return success with account data
            return JsonResponse({
                'success': True,
                'account': {
                    'id': new_account.id,
                    'name': new_account.name,
                    'account_type': new_account.account_type,
                    'description': new_account.description
                },
                'message': f'{account_type.title()} account "{name}" created successfully'
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error creating account: {str(e)}'}, status=500)
