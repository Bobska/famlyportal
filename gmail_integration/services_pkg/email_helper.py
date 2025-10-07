"""
Email Helper Service
====================

Helper class to bridge EmailMessage model with AI classifier.
Converts Django model instances to dictionary format for ML processing.
"""
import re
from typing import Dict, Any
from gmail_integration.models import EmailMessage


class EmailHelper:
    """
    Helper class for preparing emails for AI classification.
    
    Converts EmailMessage model instances into the standardized
    dictionary format expected by the DaycareInvoiceClassifier.
    """
    
    @staticmethod
    def prepare_email_for_classification(email: EmailMessage) -> Dict[str, Any]:
        """
        Convert EmailMessage model instance to classifier-ready dictionary.
        
        Args:
            email: EmailMessage model instance
        
        Returns:
            Dictionary with keys:
                - subject: Email subject line
                - sender: Sender email address
                - body: Email body text (plain text preferred)
                - has_attachment: Boolean if email has attachments
                - has_pdf_attachment: Boolean if email has PDF attachments
                - date: Email sent date
        """
        return {
            'subject': email.subject or '',
            'sender': email.sender_email or '',
            'body': EmailHelper._get_email_body(email),
            'has_attachment': email.has_attachments,
            'has_pdf_attachment': EmailHelper._check_pdf_attachments(email),
            'date': email.sent_date
        }
    
    @staticmethod
    def _get_email_body(email: EmailMessage) -> str:
        """
        Extract email body text, preferring plain text over HTML.
        
        For classification purposes, plain text is more reliable.
        If only HTML is available, strips tags for text analysis.
        
        Args:
            email: EmailMessage model instance
        
        Returns:
            Email body as plain text string
        """
        # Prefer plain text body if available
        if email.body_text:
            return email.body_text
        
        # Fallback to HTML body (strip HTML tags)
        if email.body_html:
            return EmailHelper._strip_html_tags(email.body_html)
        
        # No body content
        return ''
    
    @staticmethod
    def _strip_html_tags(html_content: str) -> str:
        """
        Remove HTML tags from content for text analysis.
        
        Uses regex to strip HTML tags while preserving text content.
        Also handles HTML entities and excessive whitespace.
        
        Args:
            html_content: HTML string
        
        Returns:
            Plain text string
        """
        if not html_content:
            return ''
        
        # Remove HTML comments
        text = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        
        # Remove script and style tags with their content
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode common HTML entities
        html_entities = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&mdash;': '—',
            '&ndash;': '–'
        }
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        # Clean up excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    @staticmethod
    def _check_pdf_attachments(email: EmailMessage) -> bool:
        """
        Check if email has PDF attachments.
        
        Invoices are frequently sent as PDF attachments, so this is
        a strong indicator for classification.
        
        Args:
            email: EmailMessage model instance
        
        Returns:
            True if email has at least one PDF attachment
        """
        if not email.has_attachments:
            return False
        
        try:
            # Check if email has attachments related manager
            if hasattr(email, 'attachments'):
                # Query attachments for PDF content type
                pdf_attachments = email.attachments.filter(
                    content_type__icontains='pdf'
                ).exists()
                
                if pdf_attachments:
                    return True
                
                # Also check filename extensions as fallback
                pdf_by_filename = email.attachments.filter(
                    filename__iendswith='.pdf'
                ).exists()
                
                return pdf_by_filename
        except Exception as e:
            # Log error but don't break classification
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error checking PDF attachments for email {email.gmail_id}: {e}")
        
        return False
    
    @staticmethod
    def batch_prepare_emails(emails: list) -> list:
        """
        Prepare multiple emails for batch classification.
        
        Args:
            emails: List of EmailMessage instances
        
        Returns:
            List of email data dictionaries
        """
        return [
            EmailHelper.prepare_email_for_classification(email)
            for email in emails
        ]
