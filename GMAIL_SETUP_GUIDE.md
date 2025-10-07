# Gmail Integration Setup Guide

## Complete Step-by-Step Setup Instructions

Follow these steps to set up Gmail OAuth2 integration for FamlyPortal.

---

## Step 1: Google Cloud Console Setup

### 1.1 Create Google Cloud Project

1. Go to **Google Cloud Console**: https://console.cloud.google.com/
2. Click on the project dropdown (top left, next to "Google Cloud")
3. Click **"New Project"**
4. Enter project name: `FamlyPortal` (or your preferred name)
5. Click **"Create"**
6. Wait for project creation to complete

### 1.2 Enable Gmail API

1. In the Google Cloud Console, select your project
2. Go to **"APIs & Services"** > **"Library"** (from the left sidebar)
3. Search for **"Gmail API"**
4. Click on **"Gmail API"** from the results
5. Click **"Enable"**
6. Wait for the API to be enabled

### 1.3 Configure OAuth Consent Screen

1. Go to **"APIs & Services"** > **"OAuth consent screen"**
2. Select **"External"** user type
3. Click **"Create"**
4. Fill in the required fields:
   - **App name**: `FamlyPortal`
   - **User support email**: Your email address
   - **Developer contact email**: Your email address
5. Click **"Save and Continue"**
6. On the **Scopes** page, click **"Add or Remove Scopes"**
7. Add these scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
8. Click **"Update"** and then **"Save and Continue"**
9. On **Test users** page, add your email address as a test user
10. Click **"Save and Continue"** and then **"Back to Dashboard"**

### 1.4 Create OAuth2 Credentials

1. Go to **"APIs & Services"** > **"Credentials"**
2. Click **"Create Credentials"** > **"OAuth 2.0 Client IDs"**
3. If prompted, configure the consent screen (already done above)
4. For **Application type**, select **"Web application"**
5. Enter **Name**: `FamlyPortal Web Client`
6. Under **Authorized redirect URIs**, click **"Add URI"** and add:
   ```
   http://localhost:8000/gmail/oauth/callback/
   ```
   
   For production, also add:
   ```
   https://yourdomain.com/gmail/oauth/callback/
   ```
7. Click **"Create"**
8. A dialog will appear with your credentials - **keep this open**

### 1.5 Download Client Secrets

1. From the credentials dialog, click **"Download JSON"**
2. Save the file to your computer
3. Rename the file to: `google_client_secrets.json`
4. Move this file to your FamlyPortal project root directory:
   ```
   C:\dev-projects\famlyportal\google_client_secrets.json
   ```
   (Same folder as `manage.py`)

---

## Step 2: Configure Django Settings

### 2.1 Add Environment Variables

You have two options for setting the encryption key:

#### Option A: Using .env file (Recommended for Development)

1. Create or edit `.env` file in your project root:
   ```
   C:\dev-projects\famlyportal\.env
   ```

2. Add these lines to your `.env` file:
   ```env
   # Gmail Integration Settings
   GOOGLE_OAUTH2_CLIENT_SECRETS_FILE=google_client_secrets.json
   GMAIL_ENCRYPTION_KEY=tXnLqbaAOojSmZYiYe4Iy93k5EB69fDtMD4EUSCA9Ns=
   ```

#### Option B: Using Windows Environment Variables (Production)

1. Open **System Properties** > **Environment Variables**
2. Add new system or user variables:
   - Variable: `GOOGLE_OAUTH2_CLIENT_SECRETS_FILE`
   - Value: `google_client_secrets.json`
   
   - Variable: `GMAIL_ENCRYPTION_KEY`
   - Value: `tXnLqbaAOojSmZYiYe4Iy93k5EB69fDtMD4EUSCA9Ns=`

### 2.2 Verify Settings

The settings are already configured in `famlyportal/settings.py`:

