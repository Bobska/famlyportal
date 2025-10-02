"""
Advanced Gmail API diagnostic - checking what's different
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from gmail_integration.models import GmailAccount
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient import _auth
import google.auth.transport.requests
import requests
import socket

print("=" * 70)
print("ADVANCED GMAIL API DIAGNOSTICS")
print("=" * 70)

# Get account
account = GmailAccount.objects.first()
print(f"\n✓ Account: {account.email_address}")

# Create credentials
creds_dict = account.credentials
credentials = Credentials(
    token=creds_dict.get('token'),
    refresh_token=creds_dict.get('refresh_token'),
    token_uri=creds_dict.get('token_uri'),
    client_id=creds_dict.get('client_id'),
    client_secret=creds_dict.get('client_secret'),
    scopes=creds_dict.get('scopes')
)

print("=" * 70)
print("TEST 1: Using requests library directly")
print("=" * 70)

try:
    # Use requests library (what Google API client uses under the hood)
    headers = {
        'Authorization': f'Bearer {credentials.token}',
        'Accept': 'application/json'
    }
    
    print("Making request with requests library...")
    response = requests.get(
        'https://gmail.googleapis.com/gmail/v1/users/me/messages',
        headers=headers,
        params={'maxResults': 5},
        timeout=30
    )
    
    print(f"✓ Status Code: {response.status_code}")
    print(f"✓ Response: {response.text[:200]}")
    
    if response.status_code == 200:
        data = response.json()
        messages = data.get('messages', [])
        print(f"🎉 SUCCESS! Retrieved {len(messages)} messages using requests!")
    else:
        print(f"⚠️  HTTP {response.status_code}: {response.text[:200]}")
        
except requests.exceptions.Timeout as e:
    print(f"❌ Timeout with requests library: {e}")
except Exception as e:
    print(f"❌ Error with requests: {type(e).__name__}: {e}")

print("\n" + "=" * 70)
print("TEST 2: Using Google API client with modified http")
print("=" * 70)

try:
    import httplib2
    
    # Set very long timeout
    socket.setdefaulttimeout(120)
    
    # Build service with default settings
    print("Building Gmail service...")
    service = build('gmail', 'v1', credentials=credentials)
    
    # Check what http instance it's using
    print(f"✓ Service created")
    print(f"  Service type: {type(service)}")
    
    # Try to access the http instance
    if hasattr(service, '_http'):
        print(f"  HTTP type: {type(service._http)}")
        
    print("\nAttempting to list messages...")
    results = service.users().messages().list(
        userId='me',
        maxResults=5
    ).execute()
    
    messages = results.get('messages', [])
    print(f"🎉 SUCCESS with API client! Retrieved {len(messages)} messages!")
    
except Exception as e:
    print(f"❌ Failed: {type(e).__name__}")
    print(f"   Error: {e}")
    import traceback
    print(f"   Stack trace:")
    traceback.print_exc()

print("\n" + "=" * 70)
print("TEST 3: Check what transport Google API is using")
print("=" * 70)

try:
    import google_auth_httplib2
    print("✓ google_auth_httplib2 available")
except ImportError:
    print("✗ google_auth_httplib2 NOT installed")

try:
    import google.auth.transport.urllib3
    print("✓ urllib3 transport available")
except ImportError:
    print("✗ urllib3 transport NOT installed")

try:
    import google.auth.transport.requests as transport_requests
    print("✓ requests transport available")
    
    # Check if this uses a session
    request = transport_requests.Request()
    print(f"  Request type: {type(request)}")
    if hasattr(request, 'session'):
        print(f"  Has session: True")
        print(f"  Session type: {type(request.session)}")
        
except ImportError:
    print("✗ requests transport NOT installed")

print("\n" + "=" * 70)
print("DIAGNOSIS COMPLETE")
print("=" * 70)
