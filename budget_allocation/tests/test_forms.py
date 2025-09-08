"""
Budget Allocation Form Tests

Test form validation, field rendering, and data processing for budget allocation forms.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import User
from decimal import Decimal
from datetime import date

from accounts.models import Family, FamilyMember
from budget_allocation.models import (
    Account, WeeklyPeriod, BudgetTemplate, AccountLoan, FamilySettings
)
from budget_allocation.forms import (
    AccountForm, TransactionForm, AllocationForm, 
    BudgetTemplateForm, AccountLoanForm, LoanPaymentForm
)


class BudgetAllocationFormTestCase(TestCase):
    """Base test case for budget allocation form tests"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users and family
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.family = Family.objects.create(
            name='Test Family',
            created_by=self.user
        )
        
        self.member = FamilyMember.objects.create(
            user=self.user,
            family=self.family,
            role='admin'
        )
        
        # Create family settings
        self.family_settings = FamilySettings.objects.create(
            family=self.family
        )
        
        # Create test accounts
        self.root_account = Account.objects.create(
            family=self.family,
            name='Root',
            account_type='root'
        )
        
        self.income_account = Account.objects.create(
            family=self.family,
            name='Main Income',
            account_type='income',
            parent=self.root_account
        )
        
        self.spending_account = Account.objects.create(
            family=self.family,
            name='Food Budget',
            account_type='spending',
            parent=self.root_account
        )
        
        # Create current week
        from budget_allocation.utilities import get_current_week
        self.week = get_current_week(self.family)


class AccountFormTests(BudgetAllocationFormTestCase):
    """Test AccountForm functionality"""
    
    def test_valid_account_form(self):
        """Test form with valid data"""
        form_data = {
            'name': 'Test Account',
            'account_type': 'spending',
            'parent': self.spending_account.pk,  # Use spending account as parent
            'description': 'Test account description',
            'color': '#28a745',
            'sort_order': 1
        }
        
        form = AccountForm(data=form_data, family=self.family)
        
        self.assertTrue(form.is_valid())
        
        # Test saving the form
        account = form.save()
        
        self.assertEqual(account.name, 'Test Account')
        self.assertEqual(account.account_type, 'spending')
        self.assertEqual(account.parent, self.spending_account)
        self.assertEqual(account.family, self.family)
    
    def test_invalid_account_form_empty_name(self):
        """Test form with empty name"""
        form_data = {
            'name': '',
            'account_type': 'spending',
            'description': 'Test description'
        }
        
        form = AccountForm(data=form_data, family=self.family)
        
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_invalid_account_form_invalid_color(self):
        """Test form with invalid color format"""
        form_data = {
            'name': 'Test Account',
            'account_type': 'spending',
            'color': 'invalid-color'
        }
        
        form = AccountForm(data=form_data, family=self.family)
        
        self.assertFalse(form.is_valid())
        self.assertIn('color', form.errors)
    
    def test_account_form_parent_filtering(self):
        """Test that parent field is filtered by family"""
        # Create account in different family
        other_family = Family.objects.create(
            name='Other Family',
            created_by=self.user
        )
        other_account = Account.objects.create(
            family=other_family,
            name='Other Account',
            account_type='root'
        )
        
        form = AccountForm(family=self.family)
        
        # Parent choices should only include accounts from same family
        parent_queryset = form.fields['parent'].queryset
        parent_pks = [account.pk for account in parent_queryset]
        self.assertIn(self.root_account.pk, parent_pks)
        self.assertNotIn(other_account.pk, parent_pks)
    
    def test_root_account_no_parent(self):
        """Test that root accounts cannot have parents"""
        form_data = {
            'name': 'Root Account',
            'account_type': 'root',
            'parent': self.root_account.pk,  # Should not be allowed
            'color': '#ff0000',
            'sort_order': 0
        }
        
        form = AccountForm(data=form_data, family=self.family)
        
        self.assertFalse(form.is_valid())
        self.assertIn('parent', form.errors)


