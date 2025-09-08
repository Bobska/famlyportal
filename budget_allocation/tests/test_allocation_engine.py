"""
Budget Allocation Engine Tests

Test the auto-allocation logic, budget template processing, and allocation algorithms.
"""
from django.test import TestCase
from accounts.models import User
from decimal import Decimal
from datetime import date

from accounts.models import Family, FamilyMember
from budget_allocation.models import (
    Account, WeeklyPeriod, BudgetTemplate, Allocation, 
    Transaction, FamilySettings
)
from budget_allocation.utilities import (
    get_current_week, get_available_money, apply_budget_templates,
    get_account_balance, get_account_tree, transfer_money
)


class AllocationEngineTestCase(TestCase):
    """Base test case for allocation engine tests"""
    
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
            family=self.family,
            auto_allocate_enabled=True
        )
        
        # Create account hierarchy
        self.root_account = Account.objects.create(
            family=self.family,
            name='Root',
            account_type='root'
        )
        
        self.income_account = Account.objects.create(
            family=self.family,
            name='Weekly Income',
            account_type='income',
            parent=self.root_account
        )
        
        # Create spending accounts
        self.housing_account = Account.objects.create(
            family=self.family,
            name='Housing',
            account_type='spending',
            parent=self.root_account
        )
        
        self.food_account = Account.objects.create(
            family=self.family,
            name='Food',
            account_type='spending',
            parent=self.root_account
        )
        
        self.transport_account = Account.objects.create(
            family=self.family,
            name='Transportation',
            account_type='spending',
            parent=self.root_account
        )
        
        self.savings_account = Account.objects.create(
            family=self.family,
            name='Savings',
            account_type='spending',
            parent=self.root_account
        )
        
        # Get current week
        self.week = get_current_week(self.family)
        
        # Add weekly income
        Transaction.objects.create(
            family=self.family,
            account=self.income_account,
            week=self.week,
            transaction_date=date.today(),
            amount=Decimal('2000.00'),
            transaction_type='income',
            description='Weekly salary'
        )


class BudgetTemplateProcessingTests(AllocationEngineTestCase):
    """Test budget template processing and allocation calculations"""
    
    def test_apply_fixed_amount_templates(self):
        """Test applying fixed amount budget templates"""
        # Create fixed amount templates
        BudgetTemplate.objects.create(
            family=self.family,
            account=self.housing_account,
            allocation_type='fixed',
            weekly_amount=Decimal('800.00'),
            priority=1,
            is_essential=True,
            never_miss=True
        )
        
        BudgetTemplate.objects.create(
            family=self.family,
            account=self.food_account,
            allocation_type='fixed',
            weekly_amount=Decimal('300.00'),
            priority=2,
            is_essential=True
        )
        
        # Apply templates
        apply_budget_templates(self.family, self.week)
        
        # Check that allocations were created
        housing_allocation = Allocation.objects.filter(
            week=self.week,
            to_account=self.housing_account
        ).first()
        
        food_allocation = Allocation.objects.filter(
            week=self.week,
            to_account=self.food_account
        ).first()
        
        self.assertIsNotNone(housing_allocation)
        self.assertIsNotNone(food_allocation)
        if housing_allocation:
            self.assertEqual(housing_allocation.amount, Decimal('800.00'))
        if food_allocation:
            self.assertEqual(food_allocation.amount, Decimal('300.00'))
    
    def test_apply_percentage_templates(self):
        """Test applying percentage-based budget templates"""
        # Create percentage templates
        BudgetTemplate.objects.create(
            family=self.family,
            account=self.savings_account,
            allocation_type='percentage',
            percentage=Decimal('20.00'),  # 20% of income
            priority=1
        )
        
        BudgetTemplate.objects.create(
            family=self.family,
            account=self.transport_account,
            allocation_type='percentage',
            percentage=Decimal('10.00'),  # 10% of income
            priority=2
        )
        
        # Apply templates
        apply_budget_templates(self.family, self.week)
        
        # Check allocations
        savings_allocation = Allocation.objects.filter(
            week=self.week,
            to_account=self.savings_account
        ).first()
        
        transport_allocation = Allocation.objects.filter(
            week=self.week,
            to_account=self.transport_account
        ).first()
        
        self.assertIsNotNone(savings_allocation)
        self.assertIsNotNone(transport_allocation)
        if savings_allocation:
            self.assertEqual(savings_allocation.amount, Decimal('400.00'))  # 20% of 2000
        if transport_allocation:
            self.assertEqual(transport_allocation.amount, Decimal('200.00'))  # 10% of 2000
    
    def test_priority_based_allocation(self):
        """Test that allocations respect priority order"""
        # Create templates with different priorities requiring more than available
        BudgetTemplate.objects.create(
            family=self.family,
            account=self.housing_account,
            allocation_type='fixed',
            weekly_amount=Decimal('1500.00'),
            priority=1,  # Highest priority
            is_essential=True,
            never_miss=True
        )
        
        BudgetTemplate.objects.create(
            family=self.family,
            account=self.food_account,
            allocation_type='fixed',
            weekly_amount=Decimal('400.00'),
            priority=2
        )
        
        BudgetTemplate.objects.create(
            family=self.family,
            account=self.savings_account,
            allocation_type='fixed',
            weekly_amount=Decimal('500.00'),
            priority=3  # Lowest priority
        )
        
        # Apply templates (total requirement: 2400, available: 2000)
        apply_budget_templates(self.family, self.week)
        
        # Check allocations
        housing_allocation = Allocation.objects.filter(
            week=self.week,
            to_account=self.housing_account
        ).first()
        
        food_allocation = Allocation.objects.filter(
            week=self.week,
            to_account=self.food_account
        ).first()
        
        savings_allocation = Allocation.objects.filter(
            week=self.week,
            to_account=self.savings_account
        ).first()
        
        # Housing should get full amount (priority 1)
        self.assertIsNotNone(housing_allocation)
        if housing_allocation:
            self.assertEqual(housing_allocation.amount, Decimal('1500.00'))
        
        # Food should get its requested amount (priority 2)
        self.assertIsNotNone(food_allocation)
        if food_allocation:
            self.assertEqual(food_allocation.amount, Decimal('400.00'))  # Requested amount
        
        # Savings should get remainder (priority 3, gets what's left)
        self.assertIsNotNone(savings_allocation)
        if savings_allocation:
            self.assertEqual(savings_allocation.amount, Decimal('100.00'))  # 2000 - 1500 - 400


