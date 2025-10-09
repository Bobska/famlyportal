"""
Custom template tags for Bank app.
"""
from django import template

register = template.Library()


@register.simple_tag
def get_all_transactions(income_entries, expense_entries):
    """
    Combine income and expense entries and sort by date (most recent first).
    
    Returns a list of dicts with 'type' and 'entry' keys for unified rendering.
    """
    all_transactions = []
    
    # Add income entries
    for entry in income_entries:
        all_transactions.append({
            'type': 'income',
            'entry': entry,
            'date': entry.date
        })
    
    # Add expense entries
    for entry in expense_entries:
        all_transactions.append({
            'type': 'expense',
            'entry': entry,
            'date': entry.date
        })
    
    # Sort by date, most recent first
    all_transactions.sort(key=lambda x: x['date'], reverse=True)
    
    return all_transactions