class TransactionFormTests(BudgetAllocationFormTestCase):
    """Test TransactionForm functionality"""
    
    def test_valid_transaction_form(self):
        """Test form with valid data"""
        form_data = {
            'account': self.spending_account.pk,
            'amount': '50.00',
            'transaction_type': 'expense',
            'description': 'Grocery shopping',
            'payee': 'Local Store',
            'transaction_date': date.today().strftime('%Y-%m-%d')
        }
        
        form = TransactionForm(data=form_data, family=self.family)
        
        self.assertTrue(form.is_valid())
        
        # Test saving the form
        transaction = form.save()
        
        self.assertEqual(transaction.account, self.spending_account)
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.transaction_type, 'expense')
        self.assertEqual(transaction.family, self.family)
    
    def test_invalid_transaction_form_negative_amount(self):
        """Test form with negative amount"""
        form_data = {
            'account': self.spending_account.pk,
            'amount': '-10.00',
            'transaction_type': 'expense',
            'description': 'Invalid transaction',
            'transaction_date': date.today().isoformat()
        }
        
        form = TransactionForm(data=form_data, family=self.family)
        
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
    
    def test_invalid_transaction_form_zero_amount(self):
        """Test form with zero amount"""
        form_data = {
            'account': self.spending_account.pk,
            'amount': '0.00',
            'transaction_type': 'expense',
            'description': 'Invalid transaction',
            'transaction_date': date.today().isoformat()
        }
        
        form = TransactionForm(data=form_data, family=self.family)
        
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
    
    def test_transaction_form_account_filtering(self):
        """Test that account field is filtered by family"""
        # Create account in different family
        other_family = Family.objects.create(
            name='Other Family',
            created_by=self.user
        )
        other_account = Account.objects.create(
            family=other_family,
            name='Other Account',
            account_type='spending'
        )
        
        form = TransactionForm(family=self.family)
        
        # Account choices should only include accounts from same family
        account_queryset = form.fields['account'].queryset
        account_pks = [account.pk for account in account_queryset]
        self.assertIn(self.spending_account.pk, account_pks)
        self.assertNotIn(other_account.pk, account_pks)
    
    def test_transaction_form_future_date_validation(self):
        """Test validation for future dates"""
        from datetime import timedelta
        future_date = date.today() + timedelta(days=30)
        
        form_data = {
            'account': self.spending_account.pk,
            'amount': '25.00',
            'transaction_type': 'expense',
            'description': 'Future transaction',
            'transaction_date': future_date.strftime('%Y-%m-%d')
        }
        
        form = TransactionForm(data=form_data, family=self.family)
        
        # Should be valid (future transactions might be allowed for planning)
        # If your business logic doesn't allow future dates, modify this test
        self.assertTrue(form.is_valid())


class AllocationFormTests(BudgetAllocationFormTestCase):
    """Test AllocationForm functionality"""
    
    def setUp(self):
        super().setUp()
        # Create additional account for allocations
        self.savings_account = Account.objects.create(
            family=self.family,
            name='Savings',
            account_type='spending',
            parent=self.root_account
        )
    
    def test_valid_allocation_form(self):
        """Test form with valid data"""
        form_data = {
            'week': self.week.pk,
            'from_account': self.income_account.pk,
            'to_account': self.spending_account.pk,
            'amount': '200.00',
            'notes': 'Weekly food allocation'
        }
        
        form = AllocationForm(data=form_data, family=self.family)
        
        self.assertTrue(form.is_valid())
        
        # Test saving the form
        allocation = form.save()
        
        self.assertEqual(allocation.from_account, self.income_account)
        self.assertEqual(allocation.to_account, self.spending_account)
        self.assertEqual(allocation.amount, Decimal('200.00'))
    
    def test_invalid_allocation_same_account(self):
        """Test form with same from and to account"""
        form_data = {
            'week': self.week.pk,
            'from_account': self.spending_account.pk,
            'to_account': self.spending_account.pk,  # Same account
            'amount': '100.00',
            'notes': 'Invalid allocation'
        }
        
        form = AllocationForm(data=form_data, family=self.family)
        
        self.assertFalse(form.is_valid())
        self.assertIn('to_account', form.errors)
    
    def test_invalid_allocation_zero_amount(self):
        """Test form with zero amount"""
        form_data = {
            'week': self.week.pk,
            'from_account': self.income_account.pk,
            'to_account': self.spending_account.pk,
            'amount': '0.00',
            'notes': 'Invalid allocation'
        }
        
        form = AllocationForm(data=form_data, family=self.family)
        
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
    
    def test_allocation_form_account_filtering(self):
        """Test that account fields are filtered by family"""
        form = AllocationForm(family=self.family)
        
        # Check that only family accounts are in choices
        from_account_queryset = form.fields['from_account'].queryset
        to_account_queryset = form.fields['to_account'].queryset
        
        family_account_pks = [acc.pk for acc in Account.objects.filter(family=self.family)]
        
        for account in from_account_queryset:
            self.assertIn(account.pk, family_account_pks)
        
        for account in to_account_queryset:
            self.assertIn(account.pk, family_account_pks)


