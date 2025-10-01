import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from django.contrib.auth import get_user_model
from gmail_integration.services import GmailService
import traceback

User = get_user_model()

print("=" * 60)
print("GMAIL OAUTH TEST")
print("=" * 60)

# Get a test user
try:
    user = User.objects.first()
    if not user:
        print("✗ No users found in database. Create a user first.")
        exit(1)
    
    print(f"✓ Testing with user: {user.username}")
    
    # Test creating service
    service = GmailService(user=user)
    print("✓ GmailService created successfully")
    
    # Test getting authorization URL
    redirect_uri = "http://localhost:8000/gmail/oauth/callback/"
    print(f"\nTesting authorization URL generation...")
    print(f"  Redirect URI: {redirect_uri}")
    
    auth_url = service.get_authorization_url(redirect_uri)
    print(f"✓ Authorization URL generated successfully")
    print(f"  URL: {auth_url[:100]}...")
    
    print("\n" + "=" * 60)
    print("Configuration appears to be working!")
    print("=" * 60)
    print("\nIf you're still getting errors, the issue might be:")
    print("1. OAuth consent screen not configured in Google Cloud Console")
    print("2. Redirect URI mismatch")
    print("3. Missing scopes in OAuth consent screen")
    print("4. User not added as test user in Google Cloud Console")
    
except Exception as e:
    print(f"\n✗ ERROR FOUND: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    
print("=" * 60)
