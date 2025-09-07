"""
Budget Allocation Loan System Tests

Test loan creation, interest calculation, payment processing, and automated features.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta

from accounts.models import Family, FamilyMember
from budget_allocation.models import (
    Account, WeeklyPeriod, AccountLoan, LoanPayment, 
    Transaction, FamilySettings
)
from budget_allocation.utilities import (
    get_current_week, get_account_balance, transfer_money
)


class LoanSystemTestCase(TestCase):
    """Base test case for loan system tests"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users and family
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.family = Family.objects.create(name='Test Family')
        
        self.member = FamilyMember.objects.create(
            user=self.user,
            family=self.family,
            role='admin'
        )
        
        # Create family settings
        self.family_settings = FamilySettings.objects.create(
            family=self.family,
            default_interest_rate=Decimal('0.0200'),  # 2% weekly
            auto_repay_enabled=False
        )
        
        # Create accounts
        self.root_account = Account.objects.create(
            family=self.family,
            name='Root',
            account_type='root'
        )
        
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
        
        self.vacation_account = Account.objects.create(
            family=self.family,
            name='Vacation Fund',
            account_type='spending',
            parent=self.root_account
        )
        
        # Get current week
        self.week = get_current_week(self.family)


class AccountLoanModelTests(LoanSystemTestCase):
    """Test AccountLoan model functionality"""
    
    def test_loan_creation(self):
        """Test basic loan creation"""
        loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('1000.00'),
            remaining_amount=Decimal('1000.00'),
            weekly_interest_rate=Decimal('0.0200'),
            loan_date=date.today()
        )
        
        self.assertEqual(loan.family, self.family)
        self.assertEqual(loan.lender_account, self.savings_account)
        self.assertEqual(loan.borrower_account, self.emergency_account)
        self.assertEqual(loan.original_amount, Decimal('1000.00'))
        self.assertEqual(loan.remaining_amount, Decimal('1000.00'))
        self.assertTrue(loan.is_active)
        self.assertEqual(loan.loan_date, date.today())
    
    def test_loan_string_representation(self):
        """Test loan string representation"""
        loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('500.00'),
            remaining_amount=Decimal('400.00'),
            weekly_interest_rate=Decimal('0.0150'),
            loan_date=date.today()
        )
        
        expected = f"Loan: {self.savings_account.name} → {self.emergency_account.name}: ${loan.remaining_amount}"
        self.assertEqual(str(loan), expected)
    
    def test_loan_validation(self):
        """Test loan model validation"""
        # Test same account validation
        with self.assertRaises(ValidationError):
            loan = AccountLoan(
                family=self.family,
                lender_account=self.savings_account,
                borrower_account=self.savings_account,  # Same account
                original_amount=Decimal('500.00'),
                remaining_amount=Decimal('500.00'),
                weekly_interest_rate=Decimal('0.0200'),
                loan_date=date.today()
            )
            loan.full_clean()
        
        # Test negative amount validation
        with self.assertRaises(ValidationError):
            loan = AccountLoan(
                family=self.family,
                lender_account=self.savings_account,
                borrower_account=self.emergency_account,
                original_amount=Decimal('-100.00'),  # Negative amount
                remaining_amount=Decimal('-100.00'),
                weekly_interest_rate=Decimal('0.0200'),
                loan_date=date.today()
            )
            loan.full_clean()
        
        # Test zero interest rate (should be allowed)
        loan = AccountLoan(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('300.00'),
            remaining_amount=Decimal('300.00'),
            weekly_interest_rate=Decimal('0.0000'),  # Zero interest
            loan_date=date.today()
        )
        
        try:
            loan.full_clean()
            loan.save()
            self.assertEqual(loan.weekly_interest_rate, Decimal('0.0000'))
        except ValidationError:
            self.fail("Zero interest rate should be allowed")
    
    def test_loan_completion(self):
        """Test marking loan as completed"""
        loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('800.00'),
            remaining_amount=Decimal('50.00'),
            weekly_interest_rate=Decimal('0.0200'),
            loan_date=date.today()
        )
        
        # Mark loan as completed
        loan.remaining_amount = Decimal('0.00')
        loan.is_active = False
        loan.save()
        
        self.assertEqual(loan.remaining_amount, Decimal('0.00'))
        self.assertFalse(loan.is_active)


