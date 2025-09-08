"""
Budget Allocation Model Tests

Test model logic, relationships, and calculations for the budget allocation system.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from accounts.models import User
from decimal import Decimal
from datetime import date, timedelta

from accounts.models import Family, FamilyMember
from budget_allocation.models import (
    Account, WeeklyPeriod, BudgetTemplate, Allocation, 
    Transaction, AccountLoan, LoanPayment, FamilySettings
)
from budget_allocation.utilities import (
    get_current_week, get_account_balance, get_available_money,
    transfer_money, get_account_tree
)


class BudgetAllocationModelTestCase(TestCase):
    """Base test case with common setup for budget allocation tests"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users and family
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        self.family = Family.objects.create(
            name='Test Family',
            created_by=self.user1
        )
        
        # Create family members
        self.member1 = FamilyMember.objects.create(
            user=self.user1,
            family=self.family,
            role='admin'
        )
        self.member2 = FamilyMember.objects.create(
            user=self.user2,
            family=self.family,
            role='parent'
        )
        
        # Create family settings
        self.family_settings = FamilySettings.objects.create(
            family=self.family,
            week_start_day=0,  # Monday
            default_interest_rate=Decimal('0.0200'),  # 2%
            auto_allocate_enabled=True,
            auto_repay_enabled=False,
            notification_threshold=Decimal('100.00')
        )


class AccountModelTests(BudgetAllocationModelTestCase):
    """Test Account model functionality"""
    
    def test_account_creation(self):
        """Test basic account creation"""
        account = Account.objects.create(
            family=self.family,
            name='Test Account',
            account_type='spending',
            description='Test account for unit testing'
        )
        
        self.assertEqual(account.name, 'Test Account')
        self.assertEqual(account.account_type, 'spending')
        self.assertEqual(account.family, self.family)
        self.assertTrue(account.is_active)
        self.assertEqual(account.sort_order, 0)
    
    def test_account_hierarchy(self):
        """Test parent-child account relationships"""
        # Create parent account
        parent = Account.objects.create(
            family=self.family,
            name='Housing',
            account_type='spending'
        )
        
        # Create child accounts
        rent = Account.objects.create(
            family=self.family,
            name='Rent',
            account_type='spending',
            parent=parent
        )
        
        utilities = Account.objects.create(
            family=self.family,
            name='Utilities',
            account_type='spending',
            parent=parent
        )
        
        # Test relationships
        self.assertEqual(rent.parent, parent)
        self.assertEqual(utilities.parent, parent)
        self.assertIn(rent, parent.children.all())
        self.assertIn(utilities, parent.children.all())
    
    def test_account_type_validation(self):
        """Test account type validation with parent-child relationships"""
        # Create income parent
        income_parent = Account.objects.create(
            family=self.family,
            name='Income',
            account_type='income'
        )
        
        # Child must match parent type
        income_child = Account.objects.create(
            family=self.family,
            name='Salary',
            account_type='income',
            parent=income_parent
        )
        
        self.assertEqual(income_child.account_type, 'income')
        self.assertEqual(income_child.parent, income_parent)
    
    def test_account_string_representation(self):
        """Test account string representation"""
        account = Account.objects.create(
            family=self.family,
            name='Test Account',
            account_type='spending'
        )
        
        expected = f"{self.family.name} - Test Account"
        self.assertEqual(str(account), expected)


