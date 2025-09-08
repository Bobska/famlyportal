#!/usr/bin/env python

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

# Setup Django environment
sys.path.append('c:/dev-projects/famlyportal')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from accounts.models import Family, FamilyMember
from budget_allocation.models import Account

def test_budget_allocation_forms():
    """Test all Budget Allocation forms to identify issues"""
    print("🔍 Testing Budget Allocation App Forms...")
    
    # Create test client
    client = Client()
    User = get_user_model()
    
    # Create test user and family
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    family = Family.objects.create(
        name='Test Family',
        created_by=user
    )
    
    FamilyMember.objects.create(
        user=user,
        family=family,
        role='admin'
    )
    
    # Login
    client.login(username='testuser', password='testpass123')
    
    print("✅ Test user and family created")
    
    # Test 1: Account Creation Form
    print("\n🧪 Testing Account Creation Form...")
    try:
        response = client.get(reverse('budget_allocation:account_create'))
        if response.status_code == 200:
            print("✅ Account create form loads successfully")
            
            # Test form submission
            form_data = {
                'name': 'Test Savings Account',
                'account_type': 'savings',
                'color': '#007bff',
                'sort_order': 1,
                'is_active': True
            }
            
            response = client.post(reverse('budget_allocation:account_create'), form_data)
            if response.status_code == 302:  # Redirect after successful creation
                print("✅ Account creation successful")
                account = Account.objects.filter(name='Test Savings Account').first()
                if account:
                    print(f"✅ Account created: {account.name}")
                else:
                    print("❌ Account not found in database")
            else:
                print(f"❌ Account creation failed. Status: {response.status_code}")
                if hasattr(response, 'context') and 'form' in response.context:
                    form = response.context['form']
                    print(f"Form errors: {form.errors}")
        else:
            print(f"❌ Account create form failed to load. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Account creation test failed: {str(e)}")
    
    # Test 2: Transaction Creation Form  
    print("\n🧪 Testing Transaction Creation Form...")
    try:
        response = client.get(reverse('budget_allocation:transaction_create'))
        if response.status_code == 200:
            print("✅ Transaction create form loads successfully")
            
            # First create an account for the transaction
            account = Account.objects.filter(family=family).first()
            if not account:
                account = Account.objects.create(
                    name='Test Account',
                    account_type='checking',
                    family=family,
                    color='#28a745'
                )
            
            # Test form submission
            form_data = {
                'account': account.pk,
                'amount': '100.00',
                'transaction_type': 'income',
                'transaction_date': '2025-09-08',
                'description': 'Test Income Transaction'
            }
            
            response = client.post(reverse('budget_allocation:transaction_create'), form_data)
            if response.status_code == 302:
                print("✅ Transaction creation successful")
            else:
                print(f"❌ Transaction creation failed. Status: {response.status_code}")
                if hasattr(response, 'context') and 'form' in response.context:
                    form = response.context['form']
                    print(f"Form errors: {form.errors}")
        else:
            print(f"❌ Transaction create form failed to load. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Transaction creation test failed: {str(e)}")
    
    # Test 3: Allocation Creation Form
    print("\n🧪 Testing Allocation Creation Form...")
    try:
        response = client.get(reverse('budget_allocation:create_allocation'))
        if response.status_code == 200:
            print("✅ Allocation create form loads successfully")
            
            # Create two accounts for allocation
            from_account = Account.objects.create(
                name='From Account',
                account_type='checking',
                family=family,
                color='#dc3545'
            )
            to_account = Account.objects.create(
                name='To Account',
                account_type='savings',
                family=family,
                color='#28a745'
            )
            
            # Test form submission
            form_data = {
                'from_account': from_account.pk,
                'to_account': to_account.pk,
                'amount': '50.00',
                'notes': 'Test allocation'
            }
            
            response = client.post(reverse('budget_allocation:create_allocation'), form_data)
            if response.status_code == 302:
                print("✅ Allocation creation successful")
            else:
                print(f"❌ Allocation creation failed. Status: {response.status_code}")
                if hasattr(response, 'context') and 'form' in response.context:
                    form = response.context['form']
                    print(f"Form errors: {form.errors}")
        else:
            print(f"❌ Allocation create form failed to load. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Allocation creation test failed: {str(e)}")
    
    # Test 4: Budget Template Creation Form
    print("\n🧪 Testing Budget Template Creation Form...")
    try:
        response = client.get(reverse('budget_allocation:budget_template_create'))
        if response.status_code == 200:
            print("✅ Budget template create form loads successfully")
            
            account = Account.objects.filter(family=family).first()
            if not account:
                account = Account.objects.create(
                    name='Template Test Account',
                    account_type='savings',
                    family=family,
                    color='#ffc107'
                )
            
            # Test form submission
            form_data = {
                'account': account.pk,
                'allocation_type': 'fixed',
                'weekly_amount': '25.00',
                'priority': 1,
                'is_active': True,
                'notes': 'Test budget template'
            }
            
            response = client.post(reverse('budget_allocation:budget_template_create'), form_data)
            if response.status_code == 302:
                print("✅ Budget template creation successful")
            else:
                print(f"❌ Budget template creation failed. Status: {response.status_code}")
                if hasattr(response, 'context') and 'form' in response.context:
                    form = response.context['form']
                    print(f"Form errors: {form.errors}")
        else:
            print(f"❌ Budget template create form failed to load. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Budget template creation test failed: {str(e)}")
    
    print("\n🎯 Form Testing Complete!")
    print("=" * 50)

if __name__ == '__main__':
    test_budget_allocation_forms()
