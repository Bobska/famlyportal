from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.utils.decorators import method_decorator
from django.db.models import Sum, Q, Count, Max
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.views.decorators.http import require_POST
import json
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

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

# Initialize logger
logger = logging.getLogger(__name__)

# Test/development toggle: allow bypassing weekly allocation locks
try:
    from django.conf import settings
    ALLOCATION_LOCKS_ENABLED = getattr(settings, 'ALLOCATION_LOCKS_ENABLED', True)
except Exception:
    # Default to enabled if settings unavailable
    ALLOCATION_LOCKS_ENABLED = True


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


def get_account_subtree(account):
    """Yield account and all descendants (DFS)."""
    yield account
    for child in account.children.all():
        yield from get_account_subtree(child)


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


def get_or_create_week_for_date(family, target_date):
    """Resolve the WeeklyPeriod containing target_date using Monday-Sunday weeks.
    Falls back to simple computation without relying on custom manager methods.
    """
    # Find Monday of the week
    week_start = target_date - timedelta(days=target_date.weekday())
    week_end = week_start + timedelta(days=6)
    week, _ = WeeklyPeriod.objects.get_or_create(
        family=family,
        start_date=week_start,
        defaults={
            'end_date': week_end,
            'is_active': True,
        }
    )
    # Ensure end_date is correct if record existed with different value
    if week.end_date != week_end:
        week.end_date = week_end
        week.save(update_fields=['end_date'])
    return week


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
    # Get children of root accounts (hide the root Income/Expense accounts)
    root_income = Account.objects.filter(
        family=family, 
        account_type='income',
        parent__isnull=True
    ).first()
    
    root_expense = Account.objects.filter(
        family=family, 
        account_type='expense',
        parent__isnull=True
    ).first()
    
    # Get children of root accounts instead of root accounts themselves
    # Order by number of children (descending), then by name
    income_accounts = Account.objects.filter(
        family=family, 
        parent=root_income,
        is_active=True
    ).select_related('parent').prefetch_related('children__children__children').annotate(
        children_count=Count('children', filter=Q(children__is_active=True))
    ).order_by('-children_count', 'name') if root_income else Account.objects.none()
    
    expense_accounts = Account.objects.filter(
        family=family, 
        parent=root_expense,
        is_active=True
    ).select_related('parent').prefetch_related('children__children__children').annotate(
        children_count=Count('children', filter=Q(children__is_active=True))
    ).order_by('-children_count', 'name') if root_expense else Account.objects.none()
    
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
def account_list_all(request):
    """Duplicated All Accounts view for Budget Allocation"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access accounts.")
        return redirect('accounts:dashboard')

    from .utils import ensure_default_accounts_exist
    ensure_default_accounts_exist(family)

    root_income = Account.objects.filter(
        family=family,
        account_type='income',
        parent__isnull=True
    ).first()
    root_expense = Account.objects.filter(
        family=family,
        account_type='expense',
        parent__isnull=True
    ).first()

    income_accounts = Account.objects.filter(
        family=family,
        parent=root_income,
        is_active=True
    ).select_related('parent').prefetch_related('children__children__children').annotate(
        children_count=Count('children', filter=Q(children__is_active=True))
    ).order_by('-children_count', 'name') if root_income else Account.objects.none()

    expense_accounts = Account.objects.filter(
        family=family,
        parent=root_expense,
        is_active=True
    ).select_related('parent').prefetch_related('children__children__children').annotate(
        children_count=Count('children', filter=Q(children__is_active=True))
    ).order_by('-children_count', 'name') if root_expense else Account.objects.none()

    current_week = get_current_week(family)
    overall_balance = calculate_overall_balance(family, current_week)

    context = {
        'title': 'All Accounts (Duplicate)',
        'income_accounts': income_accounts,
        'expense_accounts': expense_accounts,
        'overall_balance': overall_balance,
        'current_week': current_week,
        'show_management_tools': True,
        'family': family,
    }
    return render(request, 'budget_allocation/account/list_all_accounts.html', context)


@login_required
@family_required
@app_permission_required('budget_allocation')
def account_list_weekly(request):
    """Weekly view of All Accounts with week navigation"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access accounts.")
        return redirect('accounts:dashboard')

    # Ensure default accounts exist
    from .utils import ensure_default_accounts_exist
    ensure_default_accounts_exist(family)

    # Determine current week from query or today
    week_param = request.GET.get('week')
    if week_param:
        try:
            parsed_date = datetime.strptime(week_param, '%Y-%m-%d').date()
        except ValueError:
            parsed_date = date.today()
    else:
        parsed_date = date.today()

    current_week = get_or_create_week_for_date(family, parsed_date)

    # Compute previous and next weeks
    prev_start = current_week.start_date - timedelta(days=7)
    next_start = current_week.start_date + timedelta(days=7)
    prev_week = get_or_create_week_for_date(family, prev_start)
    next_week = get_or_create_week_for_date(family, next_start)

    # Same account trees as regular list (children of root accounts)
    root_income = Account.objects.filter(
        family=family,
        account_type='income',
        parent__isnull=True
    ).first()

    root_expense = Account.objects.filter(
        family=family,
        account_type='expense',
        parent__isnull=True
    ).first()

    income_accounts = Account.objects.filter(
        family=family,
        parent=root_income,
        is_active=True
    ).select_related('parent').prefetch_related('children__children__children').annotate(
        children_count=Count('children', filter=Q(children__is_active=True))
    ).order_by('-children_count', 'name') if root_income else Account.objects.none()

    expense_accounts = Account.objects.filter(
        family=family,
        parent=root_expense,
        is_active=True
    ).select_related('parent').prefetch_related('children__children__children').annotate(
        children_count=Count('children', filter=Q(children__is_active=True))
    ).order_by('-children_count', 'name') if root_expense else Account.objects.none()

    # Use helper to compute balances for this week
    overall_balance = calculate_overall_balance(family, current_week)

    context = {
        'title': 'Weekly Accounts',
        'income_accounts': income_accounts,
        'expense_accounts': expense_accounts,
        'overall_balance': overall_balance,
        'current_week': current_week,
        'prev_week': prev_week,
        'next_week': next_week,
        'show_management_tools': True,
        'family': family,
    }
    return render(request, 'budget_allocation/account/list_weekly.html', context)