class WeeklyPeriodModelTests(BudgetAllocationModelTestCase):
    """Test WeeklyPeriod model functionality"""
    
    def test_weekly_period_creation(self):
        """Test weekly period creation"""
        start_date = date(2025, 9, 1)  # Monday
        end_date = date(2025, 9, 7)    # Sunday
        
        week = WeeklyPeriod.objects.create(
            family=self.family,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        
        self.assertEqual(week.start_date, start_date)
        self.assertEqual(week.end_date, end_date)
        self.assertTrue(week.is_active)
        self.assertFalse(week.is_allocated)
        self.assertFalse(week.allocation_locked)
    
    def test_weekly_period_validation(self):
        """Test weekly period date validation"""
        start_date = date(2025, 9, 7)  # Sunday
        end_date = date(2025, 9, 1)    # Monday (before start)
        
        week = WeeklyPeriod(
            family=self.family,
            start_date=start_date,
            end_date=end_date
        )
        
        with self.assertRaises(ValidationError):
            week.full_clean()
    
    def test_get_current_week_utility(self):
        """Test get_current_week utility function"""
        current_week = get_current_week(self.family)
        
        self.assertIsInstance(current_week, WeeklyPeriod)
        self.assertEqual(current_week.family, self.family)
        self.assertTrue(current_week.is_active)
    
    def test_weekly_period_string_representation(self):
        """Test weekly period string representation"""
        start_date = date(2025, 9, 1)
        end_date = date(2025, 9, 7)
        
        week = WeeklyPeriod.objects.create(
            family=self.family,
            start_date=start_date,
            end_date=end_date
        )
        
        expected = f"{self.family.name} - Week 2025-09-01 to 2025-09-07"
        self.assertEqual(str(week), expected)


class BudgetTemplateModelTests(BudgetAllocationModelTestCase):
    """Test BudgetTemplate model functionality"""
    
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            family=self.family,
            name='Rent',
            account_type='spending'
        )
    
    def test_fixed_amount_template(self):
        """Test fixed amount budget template"""
        template = BudgetTemplate.objects.create(
            family=self.family,
            account=self.account,
            allocation_type='fixed',
            weekly_amount=Decimal('480.00'),
            priority=1,
            is_essential=True,
            never_miss=True
        )
        
        self.assertEqual(template.allocation_type, 'fixed')
        self.assertEqual(template.weekly_amount, Decimal('480.00'))
        self.assertEqual(template.priority, 1)
        self.assertTrue(template.is_essential)
        self.assertTrue(template.never_miss)
    
    def test_percentage_template(self):
        """Test percentage-based budget template"""
        template = BudgetTemplate.objects.create(
            family=self.family,
            account=self.account,
            allocation_type='percentage',
            percentage=Decimal('15.00'),
            priority=3
        )
        
        self.assertEqual(template.allocation_type, 'percentage')
        self.assertEqual(template.percentage, Decimal('15.00'))
        self.assertEqual(template.priority, 3)
    
    def test_range_template(self):
        """Test range-based budget template"""
        template = BudgetTemplate.objects.create(
            family=self.family,
            account=self.account,
            allocation_type='range',
            min_amount=Decimal('150.00'),
            max_amount=Decimal('250.00'),
            priority=2
        )
        
        self.assertEqual(template.allocation_type, 'range')
        self.assertEqual(template.min_amount, Decimal('150.00'))
        self.assertEqual(template.max_amount, Decimal('250.00'))
    
    def test_template_validation(self):
        """Test budget template validation"""
        # Test missing weekly_amount for fixed type
        template = BudgetTemplate(
            family=self.family,
            account=self.account,
            allocation_type='fixed'
            # missing weekly_amount
        )
        
        with self.assertRaises(ValidationError):
            template.full_clean()


