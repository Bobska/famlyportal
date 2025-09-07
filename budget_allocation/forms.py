# Budget Allocation App Forms
from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Account, Allocation, Transaction, BudgetTemplate, FamilySettings,
    AccountLoan, LoanPayment
)


class AccountForm(forms.ModelForm):
    """Form for creating and editing accounts"""
    
    class Meta:
        model = Account
        fields = [
            'name', 'account_type', 'parent', 'description', 
            'color', 'is_active', 'sort_order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter account name'
            }),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter account description (optional)'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#6c757d'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'value': 0
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        # Filter parent choices to accounts in the same family
        if self.family:
            self.fields['parent'].queryset = Account.objects.filter(
                family=self.family,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
        
        # Add CSS classes and help text
        self.fields['name'].help_text = "Choose a descriptive name for this account"
        self.fields['parent'].help_text = "Select a parent account to create a hierarchy (optional)"
        self.fields['sort_order'].help_text = "Lower numbers appear first in lists"
        
        # Make parent field optional
        self.fields['parent'].required = False
        self.fields['parent'].empty_label = "No parent (root account)"
    
    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        account_type = cleaned_data.get('account_type')
        
        # Validate parent-child relationship
        if parent:
            # Prevent circular references
            if self.instance.pk and parent.pk == self.instance.pk:
                raise ValidationError("An account cannot be its own parent.")
            
            # Check if parent would create a cycle
            if self.instance.pk and parent.has_ancestor(self.instance):
                raise ValidationError("This would create a circular reference.")
            
            # Validate account type compatibility
            if account_type != parent.account_type:
                raise ValidationError(
                    f"Child account type ({account_type}) must match parent account type ({parent.account_type})."
                )
        
        return cleaned_data


class AllocationForm(forms.ModelForm):
    """Form for creating manual allocations"""
    
    class Meta:
        model = Allocation
        fields = ['week', 'from_account', 'to_account', 'amount', 'notes']
        widgets = {
            'week': forms.Select(attrs={'class': 'form-select'}),
            'from_account': forms.Select(attrs={'class': 'form-select'}),
            'to_account': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add notes about this allocation (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        if self.family:
            # Filter accounts to family accounts
            family_accounts = Account.objects.filter(
                family=self.family,
                is_active=True
            ).order_by('account_type', 'name')
            
            self.fields['from_account'].queryset = family_accounts
            self.fields['to_account'].queryset = family_accounts
            
            # Filter weeks to family weeks
            self.fields['week'].queryset = self.family.weeklyperiod_set.order_by('-start_date')
        
        # Add help text
        self.fields['from_account'].help_text = "Account to transfer money from"
        self.fields['to_account'].help_text = "Account to transfer money to"
        self.fields['amount'].help_text = "Amount to allocate in dollars"
        self.fields['notes'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        from_account = cleaned_data.get('from_account')
        to_account = cleaned_data.get('to_account')
        amount = cleaned_data.get('amount')
        
        # Validate different accounts
        if from_account and to_account and from_account == to_account:
            raise ValidationError("From and To accounts must be different.")
        
        # Validate positive amount
        if amount and amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        
        return cleaned_data


class TransactionForm(forms.ModelForm):
    """Form for recording transactions"""
    
    class Meta:
        model = Transaction
        fields = [
            'transaction_date', 'account', 'description', 'amount',
            'transaction_type', 'payee', 'reference', 'week'
        ]
        widgets = {
            'transaction_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Describe this transaction'
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
                'placeholder': 'Who was this transaction with? (optional)'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Reference number or check number (optional)'
            }),
            'week': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        if self.family:
            # Filter accounts to family accounts
            self.fields['account'].queryset = Account.objects.filter(
                family=self.family,
                is_active=True
            ).order_by('account_type', 'name')
            
            # Filter weeks to family weeks
            self.fields['week'].queryset = self.family.weeklyperiod_set.order_by('-start_date')
        
        # Make optional fields not required
        self.fields['payee'].required = False
        self.fields['reference'].required = False
        self.fields['week'].required = False
        
        # Add help text
        self.fields['transaction_date'].help_text = "Date when this transaction occurred"
        self.fields['amount'].help_text = "Transaction amount in dollars"
        self.fields['week'].help_text = "Leave blank to auto-assign to current week"
        
        # Set default date to today
        if not self.instance.pk:
            from datetime import date
            self.fields['transaction_date'].initial = date.today()


class BudgetTemplateForm(forms.ModelForm):
    """Form for creating budget templates"""
    
    class Meta:
        model = BudgetTemplate
        fields = [
            'account', 'allocation_type', 'weekly_amount', 'percentage',
            'min_amount', 'max_amount', 'priority', 'is_essential', 
            'never_miss', 'auto_allocate', 'annual_amount', 'due_date',
            'current_saved', 'is_active'
        ]
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'allocation_type': forms.Select(attrs={'class': 'form-select'}),
            'weekly_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.00',
                'placeholder': '0.00'
            }),
            'percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0.0',
                'max': '100.0',
                'placeholder': '0.0'
            }),
            'min_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.00',
                'placeholder': '0.00'
            }),
            'max_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.00',
                'placeholder': '0.00'
            }),
            'priority': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10',
                'value': '5'
            }),
            'annual_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.00',
                'placeholder': '0.00'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'current_saved': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.00',
                'placeholder': '0.00'
            }),
            'is_essential': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'never_miss': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_allocate': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        if self.family:
            # Filter accounts to family accounts
            self.fields['account'].queryset = Account.objects.filter(
                family=self.family,
                is_active=True
            ).order_by('account_type', 'name')
        
        # Make optional fields not required
        optional_fields = [
            'weekly_amount', 'percentage', 'min_amount', 'max_amount',
            'annual_amount', 'due_date', 'current_saved'
        ]
        for field in optional_fields:
            self.fields[field].required = False
        
        # Add help text
        self.fields['allocation_type'].help_text = "How should the allocation amount be calculated?"
        self.fields['weekly_amount'].help_text = "Fixed amount to allocate each week (for Fixed type)"
        self.fields['percentage'].help_text = "Percentage of income to allocate (for Percentage type)"
        self.fields['priority'].help_text = "1 = highest priority, 10 = lowest priority"
        self.fields['is_essential'].help_text = "Mark as essential expense"
        self.fields['never_miss'].help_text = "Never skip this allocation"
        self.fields['auto_allocate'].help_text = "Automatically allocate when processing weekly budget"
    
    def clean(self):
        cleaned_data = super().clean()
        allocation_type = cleaned_data.get('allocation_type')
        weekly_amount = cleaned_data.get('weekly_amount')
        percentage = cleaned_data.get('percentage')
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')
        
        # Validate required fields based on allocation type
        if allocation_type == 'fixed' and not weekly_amount:
            raise ValidationError("Weekly amount is required for fixed allocation type.")
        
        if allocation_type == 'percentage' and not percentage:
            raise ValidationError("Percentage is required for percentage allocation type.")
        
        if allocation_type == 'range':
            if not min_amount and not max_amount:
                raise ValidationError("At least one of min or max amount is required for range allocation type.")
        
        # Validate min/max relationship
        if min_amount and max_amount and min_amount > max_amount:
            raise ValidationError("Minimum amount cannot be greater than maximum amount.")
        
        return cleaned_data


