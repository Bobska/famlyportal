"""
Test script for invoice detection functionality
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from gmail_integration.services import GmailService

# Test data
test_emails = [
    {
        'gmail_id': 'test_001',
        'subject': 'Your Invoice #12345 for September',
        'body_text': 'Thank you for your business. Amount due: $150.00',
        'body_html': '',
        'sender_email': 'billing@example.com',
        'attachments': [
            {'filename': 'invoice_12345.pdf', 'content_type': 'application/pdf', 'size_bytes': 50000, 'attachment_id': 'att1'}
        ]
    },
    {
        'gmail_id': 'test_002',
        'subject': 'Thank you for your order',
        'body_text': 'Your order has been shipped. Tracking number: ABC123',
        'body_html': '',
        'sender_email': 'orders@shop.com',
        'attachments': []
    },
    {
        'gmail_id': 'test_003',
        'subject': 'Monthly Statement - Account 789',
        'body_text': 'Please find attached your monthly statement. Balance due: $500.00. Payment deadline: Oct 15.',
        'body_html': '',
        'sender_email': 'statements@bank.com',
        'attachments': [
            {'filename': 'statement_sept_2024.pdf', 'content_type': 'application/pdf', 'size_bytes': 75000, 'attachment_id': 'att2'}
        ]
    },
    {
        'gmail_id': 'test_004',
        'subject': 'Payment reminder',
        'body_text': 'This is a reminder that your invoice is overdue.',
        'body_html': '',
        'sender_email': 'noreply@vendor.com',
        'attachments': []
    }
]

# Test invoice detection
service = GmailService()

print("=" * 80)
print("TESTING INVOICE DETECTION")
print("=" * 80)

for email_data in test_emails:
    print(f"\n📧 Email: {email_data['subject']}")
    print(f"   From: {email_data['sender_email']}")
    print(f"   Attachments: {len(email_data.get('attachments', []))}")
    
    has_invoice, confidence, keywords = service._detect_invoice(email_data)
    
    print(f"   ✓ Has Invoice: {has_invoice}")
    print(f"   ✓ Confidence: {confidence}")
    print(f"   ✓ Keywords Found: {len(keywords)}")
    
    if keywords:
        print(f"   ✓ Detected Keywords:")
        for kw in keywords[:5]:  # Show first 5
            print(f"     - {kw}")
        if len(keywords) > 5:
            print(f"     ... and {len(keywords) - 5} more")
    
    print()

print("=" * 80)
print("✅ Invoice detection test completed!")
print("=" * 80)