class TransactionModelTests(BudgetAllocationModelTestCase):
    """Test Transaction model functionality"""
    
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            family=self.family,
            name='Checking',
            account_type='spending'
        )
        self.week = get_current_week(self.family)
    
    def test_income_transaction(self):
        """Test income transaction creation"""
        transaction = Transaction.objects.create(
            family=self.family,
            account=self.account,
            week=self.week,
            transaction_date=date.today(),
            amount=Decimal('1000.00'),
            transaction_type='income',
            description='Weekly salary',
            payee='Employer Inc.'
        )
        
        self.assertEqual(transaction.transaction_type, 'income')
        self.assertEqual(transaction.amount, Decimal('1000.00'))
        self.assertEqual(transaction.description, 'Weekly salary')
    
    def test_expense_transaction(self):
        """Test expense transaction creation"""
        transaction = Transaction.objects.create(
            family=self.family,
            account=self.account,
            week=self.week,
            transaction_date=date.today(),
            amount=Decimal('50.00'),
            transaction_type='expense',
            description='Grocery shopping',
            payee='Supermarket'
        )
        
        self.assertEqual(transaction.transaction_type, 'expense')
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.description, 'Grocery shopping')
    
    def test_transaction_validation(self):
        """Test transaction amount validation"""
        transaction = Transaction(
            account=self.account,
            week=self.week,
            transaction_date=date.today(),
            amount=Decimal('-10.00'),  # Negative amount
            transaction_type='income',
            description='Invalid transaction'
        )
        
        with self.assertRaises(ValidationError):
            transaction.full_clean()


class AllocationModelTests(BudgetAllocationModelTestCase):
    """Test Allocation model functionality"""
    
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            family=self.family,
            name='Food',
            account_type='spending'
        )
        self.week = get_current_week(self.family)
    
    def test_allocation_creation(self):
        """Test allocation creation"""
        # Create a second account for valid allocation
        to_account = Account.objects.create(
            family=self.family,
            name='Savings',
            account_type='spending'
        )
        
        allocation = Allocation.objects.create(
            family=self.family,
            week=self.week,
            from_account=self.account,
            to_account=to_account,
            amount=Decimal('200.00'),
            notes='Weekly food budget'
        )
        
        self.assertEqual(allocation.from_account, self.account)
        self.assertEqual(allocation.to_account, to_account)
        self.assertEqual(allocation.week, self.week)
        self.assertEqual(allocation.amount, Decimal('200.00'))
        self.assertEqual(allocation.notes, 'Weekly food budget')
    
    def test_allocation_validation(self):
        """Test allocation amount validation"""
        # Need a second account for valid allocation
        to_account = Account.objects.create(
            family=self.family,
            name='Savings',
            account_type='spending'
        )
        
        allocation = Allocation(
            week=self.week,
            from_account=self.account,
            to_account=to_account,
            amount=Decimal('0.00'),  # Zero amount
            notes='Invalid allocation'
        )
        
        with self.assertRaises(ValidationError):
            allocation.full_clean()


class AccountLoanModelTests(BudgetAllocationModelTestCase):
    """Test AccountLoan model functionality"""
    
    def setUp(self):
        super().setUp()
        self.lender = Account.objects.create(
            family=self.family,
            name='Savings',
            account_type='spending'
        )
        self.borrower = Account.objects.create(
            family=self.family,
            name='Emergency',
            account_type='spending'
        )
    
    def test_loan_creation(self):
        """Test loan creation"""
        loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.lender,
            borrower_account=self.borrower,
            original_amount=Decimal('500.00'),
            remaining_amount=Decimal('500.00'),
            weekly_interest_rate=Decimal('0.0200'),
            loan_date=date.today()
        )
        
        self.assertEqual(loan.lender_account, self.lender)
        self.assertEqual(loan.borrower_account, self.borrower)
        self.assertEqual(loan.original_amount, Decimal('500.00'))
        self.assertEqual(loan.remaining_amount, Decimal('500.00'))
        self.assertEqual(loan.weekly_interest_rate, Decimal('0.0200'))
        self.assertTrue(loan.is_active)
    
    def test_loan_interest_calculation(self):
        """Test loan interest calculation"""
        loan = AccountLoan.objects.create(
            family=self.family,
            lender_account=self.lender,
            borrower_account=self.borrower,
            original_amount=Decimal('1000.00'),
            remaining_amount=Decimal('1000.00'),
            weekly_interest_rate=Decimal('0.0200'),  # 2%
            loan_date=date.today()
        )
        
        # Calculate expected interest: 1000 * 0.02 = 20
        expected_interest = Decimal('20.00')
        calculated_interest = loan.remaining_amount * loan.weekly_interest_rate
        
        self.assertEqual(calculated_interest, expected_interest)


