# Budget Allocation App Forms
from django import forms
from django.db import models
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, Div, HTML
from crispy_forms.bootstrap import FormActions
from .models import (
    Account, Allocation, Transaction, BudgetTemplate, FamilySettings,
    AccountLoan, LoanPayment
)


class ChildAccountForm(forms.ModelForm):
    """Simple form for creating child accounts"""
    
    class Meta:
        model = Account
        fields = ['name', 'description', 'color', 'is_merchant_payee']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Salary, Groceries, Car Insurance'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional: What is this account for?'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'is_merchant_payee': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        
        # Auto-assign color based on parent
        if parent and not self.instance.pk:
            from .utils import get_next_color_for_parent
            suggested_color = get_next_color_for_parent(parent)
            self.fields['color'].initial = suggested_color
        
        # Make description optional but helpful
        self.fields['description'].required = False
        
        # Customize labels
        self.fields['name'].label = 'Account Name'
        self.fields['description'].label = 'Description (Optional)'
        self.fields['color'].label = 'Color'
        self.fields['is_merchant_payee'].label = 'Is this a merchant/payee?'
        
        # Add help text
        if parent:
            self.fields['name'].help_text = f'Create a new account under "{parent.name}"'
            self.fields['color'].help_text = 'Choose a color to easily identify this account'
        self.fields['is_merchant_payee'].help_text = 'Check this if this account represents a specific merchant, store, or payee for easier transaction entry'

    def clean_name(self):
        """Validate account name is unique within parent"""
        name = self.cleaned_data['name']
        if self.parent:
            existing = Account.objects.filter(
                family=self.parent.family,
                parent=self.parent,
                name__iexact=name
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise forms.ValidationError(
                    f'An account named "{name}" already exists under {self.parent.name}.'
                )
        return name

    def clean_color(self):
        """Validate color is a valid hex code"""
        color = self.cleaned_data['color']
        if color and not color.startswith('#'):
            color = '#' + color
        
        # Basic hex color validation
        if color and len(color) != 7:
            raise forms.ValidationError('Color must be a valid hex code (e.g., #FF5733)')
        
        return color
    
    def clean(self):
        """Set parent before model validation"""
        cleaned_data = super().clean()
        
        # Set the parent on the instance before model validation
        if self.parent:
            self.instance.parent = self.parent
            self.instance.family = self.parent.family
            self.instance.account_type = self.parent.account_type
        
        return cleaned_data

    def save(self, commit=True):
        """Override save to ensure parent and other required fields are set"""
        instance = super().save(commit=False)
        
        # Ensure parent is set (should already be set in clean(), but just in case)
        if self.parent:
            instance.parent = self.parent
            instance.family = self.parent.family
            instance.account_type = self.parent.account_type
        
        if commit:
            instance.save()
        
        return instance


class AccountForm(forms.ModelForm):
    """Form for editing existing accounts"""
    
    class Meta:
        model = Account
        fields = ['name', 'description', 'color', 'is_active', 'is_merchant_payee']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_merchant_payee': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        # Don't allow editing of Income/Expense root accounts
        if self.instance and self.instance.parent is None:
            self.fields['name'].widget.attrs['readonly'] = True
            self.fields['name'].help_text = 'Root account names cannot be changed'
        
        # Make description optional
        self.fields['description'].required = False
        
        # Customize labels
        self.fields['is_active'].label = 'Account is active'
        self.fields['is_merchant_payee'].label = 'Is this a merchant/payee?'
        self.fields['color'].help_text = 'Choose a color to easily identify this account'
        self.fields['is_merchant_payee'].help_text = 'Check this if this account represents a specific merchant, store, or payee for easier transaction entry'
        
        # Add validation warning for deactivation
        if self.instance and self.instance.pk:
            child_count = self.instance.children.filter(is_active=True).count()
            if child_count > 0:
                self.fields['is_active'].help_text = f'Warning: This account has {child_count} active child accounts'
        
        # Setup crispy forms helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('name', css_class='mb-3'),
            Field('description', css_class='mb-3'),
            Div(
                Field('color', css_class='w-50'),
                HTML('<small class="form-text text-muted">Preview: <span id="color-preview-edit" style="display:inline-block; width:20px; height:20px; border:1px solid #ccc; margin-left:10px;"></span></small>'),
                css_class='mb-3'
            ),
            Field('is_active', css_class='mb-3'),
            Field('is_merchant_payee', css_class='mb-3'),
            FormActions(
                Submit('submit', 'Update Account' if self.instance.pk else 'Create Account', css_class='btn btn-primary'),
                # Cancel button will be handled in template
            )
        )
        self.helper.form_method = 'post'
    
    def clean_name(self):
        """Validate account name"""
        name = self.cleaned_data['name']
        
        # Prevent changes to root account names
        if self.instance and self.instance.parent is None and self.instance.name != name:
            raise forms.ValidationError('Root account names cannot be changed')
        
        # Check for uniqueness within parent (if has parent)
        if self.instance and self.instance.parent:
            existing = Account.objects.filter(
                family=self.instance.family,
                parent=self.instance.parent,
                name__iexact=name
            ).exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(
                    f'An account named "{name}" already exists under {self.instance.parent.name}.'
                )
        
        return name
    
    def clean_is_active(self):
        """Validate account deactivation"""
        is_active = self.cleaned_data['is_active']
        
        if self.instance and self.instance.pk and not is_active:
            # Check for active children
            active_children = self.instance.children.filter(is_active=True).count()
            if active_children > 0:
                raise forms.ValidationError(
                    f'Cannot deactivate account with {active_children} active child accounts. '
                    'Please deactivate child accounts first.'
                )
            
            # Check for recent transactions (last 30 days)
            from django.utils import timezone
            from datetime import timedelta
            
            recent_date = timezone.now().date() - timedelta(days=30)
            recent_transactions = Transaction.objects.filter(
                account=self.instance,
                transaction_date__gte=recent_date
            ).count()
            
            if recent_transactions > 0:
                # Don't prevent, but warn (this is just a form validation, view can handle the warning)
                pass
        
        return is_active
    
    def clean_color(self):
        """Validate color is a valid hex code"""
        color = self.cleaned_data['color']
        if color and not color.startswith('#'):
            color = '#' + color
        
        # Basic hex color validation
        if color and len(color) != 7:
            raise forms.ValidationError('Color must be a valid hex code (e.g., #FF5733)')
        
        return color


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
            
            # Set default week if none provided
            if not self.instance.pk and 'week' not in self.initial:
                current_week = self.family.weeklyperiod_set.filter(is_active=True).first()
                if current_week:
                    self.initial['week'] = current_week.pk
        
        # Add help text
        self.fields['from_account'].help_text = "Account to transfer money from"
        self.fields['to_account'].help_text = "Account to transfer money to"
        self.fields['amount'].help_text = "Amount to allocate in dollars"
        self.fields['notes'].required = False
        self.fields['week'].required = False  # Make week optional
    
    def clean_to_account(self):
        """Validate to_account selection"""
        to_account = self.cleaned_data.get('to_account')
        from_account = self.cleaned_data.get('from_account')
        
        if from_account and to_account and from_account == to_account:
            raise forms.ValidationError("From and To accounts must be different")
        
        return to_account
    
    def clean_amount(self):
        """Validate allocation amount"""
        amount = self.cleaned_data.get('amount')
        
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0")
        
        return amount
    
    def save(self, commit=True):
        """Save allocation with family assignment"""
        allocation = super().save(commit=False)
        
        if self.family:
            allocation.family = self.family
            
            # Auto-assign week if not provided
            if not allocation.week_id:
                from .models import WeeklyPeriod
                from datetime import date, timedelta
                
                # Get or create current week
                today = date.today()
                week_start = today - timedelta(days=today.weekday())
                week_end = week_start + timedelta(days=6)
                
                current_week, created = WeeklyPeriod.objects.get_or_create(
                    start_date=week_start,
                    end_date=week_end,
                    family=self.family,
                    defaults={'is_active': True}
                )
                allocation.week = current_week
            
        if commit:
            allocation.save()
            
        return allocation


