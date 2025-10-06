from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, date
import re
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, Any
import os
from django.conf import settings

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from ai.models import InvoiceExtraction
from gmail_integration.models import EmailMessage


def _ensure_pdf_attachments_downloaded(email: EmailMessage) -> dict:
    """Ensure PDF attachments are present on disk by downloading on-demand via Gmail.

    Returns a dict with counts to include in raw_fields for transparency.
    """
    stats = {
        'pdf_attachments_count': 0,
        'pdf_downloaded_now': 0,
        'pdf_missing_after_download': 0,
    }
    try:
        from gmail_integration.models import EmailAttachment
        pdf_qs = EmailAttachment.objects.filter(email=email).filter(
            content_type__icontains='pdf'
        )
        # If content_type isn't set, fall back to filename check
        if not pdf_qs.exists():
            pdf_qs = EmailAttachment.objects.filter(email=email, filename__iendswith='.pdf')
        stats['pdf_attachments_count'] = pdf_qs.count()

        if stats['pdf_attachments_count'] == 0:
            return stats

        # Attempt download for any not-yet-on-disk file
        for att in pdf_qs:
            rel = att.file_path
            abs_path = rel if (rel and os.path.isabs(rel)) else (os.path.join(settings.MEDIA_ROOT, rel) if rel else None)
            needs_download = not rel or not abs_path or not os.path.exists(abs_path)
            if needs_download:
                try:
                    from gmail_integration.services import GmailService
                    svc = GmailService(gmail_account=email.gmail_account)
                    saved_rel = svc.download_attachment_to_storage(email=email, attachment=att)
                    if saved_rel:
                        stats['pdf_downloaded_now'] += 1
                    else:
                        stats['pdf_missing_after_download'] += 1
                except Exception:
                    stats['pdf_missing_after_download'] += 1
    except Exception:
        # On any unexpected failure, return what we have
        return stats
    return stats


