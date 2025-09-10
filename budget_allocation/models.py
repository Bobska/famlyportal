from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta
from core.models import FamilyScopedModel


class AccountManager(models.Manager):
    """Custom manager for Account model"""
    
    def root_accounts(self):
        """Get all root accounts (no parent)"""
        return self.filter(parent__isnull=True)
    
    def income_accounts(self):
        """Get all income accounts"""
        return self.filter(account_type='income')
    
    def spending_accounts(self):
        """Get all spending accounts"""
        return self.filter(account_type='spending')
    
    def by_type(self, account_type):
        """Get accounts by type"""
        return self.filter(account_type=account_type)


class Account(FamilyScopedModel):
    """Hierarchical account structure for budget allocation"""
    
    ACCOUNT_TYPE_CHOICES = [
        ('root', 'Root Account'),
        ('income', 'Income Account'),
        ('expense', 'Expense Account'),  # Changed from 'spending'
    ]
    
    # Color families for auto-assignment
    INCOME_COLORS = ['#28a745', '#20c997', '#198754']  # Green family
    EXPENSE_COLORS = ['#dc3545', '#fd7e14', '#ffc107', '#0d6efd', '#6f42c1']  # Warm colors
    
    name = models.CharField(
        max_length=100,
        help_text="Name of the account"
    )
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
        help_text="Type of account: root, income, or expense"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent account for hierarchical structure"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of what this account is for"
    )
    color = models.CharField(
        max_length=7,
        default='#007bff',
        help_text="Color code for visual representation (hex format)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this account is currently active"
    )
    date_activated = models.DateField(
        null=True,
        blank=True,
        help_text="Date when account was activated"
    )
    date_deactivated = models.DateField(
        null=True,
        blank=True,
        help_text="Date when account was deactivated"
    )
    sort_order = models.IntegerField(
        default=0,
        help_text="Order for sorting accounts within same parent"
    )
    
    objects = AccountManager()
    
    class Meta:
        unique_together = ['family', 'name', 'parent']
        ordering = ['sort_order', 'name']
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
    
    def __str__(self):
        return f"{self.family.name} - {self.full_path}"
    
    def save(self, *args, **kwargs):
        """Override save to auto-assign color if not set"""
        if not self.color or self.color == '#007bff':  # Default blue color
            self.color = self.get_auto_assigned_color()
        super().save(*args, **kwargs)
    
    def get_auto_assigned_color(self):
        """Auto-assign color based on account type and hierarchy"""
        if self.account_type == 'income':
            # Use green family colors for income accounts
            colors = self.INCOME_COLORS
        elif self.account_type == 'expense':
            # Use warm colors for expense accounts
            colors = self.EXPENSE_COLORS
        else:
            # Root accounts or other types use default blue
            return '#007bff'
        
        # If this account has a parent, get colors already used by siblings
        if self.parent:
            sibling_colors = set(
                self.parent.children.exclude(pk=self.pk).values_list('color', flat=True)
            )
            # Find first available color in the family
            for color in colors:
                if color not in sibling_colors:
                    return color
        
        # If no parent, use the first color or cycle through if all colors used
        family_accounts = Account.objects.filter(
            family=self.family, 
            account_type=self.account_type
        ).exclude(pk=self.pk)
        
        used_colors = set(family_accounts.values_list('color', flat=True))
        
        # Find first available color
        for color in colors:
            if color not in used_colors:
                return color
        
        # If all colors used, cycle through them
        return colors[family_accounts.count() % len(colors)]
    
    @property
    def is_user_visible(self):
        """Returns False for root accounts that should be hidden from users"""
        return self.account_type != 'root'
    
    @property
    def can_have_children(self):
        """Returns True for accounts that can have child accounts"""
        return self.account_type in ['income', 'expense']
    
    @classmethod
    def setup_default_accounts_for_family(cls, family):
        """Create default Income and Expense accounts for new family"""
        created_accounts = []
        
        # Create Income account if it doesn't exist
        income_account, created = cls.objects.get_or_create(
            family=family,
            name='Income',
            account_type='income',
            defaults={
                'description': 'All sources of income for your family',
                'color': cls.INCOME_COLORS[0],
                'sort_order': 1,
                'is_active': True,
            }
        )
        if created:
            created_accounts.append(income_account)
        
        # Create Expense account if it doesn't exist
        expense_account, created = cls.objects.get_or_create(
            family=family,
            name='Expenses',
            account_type='expense',
            defaults={
                'description': 'All family expenses and spending categories',
                'color': cls.EXPENSE_COLORS[0],
                'sort_order': 2,
                'is_active': True,
            }
        )
        if created:
            created_accounts.append(expense_account)
        
        return created_accounts
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        # Root accounts cannot have parents
        if self.account_type == 'root' and self.parent:
            raise ValidationError("Root accounts cannot have a parent")
        
        # Non-root accounts must have parents
        if self.account_type != 'root' and not self.parent:
            raise ValidationError("Non-root accounts must have a parent")
        
        # Cannot be parent of itself
        if self.parent and self.parent == self:
            raise ValidationError("Account cannot be its own parent")
    
    def activate(self):
        """Activate the account"""
        self.is_active = True
        self.date_activated = date.today()
        self.date_deactivated = None
        self.save()
    
    def deactivate(self):
        """Deactivate the account"""
        self.is_active = False
        self.date_deactivated = date.today()
        self.save()
    
    @property
    def current_balance(self):
        """Calculate current balance including child accounts"""
        from .utilities import get_current_week, get_account_balance_with_children
        
        try:
            current_week = get_current_week(self.family)
            return get_account_balance_with_children(self, current_week)
        except Exception:
            # Fallback if there's any issue with week calculation
            return Decimal('0.00')
    
    @property
    def account_only_balance(self):
        """Calculate balance for this account only (excluding children)"""
        from .utilities import get_current_week, get_account_balance
        
        try:
            current_week = get_current_week(self.family)
            return get_account_balance(self, current_week)
        except Exception:
            # Fallback if there's any issue with week calculation
            return Decimal('0.00')
    
    def get_allocated_amount(self, week=None):
        """Get total amount allocated to this account for a specific week"""
        # Placeholder implementation
        return Decimal('0.00')
    
    def get_spent_amount(self, week=None):
        """Get total amount spent from this account for a specific week"""
        # Placeholder implementation
        return Decimal('0.00')
    
    @property
    def full_path(self):
        """Get full hierarchical path (e.g., 'Spending > Food > Groceries')"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name


class AccountHistoryManager(models.Manager):
    """Custom manager for AccountHistory model"""
    
    def for_account(self, account):
        """Get history for specific account"""
        return self.filter(account=account)
    
    def activations(self):
        """Get activation events"""
        return self.filter(action='activated')
    
    def deactivations(self):
        """Get deactivation events"""
        return self.filter(action='deactivated')


class AccountHistory(FamilyScopedModel):
    """Track account activation/deactivation events"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('activated', 'Activated'),
        ('deactivated', 'Deactivated'),
        ('renamed', 'Renamed'),
        ('moved', 'Moved'),
    ]
    
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='history',
        help_text="Account this history entry relates to"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Type of action performed"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When the action occurred"
    )
    old_value = models.TextField(
        blank=True,
        help_text="Previous value before change"
    )
    new_value = models.TextField(
        blank=True,
        help_text="New value after change"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the change"
    )
    
    objects = AccountHistoryManager()
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Account History'
        verbose_name_plural = 'Account Histories'
    
    def __str__(self):
        return f"{self.account.name} - {self.get_action_display()} ({self.timestamp.date()})"


