# 🔥 Fixing Windows Firewall for Gmail API Access

## 🎯 Problem
You're getting this error:
```
[WinError 10060] A connection attempt failed because the connected party did not properly respond after a period of time, or established connection failed because connected host has failed to respond
```

This means Windows Firewall (or antivirus) is blocking Python from making HTTPS connections to Google's Gmail API servers.

## ✅ Solution Options

Choose the method that works best for you:

---

## 🛡️ **Method 1: Allow Python Through Windows Firewall (Recommended)**

### Step-by-Step Instructions:

1. **Open Windows Security**
   - Press `Win + I` to open Settings
   - Go to **Privacy & Security** → **Windows Security**
   - Click **Firewall & network protection**

2. **Allow an app through firewall**
   - Click **Allow an app through firewall**
   - Click **Change settings** button (requires admin)
   - Click **Allow another app...**

3. **Add Python executable**
   - Click **Browse...**
   - Navigate to: `C:\Users\Dmitry\AppData\Local\Programs\Python\Python310\python.exe`
   - Select `python.exe` and click **Open**
   - Click **Add**

4. **Configure network types**
   - Find `python.exe` in the list
   - Check BOTH boxes:
     - ✅ **Private** networks (like home, work)
     - ✅ **Public** networks (like WiFi hotspots)
   - Click **OK**

5. **Repeat for pythonw.exe** (optional but recommended)
   - Repeat steps 3-4 for: `C:\Users\Dmitry\AppData\Local\Programs\Python\Python310\pythonw.exe`

### PowerShell Command (Run as Administrator):

Alternatively, run this in PowerShell as Administrator:

```powershell
# Add firewall rule for Python
New-NetFirewallRule -DisplayName "Python 3.10" -Direction Outbound -Program "C:\Users\Dmitry\AppData\Local\Programs\Python\Python310\python.exe" -Action Allow

New-NetFirewallRule -DisplayName "Python 3.10 (windowed)" -Direction Outbound -Program "C:\Users\Dmitry\AppData\Local\Programs\Python\Python310\pythonw.exe" -Action Allow
```

---

## 🦠 **Method 2: Check Antivirus Software**

Many antivirus programs have their own firewalls that can block Python:

### Windows Defender:
1. Open **Windows Security**
2. Go to **Virus & threat protection**
3. Click **Manage settings** under "Virus & threat protection settings"
4. Scroll to **Exclusions**
5. Click **Add or remove exclusions**
6. Add folder: `C:\Users\Dmitry\AppData\Local\Programs\Python\Python310\`

### Other Antivirus (Norton, McAfee, Avast, etc.):
1. Open your antivirus software
2. Look for **Firewall** or **Network Protection** settings
3. Add Python to **allowed applications** or **exclusions**
4. Look for: `C:\Users\Dmitry\AppData\Local\Programs\Python\Python310\python.exe`

---

## 🌐 **Method 3: Test Network Connectivity**

Before and after fixing firewall, test if Python can reach Google:

### Test 1: Basic Connection
```powershell
python -c "import urllib.request; response = urllib.request.urlopen('https://www.googleapis.com', timeout=10); print(f'Success! Status: {response.status}')"
```

**Expected Result:**
- ✅ Success: `Success! Status: 200`
- ❌ Failure: `TimeoutError` or `URLError`

### Test 2: Gmail API Connection
```powershell
python -c "import urllib.request; response = urllib.request.urlopen('https://gmail.googleapis.com', timeout=10); print(f'Gmail API reachable! Status: {response.status}')"
```

### Test 3: OAuth API Connection
```powershell
python -c "import urllib.request; response = urllib.request.urlopen('https://oauth2.googleapis.com', timeout=10); print(f'OAuth API reachable! Status: {response.status}')"
```

---

## 🔌 **Method 4: Check Proxy Settings**

If you're behind a corporate proxy:

### Check Current Proxy:
```powershell
# Check Windows proxy settings
netsh winhttp show proxy
```

### Set Proxy (if needed):
```powershell
# Replace with your proxy details
$env:HTTP_PROXY = "http://proxy.company.com:8080"
$env:HTTPS_PROXY = "http://proxy.company.com:8080"
```

### Add to .env file:
```env
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
```

---

## 🚀 **Method 5: Try Different Network**

Quick test to confirm it's a firewall issue:

1. **Disconnect from current WiFi**
2. **Connect to mobile hotspot** (from your phone)
3. **Try syncing Gmail again**
4. **If it works** → Confirms firewall/network issue
5. **Return to original network** and apply Method 1 or 2

---

## 🧪 **Testing After Fix**

### Step 1: Test Connection
```powershell
python -c "import urllib.request; print('Testing Gmail API...'); response = urllib.request.urlopen('https://gmail.googleapis.com', timeout=10); print(f'✓ Success! Status: {response.status}')"
```

### Step 2: Test in Django Shell
```powershell
python manage.py shell
```

Then in the shell:
```python
from gmail_integration.services import GmailService
from gmail_integration.models import GmailAccount

