"""Test if IPv4 fix resolves Gmail API timeout"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from gmail_integration.models import GmailAccount
from gmail_integration.services import GmailService

print("\n" + "="*60)
print("Testing Gmail API with IPv4 Fix")
print("="*60)

account = GmailAccount.objects.first()
if not account:
    print("\n❌ No Gmail account found!")
    exit(1)

print(f"\n✓ Found account: {account.email_address}")
print(f"✓ Account created: {account.created_at}")
print(f"✓ Has credentials: {bool(account.credentials)}")

print("\n" + "-"*60)
print("Testing Gmail API with IPv4-only socket...")
print("-"*60)

try:
    service = GmailService(gmail_account=account)
    authenticated = service.authenticate()
    print(f"✓ Authentication successful: {authenticated}")
    
    if authenticated:
        print("\nFetching emails...")
        emails, next_page = service.get_emails(max_results=5)
        print(f"\n🎉 SUCCESS! Retrieved {len(emails)} emails!")
        print("✅ Gmail API is working with IPv4 fix!")
        
        if emails:
            print("\nFirst email:")
            print(f"  Subject: {emails[0].get('subject', 'No subject')}")
            print(f"  From: {emails[0].get('from', 'Unknown')}")
            print(f"  Date: {emails[0].get('date', 'Unknown')}")
    else:
        print("\n❌ Authentication failed")

except Exception as e:
    print(f"\n❌ Failed: {e}")
    print("\n⚠️ IPv4 fix may not have resolved the issue")
    import traceback
    traceback.print_exc()

print("\n" + "="*60 + "\n")
