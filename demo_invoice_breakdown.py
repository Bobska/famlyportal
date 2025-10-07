"""
Test to demonstrate the difference between Current Invoice Total and Amount Due
"""
import sys
import os
import django

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from ai.services.invoice_extraction_service import _parse_line_items
from decimal import Decimal

# Sample Active Explorers invoice text
sample_text = """
Previous Balance $160.88

Item Description Type Ref Date Debit Credit
1 Under 3 Fee May 2025 27 Sep-03 Oct INV 7896993 Oct 2025 $331.50
2 Fee Discount of 75.00% INV 7896993 Oct 2025 -$248.63

Amount due (GST incl) $243.75
"""

print("=" * 80)
print("INVOICE BREAKDOWN ANALYSIS")
print("=" * 80)
print()

line_items = _parse_line_items(sample_text)

# Calculate totals
previous_balance = Decimal('0')
current_charges = Decimal('0')
total_amount_due = Decimal('0')

print("📋 LINE ITEMS:")
print("-" * 80)
for i, item in enumerate(line_items, 1):
    amount = Decimal(str(item['amount']))
    print(f"{i}. {item['type'].upper():20} | ${amount:>9.2f} | {item['description'][:45]}")
    
    if item['type'] == 'previous_balance':
        previous_balance += amount
    else:
        current_charges += amount
    
    total_amount_due += amount

print("-" * 80)
print()

print("💰 FINANCIAL SUMMARY:")
print("-" * 80)
print(f"Previous Balance:           ${previous_balance:>9.2f}  (what you owed before)")
print(f"Current Invoice Total:      ${current_charges:>9.2f}  (new charges this period)")
print(f"                            {'─' * 30}")
print(f"Amount Due:                 ${total_amount_due:>9.2f}  (what you pay now)")
print("-" * 80)
print()

print("🎯 USE CASES:")
print("-" * 80)
print(f"• Budgeting:     Track ${current_charges:.2f} as this period's daycare cost")
print(f"• Payment:       Pay ${total_amount_due:.2f} to the provider")
print(f"• Reconciliation: Previous ${previous_balance:.2f} + Current ${current_charges:.2f} = Due ${total_amount_due:.2f}")
print("-" * 80)
print()

print("✨ CALCULATION VERIFICATION:")
print("-" * 80)
debit = Decimal('331.50')
discount = Decimal('-248.63')
print(f"  Debit (Under 3 Fee):        ${debit:>9.2f}")
print(f"  Discount (75% off):         ${discount:>9.2f}")
print(f"                              {'─' * 15}")
print(f"  Current Invoice Total:      ${debit + discount:>9.2f}")
print()
print(f"  Current Invoice Total:      ${debit + discount:>9.2f}")
print(f"  Previous Balance:           ${previous_balance:>9.2f}")
print(f"                              {'─' * 15}")
print(f"  Amount Due:                 ${debit + discount + previous_balance:>9.2f}")
print("-" * 80)
print()

print("💡 AI LEARNING:")
print("-" * 80)
print("The system stores all line items in the database. After you verify 20-30")
print("invoices, the AI learns patterns like:")
print("  • How different providers format fees vs discounts")
print("  • Where to find previous balances")
print("  • How to calculate the final 'Amount Due'")
print()
print("This means NEW providers work automatically - no hard-coding needed!")
print("=" * 80)