class WeeklyPeriodManager(models.Manager):
    """Custom manager for WeeklyPeriod model"""
    
    def get_current_week(self, family):
        """Get the current week for a family"""
        today = date.today()
        try:
            settings = FamilySettings.objects.get(family=family)
            week_start = settings.week_start_day
        except FamilySettings.DoesNotExist:
            week_start = 0  # Monday default
        
        # Calculate start of current week
        days_since_start = (today.weekday() - week_start) % 7
        start_date = today - timedelta(days=days_since_start)
        
        return self.filter(
            family=family,
            start_date=start_date
        ).first()
    
    def get_or_create_week(self, family, start_date=None):
        """Get or create a week period"""
        if start_date is None:
            start_date = date.today()
        
        try:
            settings = FamilySettings.objects.get(family=family)
            week_start = settings.week_start_day
        except FamilySettings.DoesNotExist:
            week_start = 0  # Monday default
        
        # Calculate start of week
        days_since_start = (start_date.weekday() - week_start) % 7
        week_start_date = start_date - timedelta(days=days_since_start)
        week_end_date = week_start_date + timedelta(days=6)
        
        week, created = self.get_or_create(
            family=family,
            start_date=week_start_date,
            defaults={
                'end_date': week_end_date,
                'is_active': True,
                'is_allocated': False,
                'allocation_locked': False,
            }
        )
        return week, created