class BudgetTemplateFormTests(BudgetAllocationFormTestCase):
    """Test BudgetTemplateForm functionality"""
    
    def test_valid_fixed_template_form(self):
        """Test form with valid fixed allocation type"""
        form_data = {
            'account': self.spending_account.pk,
            'allocation_type': 'fixed',
            'weekly_amount': '150.00',
            'priority': 1,
            'is_essential': True,
            'never_miss': False
        }
        
        form = BudgetTemplateForm(data=form_data, family=self.family)
        
        self.assertTrue(form.is_valid())
        
        # Test saving the form
        template = form.save(commit=False)
        template.family = self.family
        template.save()
        
        self.assertEqual(template.account, self.spending_account)
        self.assertEqual(template.allocation_type, 'fixed')
        self.assertEqual(template.weekly_amount, Decimal('150.00'))
    
    def test_valid_percentage_template_form(self):
        """Test form with valid percentage allocation type"""
        form_data = {
            'account': self.spending_account.pk,
            'allocation_type': 'percentage',
            'percentage': '15.00',
            'priority': 2
        }
        
        form = BudgetTemplateForm(data=form_data, family=self.family)
        
        self.assertTrue(form.is_valid())
        
        template = form.save(commit=False)
        template.family = self.family
        template.save()
        
        self.assertEqual(template.allocation_type, 'percentage')
        self.assertEqual(template.percentage, Decimal('15.00'))
    
    def test_valid_range_template_form(self):
        """Test form with valid range allocation type"""
        form_data = {
            'account': self.spending_account.pk,
            'allocation_type': 'range',
            'min_amount': '100.00',
            'max_amount': '200.00',
            'priority': 3
        }
        
        form = BudgetTemplateForm(data=form_data, family=self.family)
        
        self.assertTrue(form.is_valid())
        
        template = form.save(commit=False)
        template.family = self.family
        template.save()
        
        self.assertEqual(template.allocation_type, 'range')
        self.assertEqual(template.min_amount, Decimal('100.00'))
        self.assertEqual(template.max_amount, Decimal('200.00'))
    
    def test_invalid_fixed_template_no_amount(self):
        """Test fixed template without weekly_amount"""
        form_data = {
            'account': self.spending_account.pk,
            'allocation_type': 'fixed',
            'priority': 1
            # Missing weekly_amount
        }
        
        form = BudgetTemplateForm(data=form_data, family=self.family)
        
        self.assertFalse(form.is_valid())
        self.assertIn('weekly_amount', form.errors)
    
    def test_invalid_percentage_template_no_percentage(self):
        """Test percentage template without percentage"""
        form_data = {
            'account': self.spending_account.pk,
            'allocation_type': 'percentage',
            'priority': 2
            # Missing percentage
        }
        
        form = BudgetTemplateForm(data=form_data, family=self.family)
        
        self.assertFalse(form.is_valid())
        self.assertIn('percentage', form.errors)
    
    def test_invalid_range_template_missing_amounts(self):
        """Test range template without min/max amounts"""
        form_data = {
            'account': self.spending_account.pk,
            'allocation_type': 'range',
            'priority': 3
            # Missing min_amount and max_amount
        }
        
        form = BudgetTemplateForm(data=form_data, family=self.family)
        
        self.assertFalse(form.is_valid())
        self.assertIn('min_amount', form.errors)
        self.assertIn('max_amount', form.errors)
    
    def test_invalid_range_template_min_greater_than_max(self):
        """Test range template with min > max"""
        form_data = {
            'account': self.spending_account.pk,
            'allocation_type': 'range',
            'min_amount': '200.00',
            'max_amount': '100.00',  # Less than min
            'priority': 3
        }
        
        form = BudgetTemplateForm(data=form_data, family=self.family)
        
        self.assertFalse(form.is_valid())
        self.assertIn('max_amount', form.errors)


