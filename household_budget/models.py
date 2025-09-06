from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel, FamilyScopedModel

User = get_user_model()


class CategoryManager(models.Manager):
    """Custom manager for Category model"""
    
    def active(self):
        """Return active categories"""
        return self.filter(is_active=True)
    
    def root_categories(self):
        """Return root categories (no parent)"""
        return self.filter(parent__isnull=True, is_active=True)
    
    def by_family(self, family):
        """Return categories for specific family"""
        return self.filter(family=family, is_active=True)


class Category(FamilyScopedModel):
    """Hierarchical category model for transactions"""
    
    name = models.CharField(
        max_length=100,
        help_text="Category name (e.g., Groceries, Salary, Entertainment)"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Parent category for hierarchical structure"
    )
    icon = models.CharField(
        max_length=50,
        default='bi-folder',
        help_text="Bootstrap icon class (e.g., bi-cart, bi-house)"
    )
    color = models.CharField(
        max_length=7,
        default='#007bff',
        help_text="Hex color code for UI display"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this category is active"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Order for displaying categories"
    )
    
    objects = CategoryManager()
    
    class Meta:
        unique_together = ['family', 'name', 'parent']
        ordering = ['sort_order', 'name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def get_full_path(self):
        """Get full category path for display"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name
    
    def get_children(self):
        """Get child categories"""
        return Category.objects.filter(parent=self, is_active=True).order_by('sort_order', 'name')
    
    def has_children(self):
        """Check if category has children"""
        return self.get_children().exists()


class TransactionManager(models.Manager):
    """Custom manager for Transaction model"""
    
    def income(self):
        """Return income transactions"""
        return self.filter(transaction_type='income')
    
    def expenses(self):
        """Return expense transactions"""
        return self.filter(transaction_type='expense')
    
    def transfers(self):
        """Return transfer transactions"""
        return self.filter(transaction_type='transfer')
    
    def for_month(self, year, month):
        """Return transactions for specific month"""
        return self.filter(date__year=year, date__month=month)
    
    def for_category(self, category):
        """Return transactions for specific category and its children"""
        category_ids = [category.pk]
        # Include child categories
        for child in category.get_children():
            category_ids.append(child.pk)
        return self.filter(category_id__in=category_ids)


class Transaction(FamilyScopedModel):
    """Simplified transaction model"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
    ]
    
    merchant_payee = models.CharField(
        max_length=200,
        help_text="Who you paid or received money from"
    )
    date = models.DateField(
        help_text="Transaction date"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Transaction amount"
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text="Type of transaction"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Transaction category"
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional notes"
    )
    
    objects = TransactionManager()
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        indexes = [
            models.Index(fields=['family', 'date']),
            models.Index(fields=['family', 'transaction_type']),
            models.Index(fields=['family', 'category']),
        ]
    
    def __str__(self):
        type_display = dict(self.TRANSACTION_TYPE_CHOICES)[self.transaction_type]
        return f"{self.merchant_payee} - ${self.amount} ({type_display})"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.amount is not None and self.amount <= 0:
            raise ValidationError("Amount must be greater than 0.")
        
        if self.date and self.date > timezone.now().date():
            raise ValidationError("Transaction date cannot be in the future.")
    
    @property
    def display_amount(self):
        """Format amount for display with sign"""
        if self.transaction_type == 'income':
            return f"+${self.amount:,.2f}"
        elif self.transaction_type == 'expense':
            return f"-${self.amount:,.2f}"
        else:  # transfer
            return f"${self.amount:,.2f}"
    
    @property
    def amount_class(self):
        """CSS class for amount styling"""
        if self.transaction_type == 'income':
            return 'text-success'
        elif self.transaction_type == 'expense':
            return 'text-danger'
        else:  # transfer
            return 'text-warning'