class WeeklyPeriod(FamilyScopedModel):
    """Weekly budget cycles (Monday-Sunday configurable)"""
    
    start_date = models.DateField(
        help_text="Start date of the weekly period"
    )
    end_date = models.DateField(
        help_text="End date of the weekly period"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this week is currently active"
    )
    is_allocated = models.BooleanField(
        default=False,
        help_text="Whether budget has been allocated for this week"
    )
    allocation_locked = models.BooleanField(
        default=False,
        help_text="Whether allocations are locked for this week"
    )
    
    objects = WeeklyPeriodManager()
    
    class Meta:
        unique_together = ['family', 'start_date']
        ordering = ['-start_date']
        verbose_name = 'Weekly Period'
        verbose_name_plural = 'Weekly Periods'
    
    def __str__(self):
        return f"{self.family.name} - Week {self.start_date} to {self.end_date}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date")
    
    @property
    def total_income(self):
        """Calculate total income for this week"""
        # This would sum all income transactions for this week
        return Decimal('0.00')
    
    @property
    def total_allocated(self):
        """Calculate total amount allocated for this week"""
        # This would sum all allocations for this week
        return Decimal('0.00')
    
    @property
    def available_to_allocate(self):
        """Calculate amount still available to allocate"""
        return self.total_income - self.total_allocated


class BudgetTemplate(FamilyScopedModel):
    """Smart budget planning with multiple allocation types"""
    
    ALLOCATION_TYPE_CHOICES = [
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage of Income'),
        ('range', 'Range Based'),
        ('calculated', 'Calculated Amount'),
    ]
    
    PRIORITY_CHOICES = [
        (1, 'Priority 1 (Highest)'),
        (2, 'Priority 2'),
        (3, 'Priority 3'),
        (4, 'Priority 4'),
        (5, 'Priority 5 (Lowest)'),
    ]
    
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='budget_templates',
        help_text="Account this template applies to"
    )
    allocation_type = models.CharField(
        max_length=20,
        choices=ALLOCATION_TYPE_CHOICES,
        help_text="How the allocation amount is calculated"
    )
    weekly_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Fixed weekly amount (for fixed allocation type)"
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage of income (for percentage allocation type)"
    )
    min_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum amount (for range allocation type)"
    )
    max_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum amount (for range allocation type)"
    )
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=3,
        help_text="Priority level for allocation (1=highest, 5=lowest)"
    )
    is_essential = models.BooleanField(
        default=False,
        help_text="Whether this is an essential allocation"
    )
    never_miss = models.BooleanField(
        default=False,
        help_text="Whether this allocation should never be skipped"
    )
    auto_allocate = models.BooleanField(
        default=True,
        help_text="Whether to automatically allocate this amount"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this template is currently active"
    )
    
    # Bill planning fields
    annual_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual amount for bill planning"
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Due date for bill planning"
    )
    current_saved = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount currently saved for this bill"
    )
    
    class Meta:
        unique_together = ['family', 'account']
        ordering = ['priority', 'account__name']
        verbose_name = 'Budget Template'
        verbose_name_plural = 'Budget Templates'
    
    def __str__(self):
        return f"{self.account.name} - {self.get_allocation_type_display()}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.allocation_type == 'fixed' and not self.weekly_amount:
            raise ValidationError("Fixed allocation type requires weekly_amount")
        
        if self.allocation_type == 'percentage' and not self.percentage:
            raise ValidationError("Percentage allocation type requires percentage")
        
        if self.allocation_type == 'range' and (not self.min_amount or not self.max_amount):
            raise ValidationError("Range allocation type requires min_amount and max_amount")
    
    def calculate_allocation_amount(self, weekly_income=None):
        """Calculate allocation amount based on type and income"""
        if self.allocation_type == 'fixed':
            return self.weekly_amount or Decimal('0.00')
        
        if self.allocation_type == 'percentage' and weekly_income:
            return (weekly_income * self.percentage / 100).quantize(Decimal('0.01'))
        
        if self.allocation_type == 'range' and weekly_income and self.min_amount and self.max_amount:
            calculated = (weekly_income * self.percentage / 100).quantize(Decimal('0.01'))
            return max(self.min_amount, min(self.max_amount, calculated))
        
        # For calculated type, implement custom logic
        return Decimal('0.00')
    
    def calculate_weekly_amount(self):
        """Calculate weekly amount for bill planning"""
        if self.annual_amount and self.due_date:
            weeks_until_due = max(1, (self.due_date - date.today()).days // 7)
            needed_amount = self.annual_amount - self.current_saved
            return (needed_amount / weeks_until_due).quantize(Decimal('0.01'))
        return Decimal('0.00')
    
    def can_skip_if_insufficient_funds(self):
        """Check if this allocation can be skipped if funds are insufficient"""
        return not self.is_essential and not self.never_miss


class Allocation(FamilyScopedModel):
    """Money movements between accounts"""
    
    week = models.ForeignKey(
        WeeklyPeriod,
        on_delete=models.CASCADE,
        related_name='allocations',
        help_text="Week this allocation belongs to"
    )
    from_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='allocations_from',
        help_text="Account money is allocated from"
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='allocations_to',
        help_text="Account money is allocated to"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount being allocated"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes about this allocation"
    )
    
    class Meta:
        ordering = ['-week__start_date', 'to_account__name']
        verbose_name = 'Allocation'
        verbose_name_plural = 'Allocations'
    
    def __str__(self):
        return f"{self.from_account.name} → {self.to_account.name}: ${self.amount}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.amount is not None and self.amount <= 0:
            raise ValidationError("Amount must be greater than 0")
        
        if hasattr(self, 'from_account') and hasattr(self, 'to_account') and self.from_account == self.to_account:
            raise ValidationError("Cannot allocate from account to itself")
        
        # Check that both accounts belong to same family
        if (hasattr(self, 'from_account') and hasattr(self, 'to_account') and 
            self.from_account and self.to_account and 
            self.from_account.family != self.to_account.family):
            raise ValidationError("Both accounts must belong to the same family")