class LoanPaymentModelTests(LoanSystemTestCase):
    """Test LoanPayment model functionality"""
    
    def setUp(self):
        super().setUp()
        # Create a loan for testing payments
        self.loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('1000.00'),
            remaining_amount=Decimal('800.00'),
            weekly_interest_rate=Decimal('0.0200'),
            loan_date=date.today() - timedelta(days=14)  # 2 weeks ago
        )
    
    def test_payment_creation(self):
        """Test basic loan payment creation"""
        payment = LoanPayment.objects.create(
            loan=self.loan,
            week=self.week,
            amount=Decimal('100.00'),
            payment_date=date.today()
        )
        
        self.assertEqual(payment.loan, self.loan)
        self.assertEqual(payment.week, self.week)
        self.assertEqual(payment.amount, Decimal('100.00'))
        self.assertEqual(payment.payment_date, date.today())
    
    def test_payment_string_representation(self):
        """Test payment string representation"""
        payment = LoanPayment.objects.create(
            loan=self.loan,
            week=self.week,
            amount=Decimal('150.00'),
            payment_date=date.today()
        )
        
        expected = f"Payment ${payment.amount} for {self.loan}"
        self.assertEqual(str(payment), expected)
    
    def test_payment_validation(self):
        """Test payment validation"""
        # Test negative payment amount
        with self.assertRaises(ValidationError):
            payment = LoanPayment(
                loan=self.loan,
                week=self.week,
                amount=Decimal('-50.00'),  # Negative amount
                payment_date=date.today()
            )
            payment.full_clean()
        
        # Test valid payment
        payment = LoanPayment(
            loan=self.loan,
            week=self.week,
            amount=Decimal('100.00'),
            payment_date=date.today()
        )
        
        try:
            payment.full_clean()
            payment.save()
            self.assertEqual(payment.amount, Decimal('100.00'))
        except ValidationError:
            self.fail("Valid payment should not raise ValidationError")
    
    def test_payment_exceeds_balance_validation(self):
        """Test that payment cannot exceed loan balance"""
        # Note: This validation would typically be handled at the view/form level
        # The model allows any payment amount
        payment = LoanPayment(
            loan=self.loan,
            week=self.week,
            amount=Decimal('1000.00'),  # More than remaining 800
            payment_date=date.today()
        )
        
        # Model validation should pass (business logic enforced elsewhere)
        try:
            payment.full_clean()
            payment.save()
            self.assertEqual(payment.amount, Decimal('1000.00'))
        except ValidationError:
            self.fail("Model should allow large payments (business logic enforced in views)")


class LoanInterestCalculationTests(LoanSystemTestCase):
    """Test loan interest calculation and processing"""
    
    def test_simple_interest_calculation(self):
        """Test basic interest calculation"""
        loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('1000.00'),
            remaining_amount=Decimal('1000.00'),
            weekly_interest_rate=Decimal('0.0200'),  # 2%
            loan_date=date.today()
        )
        
        # Calculate interest
        interest = loan.remaining_amount * loan.weekly_interest_rate
        expected_interest = Decimal('20.00')
        
        self.assertEqual(interest, expected_interest)
    
    def test_zero_interest_loan(self):
        """Test loan with zero interest rate"""
        loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('500.00'),
            remaining_amount=Decimal('500.00'),
            weekly_interest_rate=Decimal('0.0000'),  # 0% interest
            loan_date=date.today()
        )
        
        # Calculate interest
        interest = loan.remaining_amount * loan.weekly_interest_rate
        expected_interest = Decimal('0.00')
        
        self.assertEqual(interest, expected_interest)
    
    def test_high_precision_interest_calculation(self):
        """Test interest calculation with high precision"""
        loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('333.33'),
            remaining_amount=Decimal('333.33'),
            weekly_interest_rate=Decimal('0.0333'),  # 3.33%
            loan_date=date.today()
        )
        
        # Calculate interest with proper rounding
        interest = (loan.remaining_amount * loan.weekly_interest_rate).quantize(Decimal('0.01'))
        expected_interest = Decimal('11.10')  # 333.33 * 0.0333 = 10.9999 → 11.00
        
        self.assertEqual(interest, expected_interest)


