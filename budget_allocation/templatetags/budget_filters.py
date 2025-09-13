from django import template
from decimal import Decimal
from ..utilities import (
    get_account_weekly_balance_with_children,
    get_current_week,
    get_account_balance_with_children,
)
from ..models import Transaction
from django.db.models import Sum

register = template.Library()

@register.filter
def order_by_children_count(queryset):
    """
    Custom template filter to order accounts by number of children (descending), then by name.
    """
    if not queryset:
        return queryset
    
    # Convert QuerySet to list and sort by children count (descending), then by name
    accounts_list = list(queryset)
    
    def get_children_count(account):
        """Get count of active children for an account"""
        return account.children.filter(is_active=True).count()
    
    # Sort by children count (descending), then by name (ascending)
    accounts_list.sort(key=lambda account: (-get_children_count(account), account.name.lower()))
    
    return accounts_list

@register.filter
def active_children_ordered(account):
    """
    Get active children of an account ordered by children count (descending), then by name.
    """
    active_children = account.children.filter(is_active=True)
    return order_by_children_count(active_children)

# New filters for template logic
@register.filter
def active_children_count(account):
    """
    Return the count of active children for an account.
    """
    return account.children.filter(is_active=True).count()

@register.filter
def active_children_exist(account):
    """
    Return True if the account has any active children.
    """
    return account.children.filter(is_active=True).exists()

@register.filter
def weekly_balance_with_children(account, week):
    """Return weekly balance including children for a given week."""
    try:
        return get_account_weekly_balance_with_children(account, week)
    except Exception:
        return Decimal('0.00')

@register.filter
def current_balance_with_children(account):
    """Return current balance including children using current week context."""
    try:
        week = get_current_week(account.family)
        return get_account_balance_with_children(account, week)
    except Exception:
        return Decimal('0.00')


@register.simple_tag
def recent_transactions_for_account(account, limit=5):
    """Return recent transactions for an account including its active descendants.

    Args:
        account: Account instance to fetch transactions for.
        limit: Max number of transactions to return.
    Returns:
        Queryset/list of Transaction objects ordered by most recent.
    """
    try:
        # Collect account and all active descendant account IDs
        def collect_descendant_ids(acc):
            ids = [acc.id]
            for child in acc.children.filter(is_active=True):
                ids.extend(collect_descendant_ids(child))
            return ids

        account_ids = collect_descendant_ids(account)

        qs = (
            Transaction.objects.filter(
                family=account.family, account_id__in=account_ids
            )
            .order_by("-transaction_date", "-created_at")
        )
        return list(qs[: int(limit) if limit else 5])
    except Exception:
        return []


@register.filter
def total_transactions_with_children(account):
    """Sum transactions for an account (and active descendants) across all time.

    Logic:
    - For income accounts: sum only income transactions
    - For expense accounts: sum only expense transactions
    - For other types: return 0.00
    """
    try:
        # Collect account and all active descendant account IDs
        def collect_descendant_ids(acc):
            ids = [acc.id]
            for child in acc.children.filter(is_active=True):
                ids.extend(collect_descendant_ids(child))
            return ids

        account_ids = collect_descendant_ids(account)

        tx_type = 'income' if account.account_type == 'income' else (
            'expense' if account.account_type == 'expense' else None
        )
        if not tx_type:
            return Decimal('0.00')

        total = (
            Transaction.objects.filter(
                family=account.family,
                account_id__in=account_ids,
                transaction_type=tx_type,
            ).aggregate(total=Sum('amount'))['total']
            or Decimal('0.00')
        )
        return total
    except Exception:
        return Decimal('0.00')


@register.simple_tag
def weekly_transactions_with_children(account, week):
    """Sum transactions for an account (and active descendants) for a specific week.

    Uses account type to decide whether to sum income or expense transactions.
    """
    try:
        def collect_descendant_ids(acc):
            ids = [acc.id]
            for child in acc.children.filter(is_active=True):
                ids.extend(collect_descendant_ids(child))
            return ids

        account_ids = collect_descendant_ids(account)
        tx_type = 'income' if account.account_type == 'income' else (
            'expense' if account.account_type == 'expense' else None
        )
        if not tx_type:
            return Decimal('0.00')

        total = (
            Transaction.objects.filter(
                family=account.family,
                account_id__in=account_ids,
                week=week,
                transaction_type=tx_type,
            ).aggregate(total=Sum('amount'))['total']
            or Decimal('0.00')
        )
        return total
    except Exception:
        return Decimal('0.00')