class TransactionManager(models.Manager):
    """Custom manager for Transaction model"""
    
    def for_week(self, week):
        """Get transactions for specific week"""
        return self.filter(week=week)
    
    def income_transactions(self):
        """Get income transactions"""
        return self.filter(transaction_type='income')
    
    def expense_transactions(self):
        """Get expense transactions"""
        return self.filter(transaction_type='expense')


class Transaction(FamilyScopedModel):
    """Income and expense recording"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    
    # Override family field to avoid clash with household_budget.Transaction
    family = models.ForeignKey(
        'accounts.Family',
        on_delete=models.CASCADE,
        related_name='budget_allocation_transactions',
        help_text="Family this record belongs to"
    )
    
    week = models.ForeignKey(
        WeeklyPeriod,
        on_delete=models.CASCADE,
        related_name='allocation_transactions',
        null=True,
        blank=True,
        help_text="Week this transaction belongs to (auto-assigned if not specified)"
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='allocation_transactions',
        help_text="Account this transaction affects"
    )
    transaction_date = models.DateField(
        help_text="Date when transaction occurred"
    )
    description = models.CharField(
        max_length=200,
        help_text="Description of the transaction"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Transaction amount"
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text="Type of transaction: income or expense"
    )
    payee = models.CharField(
        max_length=100,
        blank=True,
        help_text="Who the transaction was with"
    )
    reference = models.CharField(
        max_length=50,
        blank=True,
        help_text="Reference number or ID"
    )
    is_reconciled = models.BooleanField(
        default=False,
        help_text="Whether this transaction has been reconciled"
    )
    
    objects = TransactionManager()
    
    class Meta:
        ordering = ['-transaction_date', '-created_at']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
    
    def __str__(self):
        return f"{self.account.name} - {self.description}: ${self.amount}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.amount is not None and self.amount <= 0:
            raise ValidationError("Amount must be greater than 0")


class AccountLoanManager(models.Manager):
    """Custom manager for AccountLoan model"""
    
    def active_loans(self):
        """Get active loans"""
        return self.filter(is_active=True)
    
    def for_account(self, account):
        """Get loans involving specific account (as lender or borrower)"""
        return self.filter(
            models.Q(lender_account=account) | models.Q(borrower_account=account)
        )


class AccountLoan(FamilyScopedModel):
    """Inter-account lending with weekly interest"""
    
    lender_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='loans_as_lender',
        help_text="Account lending the money"
    )
    borrower_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='loans_as_borrower',
        help_text="Account borrowing the money"
    )
    original_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Original loan amount"
    )
    remaining_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount still owed"
    )
    weekly_interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        help_text="Weekly interest rate (as decimal, e.g. 0.0200 for 2%)"
    )
    loan_date = models.DateField(
        help_text="Date when loan was created"
    )
    total_interest_charged = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total interest charged so far"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this loan is still active"
    )
    
    objects = AccountLoanManager()
    
    class Meta:
        ordering = ['-loan_date']
        verbose_name = 'Account Loan'
        verbose_name_plural = 'Account Loans'
    
    def __str__(self):
        return f"{self.lender_account.name} → {self.borrower_account.name}: ${self.remaining_amount}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.original_amount is not None and self.original_amount <= 0:
            raise ValidationError("Original amount must be greater than 0")
        
        if self.remaining_amount is not None and self.remaining_amount < 0:
            raise ValidationError("Remaining amount cannot be negative")
        
        # Only validate accounts if both IDs are set (not None)
        if self.lender_account_id and self.borrower_account_id and self.lender_account_id == self.borrower_account_id:
            raise ValidationError("Cannot loan from account to itself")
        
        # Check that both accounts belong to same family (only if both are set)
        if self.lender_account_id and self.borrower_account_id:
            try:
                if self.lender_account.family != self.borrower_account.family:
                    raise ValidationError("Both accounts must belong to the same family")
            except (Account.DoesNotExist, AttributeError):
                # Skip validation if accounts don't exist yet
                pass
    
    def calculate_weekly_interest(self):
        """Calculate weekly interest on remaining amount"""
        return (self.remaining_amount * self.weekly_interest_rate).quantize(Decimal('0.01'))
    
    def add_interest(self):
        """Add weekly interest to remaining amount"""
        if self.is_active and self.remaining_amount > 0:
            interest = self.calculate_weekly_interest()
            self.remaining_amount += interest
            self.total_interest_charged += interest
            self.save()
            return interest
        return Decimal('0.00')
    
    def make_payment(self, amount):
        """Make a payment towards the loan"""
        if amount <= 0:
            raise ValueError("Payment amount must be greater than 0")
        
        if amount > self.remaining_amount:
            amount = self.remaining_amount
        
        self.remaining_amount -= amount
        
        if self.remaining_amount <= 0:
            self.is_active = False
            self.remaining_amount = Decimal('0.00')
        
        self.save()
        return amount


class LoanPaymentManager(models.Manager):
    """Custom manager for LoanPayment model"""
    
    def for_loan(self, loan):
        """Get payments for specific loan"""
        return self.filter(loan=loan)


class LoanPayment(FamilyScopedModel):
    """Loan repayment tracking"""
    
    loan = models.ForeignKey(
        AccountLoan,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="Loan this payment is for"
    )
    week = models.ForeignKey(
        WeeklyPeriod,
        on_delete=models.CASCADE,
        related_name='loan_payments',
        help_text="Week this payment was made"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Payment amount"
    )
    payment_date = models.DateField(
        help_text="Date when payment was made"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes about this payment"
    )
    
    objects = LoanPaymentManager()
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Loan Payment'
        verbose_name_plural = 'Loan Payments'
    
    def __str__(self):
        return f"Payment ${self.amount} for {self.loan}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.amount is not None and self.amount <= 0:
            raise ValidationError("Payment amount must be greater than 0")


class FamilySettingsManager(models.Manager):
    """Custom manager for FamilySettings model"""
    
    def get_for_family(self, family):
        """Get settings for family, creating defaults if needed"""
        settings, created = self.get_or_create(
            family=family,
            defaults={
                'week_start_day': 0,  # Monday
                'default_interest_rate': Decimal('0.0200'),  # 2%
                'auto_allocate_enabled': True,
                'auto_repay_enabled': False,
                'notification_threshold': Decimal('100.00'),
            }
        )
        return settings


class FamilySettings(FamilyScopedModel):
    """Configurable family preferences"""
    
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    week_start_day = models.IntegerField(
        choices=WEEKDAY_CHOICES,
        default=0,
        help_text="Day of week when budget week starts (0=Monday, 6=Sunday)"
    )
    default_interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.0200'),
        help_text="Default weekly interest rate for loans (as decimal)"
    )
    auto_allocate_enabled = models.BooleanField(
        default=True,
        help_text="Whether to automatically allocate budget based on templates"
    )
    auto_repay_enabled = models.BooleanField(
        default=False,
        help_text="Whether to automatically repay loans when possible"
    )
    notification_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('100.00'),
        help_text="Threshold amount for notifications"
    )
    
    objects = FamilySettingsManager()
    
    class Meta:
        verbose_name = 'Family Settings'
        verbose_name_plural = 'Family Settings'
    
    def __str__(self):
        return f"{self.family.name} - Settings"