```python
# Gmail Integration Settings
GOOGLE_OAUTH2_CLIENT_SECRETS_FILE = config(
    'GOOGLE_OAUTH2_CLIENT_SECRETS_FILE',
    default='google_client_secrets.json'
)

GMAIL_ENCRYPTION_KEY = config(
    'GMAIL_ENCRYPTION_KEY',
    default='generate-a-real-key-in-production'
)
```

---

## Step 3: Database Setup

The migrations are already created and applied. If you need to re-apply them:

```bash
python manage.py migrate gmail_integration
```

---

## Step 4: Test the Integration

### 4.1 Start Development Server

```bash
python manage.py runserver
```

### 4.2 Access Gmail Integration

1. Open your browser and go to: http://localhost:8000/
2. Log in to your FamlyPortal account
3. You should see the **"Gmail Integration"** card on the dashboard
4. Click on the Gmail Integration card

### 4.3 Connect Your Gmail Account

1. Click **"Connect Gmail Account"** button
2. You'll be redirected to Google's OAuth consent screen
3. Select your Google account
4. Review the permissions:
   - Read your email messages and settings
   - See your personal info
5. Click **"Allow"**
6. You'll be redirected back to FamlyPortal
7. You should see a success message and your Gmail account listed

### 4.4 Sync Emails

1. From the Gmail account detail page, click **"Sync Emails"**
2. The sync will start processing
3. You can monitor the progress in the sync logs section
4. Once complete, you'll see your emails listed

---

## Step 5: Verify Setup

### 5.1 Check Gmail Account

Navigate to: http://localhost:8000/gmail/

You should see:
- Your connected Gmail account
- Account status (Active)
- Sync status
- Recent emails (if synced)

### 5.2 Check Admin Interface

1. Go to: http://localhost:8000/admin/
2. Log in as superuser
3. You should see:
   - **Gmail Accounts**
   - **Email Messages**
   - **Email Attachments**
   - **Sync Logs**

### 5.3 Test Email Search

1. From the Gmail account page, click **"View All Emails"**
2. Use the search box to search for emails by:
   - Subject
   - Sender
   - Content
3. Verify pagination works correctly

---

## Troubleshooting

### Issue: "No module named 'google'"

**Solution**: Install required packages:
```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install google-auth==2.26.2
pip install google-auth-oauthlib==1.2.0
pip install google-api-python-client==2.116.0
pip install cryptography==41.0.8
```

### Issue: "Client secrets not found"

**Solution**: 
- Verify `google_client_secrets.json` is in project root
- Check the filename is exactly `google_client_secrets.json`
- Verify the path in `.env` or environment variable

### Issue: "Invalid encryption key"

**Solution**:
- Generate a new key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- Update the key in your `.env` file or environment variables
- The key must be a valid Fernet key (base64 encoded)

### Issue: "Redirect URI mismatch"

**Solution**:
- Go to Google Cloud Console > Credentials
- Edit your OAuth 2.0 Client ID
- Verify the redirect URI exactly matches: `http://localhost:8000/gmail/oauth/callback/`
- Make sure there's no trailing slash mismatch
- After updating, wait a few minutes for changes to propagate

### Issue: "Access blocked: This app's request is invalid"

**Solution**:
- Complete the OAuth consent screen configuration
- Add your email as a test user in Google Cloud Console
- Ensure all required scopes are added
- The app is in "Testing" mode, which is fine for development

### Issue: Gmail API quota exceeded

**Solution**:
- Gmail API has daily quotas (1 billion quota units per day)
- Check your quota usage in Google Cloud Console
- Reduce sync frequency or email count
- Request quota increase if needed for production

---

## Security Best Practices

### For Development:
1. ✅ Use `.env` file for secrets (already in `.gitignore`)
2. ✅ Never commit `google_client_secrets.json` to git
3. ✅ Use the generated encryption key from this guide
4. ✅ Keep your Google Cloud project in "Testing" mode