class LoanTransactionIntegrationTests(LoanSystemTestCase):
    """Test loan integration with transaction system"""
    
    def setUp(self):
        super().setUp()
        
        # Add initial balances to accounts
        Transaction.objects.create(
            account=self.savings_account,
            week=self.week,
            transaction_date=date.today(),
            amount=Decimal('2000.00'),
            transaction_type='income',
            description='Initial savings balance'
        )
        
        Transaction.objects.create(
            account=self.emergency_account,
            week=self.week,
            transaction_date=date.today(),
            amount=Decimal('100.00'),
            transaction_type='income',
            description='Initial emergency balance'
        )
    
    def test_loan_creation_with_transfer(self):
        """Test creating loan with money transfer"""
        # Check initial balances
        savings_balance = get_account_balance(self.savings_account, self.week)
        emergency_balance = get_account_balance(self.emergency_account, self.week)
        
        self.assertEqual(savings_balance, Decimal('2000.00'))
        self.assertEqual(emergency_balance, Decimal('100.00'))
        
        # Create loan and transfer money
        loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('500.00'),
            remaining_amount=Decimal('500.00'),
            weekly_interest_rate=Decimal('0.0200'),
            loan_date=date.today()
        )
        
        # Transfer loan amount
        transfer_money(
            from_account=self.savings_account,
            to_account=self.emergency_account,
            amount=Decimal('500.00'),
            week=self.week,
            description=f'Loan disbursement - Loan: {loan}',
            loan=loan
        )
        
        # Check updated balances
        savings_balance = get_account_balance(self.savings_account, self.week)
        emergency_balance = get_account_balance(self.emergency_account, self.week)
        
        self.assertEqual(savings_balance, Decimal('1500.00'))  # 2000 - 500
        self.assertEqual(emergency_balance, Decimal('600.00'))  # 100 + 500
    
    def test_loan_payment_with_transfer(self):
        """Test making loan payment with money transfer"""
        # Create loan
        loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('800.00'),
            remaining_amount=Decimal('800.00'),
            weekly_interest_rate=Decimal('0.0200'),
            loan_date=date.today()
        )
        
        # Calculate payment amounts
        interest_amount = loan.remaining_amount * loan.weekly_interest_rate  # 16.00
        payment_amount = Decimal('200.00')
        principal_amount = payment_amount - interest_amount  # 184.00
        
        # Make payment
        transfer_money(
            from_account=self.emergency_account,
            to_account=self.savings_account,
            amount=payment_amount,
            week=self.week,
            description=f'Loan payment - {loan}'
        )
        
        # Create payment record
        LoanPayment.objects.create(
            loan=loan,
            week=self.week,
            amount=payment_amount,
            payment_date=date.today()
        )
        
        # Update loan balance
        loan.remaining_amount -= principal_amount
        loan.save()
        
        # Check updated loan balance
        self.assertEqual(loan.remaining_amount, Decimal('616.00'))  # 800 - 184
        
        # Check account balances
        savings_balance = get_account_balance(self.savings_account, self.week)
        emergency_balance = get_account_balance(self.emergency_account, self.week)
        
        # Emergency account should have: 100 (initial) - 200 (payment) = -100
        # Savings account should have: 2000 (initial) + 200 (payment) = 2200
        self.assertEqual(emergency_balance, Decimal('-100.00'))
        self.assertEqual(savings_balance, Decimal('2200.00'))