class BalanceCalculationTests(BudgetAllocationModelTestCase):
    """Test account balance calculation utilities"""
    
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            family=self.family,
            name='Checking',
            account_type='spending'
        )
        self.week = get_current_week(self.family)
    
    def test_simple_balance_calculation(self):
        """Test basic balance calculation with allocations and transactions"""
        # Create a second account for valid allocation
        source_account = Account.objects.create(
            family=self.family,
            name='Income',
            account_type='income'
        )
        
        # Add allocation
        Allocation.objects.create(
            family=self.family,
            from_account=source_account,
            to_account=self.account,
            week=self.week,
            amount=Decimal('500.00'),
            notes='Weekly allocation'
        )
        
        # Add income transaction
        Transaction.objects.create(
            family=self.family,
            account=self.account,
            week=self.week,
            transaction_date=date.today(),
            amount=Decimal('100.00'),
            transaction_type='income',
            description='Bonus payment'
        )
        
        # Add expense transaction
        Transaction.objects.create(
            family=self.family,
            account=self.account,
            week=self.week,
            transaction_date=date.today(),
            amount=Decimal('50.00'),
            transaction_type='expense',
            description='Purchase'
        )
        
        # Calculate balance: 500 (allocation) + 100 (income) - 50 (expense) = 550
        balance = get_account_balance(self.account, self.week)
        expected_balance = Decimal('550.00')
        
        self.assertEqual(balance, expected_balance)
    
    def test_zero_balance_calculation(self):
        """Test balance calculation with no transactions"""
        balance = get_account_balance(self.account, self.week)
        self.assertEqual(balance, Decimal('0.00'))
    
    def test_negative_balance_calculation(self):
        """Test balance calculation resulting in negative balance"""
        # Create a second account for valid allocation
        source_account = Account.objects.create(
            family=self.family,
            name='Income',
            account_type='income'
        )
        
        # Add small allocation
        Allocation.objects.create(
            family=self.family,
            from_account=source_account,
            to_account=self.account,
            week=self.week,
            amount=Decimal('50.00'),
            notes='Small allocation'
        )
        
        # Add large expense
        Transaction.objects.create(
            family=self.family,
            account=self.account,
            week=self.week,
            transaction_date=date.today(),
            amount=Decimal('100.00'),
            transaction_type='expense',
            description='Overdraft'
        )
        
        # Balance: 50 - 100 = -50
        balance = get_account_balance(self.account, self.week)
        expected_balance = Decimal('-50.00')
        
        self.assertEqual(balance, expected_balance)


