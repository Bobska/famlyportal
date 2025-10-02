"""
Utility script to update existing emails with invoice detection

This script re-processes all existing EmailMessage records to add invoice detection.
Use this after implementing the invoice detection feature to update historical data.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from gmail_integration.models import EmailMessage, EmailAttachment
from gmail_integration.services import GmailService
from django.db.models import Q

def update_invoice_detection():
    """
    Update all existing emails with invoice detection
    """
    service = GmailService()
    
    # Get all emails that haven't been checked for invoices
    emails = EmailMessage.objects.filter(
        Q(has_invoice=False) & Q(invoice_confidence='none')
    )
    
    total = emails.count()
    print(f"Found {total} emails to process")
    print("=" * 80)
    
    updated_count = 0
    invoice_count = 0
    batch_size = 100
    
    for idx, email in enumerate(emails, 1):
        # Prepare email data for detection
        email_data = {
            'gmail_id': email.gmail_id,
            'subject': email.subject or '',
            'body_text': email.body_text or '',
            'body_html': email.body_html or '',
            'sender_email': email.sender_email or '',
            'attachments': []
        }
        
        # Get attachments
        if email.has_attachments:
            for attachment in email.attachments.all():
                email_data['attachments'].append({
                    'filename': attachment.filename,
                    'content_type': attachment.content_type,
                    'size_bytes': attachment.size_bytes,
                    'attachment_id': attachment.attachment_id
                })
        
        # Run invoice detection
        has_invoice, confidence, keywords = service._detect_invoice(email_data)
        
        # Update email
        email.has_invoice = has_invoice
        email.invoice_confidence = confidence
        email.invoice_keywords_found = keywords
        email.save(update_fields=['has_invoice', 'invoice_confidence', 'invoice_keywords_found'])
        
        updated_count += 1
        if has_invoice:
            invoice_count += 1
        
        # Progress update
        if idx % batch_size == 0:
            print(f"Processed {idx}/{total} emails ({invoice_count} invoices detected)")
    
    print("=" * 80)
    print(f"✅ Completed!")
    print(f"   Total emails processed: {updated_count}")
    print(f"   Invoices detected: {invoice_count}")
    print(f"   Detection rate: {(invoice_count/updated_count*100):.1f}%")
    print()
    print("Breakdown by confidence:")
    high = EmailMessage.objects.filter(invoice_confidence='high').count()
    medium = EmailMessage.objects.filter(invoice_confidence='medium').count()
    low = EmailMessage.objects.filter(invoice_confidence='low').count()
    print(f"   High confidence: {high}")
    print(f"   Medium confidence: {medium}")
    print(f"   Low confidence: {low}")

if __name__ == '__main__':
    import sys
    
    print("=" * 80)
    print("UPDATE EXISTING EMAILS WITH INVOICE DETECTION")
    print("=" * 80)
    print()
    
    response = input("This will update all existing emails. Continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        print("\nStarting update process...")
        print()
        update_invoice_detection()
    else:
        print("Operation cancelled.")
