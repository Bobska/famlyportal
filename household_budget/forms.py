from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
from .models import (
    BudgetCategory, Budget, BudgetItem, Transaction, SavingsGoal
)


class BudgetCategoryForm(forms.ModelForm):
    """Form for creating and editing budget categories"""
    
    parent_category = forms.ModelChoiceField(
        queryset=BudgetCategory.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Optional parent category for organization'
    )
    
    class Meta:
        model = BudgetCategory
        fields = [
            'name', 'description', 'category_type', 'color', 
            'is_essential', 'parent_category', 'sort_order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Groceries, Salary, Utilities'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description of this category'
            }),
            'category_type': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'title': 'Choose a color for this category'
            }),
            'is_essential': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0'
            }),
        }
        help_texts = {
            'name': 'Unique name for this category',
            'category_type': 'Whether this represents income or expenses',
            'color': 'Color used to display this category in charts and reports',
            'is_essential': 'Check if this is an essential category (needs vs wants)',
            'sort_order': 'Order for displaying categories (0 = first)',
        }
    
    def __init__(self, *args, family=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.family = family
        
        if family:
            # Filter parent categories by family and same type
            if self.instance and self.instance.pk:
                # When editing, exclude self from parent options
                parent_qs = BudgetCategory.objects.filter(
                    family=family
                ).exclude(pk=self.instance.pk)
            else:
                parent_qs = BudgetCategory.objects.filter(family=family)
            
            self.fields['parent_category'].queryset = parent_qs
        else:
            self.fields['parent_category'].queryset = BudgetCategory.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent_category')
        category_type = cleaned_data.get('category_type')
        
        # Ensure parent category is same type
        if parent and parent.category_type != category_type:
            raise ValidationError({
                'parent_category': 'Parent category must be the same type (income/expense)'
            })
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.family:
            instance.family = self.family
        if commit:
            instance.save()
        return instance


class BudgetForm(forms.ModelForm):
    """Form for creating and editing budgets"""
    
    class Meta:
        model = Budget
        fields = ['name', 'description', 'start_date', 'end_date', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2024 Family Budget'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description of this budget'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        help_texts = {
            'name': 'A descriptive name for this budget',
            'start_date': 'When this budget becomes effective',
            'end_date': 'When this budget expires (leave blank for ongoing)',
            'is_active': 'Only one budget can be active at a time',
        }
    
    def __init__(self, *args, family=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.family = family
        
        # Set default start date to beginning of current month
        if not self.instance.pk:
            today = timezone.now().date()
            self.fields['start_date'].initial = today.replace(day=1)
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        is_active = cleaned_data.get('is_active')
        
        if end_date and start_date and end_date <= start_date:
            raise ValidationError({
                'end_date': 'End date must be after start date'
            })
        
        # Check for overlapping active budgets
        if is_active and self.family:
            active_budgets = Budget.objects.filter(
                family=self.family,
                is_active=True
            )
            if self.instance.pk:
                active_budgets = active_budgets.exclude(pk=self.instance.pk)
            
            if active_budgets.exists():
                raise ValidationError({
                    'is_active': 'Only one budget can be active at a time. Please deactivate other budgets first.'
                })
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.family:
            instance.family = self.family
        if commit:
            instance.save()
        return instance


class BudgetItemForm(forms.ModelForm):
    """Form for creating and editing budget items"""
    
    category = forms.ModelChoiceField(
        queryset=BudgetCategory.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select the budget category'
    )
    
    class Meta:
        model = BudgetItem
        fields = ['category', 'budgeted_amount', 'notes']
        widgets = {
            'budgeted_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes about this budget item'
            }),
        }
        help_texts = {
            'budgeted_amount': 'Amount budgeted for this category',
            'notes': 'Additional notes or details',
        }
    
    def __init__(self, *args, family=None, budget=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.family = family
        self.budget = budget
        
        if family:
            # Filter categories by family
            self.fields['category'].queryset = BudgetCategory.objects.filter(
                family=family,
                is_active=True
            ).order_by('category_type', 'name')
        else:
            self.fields['category'].queryset = BudgetCategory.objects.none()
    
    def clean_budgeted_amount(self):
        amount = self.cleaned_data['budgeted_amount']
        if amount < 0:
            raise ValidationError('Budgeted amount cannot be negative')
        return amount
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.budget:
            instance.budget = self.budget
        if commit:
            instance.save()
        return instance


class TransactionForm(forms.ModelForm):
    """Form for creating and editing transactions"""
    
    category = forms.ModelChoiceField(
        queryset=BudgetCategory.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Budget category for this transaction'
    )
    
    class Meta:
        model = Transaction
        fields = [
            'transaction_date', 'description', 'amount', 'category',
            'transaction_type', 'payee', 'account', 'notes', 'receipt_image'
        ]
        widgets = {
            'transaction_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Grocery shopping at Walmart'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'payee': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Walmart, ABC Company',
                'list': 'payee-suggestions'
            }),
            'account': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Checking, Credit Card, Cash'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes about this transaction'
            }),
            'receipt_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        help_texts = {
            'transaction_date': 'Date the transaction occurred',
            'description': 'Brief description of the transaction',
            'amount': 'Transaction amount (always positive)',
            'transaction_type': 'Type of transaction',
            'payee': 'Who you paid or received money from',
            'account': 'Account used for this transaction',
            'receipt_image': 'Upload receipt image (optional)',
        }
    
    def __init__(self, *args, family=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.family = family
        
        # Set default date to today
        if not self.instance.pk:
            self.fields['transaction_date'].initial = timezone.now().date()
        
        if family:
            # Filter categories by family
            self.fields['category'].queryset = BudgetCategory.objects.filter(
                family=family,
                is_active=True
            ).order_by('category_type', 'name')
        else:
            self.fields['category'].queryset = BudgetCategory.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        transaction_type = cleaned_data.get('transaction_type')
        transaction_date = cleaned_data.get('transaction_date')
        
        # Validate transaction date
        if transaction_date and transaction_date > timezone.now().date():
            raise ValidationError({
                'transaction_date': 'Transaction date cannot be in the future'
            })
        
        # Validate category type matches transaction type
        if category and transaction_type and transaction_type != 'transfer':
            if category.category_type != transaction_type:
                raise ValidationError({
                    'category': f'Selected category is for {category.category_type}, but transaction type is {transaction_type}'
                })
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.family:
            instance.family = self.family
        if commit:
            instance.save()
        return instance


class QuickTransactionForm(forms.ModelForm):
    """Simplified form for quick transaction entry"""
    
    category = forms.ModelChoiceField(
        queryset=BudgetCategory.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        help_text='Budget category'
    )
    
    class Meta:
        model = Transaction
        fields = ['description', 'amount', 'category', 'transaction_type']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Transaction description'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'transaction_type': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }
    
    def __init__(self, *args, family=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.family = family
        
        if family:
            # Filter categories by family
            self.fields['category'].queryset = BudgetCategory.objects.filter(
                family=family,
                is_active=True
            ).order_by('category_type', 'name')
        else:
            self.fields['category'].queryset = BudgetCategory.objects.none()
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.family:
            instance.family = self.family
            instance.transaction_date = timezone.now().date()
        if commit:
            instance.save()
        return instance


class SavingsGoalForm(forms.ModelForm):
    """Form for creating and editing savings goals"""
    
    class Meta:
        model = SavingsGoal
        fields = [
            'name', 'description', 'target_amount', 'current_amount',
            'target_date', 'monthly_contribution', 'priority'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Emergency Fund, Vacation'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description of this savings goal'
            }),
            'target_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'current_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'target_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'monthly_contribution': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'priority': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
        }
        help_texts = {
            'name': 'A descriptive name for this savings goal',
            'target_amount': 'Amount you want to save',
            'current_amount': 'Amount already saved toward this goal',
            'target_date': 'When you want to achieve this goal (optional)',
            'monthly_contribution': 'Planned monthly contribution (optional)',
            'priority': 'Goal priority (1 = highest priority)',
        }
    
    def __init__(self, *args, family=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.family = family
        
        # Set default current amount to 0
        if not self.instance.pk:
            self.fields['current_amount'].initial = Decimal('0.00')
    
    def clean(self):
        cleaned_data = super().clean()
        target_amount = cleaned_data.get('target_amount')
        current_amount = cleaned_data.get('current_amount')
        target_date = cleaned_data.get('target_date')
        
        if target_amount and target_amount <= 0:
            raise ValidationError({
                'target_amount': 'Target amount must be greater than zero'
            })
        
        if current_amount and current_amount < 0:
            raise ValidationError({
                'current_amount': 'Current amount cannot be negative'
            })
        
        if target_date and target_date <= timezone.now().date():
            raise ValidationError({
                'target_date': 'Target date must be in the future'
            })
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.family:
            instance.family = self.family
        if commit:
            instance.save()
        return instance


class BudgetFilterForm(forms.Form):
    """Form for filtering transactions and budget reports"""
    
    SORT_CHOICES = [
        ('-transaction_date', 'Date (newest first)'),
        ('transaction_date', 'Date (oldest first)'),
        ('-amount', 'Amount (highest first)'),
        ('amount', 'Amount (lowest first)'),
        ('description', 'Description (A-Z)'),
        ('-description', 'Description (Z-A)'),
        ('category__name', 'Category (A-Z)'),
        ('payee', 'Payee (A-Z)'),
    ]
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text='Filter transactions from this date'
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text='Filter transactions to this date'
    )
    category = forms.ModelChoiceField(
        queryset=BudgetCategory.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Filter by category'
    )
    transaction_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Transaction.TRANSACTION_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Filter by transaction type'
    )
    min_amount = forms.DecimalField(
        required=False,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Min amount'
        }),
        help_text='Minimum transaction amount'
    )
    max_amount = forms.DecimalField(
        required=False,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Max amount'
        }),
        help_text='Maximum transaction amount'
    )
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search description, payee, notes...'
        }),
        help_text='Search in description, payee, and notes'
    )
    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='-transaction_date',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Sort transactions by'
    )
    is_reconciled = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('true', 'Reconciled'),
            ('false', 'Not Reconciled'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Filter by reconciliation status'
    )
    
    def __init__(self, *args, family=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if family:
            self.fields['category'].queryset = BudgetCategory.objects.filter(
                family=family,
                is_active=True
            ).order_by('category_type', 'name')
        
        # Set default date range to current month
        if not self.is_bound:
            today = timezone.now().date()
            self.fields['start_date'].initial = today.replace(day=1)
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError('Start date must be before end date')
        
        if min_amount and max_amount and min_amount > max_amount:
            raise ValidationError('Minimum amount must be less than maximum amount')
        
        return cleaned_data


class ContributionForm(forms.Form):
    """Form for adding contributions to savings goals"""
    
    amount = forms.DecimalField(
        decimal_places=2,
        max_digits=10,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.00'
        }),
        help_text='Contribution amount'
    )
    description = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional description'
        }),
        help_text='Optional description for this contribution'
    )
