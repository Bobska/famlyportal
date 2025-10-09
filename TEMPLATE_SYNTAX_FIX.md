# Template Syntax Fix - Dashboard

**Date**: October 9, 2025  
**Issue**: TemplateSyntaxError - "Unused 'user' at end of if expression"  
**Status**: ✅ Fixed

---

## The Problem

The dashboard template was using incorrect Django template tag syntax for checking app permissions:

```django
❌ WRONG:
{% if has_app_permission user 'timesheet' %}

Error: "Unused 'user' at end of if expression"
```

## The Cause

`has_app_permission` is defined as a `@register.simple_tag(takes_context=True)` in `core/templatetags/family_tags.py`, which means:

1. It takes context automatically (includes `user` from request)
2. It cannot be used directly in `{% if %}` statements
3. It must assign its result to a variable using `as variable_name`

## The Solution

Changed all occurrences (12 total across 3 dashboard styles) to use correct syntax:

```django
✅ CORRECT:
{% has_app_permission 'timesheet' as can_timesheet %}
{% if can_timesheet %}
    <!-- Show timesheet card -->
{% endif %}
```

## Files Modified

- `templates/accounts/dashboard.html`
  - Quantum Glass section (4 app checks)
  - Terminal Matrix section (4 app checks)
  - Neon Synthwave section (4 app checks)

## Changes Made

### Quantum Glass Apps
```django
{% has_app_permission 'timesheet' as can_timesheet %}
{% has_app_permission 'daycare_invoices' as can_daycare %}
{% has_app_permission 'household_budget' as can_household_budget %}
{% has_app_permission 'budget_allocation' as can_budget_allocation %}
```

### Terminal Matrix Apps
```django
{% has_app_permission 'timesheet' as can_timesheet %}
{% has_app_permission 'daycare_invoices' as can_daycare %}
{% has_app_permission 'household_budget' as can_household_budget %}
{% has_app_permission 'budget_allocation' as can_budget_allocation %}
```

### Neon Synthwave Apps
```django
{% has_app_permission 'timesheet' as can_timesheet %}
{% has_app_permission 'daycare_invoices' as can_daycare %}
{% has_app_permission 'household_budget' as can_household_budget %}
{% has_app_permission 'budget_allocation' as can_budget_allocation %}
```

## How This Works

1. **Template Tag Execution**: `{% has_app_permission 'timesheet' as can_timesheet %}`
   - Calls the `has_app_permission()` function with context
   - Context automatically includes `request.user`
   - Returns `True` or `False`
   - Stores result in `can_timesheet` variable

2. **Conditional Check**: `{% if can_timesheet %}`
   - Checks the boolean variable
   - Shows/hides content based on permission

## Reference: Correct Template Tag Usage

From `core/templatetags/family_tags.py`:

```python
@register.simple_tag(takes_context=True)
def has_app_permission(context, app_name):
    """
    Check if the current user has permission to access a specific app.
    Usage: {% has_app_permission 'timesheet' as can_access_timesheet %}
    """
    request = context['request']
    user = request.user
    # ... permission logic ...
    return True/False
```

## Testing

✅ Dashboard loads without TemplateSyntaxError  
✅ All three styles render correctly  
✅ App cards shown/hidden based on user permissions  
✅ No JavaScript console errors  

---

## Lessons Learned

1. **Simple Tags**: Cannot be used directly in `{% if %}` conditions
2. **Must Use `as`**: Always assign result to variable first
3. **Context is Automatic**: `takes_context=True` means don't pass `user` manually
4. **Check Existing Templates**: Other templates (like `app_cards.html`) already use correct syntax

## Prevention

When using custom template tags:
1. Check the tag definition (`@register.simple_tag` vs `@register.filter`)
2. Read the docstring for correct usage example
3. Look at existing templates for reference
4. Simple tags require `as variable_name` syntax

---

**Status**: Fixed and tested ✅  
**Dashboard URL**: http://localhost:8000/accounts/dashboard/
