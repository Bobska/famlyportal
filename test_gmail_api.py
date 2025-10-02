"""
Test Gmail API connectivity
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from gmail_integration.models import GmailAccount
from gmail_integration.services import GmailService

print("=" * 80)
print("Gmail API Connectivity Test")
print("=" * 80)
print()

# Get the account
try:
    account = GmailAccount.objects.first()
    if not account:
        print("❌ No Gmail account found. Please connect an account first.")
        exit(1)
    
    print(f"✓ Found account: {account.email_address}")
    print(f"✓ Account created: {account.created_at}")
    print(f"✓ Has credentials: {bool(account.credentials)}")
    print()
    
    # Test authentication
    print("Testing authentication...")
    service = GmailService(gmail_account=account)
    
    try:
        authenticated = service.authenticate()
        print(f"✓ Authentication successful: {authenticated}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print()
        print("This might be normal - credentials may need refresh")
    
    print()
    
    # Test getting emails
    print("Testing Gmail API access (get_emails)...")
    print("This will attempt to fetch 5 emails from Gmail...")
    print()
    
    try:
        emails, next_page = service.get_emails(max_results=5)
        print(f"🎉 SUCCESS! Retrieved {len(emails)} emails!")
        print()
        
        if emails:
            print("Sample emails:")
            for i, email in enumerate(emails[:3], 1):
                subject = email.get('snippet', 'No subject')[:50]
                print(f"  {i}. {subject}...")
        
        print()
        print("=" * 80)
        print("✅ Gmail API is working! No firewall blocking detected!")
        print("=" * 80)
        print()
        print("You can now sync emails in the browser:")
        print("  http://127.0.0.1:8000/gmail/account/1/")
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Failed to get emails: {error_msg}")
        print()
        
        if "10060" in error_msg or "timed out" in error_msg.lower():
            print("=" * 80)
            print("⚠️  FIREWALL IS BLOCKING GMAIL API ACCESS")
            print("=" * 80)
            print()
            print("To fix this, run as Administrator:")
            print()
            print("  Right-click 'fix_firewall_admin.bat' → Run as administrator")
            print()
            print("Or manually:")
            print("  1. Open Windows Security → Firewall")
            print("  2. Allow Python through firewall")
            print(f"  3. Path: C:\\Users\\Dmitry\\AppData\\Local\\Programs\\Python\\Python310\\python.exe")
        else:
            print("This might be a credentials issue, not firewall.")
            print("Try re-connecting your Gmail account.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