class UtilityFunctionTests(AllocationEngineTestCase):
    """Test utility functions"""
    
    def test_get_available_money(self):
        """Test calculating available money for allocation"""
        # Initially should have full income available
        available = get_available_money(self.family, self.week)
        self.assertEqual(available, Decimal('2000.00'))
        
        # Create allocation to reduce available money
        Allocation.objects.create(
            family=self.family,
            week=self.week,
            from_account=self.income_account,
            to_account=self.housing_account,
            amount=Decimal('500.00'),
            notes='Housing allocation'
        )
        
        # Available money should be reduced
        available = get_available_money(self.family, self.week)
        self.assertEqual(available, Decimal('1500.00'))
    
    def test_get_account_balance(self):
        """Test calculating account balance"""
        # Initially account should have zero balance
        balance = get_account_balance(self.housing_account, self.week)
        self.assertEqual(balance, Decimal('0.00'))
        
        # Add allocation to account
        Allocation.objects.create(
            family=self.family,
            week=self.week,
            from_account=self.income_account,
            to_account=self.housing_account,
            amount=Decimal('800.00'),
            notes='Housing allocation'
        )
        
        # Balance should increase
        balance = get_account_balance(self.housing_account, self.week)
        self.assertEqual(balance, Decimal('800.00'))
        
        # Add expense to reduce balance
        Transaction.objects.create(
            family=self.family,
            account=self.housing_account,
            week=self.week,
            transaction_date=date.today(),
            amount=Decimal('200.00'),
            transaction_type='expense',
            description='Rent payment'
        )
        
        # Balance should decrease
        balance = get_account_balance(self.housing_account, self.week)
        self.assertEqual(balance, Decimal('600.00'))
    
    def test_transfer_money(self):
        """Test money transfer between accounts"""
        # First allocate money to from_account
        Allocation.objects.create(
            family=self.family,
            week=self.week,
            from_account=self.income_account,
            to_account=self.savings_account,
            amount=Decimal('1000.00'),
            notes='Initial savings'
        )
        
        # Transfer money to housing account
        transfer_money(
            from_account=self.savings_account,
            to_account=self.housing_account,
            amount=Decimal('300.00'),
            week=self.week,
            description='Emergency housing fund'
        )
        
        # Check balances
        savings_balance = get_account_balance(self.savings_account, self.week)
        housing_balance = get_account_balance(self.housing_account, self.week)
        
        self.assertEqual(savings_balance, Decimal('700.00'))  # 1000 - 300
        self.assertEqual(housing_balance, Decimal('300.00'))   # 0 + 300
        
        # Check transactions were created
        savings_expenses = Transaction.objects.filter(
            account=self.savings_account,
            transaction_type='expense'
        ).count()
        
        housing_income = Transaction.objects.filter(
            account=self.housing_account,
            transaction_type='income'
        ).count()
        
        self.assertEqual(savings_expenses, 1)
        self.assertEqual(housing_income, 1)
    
    def test_get_account_tree(self):
        """Test account tree generation"""
        tree = get_account_tree(self.family)
        
        # Should have accounts organized hierarchically
        self.assertIsInstance(tree, list)
        self.assertGreater(len(tree), 0)
        
        # Find root account
        root_node = None
        for node in tree:
            if node['account'].name == 'Root':
                root_node = node
                break
        
        # Verify root node structure if found
        if root_node:
            self.assertEqual(root_node['level'], 0)
            self.assertGreater(len(root_node['children']), 0)


