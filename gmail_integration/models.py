"""
Models for Gmail Integration Django App
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings
import json
import base64

User = get_user_model()


class GmailAccount(models.Model):
    """
    Model to store Gmail account OAuth2 credentials and metadata
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gmail_accounts')
    email_address = models.EmailField(unique=True)
    display_name = models.CharField(max_length=200, blank=True)
    
    # OAuth2 credentials (encrypted)
    encrypted_credentials = models.TextField()
    
    # Account metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)  # Alias for admin consistency
    
    # Sync statistics
    total_emails = models.IntegerField(default=0)
    sync_enabled = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Gmail Account"
        verbose_name_plural = "Gmail Accounts"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email_address} ({self.user.username})"
    
    @property
    def credentials(self):
        """Decrypt and return OAuth2 credentials"""
        if not self.encrypted_credentials:
            return None
        
        try:
            # Get encryption key from settings
            key = settings.GMAIL_ENCRYPTION_KEY.encode()
            f = Fernet(key)
            
            # Decrypt credentials
            decrypted_data = f.decrypt(self.encrypted_credentials.encode())
            return json.loads(decrypted_data.decode())
        except Exception as e:
            # Log error but don't expose sensitive information
            print(f"Failed to decrypt credentials for {self.email_address}: {e}")
            return None
    
    @credentials.setter
    def credentials(self, creds_dict):
        """Encrypt and store OAuth2 credentials"""
        if not creds_dict:
            self.encrypted_credentials = ""
            return
        
        try:
            # Get encryption key from settings
            key = settings.GMAIL_ENCRYPTION_KEY.encode()
            f = Fernet(key)
            
            # Encrypt credentials
            creds_json = json.dumps(creds_dict)
            encrypted_data = f.encrypt(creds_json.encode())
            self.encrypted_credentials = encrypted_data.decode()
        except Exception as e:
            print(f"Failed to encrypt credentials for {self.email_address}: {e}")
            raise
    
    def update_sync_stats(self, email_count=None):
        """Update sync statistics"""
        self.last_sync = timezone.now()
        if email_count is not None:
            self.total_emails = email_count
        self.save(update_fields=['last_sync', 'total_emails'])


class EmailMessage(models.Model):
    """
    Model to store email metadata and content
    """
    gmail_account = models.ForeignKey(GmailAccount, on_delete=models.CASCADE, related_name='emails')
    
    # Gmail specific fields
    gmail_id = models.CharField(max_length=100, unique=True, db_index=True)
    thread_id = models.CharField(max_length=100, db_index=True)
    
    # Email metadata
    subject = models.TextField(blank=True)
    sender_email = models.EmailField()
    sender_name = models.CharField(max_length=200, blank=True)
    recipient_emails = models.JSONField(default=list)  # List of recipient emails
    cc_emails = models.JSONField(default=list)
    bcc_emails = models.JSONField(default=list)
    
    # Timestamps
    sent_date = models.DateTimeField(db_index=True)
    received_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Content
    body_text = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    
    # Email properties
    is_read = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    has_attachments = models.BooleanField(default=False)
    attachment_count = models.IntegerField(default=0)
    
    # Labels/Categories
    labels = models.JSONField(default=list)  # Gmail labels
    
    # Processing metadata
    is_processed = models.BooleanField(default=False)
    processing_notes = models.TextField(blank=True)
    
    # Invoice detection
    has_invoice = models.BooleanField(default=False, db_index=True)
    invoice_confidence = models.CharField(
        max_length=20, 
        choices=[
            ('high', 'High - Multiple indicators'),
            ('medium', 'Medium - Some indicators'),
            ('low', 'Low - Weak indicators'),
            ('none', 'None - No indicators')
        ],
        default='none'
    )
    invoice_keywords_found = models.JSONField(default=list)  # List of keywords that matched
    
    class Meta:
        verbose_name = "Email Message"
        verbose_name_plural = "Email Messages"
        ordering = ['-sent_date']
        indexes = [
            models.Index(fields=['gmail_account', 'sent_date']),
            models.Index(fields=['sender_email', 'sent_date']),
            models.Index(fields=['gmail_id']),
            models.Index(fields=['has_invoice', 'sent_date']),
        ]
    
    def __str__(self):
        return f"{self.subject[:50]}... from {self.sender_email}"
    
    @property
    def recipient_list(self):
        """Get formatted list of all recipients"""
        recipients = []
        recipients.extend(self.recipient_emails)
        if self.cc_emails:
            recipients.extend([f"{email} (CC)" for email in self.cc_emails])
        if self.bcc_emails:
            recipients.extend([f"{email} (BCC)" for email in self.bcc_emails])
        return recipients
    
    def get_snippet(self, length=150):
        """Get email body snippet"""
        content = self.body_text or self.body_html
        if not content:
            return ""
        
        # Clean HTML if necessary
        if self.body_text:
            snippet = self.body_text
        else:
            # Basic HTML stripping for snippet
            import re
            snippet = re.sub(r'<[^>]+>', '', self.body_html)
        
        return snippet[:length] + "..." if len(snippet) > length else snippet