class MoneyTransferTests(BudgetAllocationModelTestCase):
    """Test money transfer utilities"""
    
    def setUp(self):
        super().setUp()
        self.from_account = Account.objects.create(
            family=self.family,
            name='Savings',
            account_type='spending'
        )
        self.to_account = Account.objects.create(
            family=self.family,
            name='Checking',
            account_type='spending'
        )
        self.week = get_current_week(self.family)
        
        # Create a source account for initial balance allocation
        source_account = Account.objects.create(
            family=self.family,
            name='Income',
            account_type='income'
        )
        
        # Add initial balance to from_account
        Allocation.objects.create(
            family=self.family,
            from_account=source_account,
            to_account=self.from_account,
            week=self.week,
            amount=Decimal('1000.00'),
            notes='Initial balance'
        )
    
    def test_successful_transfer(self):
        """Test successful money transfer"""
        transfer_amount = Decimal('300.00')
        
        # Execute transfer
        transfer_money(
            from_account=self.from_account,
            to_account=self.to_account,
            amount=transfer_amount,
            week=self.week,
            description='Test transfer'
        )
        
        # Check balances
        from_balance = get_account_balance(self.from_account, self.week)
        to_balance = get_account_balance(self.to_account, self.week)
        
        self.assertEqual(from_balance, Decimal('700.00'))  # 1000 - 300
        self.assertEqual(to_balance, Decimal('300.00'))    # 0 + 300
        
        # Check transactions were created
        from_transactions = Transaction.objects.filter(
            account=self.from_account,
            transaction_type='expense'
        ).count()
        to_transactions = Transaction.objects.filter(
            account=self.to_account,
            transaction_type='income'
        ).count()
        
        self.assertEqual(from_transactions, 1)
        self.assertEqual(to_transactions, 1)
    
    def test_insufficient_funds_transfer(self):
        """Test transfer with insufficient funds"""
        transfer_amount = Decimal('1500.00')  # More than available
        
        with self.assertRaises(ValidationError):
            transfer_money(
                from_account=self.from_account,
                to_account=self.to_account,
                amount=transfer_amount,
                week=self.week,
                description='Insufficient funds transfer'
            )
    
    def test_invalid_transfer_amount(self):
        """Test transfer with invalid amount"""
        with self.assertRaises(ValidationError):
            transfer_money(
                from_account=self.from_account,
                to_account=self.to_account,
                amount=Decimal('-100.00'),  # Negative amount
                week=self.week,
                description='Invalid transfer'
            )


class AccountTreeTests(BudgetAllocationModelTestCase):
    """Test account tree utilities"""
    
    def setUp(self):
        super().setUp()
        
        # Create hierarchical account structure
        self.root = Account.objects.create(
            family=self.family,
            name='Root',
            account_type='root'
        )
        
        self.income = Account.objects.create(
            family=self.family,
            name='Income',
            account_type='income',
            parent=self.root
        )
        
        self.spending = Account.objects.create(
            family=self.family,
            name='Spending',
            account_type='spending',
            parent=self.root
        )
        
        self.salary = Account.objects.create(
            family=self.family,
            name='Salary',
            account_type='income',
            parent=self.income
        )
        
        self.housing = Account.objects.create(
            family=self.family,
            name='Housing',
            account_type='spending',
            parent=self.spending
        )
    
    def test_account_tree_structure(self):
        """Test account tree generation"""
        tree = get_account_tree(self.family)
        
        # Should have root accounts at top level
        self.assertGreater(len(tree), 0)
        
        # Find the root account in tree
        root_node = None
        for node in tree:
            if node['account'].name == 'Root':
                root_node = node
                break
        
        self.assertIsNotNone(root_node)
        
        # Verify root node structure if found
        if root_node:
            self.assertEqual(root_node['level'], 0)
            self.assertEqual(len(root_node['children']), 2)  # Income and Spending
            
            # Check child nodes
            child_names = [child['account'].name for child in root_node['children']]
            self.assertIn('Income', child_names)
            self.assertIn('Spending', child_names)


class FamilySettingsTests(BudgetAllocationModelTestCase):
    """Test FamilySettings model"""
    
    def test_family_settings_creation(self):
        """Test family settings creation with defaults"""
        # Delete existing settings from setUp
        self.family_settings.delete()
        
        # Create new settings
        settings = FamilySettings.objects.create(
            family=self.family
        )
        
        # Check defaults
        self.assertEqual(settings.week_start_day, 0)  # Monday
        self.assertEqual(settings.default_interest_rate, Decimal('0.0200'))
        self.assertTrue(settings.auto_allocate_enabled)
        self.assertFalse(settings.auto_repay_enabled)
        self.assertEqual(settings.notification_threshold, Decimal('100.00'))
    
    def test_family_settings_string_representation(self):
        """Test family settings string representation"""
        expected = f"{self.family.name} - Settings"
        self.assertEqual(str(self.family_settings), expected)
