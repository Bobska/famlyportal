"""
Budget Allocation View Tests

Test view functionality, permissions, and HTTP responses for the budget allocation system.
"""
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from django.http import JsonResponse
from decimal import Decimal
from datetime import date

from accounts.models import Family, FamilyMember
from budget_allocation.models import (
    Account, WeeklyPeriod, BudgetTemplate, Allocation, 
    Transaction, AccountLoan, FamilySettings
)


class BudgetAllocationViewTestCase(TestCase):
    """Base test case for budget allocation view tests"""
    
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
        self.income_account = Account.objects.create(
            family=self.family,
            name='Main Income',
            account_type='income'
        )
        
        self.spending_account = Account.objects.create(
            family=self.family,
            name='Food Budget',
            account_type='spending'
        )
        
        # Create current week
        from budget_allocation.utilities import get_current_week
        self.week = get_current_week(self.family)
        
        # Create client and login
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')


class DashboardViewTests(BudgetAllocationViewTestCase):
    """Test dashboard view functionality"""
    
    def test_dashboard_get(self):
        """Test GET request to dashboard"""
        url = reverse('budget_allocation:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Budget Dashboard')
        self.assertContains(response, self.week.start_date.strftime('%B %d'))
    
    def test_dashboard_unauthenticated(self):
        """Test dashboard access without authentication"""
        self.client.logout()
        url = reverse('budget_allocation:dashboard')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].find('/accounts/login/') != -1)
    
    def test_dashboard_context_data(self):
        """Test dashboard context contains required data"""
        url = reverse('budget_allocation:dashboard')
        response = self.client.get(url)
        
        context = response.context
        self.assertIn('current_week', context)
        self.assertIn('account_tree', context)
        self.assertIn('weekly_summary', context)
        self.assertIn('recent_transactions', context)
        
        self.assertEqual(context['current_week'], self.week)


