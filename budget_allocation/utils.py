"""
Budget Allocation Utilities

Provides helper functions for setting up and managing budget allocation
accounts and related functionality.
"""

from django.contrib.auth.models import User
from django.db import transaction
from .models import Account


def setup_default_accounts_for_family(family, user=None):
    """
    Set up default Income and Expense accounts for a new family.
    
    This function creates the basic account structure that every family needs:
    - Income account for tracking all sources of income
    - Expenses account for tracking all spending categories
    
    Args:
        family: Family instance to create accounts for
        user: Optional User instance who triggered the setup (for logging)
    
    Returns:
        dict: Summary of created accounts
    """
    with transaction.atomic():
        created_accounts = Account.setup_default_accounts_for_family(family)
        
        result = {
            'family': family,
            'created_accounts': created_accounts,
            'created_count': len(created_accounts),
            'setup_by': user,
        }
        
        # Log the account creation if we have a user
        if user and created_accounts:
            account_names = [acc.name for acc in created_accounts]
            print(f"Created default accounts for {family.name}: {', '.join(account_names)}")
        
        return result


def auto_setup_accounts_on_family_creation(family, created_by_user=None):
    """
    Automatically set up accounts when a new family is created.
    
    This can be called from family creation signals to ensure
    every new family gets the basic account structure.
    
    Args:
        family: Newly created Family instance
        created_by_user: User who created the family
    
    Returns:
        dict: Account setup result
    """
    return setup_default_accounts_for_family(family, created_by_user)


def get_account_color_suggestions(account_type, family, parent_account=None):
    """
    Get suggested colors for a new account based on type and existing accounts.
    
    Args:
        account_type: 'income' or 'expense'
        family: Family instance
        parent_account: Optional parent account for hierarchical coloring
    
    Returns:
        list: Suggested colors in order of preference
    """
    if account_type == 'income':
        available_colors = Account.INCOME_COLORS
    elif account_type == 'expense':
        available_colors = Account.EXPENSE_COLORS
    else:
        return ['#007bff']  # Default blue for other types
    
    # Get colors already used by accounts of this type in the family
    if parent_account:
        # For child accounts, avoid colors used by siblings
        used_colors = set(
            parent_account.children.values_list('color', flat=True)
        )
    else:
        # For top-level accounts, avoid colors used by other top-level accounts
        used_colors = set(
            Account.objects.filter(
                family=family,
                account_type=account_type,
                parent__isnull=True
            ).values_list('color', flat=True)
        )
    
    # Return available colors, with unused colors first
    suggestions = []
    
    # First, add unused colors
    for color in available_colors:
        if color not in used_colors:
            suggestions.append(color)
    
    # Then add used colors (for cases where all colors are used)
    for color in available_colors:
        if color in used_colors:
            suggestions.append(color)
    
    return suggestions


def validate_account_hierarchy(account, new_parent=None):
    """
    Validate that an account hierarchy change is valid.
    
    Args:
        account: Account instance being modified
        new_parent: Proposed new parent account
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not new_parent:
        return True, None
    
    # Check if new parent is in the same family
    if account.family != new_parent.family:
        return False, "Parent account must be in the same family"
    
    # Check if new parent can have children
    if not new_parent.can_have_children:
        return False, f"Account type '{new_parent.account_type}' cannot have child accounts"
    
    # Check for circular references (account cannot be parent of itself or its ancestors)
    current = new_parent
    while current:
        if current == account:
            return False, "Cannot create circular reference in account hierarchy"
        current = current.parent
    
    # Check type compatibility
    if account.account_type != new_parent.account_type:
        return False, f"Child account type must match parent type ('{new_parent.account_type}')"
    
    return True, None


def get_account_tree_for_family(family, account_type=None, include_inactive=False):
    """
    Get a hierarchical tree structure of accounts for a family.
    
    Args:
        family: Family instance
        account_type: Optional filter by account type ('income', 'expense')
        include_inactive: Whether to include inactive accounts
    
    Returns:
        list: Hierarchical list of accounts with nested children
    """
    # Base queryset
    queryset = Account.objects.filter(family=family)
    
    # Apply filters
    if account_type:
        queryset = queryset.filter(account_type=account_type)
    
    if not include_inactive:
        queryset = queryset.filter(is_active=True)
    
    # Only get user-visible accounts (exclude root accounts)
    queryset = queryset.exclude(account_type='root')
    
    # Order by sort_order and name
    queryset = queryset.order_by('sort_order', 'name')
    
    # Build the tree structure
    accounts_by_parent = {}
    all_accounts = {}
    
    for account in queryset:
        all_accounts[account.id] = account
        parent_id = account.parent_id
        
        if parent_id not in accounts_by_parent:
            accounts_by_parent[parent_id] = []
        accounts_by_parent[parent_id].append(account)
    
    def build_tree(parent_id=None):
        """Recursively build tree structure"""
        children = accounts_by_parent.get(parent_id, [])
        tree = []
        
        for account in children:
            account_data = {
                'account': account,
                'children': build_tree(account.id)
            }
            tree.append(account_data)
        
        return tree
    
    return build_tree()


def get_account_path_display(account):
    """
    Get a display-friendly path for an account showing its hierarchy.
    
    Args:
        account: Account instance
    
    Returns:
        str: Formatted path like "Income > Salary > Base Pay"
    """
    path_parts = []
    current = account
    
    while current:
        if current.is_user_visible:  # Don't include root accounts in display
            path_parts.append(current.name)
        current = current.parent
    
    path_parts.reverse()
    return " > ".join(path_parts)
