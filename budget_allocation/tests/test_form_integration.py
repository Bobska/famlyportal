from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from accounts.models import Family, FamilyMember
from budget_allocation.models import Account, Transaction
from budget_allocation.forms import TransactionForm, AccountForm, AllocationForm

User = get_user_model()

class BudgetAllocationFormTests(TestCase):
    """Test Budget Allocation forms for saving and validation issues"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.family = Family.objects.create(
            name='Test Family',
            created_by=self.user
        )
        
        FamilyMember.objects.create(
            user=self.user,
            family=self.family,
            role='admin'
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_account_form_saving(self):
        """Test if AccountForm saves correctly"""
        print("🧪 Testing AccountForm saving...")
        
        # Create a root account first
        root_account = Account.objects.create(
            name='Root Spending Account',
            account_type='spending',
            family=self.family,
            color='#000000'
        )
        
        form_data = {
            'name': 'Test Spending Account',
            'account_type': 'spending',
            'parent': root_account.pk,
            'color': '#007bff',
            'sort_order': 1,
            'is_active': True
        }
        
        form = AccountForm(data=form_data, family=self.family)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        account = form.save(commit=False)
        account.family = self.family
        account.save()
        
        self.assertEqual(account.name, 'Test Spending Account')
        self.assertEqual(account.family, self.family)
        print("✅ AccountForm saves correctly")
    
    def test_transaction_form_saving(self):
        """Test if TransactionForm saves correctly"""
        print("🧪 Testing TransactionForm saving...")
        
        # Create test account
        account = Account.objects.create(
            name='Test Account',
            account_type='spending',
            family=self.family,
            color='#28a745'
        )
        
        form_data = {
            'transaction_date': '2025-09-08',
            'account': account.pk,
            'description': 'Test Transaction',
            'amount': '100.00',
            'transaction_type': 'income',
            'payee': 'Test Payee',
            'reference': 'REF123'
        }
        
        form = TransactionForm(data=form_data, family=self.family)
        print(f"Form is_valid: {form.is_valid()}")
        
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
            print(f"Non-field errors: {form.non_field_errors()}")
            for field_name, field_errors in form.errors.items():
                print(f"  {field_name}: {field_errors}")
        
        self.assertTrue(form.is_valid(), f"Form should be valid. Errors: {form.errors}")
        
        transaction = form.save(commit=False)
        transaction.family = self.family
        
        # Auto-assign week if needed
        if transaction.week_id is None:
            from budget_allocation.models import WeeklyPeriod
            from datetime import date, timedelta
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            
            current_week, created = WeeklyPeriod.objects.get_or_create(
                start_date=week_start,
                end_date=week_end,
                family=self.family,
                defaults={'is_active': True}
            )
            transaction.week = current_week
        
        transaction.save()
        
        self.assertEqual(transaction.description, 'Test Transaction')
        self.assertEqual(transaction.family, self.family)
        print("✅ TransactionForm saves correctly")
    
    def test_transaction_view_submission(self):
        """Test transaction creation view"""
        print("🧪 Testing transaction creation view...")
        
        # Create test account
        account = Account.objects.create(
            name='Test Account',
            account_type='spending',
            family=self.family,
            color='#28a745'
        )
        
        form_data = {
            'transaction_date': '2025-09-08',
            'account': account.pk,
            'description': 'Test Transaction',
            'amount': '100.00',
            'transaction_type': 'income',
            'payee': 'Test Payee',
            'reference': 'REF123'
        }
        
        response = self.client.post(reverse('budget_allocation:transaction_create'), form_data)
        
        if response.status_code == 302:
            print("✅ Transaction view creates and redirects successfully")
        else:
            print(f"❌ Transaction view failed. Status: {response.status_code}")
            if hasattr(response, 'context') and 'form' in response.context:
                form = response.context['form']
                print(f"Form errors: {form.errors}")
        
        # Check if transaction was created
        transaction = Transaction.objects.filter(description='Test Transaction').first()
        if transaction:
            print(f"✅ Transaction created: {transaction.description}")
        else:
            print("❌ Transaction not found in database")