class TransactionForm(forms.ModelForm):
    """Form for recording transactions"""
    
    # Add merchant/payee selection field
    merchant_payee = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Select a merchant/payee...",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_merchant_payee'
        }),
        help_text="Choose from your saved merchants/payees or leave blank to enter manually"
    )
    
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
        self.initial_account = kwargs.pop('initial_account', None)
        super().__init__(*args, **kwargs)
        
        if self.family:
            # Filter accounts to family accounts
            self.fields['account'].queryset = Account.objects.filter(
                family=self.family,
                is_active=True
            ).order_by('account_type', 'name')
            
            # Filter weeks to family weeks
            self.fields['week'].queryset = self.family.weeklyperiod_set.order_by('-start_date')
            
            # Populate merchant/payee dropdown with accounts marked as merchants/payees
            self.fields['merchant_payee'].queryset = Account.objects.filter(
                family=self.family,
                is_merchant_payee=True,
                is_active=True
            ).order_by('name')
        
        # Handle account-specific form behavior
        if self.initial_account:
            # When coming from an account, make certain fields optional/hidden
            self.fields['account'].disabled = True
            self.fields['account'].initial = self.initial_account
            self.fields['transaction_type'].required = False
            self.fields['description'].required = False
            
            # Auto-populate payee with account name
            if not self.instance.pk:
                self.fields['payee'].initial = self.initial_account.name
            
            # Update help text for account-specific context
            self.fields['payee'].help_text = "Merchant/Payee (auto-filled with account name)"
            self.fields['account'].help_text = "Transaction will be recorded to this account"
            self.fields['transaction_type'].help_text = "Leave blank to auto-determine based on account type"
            self.fields['description'].help_text = "Optional description for this transaction"
        else:
            # General transaction form behavior
            self.fields['description'].required = True
        
        # Make optional fields not required
        self.fields['payee'].required = False
        self.fields['reference'].required = False
        self.fields['week'].required = False
        
        # Add help text
        self.fields['transaction_date'].help_text = "Date when this transaction occurred"
        self.fields['amount'].help_text = "Transaction amount in dollars"
        self.fields['week'].help_text = "Leave blank to auto-assign based on transaction date"
        
        # Set default date to today
        if not self.instance.pk:
            from datetime import date
            self.fields['transaction_date'].initial = date.today()
    
    def clean_amount(self):
        """Validate transaction amount"""
        amount = self.cleaned_data.get('amount')
        
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0")
        
        return amount
    
    def clean(self):
        """Custom form validation and field handling"""
        cleaned_data = super().clean()
        
        # Handle disabled account field - Django ignores disabled fields
        if self.initial_account:
            cleaned_data['account'] = self.initial_account
        
        # Handle merchant_payee selection - auto-populate payee field and account
        merchant_payee = cleaned_data.get('merchant_payee')
        if merchant_payee:
            # Set the payee name from the merchant account
            if not cleaned_data.get('payee'):
                cleaned_data['payee'] = merchant_payee.name
            
            # Set the account to be the merchant/payee account
            if not cleaned_data.get('account'):
                cleaned_data['account'] = merchant_payee
            
        return cleaned_data
    
    def save(self, commit=True):
        """Save transaction with family assignment"""
        transaction = super().save(commit=False)
        
        if self.family:
            transaction.family = self.family
            
            # If no week specified, assign to current week
            if not hasattr(transaction, 'week') or transaction.week is None:
                from .models import WeeklyPeriod
                current_week = WeeklyPeriod.objects.filter(
                    family=self.family
                ).order_by('-start_date').first()
                if current_week:
                    transaction.week = current_week
            
        if commit:
            transaction.save()
            
        return transaction


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
                'step': '0.01',
                'min': '0',
                'max': '100',
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
    
    def clean_weekly_amount(self):
        """Validate weekly_amount for fixed allocation type"""
        weekly_amount = self.cleaned_data.get('weekly_amount')
        allocation_type = self.data.get('allocation_type')
        
        if allocation_type == 'fixed' and not weekly_amount:
            raise forms.ValidationError("Fixed allocation type requires weekly_amount")
        
        return weekly_amount
    
    def clean_percentage(self):
        """Validate percentage for percentage allocation type"""
        percentage = self.cleaned_data.get('percentage')
        allocation_type = self.data.get('allocation_type')
        
        if allocation_type == 'percentage' and not percentage:
            raise forms.ValidationError("Percentage allocation type requires percentage")
        
        return percentage
    
    def clean_min_amount(self):
        """Validate min_amount for range allocation type"""
        min_amount = self.cleaned_data.get('min_amount')
        allocation_type = self.data.get('allocation_type')
        max_amount = self.data.get('max_amount')
        
        if allocation_type == 'range' and not min_amount and not max_amount:
            raise forms.ValidationError("Range allocation type requires min_amount and max_amount")
        
        return min_amount
    
    def clean_max_amount(self):
        """Validate max_amount for range allocation type"""
        max_amount = self.cleaned_data.get('max_amount')
        min_amount = self.cleaned_data.get('min_amount')
        allocation_type = self.data.get('allocation_type')
        
        # Check if both amounts are missing for range type
        if allocation_type == 'range' and not min_amount and not max_amount:
            raise forms.ValidationError("Range allocation type requires min_amount and max_amount")
        
        # Check min/max relationship
        if min_amount and max_amount and min_amount > max_amount:
            raise forms.ValidationError("Minimum amount cannot be greater than maximum amount")
        
        return max_amount
    
    def save(self, commit=True):
        """Save budget template with family assignment"""
        template = super().save(commit=False)
        
        if self.family:
            template.family = self.family
            
        if commit:
            template.save()
            
        return template


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
    
    def clean_weekly_interest_rate(self):
        interest_rate = self.cleaned_data.get('weekly_interest_rate')
        if interest_rate is not None and interest_rate < 0:
            raise ValidationError("Interest rate cannot be negative.")
        return interest_rate
    
    def clean(self):
        cleaned_data = super().clean()
        lender_account = cleaned_data.get('lender_account')
        borrower_account = cleaned_data.get('borrower_account')
        
        # Validate different accounts
        if lender_account and borrower_account and lender_account == borrower_account:
            self.add_error('borrower_account', "Lender and borrower accounts must be different.")
        
        return cleaned_data


class LoanPaymentForm(forms.ModelForm):
    """Form for recording loan payments"""
    
    class Meta:
        model = LoanPayment
        fields = ['loan', 'amount', 'payment_date', 'notes']
        widgets = {
            'loan': forms.Select(attrs={
                'class': 'form-control'
            }),
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
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        # Filter loan choices by family and active status
        if self.family:
            from .models import AccountLoan
            self.fields['loan'].queryset = AccountLoan.objects.filter(
                family=self.family,
                is_active=True
            )
        
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
        """Validate payment amount"""
        amount = self.cleaned_data.get('amount')
        loan = self.cleaned_data.get('loan')
        
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Payment amount must be greater than 0")
        
        if loan and amount and amount > loan.remaining_amount:
            raise forms.ValidationError(
                f"Payment amount (${amount}) cannot exceed remaining loan balance (${loan.remaining_amount})"
            )
        
        return amount