class AllocationConstraintsTests(AllocationEngineTestCase):
    """Test allocation constraints and edge cases"""
    
    def test_insufficient_funds_allocation(self):
        """Test allocation when there are insufficient funds"""
        # Create templates requiring more than available income
        BudgetTemplate.objects.create(
            family=self.family,
            account=self.housing_account,
            allocation_type='fixed',
            weekly_amount=Decimal('2500.00'),  # More than 2000 available
            priority=1
        )
        
        # Apply templates
        apply_budget_templates(self.family, self.week)
        
        # Should allocate all available money
        housing_allocation = Allocation.objects.filter(
            week=self.week,
            to_account=self.housing_account
        ).first()
        
        self.assertIsNotNone(housing_allocation)
        if housing_allocation:
            self.assertEqual(housing_allocation.amount, Decimal('2000.00'))  # All available
    
    def test_no_allocations_when_disabled(self):
        """Test that no allocations are made when auto-allocation is disabled"""
        # Disable auto-allocation
        self.family_settings.auto_allocate_enabled = False
        self.family_settings.save()
        
        # Create template
        BudgetTemplate.objects.create(
            family=self.family,
            account=self.housing_account,
            allocation_type='fixed',
            weekly_amount=Decimal('800.00'),
            priority=1
        )
        
        # Apply templates
        apply_budget_templates(self.family, self.week)
        
        # No allocations should be created
        allocations = Allocation.objects.filter(week=self.week)
        self.assertEqual(allocations.count(), 0)
    
    def test_allocation_with_existing_expenses(self):
        """Test allocation when there are existing expenses"""
        # Add expense to reduce available money
        Transaction.objects.create(
            family=self.family,
            account=self.income_account,
            week=self.week,
            transaction_date=date.today(),
            amount=Decimal('500.00'),
            transaction_type='expense',
            description='Emergency expense'
        )
        
        # Available money should be reduced
        available = get_available_money(self.family, self.week)
        self.assertEqual(available, Decimal('1500.00'))  # 2000 - 500
        
        # Create template
        BudgetTemplate.objects.create(
            family=self.family,
            account=self.housing_account,
            allocation_type='fixed',
            weekly_amount=Decimal('800.00'),
            priority=1
        )
        
        # Apply templates
        apply_budget_templates(self.family, self.week)
        
        # Should allocate from remaining available money
        housing_allocation = Allocation.objects.filter(
            week=self.week,
            to_account=self.housing_account
        ).first()
        
        self.assertIsNotNone(housing_allocation)
        if housing_allocation:
            self.assertEqual(housing_allocation.amount, Decimal('800.00'))


class WeeklyPeriodTests(AllocationEngineTestCase):
    """Test weekly period functionality"""
    
    def test_get_current_week(self):
        """Test getting current week for family"""
        week = get_current_week(self.family)
        
        self.assertIsInstance(week, WeeklyPeriod)
        self.assertEqual(week.family, self.family)
        self.assertTrue(week.is_active)
        
        # Should return same week on subsequent calls
        week2 = get_current_week(self.family)
        self.assertEqual(week.pk, week2.pk)
    
    def test_week_date_calculation(self):
        """Test that week dates are calculated correctly"""
        week = get_current_week(self.family)
        
        # Week should span 7 days
        duration = (week.end_date - week.start_date).days
        self.assertEqual(duration, 6)  # 6 days difference = 7 days total
        
        # Start date should be a Monday (default week_start_day = 0)
        self.assertEqual(week.start_date.weekday(), 0)


class TemplateValidationTests(AllocationEngineTestCase):
    """Test budget template validation and edge cases"""
    
    def test_invalid_template_types_skipped(self):
        """Test that invalid templates are skipped during allocation"""
        # Create template with invalid allocation_type
        BudgetTemplate.objects.create(
            family=self.family,
            account=self.housing_account,
            allocation_type='invalid_type',
            priority=1
        )
        
        # Apply templates
        apply_budget_templates(self.family, self.week)
        
        # No allocations should be created for invalid template
        allocations = Allocation.objects.filter(week=self.week)
        self.assertEqual(allocations.count(), 0)
    
    def test_templates_without_amounts_skipped(self):
        """Test that templates without required amounts are skipped"""
        # Create fixed template without weekly_amount
        BudgetTemplate.objects.create(
            family=self.family,
            account=self.housing_account,
            allocation_type='fixed',
            # Missing weekly_amount
            priority=1
        )
        
        # Create percentage template without percentage
        BudgetTemplate.objects.create(
            family=self.family,
            account=self.food_account,
            allocation_type='percentage',
            # Missing percentage
            priority=2
        )
        
        # Apply templates
        apply_budget_templates(self.family, self.week)
        
        # No allocations should be created
        allocations = Allocation.objects.filter(week=self.week)
        self.assertEqual(allocations.count(), 0)