@login_required
@family_required
@app_permission_required('budget_allocation')
@require_POST
def account_move_api(request):
    """Move/reparent/reorder an account in the hierarchy.
    Body JSON: { source_id, target_id, mode: 'after' | 'before' | 'inside' }
    Rules:
      - Families must match, and source != target
      - Cannot move a node under itself or into its own subtree
      - If moving across account_type roots (income vs expense), propagate type to entire subtree
      - Adjust sort_order within the new parent; for 'after'/'before', parent is target.parent; for 'inside', parent is target
    Recalculations:
      - Roll-ups are computed on the fly in existing APIs; moving updates parent linkage so they reflect new lineage
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
        source_id = int(payload.get('source_id'))
        target_id = int(payload.get('target_id'))
        mode = (payload.get('mode') or 'after').lower()
        if mode not in ('after', 'before', 'inside'):
            return JsonResponse({'success': False, 'error': 'Invalid mode'}, status=400)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Invalid payload'}, status=400)

    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'success': False, 'error': 'No family found'}, status=403)

    source = get_object_or_404(Account, pk=source_id, family=family)
    target = get_object_or_404(Account, pk=target_id, family=family)

    if source.pk == target.pk:
        return JsonResponse({'success': False, 'error': 'Cannot move onto itself'}, status=400)

    # Prevent cycles: target cannot be inside source subtree
    def is_descendant(a, potential_ancestor):
        cur = a.parent
        while cur is not None:
            if cur.pk == potential_ancestor.pk:
                return True
            cur = cur.parent
        return False

    if is_descendant(target, source):
        return JsonResponse({'success': False, 'error': 'Cannot move a node into its own subtree'}, status=400)

    with transaction.atomic():
        # Determine new parent and sort order intent
        if mode == 'inside':
            # Only allowed if target can have children; otherwise treat as 'after'
            if hasattr(target, 'can_have_children') and target.can_have_children:
                new_parent = target
                siblings = Account.objects.filter(family=family, parent=new_parent).order_by('sort_order', 'name')
                new_sort = (siblings.aggregate(max_s=Max('sort_order'))['max_s'] or 0) + 1
            else:
                mode = 'after'
                new_parent = target.parent
                siblings = Account.objects.filter(family=family, parent=new_parent).order_by('sort_order', 'name')
                ordered_ids = [s.pk for s in siblings]
                try:
                    idx = ordered_ids.index(target.pk)
                except ValueError:
                    idx = len(ordered_ids) - 1
                insert_pos = idx + 1
                for i, s in enumerate(siblings):
                    s.sort_order = i + (1 if i >= insert_pos else 0)
                    s.save(update_fields=['sort_order'])
                new_sort = insert_pos
        else:
            # before/after => same parent as target
            new_parent = target.parent
            if new_parent is None:
                # Disallow moving to root unless types are root-compatible; we keep non-root accounts under Income/Expenses
                # Place under the appropriate root (Income/Expenses) implicitly
                new_parent = target  # fallback to inside
                mode = 'inside'
            siblings = Account.objects.filter(family=family, parent=new_parent).order_by('sort_order', 'name')
            # Determine position relative to target
            ordered_ids = [s.pk for s in siblings]
            try:
                idx = ordered_ids.index(target.pk)
            except ValueError:
                idx = len(ordered_ids) - 1
            insert_pos = idx + (1 if mode == 'after' else 0)
            # Reassign sort_orders to make room
            for i, s in enumerate(siblings):
                s.sort_order = i + (1 if i >= insert_pos else 0)
                s.save(update_fields=['sort_order'])
            new_sort = insert_pos

        old_parent_id = source.parent_id
        old_type = source.account_type

        # Validate parent can accept children
        if new_parent and hasattr(new_parent, 'can_have_children') and not new_parent.can_have_children:
            return JsonResponse({'success': False, 'error': 'Target cannot have children'}, status=400)

        # Update parent and sort_order
        source.parent = new_parent
        source.sort_order = new_sort
        source.save(update_fields=['parent', 'sort_order'])

        # Resequence siblings in the old parent to fill gaps
        if old_parent_id != (new_parent.pk if new_parent else None):
            old_siblings = Account.objects.filter(family=family, parent_id=old_parent_id).order_by('sort_order', 'name')
            for i, s in enumerate(old_siblings):
                if s.sort_order != i:
                    s.sort_order = i
                    s.save(update_fields=['sort_order'])

        # If account types differ between new lineage and source, propagate
        new_lineage_type = new_parent.account_type if new_parent else source.account_type
        if new_lineage_type in ('income', 'expense') and new_lineage_type != old_type:
            for node in get_account_subtree(source):
                if node.account_type != new_lineage_type:
                    node.account_type = new_lineage_type
                    node.save(update_fields=['account_type'])

        # Log history
        AccountHistory.objects.create(
            family=family,
            account=source,
            action='moved',
            old_value=f"parent={old_parent_id}, type={old_type}",
            new_value=f"parent={source.parent_id}, type={source.account_type}",
            notes=f"Moved {mode} target {target.pk}"
        )

    return JsonResponse({'success': True})


@login_required
@family_required
@app_permission_required('budget_allocation')
@require_POST
def account_update_api(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'success': False, 'error': 'Invalid payload'}, status=400)

    account_id = payload.get('account_id')
    name = (payload.get('name') or '').strip()
    description = (payload.get('description') or '').strip()
    is_mp = bool(payload.get('is_merchant_payee'))

    if not account_id:
        return JsonResponse({'success': False, 'error': 'Missing account_id'}, status=400)

    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'success': False, 'error': 'No family found'}, status=403)

    account = get_object_or_404(Account, pk=account_id, family=family)

    if name:
        account.name = name
    account.description = description
    account.is_merchant_payee = is_mp
    try:
        account.full_clean()
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': '; '.join(sum((v for v in e.message_dict.values()), []))}, status=400)
    account.save(update_fields=['name', 'description', 'is_merchant_payee'])

    AccountHistory.objects.create(
        family=family,
        account=account,
        action='renamed',
        old_value='',
        new_value=f"name={account.name}, is_mp={account.is_merchant_payee}",
        notes='Updated via API'
    )

    return JsonResponse({'success': True})


@login_required
@family_required
@app_permission_required('budget_allocation')
def disabled_accounts(request):
    """View for managing disabled accounts"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access accounts.")
        return redirect('accounts:dashboard')
    
    # Get all disabled accounts for this family
    disabled_accounts = Account.objects.filter(
        family=family, 
        is_active=False
    ).exclude(
        account_type='root'  # Exclude root accounts
    ).select_related('parent').prefetch_related('children').annotate(
        children_count=Count('children'),
        transaction_count=Count('allocation_transactions')
    ).order_by('account_type', 'name')
    
    # Check if accounts have transactions or other dependencies
    for account in disabled_accounts:
        account.has_transactions = account.allocation_transactions.exists()
        account.has_allocations = (
            account.allocations_from.exists() or 
            account.allocations_to.exists()
        )
        account.has_children = account.children.filter(is_active=True).exists()
        account.can_delete = not (account.has_transactions or account.has_allocations or account.has_children)
    
    context = {
        'title': 'Disabled Accounts',
        'disabled_accounts': disabled_accounts,
        'family': family,
    }
    return render(request, 'budget_allocation/account/disabled_list.html', context)


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
    
    # Determine week context (optional ?week=YYYY-MM-DD)
    week_param = request.GET.get('week')
    show_week_selector = False
    if week_param:
        try:
            parsed_date = datetime.strptime(week_param, '%Y-%m-%d').date()
        except ValueError:
            parsed_date = date.today()
        # Use manager helper if available
        try:
            current_week = get_or_create_week_for_date(family, parsed_date)
        except Exception:
            current_week = get_current_week(family)
        # Compute prev/next for template week selector
        prev_start = current_week.start_date - timedelta(days=7)
        next_start = current_week.start_date + timedelta(days=7)
        try:
            prev_week = get_or_create_week_for_date(family, prev_start)
            next_week = get_or_create_week_for_date(family, next_start)
        except Exception:
            prev_week = None
            next_week = None
        show_week_selector = True
    else:
        # Default to the family's current week to compute balances (no selector shown)
        current_week = get_current_week(family)
        prev_week = None
        next_week = None
    
    # Get child accounts with their balances
    child_accounts = account.children.filter(is_active=True).order_by('sort_order', 'name')
    
    # Calculate account balance including child accounts for parent display
    account_balance = get_account_balance_with_children(account, current_week)
    
    # Calculate child account balances and create enriched data structure
    child_balances = {}
    enriched_child_accounts = []
    
    def get_recursive_account_balance(account, show_week_selector, current_week, family):
        """Calculate account balance including all descendants recursively"""
        if show_week_selector:
            # For weekly view, use week-specific balance for this account
            account_balance = get_account_balance(account, current_week)
        else:
            # For regular view, get total balance across all transactions and allocations
            transactions_total = Transaction.objects.filter(
                account=account,
                family=family
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            allocations_total = Allocation.objects.filter(
                to_account=account,
                week__family=family
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            account_balance = allocations_total + transactions_total
        
        # Add balances from all children recursively
        children = account.children.filter(is_active=True)
        for child in children:
            child_balance = get_recursive_account_balance(child, show_week_selector, current_week, family)
            account_balance += child_balance
            
        return account_balance
    
    for child in child_accounts:
        # Get the recursive balance that includes all descendants
        balance = get_recursive_account_balance(child, show_week_selector, current_week, family)
        
        child_balances[child.id] = balance
        # Create enriched data with balance included
        enriched_child_accounts.append({
            'account': child,
            'balance': balance
        })
    
    # Get recent transactions with pagination
    if show_week_selector:
        # For weekly view, filter transactions by week
        transactions = Transaction.objects.filter(
            account=account,
            family=family,
            week=current_week
        ).order_by('-transaction_date', '-created_at')
    else:
        # For regular view, show all transactions
        transactions = Transaction.objects.filter(
            account=account,
            family=family
        ).order_by('-transaction_date', '-created_at')
    
    # Pagination for transactions
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Calculate total of ALL transactions for this account (not just paginated ones)
    if show_week_selector:
        # For weekly view, sum transactions for the current week
        visible_transactions_total = Transaction.objects.filter(
            account=account,
            family=family,
            week=current_week
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Add allocations to this account for the week
        visible_allocations_total = Allocation.objects.filter(
            to_account=account,
            week=current_week
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    else:
        # For regular view, sum all transactions
        visible_transactions_total = Transaction.objects.filter(
            account=account,
            family=family
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Add all allocations to this account
        visible_allocations_total = Allocation.objects.filter(
            to_account=account,
            week__family=family
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Total for this account includes both transactions and allocations
    account_total = visible_transactions_total + visible_allocations_total
    
    # Calculate total of all child account balances
    child_accounts_total = sum(child_balances.values())
    
    # Calculate combined total (account balance + child balances)
    combined_total = account_total + child_accounts_total
    
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
        'visible_transactions_total': visible_transactions_total,
        'visible_allocations_total': visible_allocations_total,
        'account_total': account_total,
        'child_accounts_total': child_accounts_total,
        'combined_total': combined_total,
        'recent_allocations_in': recent_allocations_in,
        'recent_allocations_out': recent_allocations_out,
        'can_add_children': account.can_have_children,
        'history': history,
        'weekly_summary': weekly_summary,
        'current_week': current_week,
        'prev_week': prev_week,
        'next_week': next_week,
        'show_week_selector': show_week_selector,
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

    # Handle allocation creation via modal
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
            
            # Enforce business rule: only allow allocations TO expense accounts
            if allocation.to_account and getattr(allocation.to_account, 'account_type', '').lower() != 'expense':
                if request.POST.get('ajax') == '1' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Allocations can only be made to Expense accounts.'}, status=400)
                messages.error(request, 'Allocations can only be made to Expense accounts.')
                return redirect('budget_allocation:allocation_create')

            allocation.save()
            messages.success(request, f"Allocation created: ${allocation.amount} from {allocation.from_account.name} to {allocation.to_account.name}")
            return redirect('budget_allocation:allocation_dashboard')
    else:
        form = AllocationForm(family=family)
    
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
        'form': form,  # Add form to context for modal
    }
    return render(request, 'budget_allocation/allocation/dashboard.html', context)


@login_required
@family_required
@app_permission_required('budget_allocation')
def allocation_create(request):
    """Create a new allocation"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access allocations.")
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        # Support auto-from-income pool: if flag present, inject from_account as family's root Income account
        post_data = request.POST.copy()
        auto_from_income = post_data.get('auto_from_income') == '1'
        if auto_from_income:
            root_income = Account.objects.filter(family=family, account_type='income', parent__isnull=True).first()
            if not root_income:
                err_msg = 'Income pool not configured for this family.'
                if post_data.get('ajax') == '1' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': err_msg}, status=400)
                messages.error(request, err_msg)
                return redirect('budget_allocation:allocation_dashboard')
            post_data['from_account'] = str(root_income.id)
        form = AllocationForm(post_data, family=family)
        if form.is_valid():
            allocation = form.save(commit=False)
            allocation.family = family

            # If week_start is provided (from modal), resolve to WeeklyPeriod
            week_start_str = post_data.get('week_start')
            if week_start_str:
                try:
                    parsed_date = datetime.strptime(week_start_str, '%Y-%m-%d').date()
                    resolve_week = get_or_create_week_for_date(family, parsed_date)
                    allocation.week = resolve_week
                except Exception:
                    pass

            # Auto-assign to current week if not specified
            if not allocation.week:
                current_week = get_current_week(family)
                allocation.week = current_week

            # Enforce that allocations go only to Expense accounts
            try:
                if allocation.to_account and allocation.to_account.account_type != 'expense':
                    raise ValidationError('Allocations can only be made to Expense accounts.')
            except Exception as e:
                if post_data.get('ajax') == '1' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': str(e)}, status=400)
                messages.error(request, str(e))
                return redirect('budget_allocation:allocation_dashboard')

            # Prevent creating allocations for a locked week (can be bypassed for testing)
            if ALLOCATION_LOCKS_ENABLED and allocation.week and allocation.week.allocation_locked:
                err = 'Allocations are locked for this week.'
                if post_data.get('ajax') == '1' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': err}, status=400)
                messages.error(request, err)
                return redirect('budget_allocation:allocation_dashboard')

            # Enforce available pool (carry-forward): sum of all prior weeks' income minus allocations through current week
            current_week = allocation.week
            from decimal import Decimal
            incomes_to_prev = Transaction.objects.filter(
                family=family,
                transaction_type='income',
                week__start_date__lt=current_week.start_date
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            allocations_to_current = Allocation.objects.filter(
                family=family,
                week__start_date__lte=current_week.start_date
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            available = (incomes_to_prev or Decimal('0')) - (allocations_to_current or Decimal('0'))
            if allocation.amount and allocation.amount > available:
                err = f"Insufficient available funds to allocate. Available (carry-forward): ${available:.2f}."
                if post_data.get('ajax') == '1' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': err, 'available_current': float(available)}, status=400)
                messages.error(request, err)
                return redirect('budget_allocation:allocation_dashboard')

            allocation.save()

            # Week locking semantics (can be disabled for testing)
            if allocation.week and not allocation.week.allocation_locked:
                today = date.today()
                if ALLOCATION_LOCKS_ENABLED and today >= allocation.week.start_date:
                    allocation.week.allocation_locked = True
                    allocation.week.is_allocated = True
                    allocation.week.save(update_fields=['allocation_locked', 'is_allocated'])
                else:
                    # If allocating before week starts or locks disabled, mark is_allocated True but keep unlocked
                    allocation.week.is_allocated = True
                    allocation.week.save(update_fields=['is_allocated'])

            # If ajax, return JSON
            if post_data.get('ajax') == '1' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'id': allocation.id,
                    'amount': float(allocation.amount),
                    'to_account_id': allocation.to_account_id,
                    'from_account_id': allocation.from_account_id,
                    'week_start': allocation.week.start_date.strftime('%Y-%m-%d') if allocation.week else None,
                    'locked': allocation.week.allocation_locked if allocation.week else False,
                    'message': 'Allocation created successfully'
                })

            messages.success(request, f"Allocation created: ${allocation.amount} from {allocation.from_account.name} to {allocation.to_account.name}")
            return redirect('budget_allocation:allocation_dashboard')
        else:
            if request.POST.get('ajax') == '1' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Return first error message
                err = next(iter(form.errors.values()))[0] if form.errors else 'Invalid data'
                return JsonResponse({'success': False, 'error': str(err)}, status=400)
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
    # Preserve optional week for return navigation
    return_week = request.GET.get('return_week')
    if account_id:
        try:
            initial_account = Account.objects.get(id=account_id, family=family, is_active=True)
        except Account.DoesNotExist:
            pass
    
    if request.method == 'POST':
        # Preserve optional week to return to account detail with same context
        return_week = request.GET.get('return_week') or request.POST.get('return_week') or return_week
        # If initial_account not set via GET, try POST
        if not initial_account:
            post_account_id = request.POST.get('account')
            if post_account_id:
                try:
                    initial_account = Account.objects.get(id=post_account_id, family=family, is_active=True)
                except Account.DoesNotExist:
                    initial_account = None
        form = TransactionForm(request.POST, family=family, initial_account=initial_account)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.family = family

            # Auto-determine transaction type if not provided and we have an account
            if not transaction.transaction_type and initial_account:
                if initial_account.account_type == 'income':
                    transaction.transaction_type = 'income'
                else:
                    transaction.transaction_type = 'expense'

            # Auto-assign to week based on transaction date
            if not transaction.week and transaction.transaction_date:
                from datetime import timedelta
                trans_date = transaction.transaction_date
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

            # Ensure account is set (in case disabled field scenario)
            if not transaction.account_id and initial_account:
                transaction.account = initial_account

            transaction.save()

            # If ajax, return JSON
            if request.POST.get('ajax') == '1' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'id': transaction.id,
                    'amount': float(transaction.amount),
                    'account_id': transaction.account_id,
                    'transaction_date': transaction.transaction_date.strftime('%Y-%m-%d') if transaction.transaction_date else None,
                    'week_start': transaction.week.start_date.strftime('%Y-%m-%d') if transaction.week else None,
                    'message': 'Transaction recorded successfully'
                })

            messages.success(request, f'Transaction "{transaction.description or "Transaction"}" recorded successfully.')

            # Redirect back to account detail if we came from there
            if initial_account:
                if return_week:
                    detail_url = reverse('budget_allocation:account_detail', kwargs={'account_id': initial_account.pk})
                    return redirect(f"{detail_url}?week={return_week}")
                return redirect('budget_allocation:account_detail', account_id=initial_account.pk)
            return redirect('budget_allocation:transaction_list')
        else:
            if request.POST.get('ajax') == '1' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                err = next(iter(form.errors.values()))[0] if form.errors else 'Invalid data'
                return JsonResponse({'success': False, 'error': str(err)}, status=400)
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
        'return_week': return_week,
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
    """List and manage budget templates, handle create via modal"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access budget templates.")
        return redirect('accounts:dashboard')

    templates = BudgetTemplate.objects.filter(
        family=family
    ).order_by('priority', 'account__name')

    form = BudgetTemplateForm(family=family)
    if request.method == 'POST':
        form = BudgetTemplateForm(request.POST, family=family)
        if form.is_valid():
            template = form.save(commit=False)
            template.family = family
            template.save()
            messages.success(request, f'Budget template for "{template.account.name}" created successfully.')
            return redirect('budget_allocation:budget_template_list')

    context = {
        'title': 'Budget Templates',
        'templates': templates,
        'form': form,
        'family': family,
    }
    return render(request, 'budget_allocation/budget_template/list.html', context)





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
            'account_type': account.account_type,
            'parent_id': account.parent_id,
            'account_id': account.id,
            'message': f'Account {"activated" if account.is_active else "deactivated"} successfully'
        })
        
    except Account.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Account not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@family_required
@app_permission_required('budget_allocation')
def delete_account_api(request, account_id):
    """Delete an account via AJAX with proper validation"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'}, status=405)
    
    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'success': False, 'error': 'Family not found'}, status=400)
    
    try:
        account = Account.objects.get(pk=account_id, family=family)
        
        # Validation checks
        if account.is_active:
            return JsonResponse({
                'success': False, 
                'error': 'Account must be disabled before it can be deleted'
            }, status=400)
        
        if account.account_type == 'root':
            return JsonResponse({
                'success': False, 
                'error': 'Root accounts cannot be deleted'
            }, status=400)
        
        # Check for children
        if account.children.exists():
            return JsonResponse({
                'success': False, 
                'error': 'Account has child accounts. Please delete or move them first.'
            }, status=400)
        
        # Check for transactions
        if account.allocation_transactions.exists():
            return JsonResponse({
                'success': False, 
                'error': 'Account has transactions. Cannot delete accounts with transaction history.'
            }, status=400)
        
        # Check for allocations
        if account.allocations_from.exists() or account.allocations_to.exists():
            return JsonResponse({
                'success': False, 
                'error': 'Account has allocations. Cannot delete accounts with allocation history.'
            }, status=400)
        
        # Store account info for logging
        account_name = account.name
        account_type = account.account_type
        
        # Use atomic transaction to ensure clean deletion
        with transaction.atomic():
            # Explicitly delete related AccountHistory records first
            AccountHistory.objects.filter(account=account).delete()
            
            # Now delete the account itself
            account.delete()
        
        # Log the deletion for debugging/audit purposes
        logger.info(f'Account "{account_name}" ({account_type}) deleted by {request.user.get_full_name() or request.user.username} from family {family.name}')
        
        return JsonResponse({
            'success': True,
            'message': f'Account "{account_name}" deleted successfully'
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
            # If no parent is selected, automatically use the root account of the matching type
            try:
                parent_account = Account.objects.get(
                    family=family,
                    account_type=account_type,
                    parent__isnull=True  # Root account has no parent
                )
                print(f"Auto-selected root {account_type} account as parent: {parent_account.name}")
            except Account.DoesNotExist:
                return JsonResponse({
                    'success': False, 
                    'error': f'No root {account_type} account found. Please contact administrator.'
                }, status=400)
        else:
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


@login_required
@family_required
@app_permission_required('budget_allocation')
def api_account_tree(request):
    """API endpoint to get account tree data for hierarchy selection"""
    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'success': False, 'error': 'Family not found'}, status=400)
    
    try:
        # Get account tree
        account_tree = get_account_tree(family)
        
        # Serialize tree for JSON response - enhanced version for modal
        def serialize_account_tree(tree_node):
            if isinstance(tree_node, list):
                return [serialize_account_tree(node) for node in tree_node]
            return {
                'account': {
                    'id': tree_node['account'].id,
                    'name': tree_node['account'].name,
                    'account_type': tree_node['account'].account_type,
                    'description': tree_node['account'].description or '',
                    'is_active': tree_node['account'].is_active,
                },
                'level': tree_node['level'],
                'children': serialize_account_tree(tree_node['children']) if tree_node['children'] else []
            }
        
        serialized_tree = serialize_account_tree(account_tree)
        
        return JsonResponse({
            'success': True,
            'tree': serialized_tree
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error loading account tree: {str(e)}'}, status=500)


@login_required
@family_required
@app_permission_required('budget_allocation')
def accounts_master_detail(request):
    """Master-detail view for animated account management"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access accounts.")
        return redirect('accounts:dashboard')
    
    # Determine current week (optional ?week=YYYY-MM-DD) similar to weekly view
    week_param = request.GET.get('week')
    if week_param:
        try:
            parsed_date = datetime.strptime(week_param, '%Y-%m-%d').date()
        except ValueError:
            parsed_date = timezone.now().date()
    else:
        parsed_date = timezone.now().date()

    current_week = get_or_create_week_for_date(family, parsed_date)
    prev_start = current_week.start_date - timedelta(days=7)
    next_start = current_week.start_date + timedelta(days=7)
    prev_week = get_or_create_week_for_date(family, prev_start)
    next_week = get_or_create_week_for_date(family, next_start)

    # Get account tree with enhanced data for master-detail view
    account_tree = get_account_tree(family)
    
    # Convert tree to a format suitable for collapsible display
    def enhance_tree_for_display(tree_node):
        if isinstance(tree_node, list):
            return [enhance_tree_for_display(node) for node in tree_node]
        else:
            account = tree_node['account']
            enhanced = {
                'account': {
                    'id': account.id,
                    'name': account.name,
                    'account_type': account.account_type,
                    'description': account.description or '',
                    'is_active': account.is_active,
                    'parent_name': account.parent.name if account.parent else None,
                    'parent_id': account.parent.id if account.parent else None,
                    'full_path': get_account_full_path(account),
                },
                'level': tree_node['level'],
                'children': enhance_tree_for_display(tree_node['children']) if tree_node['children'] else [],
                'has_children': bool(tree_node['children']),
                'children_count': len(tree_node['children']) if tree_node['children'] else 0
            }
            return enhanced
    
    enhanced_tree = enhance_tree_for_display(account_tree)
    
    # Also create a flattened list for search purposes and total counts
    def count_all_accounts(tree_node, counter=None):
        if counter is None:
            counter = {'total': 0, 'active': 0}
        
        if isinstance(tree_node, list):
            for node in tree_node:
                count_all_accounts(node, counter)
        else:
            counter['total'] += 1
            if tree_node['account']['is_active']:
                counter['active'] += 1
            if tree_node['children']:
                count_all_accounts(tree_node['children'], counter)
        
        return counter
    
    account_counts = count_all_accounts(enhanced_tree)
    
    # Get first account for default detail panel (if any)
    selected_account = None
    account_id = request.GET.get('account_id')
    if account_id:
        try:
            selected_account = Account.objects.get(id=account_id, family=family)
        except Account.DoesNotExist:
            pass
    # Note: Don't auto-select first account - start with detail panel hidden
    
    context = {
        'title': 'Master-Detail Account View',
        'account_tree': enhanced_tree,
        'selected_account': selected_account,
        'family': family,
        'total_accounts': account_counts['total'],
        'active_accounts': account_counts['active'],
        'current_week': current_week,
        'prev_week': prev_week,
        'next_week': next_week,
    }
    
    return render(request, 'budget_allocation/account/accounts_master_detail.html', context)


@login_required
@family_required
@app_permission_required('budget_allocation')
def account_detail_api(request, account_id):
    """API endpoint for loading account details in master-detail view"""
    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'success': False, 'error': 'Family not found'}, status=400)
    
    try:
        # Get account with all related data for detail panel
        account = Account.objects.select_related('parent').prefetch_related(
            'children',
            'allocation_transactions',
            'allocations_to'
        ).get(id=account_id, family=family)
        
        # Resolve optional week context from query param (?week=YYYY-MM-DD)
        week_param = request.GET.get('week')
        if week_param:
            try:
                parsed_date = datetime.strptime(week_param, '%Y-%m-%d').date()
            except ValueError:
                parsed_date = date.today()
            current_week = get_or_create_week_for_date(family, parsed_date)
        else:
            current_week = get_current_week(family)

        # Get recent transactions (last 10) - scoped to week when provided
        tx_qs = Transaction.objects.filter(account=account).select_related('account', 'week')
        if week_param:
            tx_qs = tx_qs.filter(week=current_week)
        recent_transactions = tx_qs.order_by('-transaction_date')[:10]

        # Get account balance for the resolved week, including all descendants (roll-up)
        account_balance = get_account_balance_with_children(account, current_week)

        # Compute weekly totals: allocations to this account (and descendants) and transactions (income/expenses)
        # Roll up descendants for a true parent summary
        def get_descendant_ids(acc):
            ids = [acc.id]
            for child in acc.children.all():
                ids.extend(get_descendant_ids(child))
            return ids

        account_ids = get_descendant_ids(account)

        weekly_tx = Transaction.objects.filter(account_id__in=account_ids)
        if week_param:
            weekly_tx = weekly_tx.filter(week=current_week)

        # If transaction types exist (e.g., 'income'/'expense'), split by type; otherwise sign-based categorization
        income_total = Decimal('0')
        expense_total = Decimal('0')
        total_transactions_amount = Decimal('0')
        for t in weekly_tx:
            amt = t.amount
            total_transactions_amount += amt
            try:
                ttype = getattr(t, 'transaction_type', None)
                if ttype == 'income':
                    income_total += amt
                elif ttype == 'expense':
                    expense_total += abs(amt)
                else:
                    # Fallback by sign
                    if amt >= 0:
                        income_total += amt
                    else:
                        expense_total += abs(amt)
            except Exception:
                if amt >= 0:
                    income_total += amt
                else:
                    expense_total += abs(amt)

        weekly_alloc = Allocation.objects.filter(to_account_id__in=account_ids)
        if week_param:
            weekly_alloc = weekly_alloc.filter(week=current_week)
        allocation_total = weekly_alloc.aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Previous week deltas (optional, only if week is provided)
        delta = {
            'income_delta': None,
            'expense_delta': None,
            'allocation_delta': None,
            'transactions_delta': None,
        }
        if week_param and current_week:
            prev_start = current_week.start_date - timedelta(days=7)
            prev_week = get_or_create_week_for_date(family, prev_start)

            prev_tx = Transaction.objects.filter(account_id__in=account_ids, week=prev_week)
            prev_income = Decimal('0')
            prev_expense = Decimal('0')
            prev_total = Decimal('0')
            for t in prev_tx:
                amt = t.amount
                prev_total += amt
                ttype = getattr(t, 'transaction_type', None)
                if ttype == 'income':
                    prev_income += amt
                elif ttype == 'expense':
                    prev_expense += abs(amt)
                else:
                    if amt >= 0:
                        prev_income += amt
                    else:
                        prev_expense += abs(amt)

            prev_alloc_total = Allocation.objects.filter(to_account_id__in=account_ids, week=prev_week).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            delta = {
                'income_delta': float(income_total - prev_income),
                'expense_delta': float(expense_total - prev_expense),
                'allocation_delta': float(allocation_total - prev_alloc_total),
                'transactions_delta': float(total_transactions_amount - prev_total),
            }
        
        # Get account children for hierarchy display
        children = list(account.children.filter(is_active=True).values(
            'id', 'name', 'account_type', 'description', 'is_active'
        ))
        
        # Build breadcrumb path
        breadcrumb = []
        current = account
        while current:
            breadcrumb.insert(0, {
                'id': current.id,
                'name': current.name,
                'account_type': current.account_type
            })
            current = current.parent
        
        # Serialize transaction data
        transaction_data = []
        for transaction in recent_transactions:
            transaction_data.append({
                'id': transaction.id,
                'amount': float(transaction.amount),
                'description': transaction.description,
                'date': transaction.transaction_date.strftime('%Y-%m-%d'),
                'transaction_type': transaction.transaction_type,
                'payee': transaction.payee,
                'week': transaction.week.start_date.strftime('%Y-%m-%d') if transaction.week else None
            })
        
        # Get recent allocations
        alloc_qs = Allocation.objects.filter(to_account=account).select_related('to_account', 'week')
        if week_param:
            alloc_qs = alloc_qs.filter(week=current_week)
        recent_allocations = alloc_qs.order_by('-id')[:5]
        
        allocation_data = []
        for allocation in recent_allocations:
            allocation_data.append({
                'id': allocation.id,
                'amount': float(allocation.amount),
                'notes': allocation.notes,
                'date': allocation.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(allocation, 'created_at') else 'N/A',
                'week': allocation.week.start_date.strftime('%Y-%m-%d') if allocation.week else None
            })
        
        # Family-level weekly income context for header cards
        # income_current = income in current_week
        # available_current (carry-forward) = sum(income for weeks before current) - sum(allocations through current)
        income_current = Transaction.objects.filter(
            family=family,
            transaction_type='income',
            week=current_week
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        incomes_to_prev = Transaction.objects.filter(
            family=family,
            transaction_type='income',
            week__start_date__lt=current_week.start_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        allocated_through_current = Allocation.objects.filter(
            family=family,
            week__start_date__lte=current_week.start_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        available_current = (incomes_to_prev or Decimal('0')) - (allocated_through_current or Decimal('0'))

        return JsonResponse({
            'success': True,
            'account': {
                'id': account.id,
                'name': account.name,
                'account_type': account.account_type,
                'description': account.description or '',
                'is_active': account.is_active,
                'is_merchant_payee': getattr(account, 'is_merchant_payee', False),
                'color': account.color,
                'full_path': get_account_full_path(account),
                'parent': {
                    'id': account.parent.id,
                    'name': account.parent.name
                } if account.parent else None,
                'balance': float(account_balance),
                'weekly_summary': {
                    'income_total': float(income_total),
                    'expense_total': float(expense_total),
                    'allocation_total': float(allocation_total),
                    'transactions_total': float(total_transactions_amount),
                    'delta': delta,
                },
                'children': children,
                'children_count': len(children),
                'breadcrumb': breadcrumb,
                'recent_transactions': transaction_data,
                'recent_allocations': allocation_data,
                'transaction_count': Transaction.objects.filter(account=account).count(),
                'allocation_count': Allocation.objects.filter(to_account=account).count(),
                'family_week': {
                    'week_start': current_week.start_date.strftime('%Y-%m-%d') if current_week else None,
                    'income_current': float(income_current or 0),
                    # For compatibility, keep keys but note semantics changed: available_current is carry-forward
                    'income_prev': 0.0,
                    'allocated_current': float(Allocation.objects.filter(week=current_week, family=family).aggregate(total=Sum('amount'))['total'] or 0),
                    'available_current': float(available_current or 0),
                    'locks_enabled': ALLOCATION_LOCKS_ENABLED
                }
            }
        })
        
    except Account.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Account not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error loading account details: {str(e)}'}, status=500)


def get_account_full_path(account):
    """Helper function to get full hierarchical path of an account"""
    path_parts = []
    current = account
    while current:
        path_parts.insert(0, current.name)
        current = current.parent
    return ' → '.join(path_parts)
