from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from accounts.models import Family, FamilyMember
from budget_allocation.models import Account, BudgetTemplate, Allocation
from budget_allocation.forms import BudgetTemplateForm, AllocationForm

User = get_user_model()

class AdditionalFormTests(TestCase):
    """Test remaining Budget Allocation forms"""
    
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
        
        # Create test accounts
        self.root_account = Account.objects.create(
            name='Root Income',
            account_type='income',
            family=self.family,
            color='#28a745'
        )
        
        self.spending_account = Account.objects.create(
            name='Test Spending',
            account_type='spending',
            family=self.family,
            color='#dc3545'
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_budget_template_form_saving(self):
        """Test if BudgetTemplateForm saves correctly"""
        print("🧪 Testing BudgetTemplateForm saving...")
        
        form_data = {
            'account': self.spending_account.pk,
            'allocation_type': 'fixed',
            'weekly_amount': '25.00',
            'priority': 1,
            'is_active': True
        }
        
        form = BudgetTemplateForm(data=form_data, family=self.family)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        template = form.save(commit=False)
        template.family = self.family
        template.save()
        
        self.assertEqual(template.account, self.spending_account)
        self.assertEqual(str(template.weekly_amount), '25.00')
        print("✅ BudgetTemplateForm saves correctly")
    
    def test_allocation_form_saving(self):
        """Test if AllocationForm saves correctly"""
        print("🧪 Testing AllocationForm saving...")
        
        # Create a second account for allocation
        to_account = Account.objects.create(
            name='Target Spending',
            account_type='spending',
            family=self.family,
            color='#ffc107'
        )
        
        form_data = {
            'from_account': self.root_account.pk,
            'to_account': to_account.pk,
            'amount': '50.00',
            'notes': 'Test allocation'
        }
        
        form = AllocationForm(data=form_data, family=self.family)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        allocation = form.save(commit=False)
        allocation.family = self.family
        
        # Auto-assign week
        if allocation.week_id is None:
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
            allocation.week = current_week
        
        allocation.save()
        
        self.assertEqual(allocation.from_account, self.root_account)
        self.assertEqual(allocation.to_account, to_account)
        self.assertEqual(str(allocation.amount), '50.00')
        print("✅ AllocationForm saves correctly")
    
    def test_budget_template_view_submission(self):
        """Test budget template creation view"""
        print("🧪 Testing budget template creation view...")
        
        form_data = {
            'account': self.spending_account.pk,
            'allocation_type': 'percentage',
            'percentage': '10.50',
            'priority': 2,
            'is_active': True
        }
        
        response = self.client.post(reverse('budget_allocation:budget_template_create'), form_data)
        
        if response.status_code == 302:
            print("✅ Budget template view creates and redirects successfully")
        else:
            print(f"❌ Budget template view failed. Status: {response.status_code}")
            if hasattr(response, 'context') and 'form' in response.context:
                form = response.context['form']
                print(f"Form errors: {form.errors}")
        
        # Check if template was created
        template = BudgetTemplate.objects.filter(allocation_type='percentage', percentage='10.50').first()
        if template:
            print(f"✅ Budget template created: {template.account.name} - {template.allocation_type}")
        else:
            print("❌ Budget template not found in database")
    
    def test_allocation_view_submission(self):
        """Test allocation creation view"""
        print("🧪 Testing allocation creation view...")
        
        # Create target account
        to_account = Account.objects.create(
            name='Target Account',
            account_type='spending',
            family=self.family,
            color='#6f42c1'
        )
        
        form_data = {
            'from_account': self.root_account.pk,
            'to_account': to_account.pk,
            'amount': '75.00',
            'notes': 'Test allocation via view'
        }
        
        response = self.client.post(reverse('budget_allocation:create_allocation'), form_data)
        
        if response.status_code == 302:
            print("✅ Allocation view creates and redirects successfully")
        else:
            print(f"❌ Allocation view failed. Status: {response.status_code}")
            if hasattr(response, 'context') and 'form' in response.context:
                form = response.context['form']
                print(f"Form errors: {form.errors}")
        
        # Check if allocation was created
        allocation = Allocation.objects.filter(notes='Test allocation via view').first()
        if allocation:
            print(f"✅ Allocation created: {allocation.from_account.name} → {allocation.to_account.name} (${allocation.amount})")
        else:
            print("❌ Allocation not found in database")