class AccountViewTests(BudgetAllocationViewTestCase):
    """Test account management views"""
    
    def test_account_list_view(self):
        """Test account list view"""
        url = reverse('budget_allocation:account_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Account Management')
        self.assertContains(response, self.income_account.name)
        self.assertContains(response, self.spending_account.name)
    
    def test_account_create_get(self):
        """Test GET request to account create view"""
        url = reverse('budget_allocation:account_create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Account')
        self.assertContains(response, 'Account Name')
    
    def test_account_create_post_valid(self):
        """Test POST request to create account with valid data"""
        url = reverse('budget_allocation:account_create')
        data = {
            'name': 'New Test Account',
            'account_type': 'spending',
            'description': 'Test account description',
            'color': '#28a745'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Check account was created
        account = Account.objects.get(name='New Test Account')
        self.assertEqual(account.family, self.family)
        self.assertEqual(account.account_type, 'spending')
        self.assertEqual(account.description, 'Test account description')
    
    def test_account_create_post_invalid(self):
        """Test POST request to create account with invalid data"""
        url = reverse('budget_allocation:account_create')
        data = {
            'name': '',  # Empty name
            'account_type': 'spending'
        }
        
        response = self.client.post(url, data)
        
        # Should return form with errors
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'name', 'This field is required.')
    
    def test_account_update_get(self):
        """Test GET request to account update view"""
        url = reverse('budget_allocation:account_update', kwargs={'pk': self.spending_account.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Account')
        self.assertContains(response, self.spending_account.name)
    
    def test_account_update_post_valid(self):
        """Test POST request to update account with valid data"""
        url = reverse('budget_allocation:account_update', kwargs={'pk': self.spending_account.pk})
        data = {
            'name': 'Updated Account Name',
            'account_type': self.spending_account.account_type,
            'description': 'Updated description',
            'color': '#ffc107'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Check account was updated
        updated_account = Account.objects.get(pk=self.spending_account.pk)
        self.assertEqual(updated_account.name, 'Updated Account Name')
        self.assertEqual(updated_account.description, 'Updated description')
    
    def test_account_delete_get(self):
        """Test GET request to account delete view"""
        url = reverse('budget_allocation:account_delete', kwargs={'pk': self.spending_account.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete Account')
        self.assertContains(response, self.spending_account.name)
    
    def test_account_delete_post(self):
        """Test POST request to delete account"""
        account_pk = self.spending_account.pk
        url = reverse('budget_allocation:account_delete', kwargs={'pk': account_pk})
        
        response = self.client.post(url)
        
        # Should redirect after successful deletion
        self.assertEqual(response.status_code, 302)
        
        # Check account was deleted
        with self.assertRaises(Account.DoesNotExist):
            Account.objects.get(pk=account_pk)


class TransactionViewTests(BudgetAllocationViewTestCase):
    """Test transaction management views"""
    
    def test_transaction_create_get(self):
        """Test GET request to transaction create view"""
        url = reverse('budget_allocation:transaction_create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Transaction')
        self.assertContains(response, 'Amount')
    
    def test_transaction_create_post_valid(self):
        """Test POST request to create transaction with valid data"""
        url = reverse('budget_allocation:transaction_create')
        data = {
            'account': self.spending_account.pk,
            'amount': '50.00',
            'transaction_type': 'expense',
            'description': 'Grocery shopping',
            'payee': 'Local Store',
            'transaction_date': date.today().strftime('%Y-%m-%d')
        }
        
        response = self.client.post(url, data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Check transaction was created
        transaction = Transaction.objects.get(description='Grocery shopping')
        self.assertEqual(transaction.account, self.spending_account)
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.transaction_type, 'expense')
    
    def test_transaction_list_view(self):
        """Test transaction list view"""
        # Create test transaction
        Transaction.objects.create(
            family=self.family,
            account=self.spending_account,
            week=self.week,
            transaction_date=date.today(),
            amount=Decimal('25.00'),
            transaction_type='expense',
            description='Test transaction'
        )
        
        url = reverse('budget_allocation:transaction_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Transactions')
        self.assertContains(response, 'Test transaction')


class AllocationViewTests(BudgetAllocationViewTestCase):
    """Test allocation management views"""
    
    def setUp(self):
        super().setUp()
        # Create additional account for valid allocations
        self.savings_account = Account.objects.create(
            family=self.family,
            name='Savings',
            account_type='spending'
        )
    
    def test_allocation_create_get(self):
        """Test GET request to allocation create view"""
        url = reverse('budget_allocation:allocation_create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Allocation')
        self.assertContains(response, 'From Account')
    
    def test_allocation_create_post_valid(self):
        """Test POST request to create allocation with valid data"""
        url = reverse('budget_allocation:allocation_create')
        data = {
            'from_account': self.income_account.pk,
            'to_account': self.spending_account.pk,
            'amount': '200.00',
            'notes': 'Weekly food allocation'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Check allocation was created
        allocation = Allocation.objects.get(notes='Weekly food allocation')
        self.assertEqual(allocation.from_account, self.income_account)
        self.assertEqual(allocation.to_account, self.spending_account)
        self.assertEqual(allocation.amount, Decimal('200.00'))
    
    def test_allocation_list_view(self):
        """Test allocation list view"""
        # Create test allocation
        Allocation.objects.create(
            week=self.week,
            from_account=self.income_account,
            to_account=self.spending_account,
            amount=Decimal('150.00'),
            notes='Test allocation'
        )
        
        url = reverse('budget_allocation:allocation_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Allocations')
        self.assertContains(response, 'Test allocation')


class BudgetTemplateViewTests(BudgetAllocationViewTestCase):
    """Test budget template management views"""
    
    def test_template_list_view(self):
        """Test budget template list view"""
        # Create test template
        BudgetTemplate.objects.create(
            family=self.family,
            account=self.spending_account,
            allocation_type='fixed',
            weekly_amount=Decimal('100.00'),
            priority=1
        )
        
        url = reverse('budget_allocation:template_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Budget Templates')
        self.assertContains(response, self.spending_account.name)
    
    def test_template_create_get(self):
        """Test GET request to template create view"""
        url = reverse('budget_allocation:template_create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Budget Template')
        self.assertContains(response, 'Allocation Type')
    
    def test_template_create_post_valid(self):
        """Test POST request to create template with valid data"""
        url = reverse('budget_allocation:template_create')
        data = {
            'account': self.spending_account.pk,
            'allocation_type': 'fixed',
            'weekly_amount': '150.00',
            'priority': 2,
            'is_essential': True
        }
        
        response = self.client.post(url, data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Check template was created
        template = BudgetTemplate.objects.get(account=self.spending_account)
        self.assertEqual(template.allocation_type, 'fixed')
        self.assertEqual(template.weekly_amount, Decimal('150.00'))
        self.assertEqual(template.priority, 2)


class LoanViewTests(BudgetAllocationViewTestCase):
    """Test loan management views"""
    
    def setUp(self):
        super().setUp()
        # Create additional account for loans
        self.savings_account = Account.objects.create(
            family=self.family,
            name='Savings',
            account_type='spending'
        )
    
    def test_loan_create_get(self):
        """Test GET request to loan create view"""
        url = reverse('budget_allocation:loan_create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Loan')
        self.assertContains(response, 'Lender Account')
    
    def test_loan_create_post_valid(self):
        """Test POST request to create loan with valid data"""
        url = reverse('budget_allocation:loan_create')
        data = {
            'lender_account': self.savings_account.pk,
            'borrower_account': self.spending_account.pk,
            'original_amount': '500.00',
            'weekly_interest_rate': '0.0200',
            'auto_repay': False
        }
        
        response = self.client.post(url, data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Check loan was created
        loan = AccountLoan.objects.get(
            lender_account=self.savings_account,
            borrower_account=self.spending_account
        )
        self.assertEqual(loan.original_amount, Decimal('500.00'))
        self.assertEqual(loan.weekly_interest_rate, Decimal('0.0200'))
    
    def test_loan_list_view(self):
        """Test loan list view"""
        # Create test loan
        AccountLoan.objects.create(
            family=self.family,
            lender_account=self.savings_account,
            borrower_account=self.spending_account,
            original_amount=Decimal('300.00'),
            remaining_amount=Decimal('300.00'),
            weekly_interest_rate=Decimal('0.0150'),
            loan_date=date.today()
        )
        
        url = reverse('budget_allocation:loan_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Active Loans')
        self.assertContains(response, '$300.00')


class APIViewTests(BudgetAllocationViewTestCase):
    """Test API endpoint views"""
    
    def test_account_balance_api(self):
        """Test account balance API endpoint"""
        # Add some transactions to create a balance
        Transaction.objects.create(
            family=self.family,
            account=self.spending_account,
            week=self.week,
            transaction_date=date.today(),
            amount=Decimal('100.00'),
            transaction_type='income',
            description='Test income'
        )
        
        url = reverse('budget_allocation:account_balance_api', kwargs={'account_id': self.spending_account.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertIn('balance', data)
        self.assertIn('account_name', data)
        self.assertEqual(data['account_name'], self.spending_account.name)
    
    def test_week_summary_api(self):
        """Test week summary API endpoint"""
        url = reverse('budget_allocation:week_summary_api')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertIn('week_start', data)
        self.assertIn('week_end', data)
        self.assertIn('total_allocated', data)
        self.assertIn('total_spent', data)
    
    def test_allocation_suggestions_api(self):
        """Test allocation suggestions API endpoint"""
        # Create budget templates for suggestions
        BudgetTemplate.objects.create(
            family=self.family,
            account=self.spending_account,
            allocation_type='fixed',
            weekly_amount=Decimal('200.00'),
            priority=1
        )
        
        url = reverse('budget_allocation:allocation_suggestions_api')
        data = {'available_amount': '1000.00'}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        result = response.json()
        self.assertIn('suggestions', result)
        self.assertIsInstance(result['suggestions'], list)


class PermissionTests(BudgetAllocationViewTestCase):
    """Test permission and security for budget allocation views"""
    
    def setUp(self):
        super().setUp()
        # Create another family and user for testing isolation
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        self.other_family = Family.objects.create(
            name='Other Family',
            created_by=self.user
        )
        
        self.other_member = FamilyMember.objects.create(
            user=self.other_user,
            family=self.other_family,
            role='parent'
        )
        
        self.other_account = Account.objects.create(
            family=self.other_family,
            name='Other Account',
            account_type='spending'
        )
    
    def test_family_data_isolation(self):
        """Test that users can only access their family's data"""
        # Login as other user
        self.client.logout()
        self.client.login(username='otheruser', password='testpass123')
        
        # Try to access original family's account
        url = reverse('budget_allocation:account_update', kwargs={'pk': self.spending_account.pk})
        response = self.client.get(url)
        
        # Should return 404 (not found) for other family's data
        self.assertEqual(response.status_code, 404)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access views"""
        self.client.logout()
        
        protected_urls = [
            reverse('budget_allocation:dashboard'),
            reverse('budget_allocation:account_list'),
            reverse('budget_allocation:transaction_create'),
            reverse('budget_allocation:allocation_list'),
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            # Should redirect to login
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response['Location'].find('/accounts/login/') != -1)
    
    def test_api_permission_required(self):
        """Test that API endpoints require authentication"""
        self.client.logout()
        
        api_urls = [
            reverse('budget_allocation:account_balance_api', kwargs={'account_id': self.spending_account.pk}),
            reverse('budget_allocation:week_summary_api'),
            reverse('budget_allocation:allocation_suggestions_api'),
        ]
        
        for url in api_urls:
            response = self.client.get(url)
            # Should return 302 redirect or 403 forbidden
            self.assertIn(response.status_code, [302, 403])


class PaginationTests(BudgetAllocationViewTestCase):
    """Test pagination functionality"""
    
    def test_transaction_list_pagination(self):
        """Test pagination on transaction list"""
        # Create many transactions to trigger pagination
        for i in range(25):
            Transaction.objects.create(
                family=self.family,
                account=self.spending_account,
                week=self.week,
                transaction_date=date.today(),
                amount=Decimal('10.00'),
                transaction_type='expense',
                description=f'Transaction {i+1}'
            )
        
        url = reverse('budget_allocation:transaction_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check pagination context
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['transaction_list']), 20)  # Default page size
    
    def test_account_list_filtering(self):
        """Test filtering functionality on account list"""
        # Create accounts of different types
        Account.objects.create(
            family=self.family,
            name='Extra Income',
            account_type='income'
        )
        
        url = reverse('budget_allocation:account_list')
        
        # Test filtering by account type
        response = self.client.get(url, {'account_type': 'income'})
        self.assertEqual(response.status_code, 200)
        
        # Should only show income accounts
        accounts = response.context['account_list']
        for account in accounts:
            self.assertEqual(account.account_type, 'income')