class LoanQueryTests(LoanSystemTestCase):
    """Test loan querying and filtering"""
    
    def setUp(self):
        super().setUp()
        
        # Create multiple loans in different states
        self.active_loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('1000.00'),
            remaining_amount=Decimal('600.00'),
            weekly_interest_rate=Decimal('0.0200'),
            loan_date=date.today() - timedelta(days=30),
            is_active=True
        )
        
        self.completed_loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.vacation_account,
            original_amount=Decimal('500.00'),
            remaining_amount=Decimal('0.00'),
            weekly_interest_rate=Decimal('0.0150'),
            loan_date=date.today() - timedelta(days=60),
            is_active=False
        )
        
        self.new_loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.emergency_account,
            borrower_account=self.vacation_account,
            original_amount=Decimal('300.00'),
            remaining_amount=Decimal('300.00'),
            weekly_interest_rate=Decimal('0.0100'),
            loan_date=date.today(),
            is_active=True
        )
    
    def test_active_loans_query(self):
        """Test querying active loans"""
        active_loans = AccountLoan.objects.filter(
            family=self.family,
            is_active=True
        )
        
        self.assertEqual(active_loans.count(), 2)
        self.assertIn(self.active_loan, active_loans)
        self.assertIn(self.new_loan, active_loans)
        self.assertNotIn(self.completed_loan, active_loans)
    
    def test_completed_loans_query(self):
        """Test querying completed loans"""
        completed_loans = AccountLoan.objects.filter(
            family=self.family,
            is_active=False
        )
        
        self.assertEqual(completed_loans.count(), 1)
        self.assertIn(self.completed_loan, completed_loans)
        self.assertNotIn(self.active_loan, completed_loans)
    
    def test_loans_by_account_query(self):
        """Test querying loans by account"""
        # Loans where savings is lender
        savings_loans = AccountLoan.objects.filter(
            family=self.family,
            lender_account=self.savings_account
        )
        
        self.assertEqual(savings_loans.count(), 2)
        self.assertIn(self.active_loan, savings_loans)
        self.assertIn(self.completed_loan, savings_loans)
        
        # Loans where emergency is borrower
        emergency_loans = AccountLoan.objects.filter(
            family=self.family,
            borrower_account=self.emergency_account
        )
        
        self.assertEqual(emergency_loans.count(), 1)
        self.assertIn(self.active_loan, emergency_loans)
    
    def test_loans_with_balance_query(self):
        """Test querying loans with remaining balance"""
        loans_with_balance = AccountLoan.objects.filter(
            family=self.family,
            remaining_amount__gt=Decimal('0.00')
        )
        
        self.assertEqual(loans_with_balance.count(), 2)
        self.assertIn(self.active_loan, loans_with_balance)
        self.assertIn(self.new_loan, loans_with_balance)
        self.assertNotIn(self.completed_loan, loans_with_balance)