class EmailAttachment(models.Model):
    """
    Model to store email attachment metadata
    """
    email = models.ForeignKey(EmailMessage, on_delete=models.CASCADE, related_name='attachments')
    
    # Attachment metadata
    filename = models.CharField(max_length=500)
    content_type = models.CharField(max_length=100)
    size_bytes = models.IntegerField()
    
    # Gmail specific
    attachment_id = models.CharField(max_length=100)
    
    # Storage (could be file path, cloud storage URL, etc.)
    file_path = models.CharField(max_length=1000, blank=True)
    is_downloaded = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Email Attachment"
        verbose_name_plural = "Email Attachments"
        ordering = ['filename']
    
    def __str__(self):
        return f"{self.filename} ({self.get_size_display()})"
    
    def get_size_display(self):
        """Human readable file size"""
        size = self.size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class SyncLog(models.Model):
    """
    Model to track synchronization history and errors
    """
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('success', 'Success'),
        ('error', 'Error'),
        ('partial', 'Partial Success'),
        ('cancelled', 'Cancelled'),
        ('interrupted', 'Interrupted'),
    ]
    
    gmail_account = models.ForeignKey(GmailAccount, on_delete=models.CASCADE, related_name='sync_logs')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Sync details
    emails_processed = models.IntegerField(default=0)
    emails_added = models.IntegerField(default=0)
    emails_updated = models.IntegerField(default=0)
    errors_count = models.IntegerField(default=0)
    
    # Logs
    message = models.TextField(blank=True)
    error_details = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Sync Log"
        verbose_name_plural = "Sync Logs"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.gmail_account.email_address} - {self.status} ({self.started_at})"
    
    def mark_completed(self, status, message="", error_details=""):
        """Mark sync as completed with status"""
        self.status = status
        self.completed_at = timezone.now()
        self.message = message
        self.error_details = error_details
        self.save()
    
    @property
    def duration(self):
        """Get sync duration"""
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        return None


class SyncHistoryEvent(models.Model):
    """
    Model to track individual events during a sync operation
    Provides a detailed timeline of sync progress
    """
    EVENT_TYPES = [
        ('start', 'Sync Started'),
        ('fetch', 'Fetching Batch'),
        ('process', 'Processing Emails'),
        ('progress', 'Progress Update'),
        ('complete', 'Batch Complete'),
        ('cancel', 'Sync Cancelled'),
        ('error', 'Error Occurred'),
        ('finish', 'Sync Finished'),
    ]
    
    sync_log = models.ForeignKey(SyncLog, on_delete=models.CASCADE, related_name='history_events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Additional context
    emails_processed = models.IntegerField(default=0)
    emails_added = models.IntegerField(default=0)
    emails_updated = models.IntegerField(default=0)
    batch_number = models.IntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Sync History Event"
        verbose_name_plural = "Sync History Events"
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sync_log.id} - {self.event_type}: {self.message[:50]}"
