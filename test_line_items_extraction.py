"""Test line items extraction from Active Explorers invoice."""
import sys
import os
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from ai.services.invoice_extraction_service import _parse_line_items
from decimal import Decimal

# Sample text from Active Explorers PDF
sample_text = """
Previous Balance $160.88

Item Description Type Ref Date Debit Credit
1 Under 3 Fee May 2025 27 Sep-03 Oct INV 7896993 Oct 2025 $331.50
2 Fee Discount of 75.00% INV 7896993 Oct 2025 -$248.63

Amount due (GST incl) $243.75
"""

print("Testing line items extraction on Active Explorers invoice:")
print("=" * 70)

line_items = _parse_line_items(sample_text)

print(f"\n✅ Extracted {len(line_items)} line items:\n")

total = Decimal('0')
for i, item in enumerate(line_items, 1):
    print(f"{i}. {item['type'].upper():20} | {item['description']:40} | ${item['amount']:>8.2f}")
    total += Decimal(str(item['amount']))

print("-" * 70)
print(f"{'CALCULATED TOTAL':60} | ${total:>8.2f}")
print(f"{'EXPECTED TOTAL':60} | ${243.75:>8.2f}")
print(f"\n{'✓ Match!' if abs(total - Decimal('243.75')) < Decimal('0.01') else '✗ Does not match'}")

# Expected breakdown:
print("\n" + "=" * 70)
print("Expected breakdown:")
print("  Previous Balance:  $160.88")
print("  Under 3 Fee:       $331.50")
print("  Discount (75%):   -$248.63")
print("  ----------------------------")
print("  Total:             $243.75")
print("\n💡 The AI learns these patterns from verified invoices.")
print("   After 20-30 samples, it can handle new providers automatically!")