def _extract_pdf_text_for_email(email: EmailMessage) -> tuple[str, dict]:
    """Best-effort PDF text extraction for the email's PDF attachments.
    Ensures PDFs are downloaded on-demand; returns (text, stats_dict).
    """
    text_chunks: list[str] = []
    # Ensure files are present
    dl_stats = _ensure_pdf_attachments_downloaded(email)

    try:
        from gmail_integration.models import EmailAttachment
        pdf_attachments = EmailAttachment.objects.filter(email=email).filter(
            content_type__icontains='pdf'
        )
        if not pdf_attachments.exists():
            pdf_attachments = EmailAttachment.objects.filter(email=email, filename__iendswith='.pdf')
    except Exception:
        pdf_attachments = []

    try:
        import PyPDF2  # type: ignore
    except Exception:
        # Dependency not available; skip but still return stats
        return '', {**dl_stats, 'pdf_text_chars': 0}

    for att in pdf_attachments:
        fp = att.file_path
        if not fp:
            continue
        abs_path = fp if os.path.isabs(fp) else os.path.join(settings.MEDIA_ROOT, fp)
        if not os.path.exists(abs_path):
            continue
        try:
            with open(abs_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    try:
                        t = page.extract_text() or ''
                    except Exception:
                        t = ''
                    if t:
                        text_chunks.append(t)
        except Exception:
            # Ignore per-file errors
            continue
    combined_text = '\n\n'.join(text_chunks)
    return combined_text, {**dl_stats, 'pdf_text_chars': len(combined_text)}


@dataclass
class ExtractionResult:
    provider_name: str | None
    invoice_number: str | None
    due_date: Optional[date]
    amount: Optional[Decimal]
    currency: str
    confidence: float
    raw_fields: Dict[str, Any]


def _parse_amount(text: str) -> Optional[Decimal]:
    """Parse monetary amounts with multiple pattern strategies."""
    # Strategy 1: Look for common invoice amount labels
    patterns = [
        r"(?i)(?:total|amount due|balance due|total amount|grand total|amount payable|payment amount)[:\s$£€]*([\d,]+\.\d{2})",
        r"(?i)(?:total|amount due|balance due)[:\s$£€]*([\d,]+)",
        # Strategy 2: Currency symbols followed by amounts
        r"(?:[$£€])\s*([\d,]+\.\d{2})",
        # Strategy 3: Standalone amounts on invoice-like lines (with decimal)
        r"(?:^|\n)\s*([\d,]{1,}\d+\.\d{2})\s*(?:$|\n)",
        # Strategy 4: Amount at end of line after colon
        r":?\s*([\d,]+\.\d{2})\s*$",
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        if matches:
            # Take the largest amount found (likely the total)
            try:
                amounts = [Decimal(m.replace(',', '')) for m in matches]
                return max(amounts)
            except (InvalidOperation, ValueError):
                continue
    return None


def _parse_due_date(text: str) -> Optional[date]:
    """Parse due dates with multiple format strategies."""
    patterns = [
        # ISO format: 2025-10-15
        (r"(?i)(?:due|payment due|pay by)[:\s-]*([0-9]{4}-[0-9]{2}-[0-9]{2})", "%Y-%m-%d"),
        # US format: Oct 15, 2025 or October 15, 2025
        (r"(?i)(?:due|payment due|pay by)(?:\sdate)?[:\s-]*([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})", "%b %d, %Y"),
        (r"(?i)(?:due|payment due|pay by)(?:\sdate)?[:\s-]*([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})", "%B %d, %Y"),
        # Slash format: 10/15/2025 or 15/10/2025
        (r"(?i)(?:due|payment due|pay by)[:\s-]*(\d{1,2}/\d{1,2}/\d{4})", "%m/%d/%Y"),
        (r"(?i)(?:due|payment due|pay by)[:\s-]*(\d{1,2}/\d{1,2}/\d{4})", "%d/%m/%Y"),
        # Dash format: 15-10-2025
        (r"(?i)(?:due|payment due|pay by)[:\s-]*(\d{1,2}-\d{1,2}-\d{4})", "%d-%m-%Y"),
        (r"(?i)(?:due|payment due|pay by)[:\s-]*(\d{1,2}-\d{1,2}-\d{4})", "%m-%d-%Y"),
        # Just date patterns without labels (fallback)
        (r"([0-9]{4}-[0-9]{2}-[0-9]{2})", "%Y-%m-%d"),
        (r"([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})", "%b %d, %Y"),
        (r"([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})", "%B %d, %Y"),
    ]
    
    for pattern, date_format in patterns:
        m = re.search(pattern, text)
        if m:
            val = m.group(1).replace(',', '').strip()
            try:
                return datetime.strptime(val, date_format).date()
            except ValueError:
                continue
    return None


def _parse_invoice_number(text: str) -> Optional[str]:
    """Parse invoice numbers with flexible patterns."""
    patterns = [
        r"(?i)invoice\s*(?:number|no\.?|#)?[:\s]*([A-Za-z0-9-]{3,20})",
        r"(?i)inv\.?\s*(?:no\.?|#)?[:\s]*([A-Za-z0-9-]{3,20})",
        r"(?i)(?:reference|ref)\s*(?:no\.?|#)?[:\s]*([A-Za-z0-9-]{3,20})",
        r"(?i)bill\s*(?:no\.?|#)?[:\s]*([A-Za-z0-9-]{3,20})",
        r"#([A-Za-z0-9-]{4,20})",  # Standalone # followed by alphanumeric
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            num = m.group(1).strip()
            # Filter out common false positives
            if num.lower() not in ['page', 'date', 'total', 'amount']:
                return num
    return None


def _parse_provider_name(text: str, sender_name: str, sender_email: str) -> str:
    """Extract provider name from text or fallback to sender info."""
    # Try to find company name in common patterns
    patterns = [
        r"(?i)(?:from|bill from|invoice from)[:\s]+([A-Za-z0-9\s&',.-]{3,50})",
        r"(?i)([A-Za-z0-9\s&',.-]{3,50})(?:\s+Invoice|\s+Bill|\s+Statement)",
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            name = m.group(1).strip()
            # Clean up common suffixes/prefixes
            name = re.sub(r'\s+(Invoice|Bill|Statement|LLC|Inc|Ltd|Limited).*$', '', name, flags=re.IGNORECASE)
            if len(name) > 2:
                return name
    
    # Fallback: use sender name or extract from email
    if sender_name:
        return sender_name
    
    # Extract company from email domain
    if sender_email and '@' in sender_email:
        domain = sender_email.split('@')[1]
        company = domain.split('.')[0]
        return company.replace('-', ' ').title()
    
    return ''


def analyze_email_for_invoice(email: EmailMessage, user=None) -> InvoiceExtraction:
    """Lightweight rule-based extraction to bootstrap structured data.
    Stores InvoiceExtraction and returns it.
    """
    body_text = email.body_text or ''
    subject = email.subject or ''
    # Append PDF text if available (and ensure PDFs are fetched on-demand)
    pdf_text, pdf_stats = _extract_pdf_text_for_email(email)
    combined = f"{subject}\n{body_text}\n\n{pdf_text}"

    amount = _parse_amount(combined)
    due_date = _parse_due_date(combined)
    invoice_number = _parse_invoice_number(combined)
    provider_name = _parse_provider_name(combined, email.sender_name or '', email.sender_email)

    currency = 'USD'

    # Heuristic confidence
    signals = sum([1 if amount else 0, 1 if due_date else 0, 1 if invoice_number else 0, 1 if provider_name else 0])
    confidence = 0.3 + 0.175 * signals  # 0.3 to 1.0 with 4 signals
    confidence = min(confidence, 1.0)

    raw_fields = {
        'subject': subject,
        'sender_email': email.sender_email,
        'body_sample': body_text[:500],
        'pdf_text_sample': pdf_text[:1000] if pdf_text else '',  # First 1000 chars for debugging
        # PDF extraction diagnostics
        'pdf_attachments_count': pdf_stats.get('pdf_attachments_count', 0),
        'pdf_downloaded_now': pdf_stats.get('pdf_downloaded_now', 0),
        'pdf_missing_after_download': pdf_stats.get('pdf_missing_after_download', 0),
        'pdf_chars': pdf_stats.get('pdf_text_chars', 0),
    }

    ct = ContentType.objects.get_for_model(EmailMessage)

    extraction = InvoiceExtraction.objects.create(
        content_type=ct,
        object_id=email.pk,
        provider_name=provider_name or '',
        invoice_number=invoice_number or '',
        due_date=due_date,
        amount=amount,
        currency=currency,
        confidence=confidence,
        raw_fields=raw_fields,
        status='complete',
        created_by=user,
    )
    return extraction
