"""
Gmail Integration Admin Interface
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import GmailAccount, EmailMessage, EmailAttachment, SyncLog


@admin.register(GmailAccount)
class GmailAccountAdmin(admin.ModelAdmin):
    """
    Admin interface for Gmail accounts
    """
    list_display = [
        'email_address',
        'user',
        'display_name',
        'is_active',
        'sync_enabled',
        'email_count',
        'last_sync_at',
        'updated_at'
    ]
    list_filter = [
        'is_active',
        'sync_enabled',
        'updated_at',
        'last_sync_at'
    ]
    search_fields = [
        'email_address',
        'display_name',
        'user__username',
        'user__email'
    ]
    readonly_fields = [
        'email_address',
        'updated_at',
        'email_count',
        'credentials_status'
    ]
    
    fieldsets = (
        ('Account Information', {
            'fields': (
                'user',
                'email_address',
                'display_name',
                'credentials_status'
            )
        }),
        ('Settings', {
            'fields': (
                'is_active',
                'sync_enabled'
            )
        }),
        ('Statistics', {
            'fields': (
                'email_count',
                'last_sync_at'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def email_count(self, obj):
        """Get count of emails for this account"""
        return obj.emails.count()
    email_count.short_description = 'Email Count'
    
    def credentials_status(self, obj):
        """Display credentials status"""
        if obj.credentials:
            return format_html(
                '<span style="color: green;">✓ Stored</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Missing</span>'
        )
    credentials_status.short_description = 'OAuth Credentials'


class EmailAttachmentInline(admin.TabularInline):
    """
    Inline admin for email attachments
    """
    model = EmailAttachment
    extra = 0
    readonly_fields = ['filename', 'content_type', 'size_bytes', 'attachment_id']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    """
    Admin interface for email messages
    """
    list_display = [
        'subject_truncated',
        'sender_email',
        'gmail_account',
        'sent_date',
        'is_read',
        'is_important',
        'has_attachments',
        'updated_at'
    ]
    list_filter = [
        'gmail_account',
        'is_read',
        'is_important',
        'has_attachments',
        'sent_date',
        'updated_at'
    ]
    search_fields = [
        'subject',
        'sender_email',
        'sender_name',
        'body_text',
        'gmail_id'
    ]
    readonly_fields = [
        'gmail_id',
        'thread_id',
        'labels',
        'attachment_count',
        'updated_at',
        'body_preview'
    ]
    
    fieldsets = (
        ('Email Information', {
            'fields': (
                'gmail_account',
                'gmail_id',
                'thread_id',
                'subject'
            )
        }),
        ('Sender/Recipients', {
            'fields': (
                'sender_email',
                'sender_name',
                'recipient_emails',
                'cc_emails',
                'bcc_emails'
            )
        }),
        ('Content', {
            'fields': (
                'body_preview',
                'body_text',
                'body_html'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'sent_date',
                'is_read',
                'is_important',
                'has_attachments',
                'attachment_count',
                'labels'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [EmailAttachmentInline]
    
    def subject_truncated(self, obj):
        """Display truncated subject"""
        if len(obj.subject) > 50:
            return f"{obj.subject[:47]}..."
        return obj.subject
    subject_truncated.short_description = 'Subject'
    
    def body_preview(self, obj):
        """Display body preview"""
        if obj.body_text:
            preview = obj.body_text[:200]
            if len(obj.body_text) > 200:
                preview += "..."
            return format_html('<pre>{}</pre>', preview)
        return "No text content"
    body_preview.short_description = 'Body Preview'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('gmail_account')


@admin.register(EmailAttachment)
class EmailAttachmentAdmin(admin.ModelAdmin):
    """
    Admin interface for email attachments
    """
    list_display = [
        'filename',
        'email_subject',
        'content_type',
        'size_display',
        'updated_at'
    ]
    list_filter = [
        'content_type',
        'updated_at'
    ]
    search_fields = [
        'filename',
        'email__subject',
        'email__sender_email'
    ]
    readonly_fields = [
        'email',
        'filename',
        'content_type',
        'size_bytes',
        'attachment_id',
        'updated_at'
    ]
    
    def email_subject(self, obj):
        """Display email subject"""
        return obj.email.subject[:50]
    email_subject.short_description = 'Email Subject'
    
    def size_display(self, obj):
        """Display file size in human readable format"""
        size = obj.size_bytes
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
    size_display.short_description = 'Size'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('email', 'email__gmail_account')


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    """
    Admin interface for sync logs
    """
    list_display = [
        'gmail_account',
        'status',
        'emails_processed',
        'emails_added',
        'emails_updated',
        'errors_count',
        'duration',
        'updated_at'
    ]
    list_filter = [
        'status',
        'gmail_account',
        'updated_at'
    ]
    search_fields = [
        'gmail_account__email_address',
        'message',
        'error_details'
    ]
    readonly_fields = [
        'gmail_account',
        'status',
        'message',
        'emails_processed',
        'emails_added',
        'emails_updated',
        'errors_count',
        'error_details',
        'completed_at',
        'duration'
    ]
    
    fieldsets = (
        ('Sync Information', {
            'fields': (
                'gmail_account',
                'status',
                'message'
            )
        }),
        ('Statistics', {
            'fields': (
                'emails_processed',
                'emails_added',
                'emails_updated',
                'errors_count'
            )
        }),
        ('Timing', {
            'fields': (
                'created_at',
                'completed_at',
                'duration'
            )
        }),
        ('Error Details', {
            'fields': (
                'error_details',
            ),
            'classes': ('collapse',)
        })
    )
    
    def duration(self, obj):
        """Calculate sync duration"""
        if obj.completed_at:
            delta = obj.completed_at - obj.created_at
            total_seconds = int(delta.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            if minutes > 0:
                return f"{minutes}m {seconds}s"
            return f"{seconds}s"
        return "In progress"
    duration.short_description = 'Duration'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('gmail_account')
