"""
Test script to display the exact redirect URI Django generates
Run this to see what redirect URI needs to be configured in Google Cloud Console
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from django.urls import reverse
from django.test import RequestFactory

print("=" * 80)
print("Gmail OAuth Redirect URI Diagnostic")
print("=" * 80)

# Create a fake request to simulate what Django does
factory = RequestFactory()

# Test different possible base URLs
test_urls = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost',
    'http://127.0.0.1',
]

print("\nPossible redirect URIs based on common development servers:")
print("-" * 80)

for base_url in test_urls:
    request = factory.get('/', SERVER_NAME=base_url.split('//')[1].split(':')[0])
    if ':' in base_url.split('//')[1]:
        request.META['SERVER_PORT'] = base_url.split(':')[1]
    else:
        request.META['SERVER_PORT'] = '80'
    
    # Get the OAuth callback path
    callback_path = reverse('gmail_integration:oauth_callback')
    full_uri = f"{base_url}{callback_path}"
    
    print(f"Base URL: {base_url:30} → Redirect URI: {full_uri}")

print("\n" + "=" * 80)
print("INSTRUCTIONS:")
print("=" * 80)
print("""
1. Check which server you're running Django on (python manage.py runserver)
2. Find the matching redirect URI above
3. Add THIS EXACT URI to Google Cloud Console:
   
   Google Cloud Console → APIs & Services → Credentials → 
   Your OAuth 2.0 Client ID → Authorized redirect URIs
   
4. IMPORTANT: The URI must match EXACTLY (including http/https, port number)

Common issues:
- Using http://localhost:8000 but Google has http://127.0.0.1:8000
- Missing port number (e.g., http://localhost vs http://localhost:8000)
- Having http but need https (or vice versa)
- Trailing slash mismatch

After adding the correct URI in Google Cloud Console, try connecting Gmail again.
""")