class AccountLoanFormTests(BudgetAllocationFormTestCase):
    """Test AccountLoanForm functionality"""
    
    def setUp(self):
        super().setUp()
        # Create additional accounts for loans
        self.savings_account = Account.objects.create(
            family=self.family,
            name='Savings',
            account_type='spending',
            parent=self.root_account
        )
        
        self.emergency_account = Account.objects.create(
            family=self.family,
            name='Emergency Fund',
            account_type='spending',
            parent=self.root_account
        )
    
    def test_valid_loan_form(self):
        """Test form with valid loan data"""
        form_data = {
            'lender_account': self.savings_account.pk,
            'borrower_account': self.emergency_account.pk,
            'original_amount': '500.00',
            'weekly_interest_rate': '0.0200',
            'loan_date': date.today()
        }
        
        form = AccountLoanForm(data=form_data, family=self.family)
        
        self.assertTrue(form.is_valid())
        
        # Test saving the form
        loan = form.save(commit=False)
        loan.family = self.family
        loan.remaining_amount = loan.original_amount
        loan.loan_date = date.today()
        loan.save()
        
        self.assertEqual(loan.lender_account, self.savings_account)
        self.assertEqual(loan.borrower_account, self.emergency_account)
        self.assertEqual(loan.original_amount, Decimal('500.00'))
    
    def test_invalid_loan_same_account(self):
        """Test loan form with same lender and borrower"""
        form_data = {
            'lender_account': self.savings_account.pk,
            'borrower_account': self.savings_account.pk,  # Same account
            'original_amount': '300.00',
            'weekly_interest_rate': '0.0150',
            'loan_date': date.today()
        }
        
        form = AccountLoanForm(data=form_data, family=self.family)
        
        self.assertFalse(form.is_valid())
        # Check for validation error on borrower_account field
        self.assertIn('borrower_account', form.errors)
        self.assertIn('Lender and borrower accounts must be different', str(form.errors))
    
    def test_invalid_loan_zero_amount(self):
        """Test loan form with zero amount"""
        form_data = {
            'lender_account': self.savings_account.pk,
            'borrower_account': self.emergency_account.pk,
            'original_amount': '0.00',
            'weekly_interest_rate': '0.0200',
            'loan_date': date.today()
        }
        
        form = AccountLoanForm(data=form_data, family=self.family)
        
        self.assertFalse(form.is_valid())
        # Check for validation error in __all__ errors
        self.assertIn('Original amount must be greater than 0', str(form.errors))
    
    def test_invalid_loan_negative_interest_rate(self):
        """Test loan form with negative interest rate"""
        form_data = {
            'lender_account': self.savings_account.pk,
            'borrower_account': self.emergency_account.pk,
            'original_amount': '400.00',
            'weekly_interest_rate': '-0.0100',
            'loan_date': date.today()
        }
        
        form = AccountLoanForm(data=form_data, family=self.family)
        
        self.assertFalse(form.is_valid())
        # The negative interest rate should be caught by the field validation
        self.assertTrue('weekly_interest_rate' in form.errors or 
                       any('interest rate' in str(error).lower() for error in form.errors.values()))


