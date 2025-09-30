from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()


class Category(models.Model):
    """Transaction category scoped to a single user.
    
    Categories help organize transactions by type (Food, Transport, Entertainment, etc.)
    and provide better reporting and budgeting capabilities.
    """
    CATEGORY_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('both', 'Both Income & Expense'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    category_type = models.CharField(
        max_length=10, 
        choices=CATEGORY_TYPE_CHOICES, 
        default='expense',
        help_text="Whether this category applies to income, expenses, or both"
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        unique_together = ['user', 'name']  # Prevent duplicate categories per user
    
    def __str__(self):
        return self.name
    
    def applies_to_type(self, transaction_type):
        """Check if this category applies to the given transaction type."""
        return self.category_type == 'both' or self.category_type == transaction_type
    
    def get_type_display_short(self):
        """Return a short display name for the category type."""
        type_map = {
            'income': 'Income',
            'expense': 'Expense', 
            'both': 'Both'
        }
        return type_map.get(self.category_type, self.category_type)
    
    def get_payees_count(self):
        """Return the number of payees associated with this category."""
        return self.payees.count()
    
    def get_payees_list(self):
        """Return a list of payee names for display purposes."""
        return [payee.name for payee in self.payees.all()]
    
    def get_payees_display(self):
        """Return a comma-separated string of payee names."""
        payees = self.get_payees_list()
        if not payees:
            return "No payees"
        return ", ".join(payees)


class Payee(models.Model):
    """Canonical payee/merchant entry scoped to a single user.

    The unique constraint prevents duplicate payees per user so dropdowns stay clean
    across the UI. Many-to-many relationship with categories allows flexible categorization.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    categories = models.ManyToManyField(
        Category, 
        blank=True, 
        related_name='payees',
        help_text="Categories that this payee/merchant is associated with"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Payee'
        verbose_name_plural = 'Payees'
        unique_together = ['user', 'name']  # Prevent duplicate payees per user
    
    def __str__(self):
        return self.name
    
    def get_categories_list(self):
        """Return a list of category names for display purposes."""
        return [category.name for category in self.categories.all()]
    
    def get_categories_display(self):
        """Return a comma-separated string of category names."""
        categories = self.get_categories_list()
        if not categories:
            return "No categories"
        return ", ".join(categories)


class Income(models.Model):
    """Income transaction captured within the Budget Basic module."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    payee = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True, related_name='income_entries')
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Income'
        verbose_name_plural = 'Income Entries'
    
    def __str__(self):
        return f"{self.payee} - ${self.amount} ({self.date})"


class Expense(models.Model):
    """Expense transaction captured within the Budget Basic module."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    payee = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True, related_name='expense_entries')
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Expense'
        verbose_name_plural = 'Expense Entries'
    
    def __str__(self):
        return f"{self.payee} - ${self.amount} ({self.date})"
