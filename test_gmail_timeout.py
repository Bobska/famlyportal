"""
Test Gmail API with various timeout settings
"""
import os
import sys
import django
import socket
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from gmail_integration.models import GmailAccount
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import httplib2

print("=" * 60)
print("Gmail API Timeout Test")
print("=" * 60)

# Get account
account = GmailAccount.objects.first()
if not account:
    print("❌ No Gmail account found")
    sys.exit(1)

print(f"✓ Testing account: {account.email_address}")
print(f"✓ Account created: {account.created_at}")

# Get credentials
creds_dict = account.credentials
if not creds_dict:
    print("❌ No credentials found")
    sys.exit(1)

print(f"✓ Has credentials: True")

# Create credentials object
credentials = Credentials(
    token=creds_dict.get('token'),
    refresh_token=creds_dict.get('refresh_token'),
    token_uri=creds_dict.get('token_uri'),
    client_id=creds_dict.get('client_id'),
    client_secret=creds_dict.get('client_secret'),
    scopes=creds_dict.get('scopes')
)

print(f"✓ Credentials object created")
print(f"✓ Token expired: {credentials.expired}")

# Test 1: Default socket timeout
print("\n" + "=" * 60)
print("Test 1: Default socket settings")
print("=" * 60)
try:
    print(f"Current default timeout: {socket.getdefaulttimeout()}")
    service = build('gmail', 'v1', credentials=credentials)
    print("✓ Service built successfully")
    
    results = service.users().messages().list(
        userId='me',
        maxResults=5
    ).execute()
    
    messages = results.get('messages', [])
    print(f"🎉 SUCCESS! Retrieved {len(messages)} messages!")
    
except Exception as e:
    print(f"❌ Failed: {type(e).__name__}: {e}")

# Test 2: Increased socket timeout
print("\n" + "=" * 60)
print("Test 2: With 60 second timeout")
print("=" * 60)
try:
    socket.setdefaulttimeout(60)
    print(f"Set default timeout to: {socket.getdefaulttimeout()} seconds")
    
    service = build('gmail', 'v1', credentials=credentials)
    print("✓ Service built successfully")
    
    results = service.users().messages().list(
        userId='me',
        maxResults=5
    ).execute()
    
    messages = results.get('messages', [])
    print(f"🎉 SUCCESS! Retrieved {len(messages)} messages!")
    
except Exception as e:
    print(f"❌ Failed: {type(e).__name__}: {e}")

# Test 3: Using httplib2 with custom timeout
print("\n" + "=" * 60)
print("Test 3: Using httplib2 with custom timeout")
print("=" * 60)
try:
    # Create http instance with timeout
    http = httplib2.Http(timeout=60)
    
    # Authorize the http instance
    http = credentials.authorize(http)
    
    service = build('gmail', 'v1', http=http)
    print("✓ Service built with custom http")
    
    results = service.users().messages().list(
        userId='me',
        maxResults=5
    ).execute()
    
    messages = results.get('messages', [])
    print(f"🎉 SUCCESS! Retrieved {len(messages)} messages!")
    
except Exception as e:
    print(f"❌ Failed: {type(e).__name__}: {e}")

# Test 4: Direct connection test
print("\n" + "=" * 60)
print("Test 4: Direct socket connection to Gmail API")
print("=" * 60)
try:
    import ssl
    
    # Create socket with timeout
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    
    # Wrap with SSL
    context = ssl.create_default_context()
    secure_sock = context.wrap_socket(sock, server_hostname='gmail.googleapis.com')
    
    # Connect
    print("Attempting connection to gmail.googleapis.com:443...")
    secure_sock.connect(('gmail.googleapis.com', 443))
    print("✓ SSL connection successful!")
    
    # Send HTTP request
    request = b"GET /gmail/v1/users/me/messages HTTP/1.1\r\nHost: gmail.googleapis.com\r\n\r\n"
    secure_sock.send(request)
    
    # Receive response
    response = secure_sock.recv(4096)
    print(f"✓ Received response: {len(response)} bytes")
    print(f"Response start: {response[:100]}")
    
    secure_sock.close()
    
except Exception as e:
    print(f"❌ Failed: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
