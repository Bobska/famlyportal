from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel, FamilyScopedModel

User = get_user_model()


class BudgetCategoryManager(models.Manager):
    """Custom manager for BudgetCategory model"""
    
    def active(self):
        """Return active categories"""
        return self.filter(is_active=True)
    
    def by_type(self, category_type):
        """Return categories by type"""
        return self.filter(category_type=category_type)
    
    def income_categories(self):
        """Return income categories"""
        return self.filter(category_type='income')
    
    def expense_categories(self):
        """Return expense categories"""
        return self.filter(category_type='expense')


class BudgetCategory(FamilyScopedModel):
    """Budget category for organizing income and expenses"""
    
    CATEGORY_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    
    name = models.CharField(
        max_length=100,
        help_text="Category name (e.g., Salary, Groceries, Utilities)"
    )
    description = models.TextField(
        blank=True,
        help_text="Category description"
    )
    category_type = models.CharField(
        max_length=10,
        choices=CATEGORY_TYPE_CHOICES,
        help_text="Whether this is income or expense category"
    )
    color = models.CharField(
        max_length=7,
        default='#007bff',
        help_text="Hex color code for UI display"
    )
    is_essential = models.BooleanField(
        default=False,
        help_text="Whether this is an essential category (needs vs wants)"
    )
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Parent category for subcategories"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this category is active"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Order for displaying categories"
    )
    
    objects = BudgetCategoryManager()
    
    class Meta:
        unique_together = ['family', 'name', 'category_type']
        ordering = ['category_type', 'sort_order', 'name']
        verbose_name = 'Budget Category'
        verbose_name_plural = 'Budget Categories'
    
    def __str__(self):
        return f"{self.name} ({dict(self.CATEGORY_TYPE_CHOICES)[self.category_type]})"


class BudgetManager(models.Manager):
    """Custom manager for Budget model"""
    
    def current(self):
        """Return current active budget"""
        return self.filter(is_active=True).first()
    
    def for_month(self, year, month):
        """Return budget for specific month"""
        return self.filter(
            start_date__year__lte=year,
            start_date__month__lte=month
        ).filter(
            models.Q(end_date__isnull=True) |
            models.Q(end_date__year__gte=year, end_date__month__gte=month)
        ).first()


class Budget(FamilyScopedModel):
    """Main budget model for family budgets"""
    name = models.CharField(
        max_length=100,
        help_text="Budget name (e.g., '2024 Family Budget')"
    )
    description = models.TextField(
        blank=True,
        help_text="Budget description"
    )
    start_date = models.DateField(
        help_text="Budget start date"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Budget end date (leave blank for ongoing)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this budget is currently active"
    )
    
    objects = BudgetManager()
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Budget'
        verbose_name_plural = 'Budgets'
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.end_date and self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date.")
        
        # Only one active budget per family
        if self.is_active:
            active_budgets = Budget.objects.filter(
                family=self.family,
                is_active=True
            )
            if self.pk:
                active_budgets = active_budgets.exclude(pk=self.pk)
            
            if active_budgets.exists():
                raise ValidationError(
                    "Only one budget can be active at a time. "
                    "Please deactivate other budgets first."
                )
    
    @property
    def total_income_budgeted(self):
        """Calculate total budgeted income"""
        return BudgetItem.objects.filter(
            budget=self,
            category__category_type='income'
        ).aggregate(
            total=models.Sum('budgeted_amount')
        )['total'] or Decimal('0.00')
    
    @property
    def total_expenses_budgeted(self):
        """Calculate total budgeted expenses"""
        return BudgetItem.objects.filter(
            budget=self,
            category__category_type='expense'
        ).aggregate(
            total=models.Sum('budgeted_amount')
        )['total'] or Decimal('0.00')
    
    @property
    def net_budget(self):
        """Calculate net budget (income - expenses)"""
        return self.total_income_budgeted - self.total_expenses_budgeted


class BudgetItemManager(models.Manager):
    """Custom manager for BudgetItem model"""
    
    def for_budget(self, budget):
        """Return items for specific budget"""
        return self.filter(budget=budget)
    
    def by_category(self, category):
        """Return items by category"""
        return self.filter(category=category)
    
    def income_items(self):
        """Return income budget items"""
        return self.filter(category__category_type='income')
    
    def expense_items(self):
        """Return expense budget items"""
        return self.filter(category__category_type='expense')


class BudgetItem(BaseModel):
    """Budget item for specific category within a budget"""
    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        help_text="Budget this item belongs to"
    )
    category = models.ForeignKey(
        BudgetCategory,
        on_delete=models.CASCADE,
        help_text="Budget category"
    )
    budgeted_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Budgeted amount for this category"
    )
    actual_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Actual amount spent/earned (auto-calculated from transactions)"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes about this budget item"
    )
    
    objects = BudgetItemManager()
    
    class Meta:
        unique_together = ['budget', 'category']
        ordering = ['category__category_type', 'category__sort_order', 'category__name']
        verbose_name = 'Budget Item'
        verbose_name_plural = 'Budget Items'
    
    def __str__(self):
        return f"{self.category.name} - ${self.budgeted_amount}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.budgeted_amount < 0:
            raise ValidationError("Budgeted amount cannot be negative.")
        
        # Ensure category belongs to same family as budget
        if self.category.family != self.budget.family:
            raise ValidationError("Category must belong to the same family as the budget.")
    
    @property
    def variance(self):
        """Calculate variance (actual - budgeted)"""
        if self.category.category_type == 'income':
            return self.actual_amount - self.budgeted_amount
        else:  # expense
            return self.budgeted_amount - self.actual_amount
    
    @property
    def variance_percentage(self):
        """Calculate variance as percentage"""
        if self.budgeted_amount == 0:
            return None
        return (self.variance / self.budgeted_amount) * 100
    
    @property
    def is_over_budget(self):
        """Check if over budget"""
        if self.category.category_type == 'income':
            return self.actual_amount < self.budgeted_amount
        else:  # expense
            return self.actual_amount > self.budgeted_amount


