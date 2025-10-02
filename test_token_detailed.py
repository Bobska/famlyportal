"""Test Gmail API call and see detailed error"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from gmail_integration.models import GmailAccount
from google.auth.transport.requests import Request
import requests

account = GmailAccount.objects.first()
creds_dict = account.credentials

print("\n" + "="*60)
print("Testing Gmail API Request")
print("="*60)

# Build URL
url = 'https://gmail.googleapis.com/gmail/v1/users/me/messages'
params = {'maxResults': 5}

# Try with current token
print(f"\n1. Testing with current token...")
print(f"   Token starts with: {creds_dict['token'][:30]}...")

headers = {
    'Authorization': f"Bearer {creds_dict['token']}",
    'Accept': 'application/json'
}

response = requests.get(url, headers=headers, params=params, timeout=30)
print(f"   Status: {response.status_code}")

if response.status_code != 200:
    print(f"   Error: {response.text}")
    
    # Try refreshing token
    print(f"\n2. Refreshing token...")
    from google.oauth2.credentials import Credentials
    
    creds = Credentials(
        token=creds_dict['token'],
        refresh_token=creds_dict.get('refresh_token'),
        token_uri=creds_dict['token_uri'],
        client_id=creds_dict['client_id'],
        client_secret=creds_dict['client_secret'],
        scopes=creds_dict['scopes']
    )
    
    # Force refresh
    creds.refresh(Request())
    print(f"   ✓ Token refreshed")
    print(f"   New token starts with: {creds.token[:30]}...")
    
    # Try again with new token
    print(f"\n3. Testing with refreshed token...")
    headers = {
        'Authorization': f"Bearer {creds.token}",
        'Accept': 'application/json'
    }
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ SUCCESS! Got {len(data.get('messages', []))} messages")
        
        # Update token in database
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
        print(f"   ✓ Updated token in database")
    else:
        print(f"   ❌ Still failing: {response.text}")
else:
    data = response.json()
    print(f"   ✅ SUCCESS! Got {len(data.get('messages', []))} messages")

print("\n" + "="*60 + "\n")
