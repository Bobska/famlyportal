# Gmail Integration Django App

## Overview

A reusable Django app that provides secure Gmail OAuth2 integration for reading emails. This app allows users to connect their Gmail accounts, sync emails, and provides a clean interface for email management within Django applications.

## Features

- **Secure OAuth2 Authentication**: Full Google OAuth2 flow with encrypted credential storage
- **Email Synchronization**: Fetch and store email metadata and content
- **Search and Filter**: Search emails by subject, sender, content
- **Attachment Management**: Track email attachments metadata
- **Sync Logging**: Complete audit trail of sync operations
- **Admin Interface**: Full Django admin integration for management
- **API Endpoints**: JSON APIs for AJAX integration
- **Reusable**: Designed to be dropped into any Django project

## Installation

### 1. Add to Django Project

1. Copy the `gmail_integration` app to your Django project
2. Add to `INSTALLED_APPS` in settings.py:

```python
INSTALLED_APPS = [
    # ... other apps
    'gmail_integration',
]
```

3. Add URL patterns to main `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... other patterns
    path('gmail/', include('gmail_integration.urls')),
]
```

### 2. Install Dependencies

Add to your `requirements.txt`:

```
google-auth==2.26.2
google-auth-oauthlib==1.2.0
google-api-python-client==2.116.0
cryptography==41.0.8
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure Settings

Add to your Django `settings.py`:

```python
# Gmail Integration Settings
GOOGLE_OAUTH2_CLIENT_SECRETS_FILE = config(
    'GOOGLE_OAUTH2_CLIENT_SECRETS_FILE',
    default='google_client_secrets.json'
)

# Gmail Integration Encryption Key (for storing OAuth tokens)
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
GMAIL_ENCRYPTION_KEY = config(
    'GMAIL_ENCRYPTION_KEY',
    default='generate-a-real-key-in-production'
)
```

### 4. Google OAuth2 Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth2 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - `http://localhost:8000/gmail/oauth/callback/` (development)
     - `https://yourdomain.com/gmail/oauth/callback/` (production)
5. Download the client secrets JSON file and save as `google_client_secrets.json` in your project root

### 5. Generate Encryption Key

Generate a secure encryption key for storing OAuth tokens:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add this key to your environment variables or settings.

### 6. Run Migrations

```bash
python manage.py makemigrations gmail_integration
python manage.py migrate
```

## Usage

### Basic Usage

1. **Connect Gmail Account**:
   - Navigate to `/gmail/` in your application
   - Click "Add Gmail Account"
   - Complete OAuth flow

2. **Sync Emails**:
   - Go to account detail page
   - Click "Sync Emails"
   - Monitor sync progress

3. **Browse Emails**:
   - View email list with search and pagination
   - Click on individual emails for details

### Programmatic Usage

```python
from gmail_integration.services import GmailService
from gmail_integration.models import GmailAccount

# Get authenticated service
gmail_account = GmailAccount.objects.get(user=request.user, is_active=True)
service = GmailService(gmail_account=gmail_account)

# Sync emails
sync_log = service.sync_emails(query="from:important@example.com", max_emails=100)

# Get emails
emails, next_page = service.get_emails(query="label:inbox", max_results=50)

# Get specific email
email_data = service.get_email_by_id("gmail_message_id")
```

### API Endpoints

- **GET `/gmail/api/accounts/`**: List user's Gmail accounts
- **GET `/gmail/api/account/{id}/search/?q=query`**: Search emails
- **POST `/gmail/account/{id}/sync/`**: Trigger email sync
- **GET `/gmail/sync/{sync_log_id}/status/`**: Check sync status

## Models

### GmailAccount
Stores Gmail account information and encrypted OAuth2 credentials.

### EmailMessage
Stores email metadata, content, and processing status.

### EmailAttachment
Stores email attachment metadata (filename, size, content type).

### SyncLog
Tracks synchronization operations and provides audit trail.

## Security Features

- **Encrypted Credentials**: OAuth2 tokens encrypted with Fernet symmetric encryption
- **User Isolation**: All data scoped to authenticated users
- **Secure Storage**: No plaintext credentials in database
- **Permission Checks**: All views require authentication

## Configuration Options

### Environment Variables

- `GOOGLE_OAUTH2_CLIENT_SECRETS_FILE`: Path to Google OAuth2 client secrets JSON
- `GMAIL_ENCRYPTION_KEY`: Fernet encryption key for credential storage

### Gmail API Scopes

The app requests these scopes:
- `https://www.googleapis.com/auth/gmail.readonly`: Read Gmail messages
- `https://www.googleapis.com/auth/userinfo.profile`: User profile info
- `https://www.googleapis.com/auth/userinfo.email`: User email address

## Admin Interface

Full Django admin integration:
- Manage Gmail accounts
- Browse emails and attachments
- Monitor sync logs
- View sync statistics

## Customization

### Email Processing

Override `EmailMessage.is_processed` and `processing_notes` for custom email processing:

```python
# Custom email processor
from gmail_integration.models import EmailMessage

def process_invoices():
    unprocessed = EmailMessage.objects.filter(
        is_processed=False,
        subject__icontains='invoice'
    )
    
    for email in unprocessed:
        # Process invoice email
        extract_invoice_data(email)
        email.is_processed = True
        email.processing_notes = "Invoice processed"
        email.save()
```

### Custom Views

Extend the provided views or create custom ones:

```python
from gmail_integration.views import EmailListView

class CustomEmailListView(EmailListView):
    template_name = 'custom/email_list.html'
    paginate_by = 25
```

## Troubleshooting

### Common Issues

1. **OAuth Callback Error**: Check redirect URI in Google Console matches exactly
2. **Token Expired**: Users need to re-authenticate when refresh tokens expire
3. **Sync Failures**: Check Gmail API quotas and limits
4. **Encryption Errors**: Ensure GMAIL_ENCRYPTION_KEY is properly set

### Logging

Enable logging for debugging:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'gmail_integration.log',
        },
    },
    'loggers': {
        'gmail_integration': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Performance Considerations

- **Pagination**: Email lists are paginated (50 emails per page)
- **Database Indexes**: Key fields are indexed for performance
- **Sync Limits**: Default max of 1000 emails per sync operation
- **Batch Processing**: Emails are processed in batches of 100

## Production Deployment

1. **Use HTTPS**: Gmail OAuth requires HTTPS in production
2. **Secure Keys**: Store encryption key securely (environment variables)
3. **Monitor Quotas**: Watch Gmail API usage quotas
4. **Backup Data**: Regular backups of email data
5. **Log Monitoring**: Monitor sync logs for failures

## API Rate Limits

Gmail API has quotas:
- 1 billion quota units per day
- 250 quota units per user per 100 seconds
- 1,000 requests per 100 seconds

Plan sync operations accordingly.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is part of the FamlyPortal Django application and follows the same licensing terms.

## Support

For issues and support:
1. Check the troubleshooting section
2. Review Django and Gmail API documentation
3. Check sync logs in admin interface
4. Enable debug logging for detailed error information