class LoanPaymentFormTests(BudgetAllocationFormTestCase):
    """Test LoanPaymentForm functionality"""
    
    def setUp(self):
        super().setUp()
        # Create accounts and loan for testing
        self.savings_account = Account.objects.create(
            family=self.family,
            name='Savings',
            account_type='spending',
            parent=self.root_account
        )
        
        self.emergency_account = Account.objects.create(
            family=self.family,
            name='Emergency Fund',
            account_type='spending',
            parent=self.root_account
        )
        
        self.loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('1000.00'),
            remaining_amount=Decimal('800.00'),
            weekly_interest_rate=Decimal('0.0200'),
            loan_date=date.today()
        )
    
    def test_valid_loan_payment_form(self):
        """Test form with valid payment data"""
        form_data = {
            'loan': self.loan.pk,
            'amount': '100.00',
            'payment_date': date.today().isoformat()
        }
        
        form = LoanPaymentForm(data=form_data, family=self.family)
        
        self.assertTrue(form.is_valid())
        
        # Test saving the form (payment creation would be handled in view)
        cleaned_data = form.cleaned_data
        self.assertEqual(cleaned_data['loan'], self.loan)
        self.assertEqual(cleaned_data['amount'], Decimal('100.00'))
    
    def test_invalid_payment_exceeds_balance(self):
        """Test payment form with amount exceeding loan balance"""
        form_data = {
            'loan': self.loan.pk,
            'amount': '1000.00',  # More than remaining amount (800)
            'payment_date': date.today().isoformat()
        }
        
        form = LoanPaymentForm(data=form_data, family=self.family)
        
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
    
    def test_invalid_payment_zero_amount(self):
        """Test payment form with zero amount"""
        form_data = {
            'loan': self.loan.pk,
            'amount': '0.00',
            'payment_date': date.today().isoformat()
        }
        
        form = LoanPaymentForm(data=form_data, family=self.family)
        
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
    
    def test_loan_payment_form_filtering(self):
        """Test that loan field is filtered by family and active status"""
        # Create loan in different family
        other_family = Family.objects.create(
            name='Other Family',
            created_by=self.user
        )
        other_account1 = Account.objects.create(
            family=other_family,
            name='Other Savings',
            account_type='spending'
        )
        other_account2 = Account.objects.create(
            family=other_family,
            name='Other Emergency',
            account_type='spending'
        )
        other_loan = AccountLoan.objects.create(
            family=other_family,
            lender_account=other_account1,
            borrower_account=other_account2,
            original_amount=Decimal('500.00'),
            remaining_amount=Decimal('500.00'),
            weekly_interest_rate=Decimal('0.0150'),
            loan_date=date.today()
        )
        
        form = LoanPaymentForm(family=self.family)
        
        # Loan choices should only include loans from same family
        loan_queryset = form.fields['loan'].queryset
        loan_pks = [loan.pk for loan in loan_queryset]
        self.assertIn(self.loan.pk, loan_pks)
        self.assertNotIn(other_loan.pk, loan_pks)