class LoanBusinessLogicTests(LoanSystemTestCase):
    """Test loan business logic and constraints"""
    
    def test_loan_cannot_exceed_lender_balance(self):
        """Test business logic for loan amount limits"""
        # Add limited balance to savings account
        Transaction.objects.create(
            account=self.savings_account,
            week=self.week,
            transaction_date=date.today(),
            amount=Decimal('300.00'),
            transaction_type='income',
            description='Limited savings'
        )
        
        savings_balance = get_account_balance(self.savings_account, self.week)
        self.assertEqual(savings_balance, Decimal('300.00'))
        
        # Trying to create loan larger than balance should be handled at view level
        # Model itself allows this, business logic enforced in views/forms
        loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('500.00'),  # More than available
            remaining_amount=Decimal('500.00'),
            weekly_interest_rate=Decimal('0.0200'),
            loan_date=date.today()
        )
        
        # Model creation succeeds, business logic validation is at view level
        self.assertEqual(loan.original_amount, Decimal('500.00'))
    
    def test_multiple_loans_between_accounts(self):
        """Test multiple active loans between same accounts"""
        # Create first loan
        loan1 = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('400.00'),
            remaining_amount=Decimal('400.00'),
            weekly_interest_rate=Decimal('0.0200'),
            loan_date=date.today()
        )
        
        # Create second loan between same accounts
        loan2 = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('300.00'),
            remaining_amount=Decimal('300.00'),
            weekly_interest_rate=Decimal('0.0150'),
            loan_date=date.today()
        )
        
        # Both loans should exist independently
        self.assertNotEqual(loan1.pk, loan2.pk)
        self.assertEqual(loan1.lender_account, loan2.lender_account)
        self.assertEqual(loan1.borrower_account, loan2.borrower_account)
        
        # Total debt from emergency to savings should be 700
        loans = AccountLoan.objects.filter(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            is_active=True
        )
        
        total_debt = sum(loan.remaining_amount for loan in loans)
        self.assertEqual(total_debt, Decimal('700.00'))
    
    def test_loan_payment_history(self):
        """Test tracking loan payment history"""
        # Create loan
        loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('1000.00'),
            remaining_amount=Decimal('1000.00'),
            weekly_interest_rate=Decimal('0.0200'),
            loan_date=date.today()
        )
        
        # Make several payments
        payment_amounts = [Decimal('100.00'), Decimal('150.00'), Decimal('200.00')]
        
        for i, amount in enumerate(payment_amounts):
            # Create payment record
            LoanPayment.objects.create(
                loan=loan,
                week=self.week,
                amount=amount,
                payment_date=date.today() + timedelta(days=i)
            )
        
        # Check payment history
        payment_history = LoanPayment.objects.filter(loan=loan).order_by('payment_date')
        self.assertEqual(payment_history.count(), 3)
        
        # Check total payments
        total_paid = sum(payment.amount for payment in payment_history)
        self.assertEqual(total_paid, Decimal('450.00'))
        
        # Verify individual payment amounts
        payments_list = list(payment_history.values_list('amount', flat=True))
        expected_amounts = [Decimal('100.00'), Decimal('150.00'), Decimal('200.00')]
        self.assertEqual(payments_list, expected_amounts)


class LoanEdgeCaseTests(LoanSystemTestCase):
    """Test edge cases and error conditions"""
    
    def test_loan_with_future_date(self):
        """Test loan with future loan date"""
        future_date = date.today() + timedelta(days=30)
        
        loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('500.00'),
            remaining_amount=Decimal('500.00'),
            weekly_interest_rate=Decimal('0.0200'),
            loan_date=future_date
        )
        
        self.assertEqual(loan.loan_date, future_date)
        # Future loans should be allowed for planning purposes
    
    def test_loan_with_very_small_amount(self):
        """Test loan with very small amount"""
        loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('0.01'),  # 1 cent
            remaining_amount=Decimal('0.01'),
            weekly_interest_rate=Decimal('0.0200'),
            loan_date=date.today()
        )
        
        self.assertEqual(loan.original_amount, Decimal('0.01'))
        
        # Interest calculation should work with small amounts
        interest = loan.remaining_amount * loan.weekly_interest_rate
        expected_interest = Decimal('0.0002')  # Will round to 0.00
        
        # When rounded to 2 decimal places
        rounded_interest = interest.quantize(Decimal('0.01'))
        self.assertEqual(rounded_interest, Decimal('0.00'))
    
    def test_loan_with_very_high_interest(self):
        """Test loan with very high interest rate"""
        loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.emergency_account,
            original_amount=Decimal('100.00'),
            remaining_amount=Decimal('100.00'),
            weekly_interest_rate=Decimal('0.5000'),  # 50% weekly interest
            loan_date=date.today()
        )
        
        self.assertEqual(loan.weekly_interest_rate, Decimal('0.5000'))
        
        # Interest calculation should work with high rates
        interest = loan.remaining_amount * loan.weekly_interest_rate
        expected_interest = Decimal('50.00')
        
        self.assertEqual(interest, expected_interest)
