"""
Custom template tags for Bank app.
"""
from django import template

register = template.Library()


@register.filter
def currency(value):
    """
    Format a number as currency with thousands separator.
    
    Usage: {{ amount|currency }}
    Examples:
        1000 -> $1,000
        1234567.89 -> $1,234,567.89
        -500 -> -$500
    """
    try:
        # Convert to float
        amount = float(value)
        
        # Handle negative numbers
        is_negative = amount < 0
        amount = abs(amount)
        
        # Format with thousands separator and 2 decimal places
        formatted = f"{amount:,.2f}"
        
        # Remove .00 if it's a whole number
        if formatted.endswith('.00'):
            formatted = formatted[:-3]
        
        # Add dollar sign and negative if needed
        if is_negative:
            return f"-${formatted}"
        return f"${formatted}"
    except (ValueError, TypeError):
        return value


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