class FormWidgetTests(BudgetAllocationFormTestCase):
    """Test form widget rendering and attributes"""
    
    def test_account_form_widgets(self):
        """Test AccountForm widget attributes"""
        form = AccountForm(family=self.family)
        
        # Check color field widget
        color_widget = form.fields['color'].widget
        self.assertTrue(hasattr(color_widget, 'attrs'))
        
        # Check form control classes are applied
        name_widget = form.fields['name'].widget
        self.assertIn('form-control', name_widget.attrs.get('class', ''))
    
    def test_transaction_form_widgets(self):
        """Test TransactionForm widget attributes"""
        form = TransactionForm(family=self.family)
        
        # Check date field widget
        date_widget = form.fields['transaction_date'].widget
        self.assertTrue(hasattr(date_widget, 'attrs'))
        
        # Check amount field has step attribute for decimals
        amount_widget = form.fields['amount'].widget
        self.assertEqual(amount_widget.attrs.get('step'), '0.01')
    
    def test_allocation_form_widgets(self):
        """Test AllocationForm widget attributes"""
        form = AllocationForm(family=self.family)
        
        # Check amount field has proper attributes
        amount_widget = form.fields['amount'].widget
        self.assertEqual(amount_widget.attrs.get('step'), '0.01')
        self.assertEqual(amount_widget.attrs.get('min'), '0.01')
    
    def test_budget_template_form_widgets(self):
        """Test BudgetTemplateForm widget attributes"""
        form = BudgetTemplateForm(family=self.family)
        
        # Check percentage field has proper attributes
        percentage_widget = form.fields['percentage'].widget
        self.assertEqual(percentage_widget.attrs.get('step'), '0.01')
        self.assertEqual(percentage_widget.attrs.get('min'), '0')
        self.assertEqual(percentage_widget.attrs.get('max'), '100')


class FormInitializationTests(BudgetAllocationFormTestCase):
    """Test form initialization with family filtering"""
    
    def test_form_initialization_with_family(self):
        """Test that forms properly initialize with family parameter"""
        forms_to_test = [
            AccountForm,
            TransactionForm,
            AllocationForm,
            BudgetTemplateForm,
            AccountLoanForm,
            LoanPaymentForm
        ]
        
        for form_class in forms_to_test:
            with self.subTest(form=form_class.__name__):
                form = form_class(family=self.family)
                self.assertIsNotNone(form)
                
                # Check that family-related querysets are filtered
                for field_name, field in form.fields.items():
                    if hasattr(field, 'queryset') and field.queryset is not None:
                        # All querysets should be filtered to current family
                        for obj in field.queryset:
                            if hasattr(obj, 'family'):
                                self.assertEqual(obj.family, self.family)
    
    def test_form_initialization_without_family(self):
        """Test that forms handle missing family parameter gracefully"""
        # Some forms should work without family (though might have empty querysets)
        try:
            form = AccountForm()
            self.assertIsNotNone(form)
        except Exception as e:
            # If forms require family, they should raise a clear error
            self.assertIn('family', str(e).lower())


class FormCleanMethodTests(BudgetAllocationFormTestCase):
    """Test custom clean methods in forms"""
    
    def setUp(self):
        super().setUp()
        # Create additional account for tests
        self.savings_account = Account.objects.create(
            family=self.family,
            name='Savings',
            account_type='spending',
            parent=self.root_account
        )
    
    def test_account_form_clean_parent(self):
        """Test AccountForm parent validation"""
        # Test that non-root accounts require parents
        form_data = {
            'name': 'Test Spending',
            'account_type': 'spending',
            # Missing parent for non-root account
        }
        
        form = AccountForm(data=form_data, family=self.family)
        self.assertFalse(form.is_valid())
    
    def test_allocation_form_clean_accounts(self):
        """Test AllocationForm account validation"""
        # Test that from_account and to_account cannot be the same
        form_data = {
            'from_account': self.spending_account.pk,
            'to_account': self.spending_account.pk,
            'amount': '100.00'
        }
        
        form = AllocationForm(data=form_data, family=self.family)
        self.assertFalse(form.is_valid())
        self.assertIn('to_account', form.errors)
    
    def test_loan_form_clean_accounts(self):
        """Test AccountLoanForm account validation"""
        # Test that lender and borrower cannot be the same
        form_data = {
            'lender_account': self.savings_account.pk,
            'borrower_account': self.savings_account.pk,
            'original_amount': '300.00',
            'weekly_interest_rate': '0.0200',
            'loan_date': timezone.now().date()
        }
        
        form = AccountLoanForm(data=form_data, family=self.family)
        self.assertFalse(form.is_valid())
        self.assertIn('borrower_account', form.errors)
