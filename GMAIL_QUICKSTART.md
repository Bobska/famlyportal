# Gmail Integration - Quick Start

## ⚡ Quick Setup (5 Minutes)

### 1. Google Cloud Console Setup

1. **Go to**: https://console.cloud.google.com/
2. **Create Project**: "FamlyPortal"
3. **Enable Gmail API**: APIs & Services > Library > Search "Gmail API" > Enable
4. **Create OAuth Credentials**:
   - APIs & Services > Credentials > Create Credentials > OAuth 2.0 Client IDs
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/gmail/oauth/callback/`
5. **Download JSON**: Download the client secrets file
6. **Save as**: `google_client_secrets.json` in your project root

### 2. Configure OAuth Consent Screen (Required for First Time)

1. **Go to**: APIs & Services > OAuth consent screen
2. **User Type**: External
3. **Required Fields**:
   - App name: FamlyPortal
   - User support email: (your email)
   - Developer contact: (your email)
4. **Scopes**: Add these scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
5. **Test Users**: Add your Gmail address

### 3. Environment Variables (Already Done ✅)

Your `.env` file has been updated with:
```env
GOOGLE_OAUTH2_CLIENT_SECRETS_FILE=google_client_secrets.json
GMAIL_ENCRYPTION_KEY=tXnLqbaAOojSmZYiYe4Iy93k5EB69fDtMD4EUSCA9Ns=
```

### 4. Test It!

```bash
# Start server
python manage.py runserver

# Open browser
http://localhost:8000

# Click Gmail Integration card on dashboard
# Click "Connect Gmail Account"
# Authorize with Google
# Start syncing emails!
```

---

## 📋 Checklist

- [ ] Created Google Cloud project
- [ ] Enabled Gmail API
- [ ] Configured OAuth consent screen
- [ ] Created OAuth 2.0 credentials
- [ ] Downloaded `google_client_secrets.json`
- [ ] Placed file in project root (same folder as manage.py)
- [ ] Environment variables configured (already done ✅)
- [ ] Started development server
- [ ] Successfully connected Gmail account
- [ ] Synced first batch of emails

---

## 🎯 What You Get

After setup, you'll be able to:

✅ **Connect Gmail Accounts**: Multiple Gmail accounts per user
✅ **Secure OAuth2**: Industry-standard authentication
✅ **Email Syncing**: Automatic email fetch and storage
✅ **Search Emails**: Full-text search across all emails
✅ **Browse Emails**: Paginated email lists with filters
✅ **Track Syncs**: Complete audit trail of sync operations
✅ **Admin Interface**: Full Django admin for management
✅ **API Access**: RESTful APIs for custom integrations

---

## 🔧 Common Issues & Fixes

### "Client secrets not found"
**Fix**: Verify `google_client_secrets.json` is in project root folder

### "Redirect URI mismatch"
**Fix**: Ensure redirect URI in Google Console exactly matches:
`http://localhost:8000/gmail/oauth/callback/`

### "Access blocked"
**Fix**: Add your email as a test user in OAuth consent screen

### "Module not found"
**Fix**: Install dependencies:
```bash
pip install -r requirements.txt
```

---

## 📚 Full Documentation

For complete details, see:
- **Setup Guide**: `GMAIL_SETUP_GUIDE.md` (comprehensive step-by-step)
- **App Documentation**: `gmail_integration/README.md`
- **Implementation Summary**: `GMAIL_INTEGRATION_SUMMARY.md`

---

## 🎉 Ready to Go!

Your Gmail integration is configured and ready. Just:
1. Download your OAuth credentials from Google Cloud Console
2. Save as `google_client_secrets.json` in project root
3. Start the server and connect your Gmail!

**Encryption Key**: `tXnLqbaAOojSmZYiYe4Iy93k5EB69fDtMD4EUSCA9Ns=`
(Already saved in your .env file)