"""Debug token refresh and credentials"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from gmail_integration.models import GmailAccount
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime

account = GmailAccount.objects.first()

print("\n" + "="*60)
print("Checking Credentials Status")
print("="*60)

creds_dict = account.credentials
print(f"\n✓ Account: {account.email_address}")
print(f"✓ Has refresh_token: {bool(creds_dict.get('refresh_token'))}")
print(f"✓ Current token starts with: {creds_dict.get('token', '')[:20]}...")

# Create credentials object
creds = Credentials(
    token=creds_dict['token'],
    refresh_token=creds_dict.get('refresh_token'),
    token_uri=creds_dict['token_uri'],
    client_id=creds_dict['client_id'],
    client_secret=creds_dict['client_secret'],
    scopes=creds_dict['scopes']
)

print(f"\nCredentials object created")
print(f"  - expired: {creds.expired}")
print(f"  - valid: {creds.valid}")
print(f"  - has refresh_token: {bool(creds.refresh_token)}")

if creds.expired:
    print("\n🔄 Token expired, refreshing...")
    try:
        creds.refresh(Request())
        print("✅ Token refreshed successfully!")
        print(f"  - New token starts with: {creds.token[:20]}...")
        
        # Update in database
        updated_creds = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        account.credentials = updated_creds
        account.save()
        print("✅ Credentials updated in database")
        
    except Exception as e:
        print(f"❌ Refresh failed: {e}")
else:
    print("\n✓ Token is still valid")

print("\n" + "="*60 + "\n")