### For Production:
1. 🔒 Use environment variables instead of `.env` file
2. 🔒 Generate a new encryption key (don't reuse development key)
3. 🔒 Use HTTPS for redirect URIs
4. 🔒 Configure proper domain restrictions in Google Cloud Console
5. 🔒 Publish your OAuth consent screen (after Google review)
6. 🔒 Monitor Gmail API usage and quotas
7. 🔒 Implement proper error handling and logging
8. 🔒 Regular security audits of stored credentials

---

## API Usage Examples

### Get User's Gmail Accounts

```python
from gmail_integration.models import GmailAccount

# Get all active accounts for a user
accounts = GmailAccount.objects.filter(user=request.user, is_active=True)
```

### Sync Emails Programmatically

```python
from gmail_integration.services import GmailService
from gmail_integration.models import GmailAccount

# Get account
account = GmailAccount.objects.get(user=request.user, email_address='user@gmail.com')

# Initialize service
service = GmailService(gmail_account=account)

# Sync emails
sync_log = service.sync_emails(
    query="from:important@example.com",
    max_emails=100
)

print(f"Synced {sync_log.emails_added} new emails")
```

### Search Emails

```python
from gmail_integration.models import EmailMessage
from django.db.models import Q

# Search emails
emails = EmailMessage.objects.filter(
    gmail_account__user=request.user
).filter(
    Q(subject__icontains='invoice') | 
    Q(sender_email__icontains='billing@')
)
```

### Access Email Content

```python
# Get email
email = EmailMessage.objects.get(id=email_id)

# Access data
print(f"Subject: {email.subject}")
print(f"From: {email.sender_email}")
print(f"Date: {email.sent_date}")
print(f"Body: {email.body_text}")

# Get attachments
attachments = email.attachments.all()
for attachment in attachments:
    print(f"File: {attachment.filename} ({attachment.get_size_display()})")
```

---

## Next Steps

### Immediate:
1. ✅ Complete Google Cloud Console setup
2. ✅ Configure environment variables
3. ✅ Test OAuth flow with your Gmail account
4. ✅ Sync your first batch of emails

### Optional Enhancements:
1. 📧 **Custom Email Processing**: Add logic to process specific email types
2. 🔔 **Email Notifications**: Alert users about important emails
3. 📊 **Email Analytics**: Track email patterns and statistics
4. 🔗 **Integration with Other Apps**: Link emails to invoices, payments, etc.
5. 🗂️ **Advanced Filtering**: Create custom filters and labels
6. 📅 **Scheduled Syncs**: Set up automatic email syncing with Celery

### Production Deployment:
1. Move encryption key to secure environment variables
2. Generate production OAuth credentials
3. Configure HTTPS redirect URI
4. Submit OAuth consent screen for verification
5. Set up monitoring and logging
6. Configure backup strategy for email data

---

## Support & Resources

### Documentation:
- **Gmail API**: https://developers.google.com/gmail/api
- **Google OAuth2**: https://developers.google.com/identity/protocols/oauth2
- **Django Settings**: Django project documentation

### Files to Reference:
- `gmail_integration/README.md` - Detailed app documentation
- `GMAIL_INTEGRATION_SUMMARY.md` - Implementation summary
- `gmail_integration/services.py` - Service layer code
- `gmail_integration/models.py` - Data models

### Getting Help:
- Check sync logs in Django admin
- Enable debug logging in Django settings
- Review Gmail API quotas in Google Cloud Console
- Check terminal output for errors

---

## Congratulations! 🎉

Your Gmail integration is now set up and ready to use. You can:
- ✅ Connect multiple Gmail accounts
- ✅ Sync emails securely
- ✅ Search and browse emails
- ✅ Track sync operations
- ✅ Manage everything through Django admin

**Your Encryption Key**: `tXnLqbaAOojSmZYiYe4Iy93k5EB69fDtMD4EUSCA9Ns=`

**Save this key securely!** You'll need it to decrypt your OAuth tokens.