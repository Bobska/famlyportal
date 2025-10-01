# 🔥 Quick Firewall Fix

## 🚀 Fastest Solution (30 seconds)

### Option 1: Automated Script (Recommended)

**Run this PowerShell command as Administrator:**

```powershell
# 1. Right-click PowerShell → "Run as Administrator"
# 2. Navigate to project:
cd C:\dev-projects\famlyportal

# 3. Run the fix script:
.\fix_firewall.ps1
```

The script will automatically:
- ✅ Detect your Python installation
- ✅ Add firewall rules for Gmail API access
- ✅ Test connectivity
- ✅ Show you next steps

---

### Option 2: Manual Command (If script fails)

**Run this in PowerShell as Administrator:**

```powershell
New-NetFirewallRule -DisplayName "Python Gmail Access" -Direction Outbound -Program "C:\Users\Dmitry\AppData\Local\Programs\Python\Python310\python.exe" -Action Allow -Profile Domain,Private,Public

Write-Host "✓ Firewall rule added! Restart Django server and try sync again."
```

---

### Option 3: GUI Method (If you prefer clicking)

1. Press **Win + R**, type `wf.msc`, press Enter
2. Click **Outbound Rules** in left panel
3. Click **New Rule...** in right panel
4. Select **Program** → Next
5. Click **Browse...** and select:
   ```
   C:\Users\Dmitry\AppData\Local\Programs\Python\Python310\python.exe
   ```
6. Click Next → Select **Allow the connection** → Next
7. Check ALL network types (Domain, Private, Public) → Next
8. Name: "Python Gmail API" → Finish

---

## ✅ After Applying Fix

1. **Restart Django server:**
   ```powershell
   # Press Ctrl+C in terminal running server
   make run
   ```

2. **Test in browser:**
   - Go to: http://127.0.0.1:8000/gmail/account/1/
   - Click "Sync Emails" button
   - Should see: "✓ Sync completed! X new emails added" 🎉

---

## 🧪 Quick Test

Run this to verify fix worked:

```powershell
python -c "import urllib.request; print('Testing...'); response = urllib.request.urlopen('https://gmail.googleapis.com', timeout=10); print(f'✓ Success! Gmail API reachable. Status: {response.status}')"
```

**Expected output:** `✓ Success! Gmail API reachable. Status: 200`

---

## 🆘 Still Not Working?

### Check Antivirus:
Many antivirus programs block Python even after firewall fix.

**Quick test:**
1. Temporarily disable antivirus
2. Try Gmail sync again
3. If works → Add Python to antivirus exclusions
4. Re-enable antivirus

**Common antivirus locations:**
- Windows Defender → Virus & threat protection → Exclusions
- Norton → Settings → Firewall → Program Control
- McAfee → Firewall → Internet Connections for Programs
- Avast → Settings → General → Exceptions

### Try Mobile Hotspot:
1. Connect phone as mobile hotspot
2. Connect computer to hotspot
3. Try Gmail sync
4. If works → Confirms network/firewall issue on main network

---

## 📖 Need More Help?

See detailed guide: **`GMAIL_FIREWALL_FIX.md`**

Includes:
- Multiple fix methods
- Troubleshooting steps
- Network diagnostics
- Proxy configuration
- DNS testing

---

**TL;DR:** Run `.\fix_firewall.ps1` as Administrator, restart server, try sync! 🚀