# Get your account
account = GmailAccount.objects.first()
print(f"Testing with account: {account.email_address}")

# Test connection
service = GmailService(gmail_account=account)
try:
    service.authenticate()
    print("✓ Authentication successful!")
    
    # Try to get emails
    emails, next_page = service.get_emails(max_results=5)
    print(f"✓ Retrieved {len(emails)} emails successfully!")
except Exception as e:
    print(f"✗ Error: {e}")
```

### Step 3: Test in Browser
1. Go to: `http://127.0.0.1:8000/gmail/account/1/`
2. Click **"Sync Emails"**
3. Watch the progress indicator
4. Should see: "✓ Sync completed! X new emails added"

---

## 🎯 **Quick Fix Checklist**

Try these in order:

- [ ] **Test 1:** Run network connectivity test (see Method 3)
  - If fails → Firewall issue confirmed
  
- [ ] **Test 2:** Try mobile hotspot (see Method 5)
  - If works → Firewall blocking on main network
  
- [ ] **Fix 1:** Add Python to Windows Firewall (see Method 1)
  - Most common solution
  
- [ ] **Fix 2:** Check antivirus exclusions (see Method 2)
  - Often overlooked
  
- [ ] **Test 3:** Run connectivity tests again
  - Should now pass
  
- [ ] **Test 4:** Try Gmail sync in browser
  - Should complete successfully

---

## 🔍 **Troubleshooting**

### Still Getting Timeout After Firewall Fix?

**1. Restart Required:**
```powershell
# After adding firewall rules, restart Python/Django
# In terminal running Django server, press Ctrl+C
# Then restart:
make run
```

**2. Check Firewall Rules Were Added:**
```powershell
Get-NetFirewallRule -DisplayName "*Python*" | Format-Table DisplayName, Enabled, Direction, Action
```

**3. Temporarily Disable Firewall (TEST ONLY):**
```powershell
# As Administrator - TEST ONLY!
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False

# Try Gmail sync

# IMPORTANT: Re-enable after testing!
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True
```

**4. Check if Other Python Apps Work:**
```powershell
# Test with simple HTTP request
python -c "import requests; print(requests.get('https://www.google.com').status_code)"
```

If this fails → Python definitely blocked
If this works → Specific to Gmail API domains

**5. Check DNS Resolution:**
```powershell
# Test if domain resolves
nslookup gmail.googleapis.com
nslookup oauth2.googleapis.com
```

---

## 💡 **Why This Happens**

### Common Causes:
1. **Windows Firewall** - Default security policy blocks unknown apps
2. **Antivirus** - Overly aggressive protection
3. **Corporate Network** - IT policies blocking certain domains
4. **VPN** - Some VPNs block Google APIs
5. **Proxy** - Corporate proxy not configured for Python

### Why OAuth Worked But Sync Doesn't:
- **OAuth:** We extract user info from ID token (no network call needed) ✅
- **Email Sync:** Requires actual API calls to Gmail servers ❌

---

## ✅ **Success Indicators**

After fixing, you should see:

### In Terminal Logs:
```
INFO "POST /gmail/account/1/sync/ HTTP/1.1" 200 86
INFO Successfully retrieved 25 emails from Gmail
INFO Added 25 new emails to database
INFO Sync completed successfully
```

### In Browser:
```
✓ Sync completed! 25 new emails added, 0 updated
```

### In Sync Logs Page:
```
Status: Success ✓
Processed: 25
Added: 25
Errors: 0
Duration: 3.2 seconds
```

---

## 🎉 **Next Steps After Fix**

1. **Test sync** - Click "Sync Emails" button
2. **Verify emails** - Should see your Gmail messages
3. **Check sync logs** - Should show successful sync
4. **Commit changes** - All code is ready!
5. **Deploy to production** - Won't have firewall issues on servers

---

## 📞 **Still Having Issues?**

Run this comprehensive diagnostic and share the output:

```powershell
# Save to file
python -c "
import urllib.request
import socket
import ssl

print('=== Network Diagnostic ===')
print(f'Python Path: {__file__}')

# Test DNS
try:
    ip = socket.gethostbyname('gmail.googleapis.com')
    print(f'✓ DNS Resolution: gmail.googleapis.com → {ip}')
except Exception as e:
    print(f'✗ DNS Failed: {e}')

# Test SSL
try:
    context = ssl.create_default_context()
    print('✓ SSL Context Created')
except Exception as e:
    print(f'✗ SSL Failed: {e}')

# Test HTTPS Connection
try:
    response = urllib.request.urlopen('https://www.googleapis.com', timeout=10)
    print(f'✓ Google APIs Reachable: Status {response.status}')
except Exception as e:
    print(f'✗ Connection Failed: {e}')

print('=== End Diagnostic ===')
" > network-diagnostic.txt

# Display results
cat network-diagnostic.txt
```

---

**Most Common Solution:** Method 1 (Windows Firewall) fixes 90% of cases! 🎯

Try Method 1 first, then test. If it still doesn't work, try Method 2 (Antivirus), then Method 5 (Mobile Hotspot test).
