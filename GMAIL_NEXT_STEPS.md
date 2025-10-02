# 🔧 Gmail OAuth - Your Action Items

## ⚠️ Current Problem
You're getting "Failed to connect Gmail account. Please try again." but no Gmail accounts are being created.

## ✅ What We've Done
1. Enhanced error logging to show actual error messages
2. Created diagnostic scripts to check configuration
3. Verified OAuth callbacks are reaching Django
4. Confirmed no accounts exist in database (OAuth is failing)

## 🎯 What You Need to Do NOW

### 1️⃣ Fix Google Cloud Console Configuration (5 minutes)

Go to [Google Cloud Console](https://console.cloud.google.com) and:

#### A. Add Missing Redirect URI
1. Navigate to: **APIs & Services** → **Credentials**
2. Click your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", add:
   ```
   http://127.0.0.1:8000/gmail/oauth/callback/
   ```
4. Click **Save**
5. **Download** the updated `google_client_secrets.json`
6. Replace your current file with the downloaded one

#### B. Configure OAuth Consent Screen
1. Navigate to: **APIs & Services** → **OAuth consent screen**
2. Make sure:
   - Publishing status: **Testing**
   - Your Gmail email is in **Test users** list
3. Under **Scopes**, verify these exist:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`

#### C. Enable Required APIs
1. Navigate to: **APIs & Services** → **Library**
2. Search and enable:
   - **Gmail API**
   - **Google+ API**

### 2️⃣ Restart Django Server

```powershell
# Stop any running server (Ctrl+C)
# Then start fresh:
python manage.py runserver
```

### 3️⃣ Test OAuth Flow Again

1. Open browser to: `http://127.0.0.1:8000/gmail/`
2. Click "Connect Gmail Account"
3. Complete Google OAuth
4. **Note the exact error message** (it will now show the real error)

### 4️⃣ View Detailed Logs

Run this PowerShell script to see what happened:

```powershell
.\view_oauth_logs.ps1
```

Or manually check:

```powershell
Select-String -Path "logs\django.log" -Pattern "OAuth Callback Started" -Context 0,50 | Select-Object -Last 1
```

### 5️⃣ Report Back

Share with me:
1. ✉️ The **exact error message** shown on screen
2. 📋 The **log output** from the script above
3. ✅ Which Google Cloud Console settings you changed

## 🤔 What Error to Expect

Based on the issue, you'll likely see one of these:

### Error: "redirect_uri_mismatch"
**Cause:** The redirect URI in Google Console doesn't match what Django sends  
**Fix:** Add `http://127.0.0.1:8000/gmail/oauth/callback/` to Google Console (Step 1A above)

### Error: "No redirect URI found in session"
**Cause:** Session not persisting between requests  
**Fix:** Check Django settings for SESSION_ENGINE and SESSION_COOKIE_HTTPONLY

### Error: "access_denied"
**Cause:** Your email isn't added as a test user  
**Fix:** Add your email to test users in OAuth consent screen (Step 1B above)

### Error: "invalid_scope"
**Cause:** Required scopes not configured in OAuth consent screen  
**Fix:** Add the 3 scopes listed in Step 1B above

## 📁 Helpful Commands

```powershell
# Check if accounts exist
python test_gmail_accounts.py

# Check configuration
python test_gmail_config.py

# View logs
.\view_oauth_logs.ps1

# Django server
python manage.py runserver
```

## 🎉 Success Indicators

You'll know it worked when:
1. ✅ No error message appears after OAuth
2. ✅ You see: "Successfully connected Gmail account: your@email.com"
3. ✅ `python test_gmail_accounts.py` shows your account
4. ✅ You can see emails in the account detail page

## 💡 Pro Tip

If you're still getting errors after following steps 1-3, the enhanced logging will show us EXACTLY what's wrong. Just run `.\view_oauth_logs.ps1` and share the output!

---

**Next:** Complete steps 1-5 above, then let me know what you find! 🚀
