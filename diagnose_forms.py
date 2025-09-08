#!/usr/bin/env python

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django environment
sys.path.append('c:/dev-projects/famlyportal')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from accounts.models import Family, FamilyMember
from budget_allocation.models import Account

def diagnose_form_errors():
    """Diagnose specific form validation errors"""
    print("🔧 Diagnosing Budget Allocation Form Issues...")
    
    client = Client()
    User = get_user_model()
    
    # Create or get test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Create or get test family
    try:
        family = Family.objects.filter(name='Test Family').first()
        if not family:
            family = Family.objects.create(
                name='Test Family',
                created_by=user
            )
            created = True
        else:
            created = False
    except Exception as e:
        print(f"Family creation error: {e}")
        return
    
    # Create or get family member
    family_member, created = FamilyMember.objects.get_or_create(
        user=user,
        family=family,
        defaults={'role': 'admin'}
    )
    
    # Login
    login_success = client.login(username='testuser', password='testpass123')
    print(f"✅ Login successful: {login_success}")
    
    # Test transaction form submission
    print("\n🧪 Testing Transaction Form Submission...")
    
    # First create a test account
    account, created = Account.objects.get_or_create(
        name='Test Checking Account',
        family=family,
        defaults={
            'account_type': 'checking',
            'color': '#007bff',
            'sort_order': 1,
            'is_active': True
        }
    )
    
    print(f"✅ Test account: {account.name} (ID: {account.pk})")
    
    # Submit transaction form
    form_data = {
        'transaction_date': '2025-09-08',
        'account': account.pk,
        'description': 'Test Transaction',
        'amount': '100.00',
        'transaction_type': 'income',
        'payee': 'Test Payee',
        'reference': 'REF123'
    }
    
    print(f"Form data: {form_data}")
    
    response = client.post('/budget-allocation/transactions/create/', form_data, follow=True)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        # Form had errors
        if hasattr(response, 'context') and 'form' in response.context:
            form = response.context['form']
            print(f"❌ Form errors: {form.errors}")
            print(f"❌ Non-field errors: {form.non_field_errors()}")
            
            # Check individual field errors
            for field_name, field in form.fields.items():
                if field_name in form.errors:
                    print(f"   - {field_name}: {form.errors[field_name]}")
        else:
            print("❌ No form in response context")
    elif response.status_code == 302:
        print("✅ Transaction created successfully (redirect)")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    diagnose_form_errors()
