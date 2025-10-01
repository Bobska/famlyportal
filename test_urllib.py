import urllib.request
import ssl

context = ssl._create_unverified_context()
req = urllib.request.Request(
    'https://gmail.googleapis.com/gmail/v1/users/me/messages',
    headers={'Authorization': 'Bearer test'}
)

try:
    response = urllib.request.urlopen(req, timeout=10, context=context)
    print(f"Success: {response.code}")
except urllib.error.HTTPError as e:
    print(f"HTTPError {e.code}: {e.reason} - This is expected (401 Unauthorized)")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
