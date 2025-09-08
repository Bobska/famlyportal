# Budget Allocation Utilities
from django.db.models import Sum, Q
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta


def get_current_week(family):
    """Get or create the current week for a family"""
    from .models import WeeklyPeriod, FamilySettings
    
    try:
        # Try to get family settings
        settings = FamilySettings.objects.filter(family=family).first()
        week_start_day = settings.week_start_day if settings else 0
    except Exception:
        week_start_day = 0  # Default to Monday
    
    # Get or create current week period
    today = date.today()
    
    # Find the start of the current week
    days_since_week_start = (today.weekday() - week_start_day) % 7
    week_start = today - timedelta(days=days_since_week_start)
    week_end = week_start + timedelta(days=6)
    
    week, created = WeeklyPeriod.objects.get_or_create(
        family=family,
        start_date=week_start,
        defaults={
            'end_date': week_end,
            'is_active': True
        }
    )
    
    return week


def get_available_money(family, week):
    """Calculate available money for allocation this week"""
    from .models import Transaction, Allocation
    
    # Income for the week
    income = Transaction.objects.filter(
        account__family=family,
        week=week,
        transaction_type='income'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Already allocated money
    allocated = Allocation.objects.filter(
        family=family,
        week=week
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Expenses for the week
    expenses = Transaction.objects.filter(
        account__family=family,
        week=week,
        transaction_type='expense'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    return income - allocated - expenses


def transfer_money(from_account, to_account, amount, week, description, loan=None, loan_payment=None):
    """Transfer money between accounts with proper transaction logging"""
    from .models import Transaction
    
    if amount <= 0:
        raise ValidationError("Transfer amount must be positive")
    
    # Check if from_account has sufficient balance
    available_balance = get_account_balance(from_account, week)
    if available_balance < amount:
        raise ValidationError(f"Insufficient funds. Available: ${available_balance}, Required: ${amount}")
    
    # Create outgoing transaction (expense)
    Transaction.objects.create(
        family=from_account.family,
        account=from_account,
        week=week,
        transaction_date=date.today(),
        amount=amount,
        transaction_type='expense',
        description=f"Transfer out: {description}"
    )
    
    # Create incoming transaction (income)
    Transaction.objects.create(
        family=to_account.family,
        account=to_account,
        week=week,
        transaction_date=date.today(),
        amount=amount,
        transaction_type='income',
        description=f"Transfer in: {description}"
    )


def get_account_balance(account, week):
    """Get current balance for an account up to specified week"""
    from .models import Allocation, Transaction
    
    # Get all allocations to this account up to this week
    allocations = Allocation.objects.filter(
        to_account=account,
        week__start_date__lte=week.start_date
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Get all expenses from this account up to this week
    expenses = Transaction.objects.filter(
        account=account,
        week__start_date__lte=week.start_date,
        transaction_type='expense'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Get all income to this account up to this week
    income = Transaction.objects.filter(
        account=account,
        week__start_date__lte=week.start_date,
        transaction_type='income'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    return allocations + income - expenses


def get_account_tree(family):
    """Get hierarchical account tree for family"""
    from .models import Account
    
    accounts = Account.objects.filter(family=family, is_active=True).order_by('sort_order', 'name')
    tree = []
    
    def build_tree(parent_id=None, level=0):
        children = []
        for account in accounts:
            if (parent_id is None and account.parent is None) or \
               (parent_id is not None and account.parent and account.parent.pk == parent_id):
                children.append({
                    'account': account,
                    'level': level,
                    'children': build_tree(account.pk, level + 1)
                })
        return children
    
    return build_tree()


def apply_budget_templates(family, week):
    """Apply budget templates to allocate money automatically"""
    from .models import FamilySettings, BudgetTemplate, Allocation, Account
    
    settings = FamilySettings.objects.filter(family=family).first()
    if not settings or not settings.auto_allocate_enabled:
        return
    
    # Get the income account for the family
    income_account = Account.objects.filter(
        family=family,
        account_type='income'
    ).first()
    
    if not income_account:
        return  # No income account to allocate from
    
    available_money = get_available_money(family, week)
    if available_money <= 0:
        return
    
    templates = BudgetTemplate.objects.filter(
        family=family,
        is_active=True
    ).order_by('priority')
    
    remaining_money = available_money
    
    for template in templates:
        if remaining_money <= 0:
            break
        
        if template.allocation_type == 'percentage' and template.percentage:
            amount = min(
                available_money * (template.percentage / 100),
                remaining_money
            )
        elif template.allocation_type == 'fixed' and template.weekly_amount:
            amount = min(template.weekly_amount, remaining_money)
        else:
            continue  # Skip invalid templates
        
        if amount > 0:
            Allocation.objects.create(
                family=family,
                from_account=income_account,
                to_account=template.account,
                week=week,
                amount=amount,
                notes=f"Auto-allocation: {template.account.name} - {template.allocation_type}"
            )
            remaining_money -= amount
