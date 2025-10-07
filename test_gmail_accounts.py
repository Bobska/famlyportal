"""
Quick test to check if Gmail account was actually created
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from gmail_integration.models import GmailAccount
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 80)
print("Gmail Account Check")
print("=" * 80)

# Get all Gmail accounts
accounts = GmailAccount.objects.all()

if not accounts:
    print("\n❌ No Gmail accounts found in database")
    print("\nThis means OAuth is failing silently.")
    print("Let's check users:")
    users = User.objects.all()
    for user in users:
        print(f"\n  User: {user.username} (ID: {user.id})")
else:
    print(f"\n✓ Found {accounts.count()} Gmail account(s):")
    for account in accounts:
        print(f"\n  Email: {account.email_address}")
        print(f"  User: {account.user.username}")
        print(f"  Active: {account.is_active}")
        print(f"  Created: {account.created_at}")
        print(f"  Has credentials: {bool(account.credentials)}")

print("\n" + "=" * 80)
