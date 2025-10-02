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


def _extract_pdf_text_for_email(email: EmailMessage) -> str:
    """Best-effort PDF text extraction for the email's PDF attachments.
    Returns concatenated text or empty string on failure or if no PDFs.
    """
    text_chunks: list[str] = []
    try:
        from gmail_integration.models import EmailAttachment
        pdf_attachments = EmailAttachment.objects.filter(email=email, is_downloaded=True).filter(
            content_type__icontains='pdf'
        )
        if not pdf_attachments.exists():
            pdf_attachments = EmailAttachment.objects.filter(email=email, is_downloaded=True, filename__iendswith='.pdf')
    except Exception:
        pdf_attachments = []

    try:
        import PyPDF2  # type: ignore
    except Exception:
        # Dependency not available; skip
        return ''

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
    return '\n\n'.join(text_chunks)


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
    amt_match = re.search(r"(?i)(?:total|amount due|balance due)[:\s$]*([\d,]+\.?\d{0,2})", text)
    if not amt_match:
        return None
    try:
        return Decimal(amt_match.group(1).replace(',', ''))
    except InvalidOperation:
        return None


def _parse_due_date(text: str) -> Optional[date]:
    # Very loose patterns: Due: 2025-10-15 or Due Date: Oct 15, 2025
    patterns = [
        r"(?i)due[:\s-]*([0-9]{4}-[0-9]{2}-[0-9]{2})",
        r"(?i)due(?:\sdate)?[:\s-]*([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            val = m.group(1)
            for fmt in ("%Y-%m-%d", "%b %d, %Y", "%B %d, %Y"):
                try:
                    return datetime.strptime(val, fmt).date()
                except ValueError:
                    continue
    return None


def _parse_invoice_number(text: str) -> Optional[str]:
    m = re.search(r"(?i)(?:invoice|inv|ref)\s*#?:?\s*([A-Za-z0-9-]{4,})", text)
    return m.group(1) if m else None


def analyze_email_for_invoice(email: EmailMessage, user=None) -> InvoiceExtraction:
    """Lightweight rule-based extraction to bootstrap structured data.
    Stores InvoiceExtraction and returns it.
    """
    body_text = email.body_text or ''
    subject = email.subject or ''
    # Append PDF text if available
    pdf_text = _extract_pdf_text_for_email(email)
    combined = f"{subject}\n{body_text}\n\n{pdf_text}"

    amount = _parse_amount(combined)
    due_date = _parse_due_date(combined)
    invoice_number = _parse_invoice_number(combined)

    provider_name = email.sender_name or None
    currency = 'USD'

    # Heuristic confidence
    signals = sum([1 if amount else 0, 1 if due_date else 0, 1 if invoice_number else 0])
    confidence = 0.4 + 0.2 * signals  # 0.4 to 1.0
    confidence = min(confidence, 1.0)

    raw_fields = {
        'subject': subject,
        'sender_email': email.sender_email,
        'body_sample': body_text[:5000],
        'pdf_chars': len(pdf_text) if pdf_text else 0,
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