class TransactionManager(models.Manager):
    """Custom manager for Transaction model"""
    
    def for_month(self, year, month):
        """Return transactions for specific month"""
        return self.filter(
            transaction_date__year=year,
            transaction_date__month=month
        )
    
    def by_category(self, category):
        """Return transactions by category"""
        return self.filter(category=category)
    
    def income_transactions(self):
        """Return income transactions"""
        return self.filter(category__category_type='income')
    
    def expense_transactions(self):
        """Return expense transactions"""
        return self.filter(category__category_type='expense')


class Transaction(FamilyScopedModel):
    """Transaction model for budget tracking"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
    ]
    
    transaction_date = models.DateField(
        help_text="Date of transaction"
    )
    description = models.CharField(
        max_length=200,
        help_text="Transaction description"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Transaction amount"
    )
    category = models.ForeignKey(
        BudgetCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Budget category for this transaction"
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text="Type of transaction"
    )
    payee = models.CharField(
        max_length=100,
        blank=True,
        help_text="Who the transaction was with"
    )
    account = models.CharField(
        max_length=100,
        blank=True,
        help_text="Account used for transaction"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )
    receipt_image = models.ImageField(
        upload_to='receipts/',
        blank=True,
        null=True,
        help_text="Receipt image"
    )
    is_reconciled = models.BooleanField(
        default=False,
        help_text="Whether transaction has been reconciled"
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Transaction reference number"
    )
    
    objects = TransactionManager()
    
    class Meta:
        ordering = ['-transaction_date', '-created_at']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
    
    def __str__(self):
        return f"{self.description} - ${self.amount} ({self.transaction_date})"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.amount <= 0:
            raise ValidationError("Transaction amount must be greater than zero.")
        
        if self.transaction_date > timezone.now().date():
            raise ValidationError("Transaction date cannot be in the future.")
        
        # Ensure category type matches transaction type
        if self.category and self.category.category_type != self.transaction_type:
            if self.transaction_type != 'transfer':  # Transfers can use any category
                raise ValidationError(
                    f"Transaction type '{self.transaction_type}' doesn't match "
                    f"category type '{self.category.category_type}'."
                )


class SavingsGoalManager(models.Manager):
    """Custom manager for SavingsGoal model"""
    
    def active(self):
        """Return active savings goals"""
        return self.filter(is_active=True)
    
    def achieved(self):
        """Return achieved savings goals"""
        return self.filter(current_amount__gte=models.F('target_amount'))


class SavingsGoal(FamilyScopedModel):
    """Savings goal model for tracking family savings targets"""
    name = models.CharField(
        max_length=100,
        help_text="Savings goal name (e.g., 'Emergency Fund', 'Vacation')"
    )
    description = models.TextField(
        blank=True,
        help_text="Goal description"
    )
    target_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Target amount to save"
    )
    current_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Current amount saved"
    )
    target_date = models.DateField(
        null=True,
        blank=True,
        help_text="Target date to achieve goal"
    )
    monthly_contribution = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Planned monthly contribution"
    )
    priority = models.PositiveIntegerField(
        default=1,
        help_text="Goal priority (1 = highest)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this goal is active"
    )
    
    objects = SavingsGoalManager()
    
    class Meta:
        ordering = ['priority', 'target_date']
        verbose_name = 'Savings Goal'
        verbose_name_plural = 'Savings Goals'
    
    def __str__(self):
        return f"{self.name} (${self.current_amount}/${self.target_amount})"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.target_amount <= 0:
            raise ValidationError("Target amount must be greater than zero.")
        
        if self.current_amount < 0:
            raise ValidationError("Current amount cannot be negative.")
        
        if self.target_date and self.target_date <= timezone.now().date():
            raise ValidationError("Target date must be in the future.")
        
        if self.monthly_contribution is not None and self.monthly_contribution < 0:
            raise ValidationError("Monthly contribution cannot be negative.")
    
    @property
    def progress_percentage(self):
        """Calculate progress as percentage"""
        if self.target_amount == 0:
            return 0
        return min((self.current_amount / self.target_amount) * 100, 100)
    
    @property
    def remaining_amount(self):
        """Calculate remaining amount to reach goal"""
        return max(self.target_amount - self.current_amount, Decimal('0.00'))
    
    @property
    def is_achieved(self):
        """Check if goal is achieved"""
        return self.current_amount >= self.target_amount
    
    @property
    def months_to_target(self):
        """Calculate months to reach target based on monthly contribution"""
        if not self.monthly_contribution or self.monthly_contribution <= 0:
            return None
        if self.is_achieved:
            return 0
        return int((self.remaining_amount / self.monthly_contribution).quantize(Decimal('1')))
    
    def add_contribution(self, amount, description=''):
        """Add contribution to savings goal"""
        if amount <= 0:
            raise ValidationError("Contribution amount must be greater than zero.")
        
        self.current_amount += amount
        self.save()
        
        # Create transaction record
        Transaction.objects.create(
            family=self.family,
            transaction_date=timezone.now().date(),
            description=f"Contribution to {self.name}: {description}".strip(),
            amount=amount,
            transaction_type='expense',  # Money going to savings
            notes=f"Savings goal contribution: {self.name}"
        )
