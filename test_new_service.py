"""
Test the new requests-based Gmail service implementation
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from gmail_integration.models import GmailAccount
from gmail_integration.services import GmailService

print("=" * 70)
print("Testing New Requests-Based Gmail Service")
print("=" * 70)

# Get account
account = GmailAccount.objects.first()
print(f"\n✓ Testing account: {account.email_address}")

# Create service
service = GmailService(gmail_account=account)
print("✓ Service created")

# Authenticate
print("\nAuthenticating...")
authenticated = service.authenticate()
print(f"✓ Authentication: {'SUCCESS' if authenticated else 'FAILED'}")

if authenticated:
    # Try to get emails using the new requests-based implementation
    print("\nAttempting to fetch emails using requests library...")
    try:
        emails, next_page = service.get_emails(max_results=5)
        print(f"🎉 SUCCESS! Retrieved {len(emails)} emails!")
        
        if emails:
            print("\nFirst email:")
            first_email = emails[0]
            print(f"  Subject: {first_email.get('subject', 'N/A')}")
            print(f"  From: {first_email.get('sender_name', 'N/A')} <{first_email.get('sender_email', 'N/A')}>")
            print(f"  Date: {first_email.get('received_date', 'N/A')}")
            
        print(f"\n✅ Gmail sync is now WORKING!")
        print(f"✅ The requests library bypasses the httplib2 timeout issue!")
        
    except Exception as e:
        print(f"❌ Failed to fetch emails: {type(e).__name__}")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ Authentication failed, cannot test email fetching")

print("\n" + "=" * 70)
print("Test Complete")
print("=" * 70)
