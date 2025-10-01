import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from django.conf import settings

print("=" * 60)
print("GMAIL INTEGRATION CONFIGURATION CHECK")
print("=" * 60)
print(f"GMAIL_ENCRYPTION_KEY: {settings.GMAIL_ENCRYPTION_KEY[:20]}...")
print(f"CLIENT_SECRETS_FILE: {settings.GOOGLE_OAUTH2_CLIENT_SECRETS_FILE}")
print(f"File exists: {os.path.exists(settings.GOOGLE_OAUTH2_CLIENT_SECRETS_FILE)}")
print(f"File path (absolute): {os.path.abspath(settings.GOOGLE_OAUTH2_CLIENT_SECRETS_FILE)}")
print("=" * 60)

# Try to import and test the service
try:
    from gmail_integration.services import GmailService
    print("✓ GmailService imported successfully")
    
    # Try to read the client secrets file
    import json
    with open(settings.GOOGLE_OAUTH2_CLIENT_SECRETS_FILE, 'r') as f:
        secrets = json.load(f)
        print("✓ Client secrets file loaded successfully")
        print(f"  Project ID: {secrets.get('web', {}).get('project_id', 'N/A')}")
        print(f"  Client ID: {secrets.get('web', {}).get('client_id', 'N/A')[:50]}...")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