class FamilySettingsForm(forms.ModelForm):
    """Form for family budget allocation settings"""
    
    class Meta:
        model = FamilySettings
        fields = [
            'week_start_day', 'default_interest_rate', 'notification_threshold',
            'auto_allocate_enabled', 'auto_repay_enabled'
        ]
        widgets = {
            'week_start_day': forms.Select(attrs={'class': 'form-select'}),
            'default_interest_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0.000',
                'max': '1.000',
                'placeholder': '0.010'
            }),
            'notification_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.00',
                'placeholder': '100.00'
            }),
            'auto_allocate_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_repay_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add help text
        self.fields['week_start_day'].help_text = "What day should your budget week start on?"
        self.fields['default_interest_rate'].help_text = "Default weekly interest rate for new loans (as decimal, e.g. 0.020 for 2%)"
        self.fields['notification_threshold'].help_text = "Minimum amount for automatic notifications and actions"
        self.fields['auto_allocate_enabled'].help_text = "Automatically apply budget templates each week"
        self.fields['auto_repay_enabled'].help_text = "Automatically repay loans when accounts have sufficient funds"


# Future loan management forms (placeholder for advanced loan features)
class AccountLoanForm(forms.ModelForm):
    """Form for creating inter-account loans"""
    
    class Meta:
        model = AccountLoan
        fields = [
            'lender_account', 'borrower_account', 'original_amount',
            'weekly_interest_rate', 'loan_date'
        ]
        widgets = {
            'lender_account': forms.Select(attrs={'class': 'form-select'}),
            'borrower_account': forms.Select(attrs={'class': 'form-select'}),
            'original_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'weekly_interest_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0.000',
                'max': '1.000',
                'placeholder': '0.020'
            }),
            'loan_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        if self.family:
            # Filter accounts to family accounts
            family_accounts = Account.objects.filter(
                family=self.family,
                is_active=True
            ).order_by('account_type', 'name')
            
            self.fields['lender_account'].queryset = family_accounts
            self.fields['borrower_account'].queryset = family_accounts
        
        # Set default date to today
        if not self.instance.pk:
            from datetime import date
            self.fields['loan_date'].initial = date.today()
        
        # Add help text
        self.fields['lender_account'].help_text = "Account providing the loan"
        self.fields['borrower_account'].help_text = "Account receiving the loan"
        self.fields['original_amount'].help_text = "Principal loan amount"
        self.fields['weekly_interest_rate'].help_text = "Weekly interest rate (e.g. 0.020 for 2%)"
    
    def clean(self):
        cleaned_data = super().clean()
        lender_account = cleaned_data.get('lender_account')
        borrower_account = cleaned_data.get('borrower_account')
        
        # Validate different accounts
        if lender_account and borrower_account and lender_account == borrower_account:
            raise ValidationError("Lender and borrower accounts must be different.")
        
        return cleaned_data


class LoanPaymentForm(forms.ModelForm):
    """Form for recording loan payments"""
    
    class Meta:
        model = LoanPayment
        fields = ['amount', 'payment_date', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes about this payment (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.loan = kwargs.pop('loan', None)
        super().__init__(*args, **kwargs)
        
        # Set default date to today
        if not self.instance.pk:
            from datetime import date
            self.fields['payment_date'].initial = date.today()
        
        # Make notes optional
        self.fields['notes'].required = False
        
        # Add help text
        self.fields['amount'].help_text = "Payment amount in dollars"
        self.fields['payment_date'].help_text = "Date when payment was made"
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if self.loan and amount:
            if amount > self.loan.remaining_amount:
                raise ValidationError(
                    f"Payment amount cannot exceed remaining balance of ${self.loan.remaining_amount}"
                )
        
        return amount
        self.fields['default_interest_rate'].help_text = "Default weekly interest rate for loans (as decimal, e.g., 0.01 = 1%)"
        self.fields['notification_threshold'].help_text = "Minimum account balance to trigger low balance notifications"
        self.fields['auto_allocate_enabled'].help_text = "Automatically allocate money based on budget templates"
        self.fields['auto_repay_enabled'].help_text = "Automatically repay loans when possible"
