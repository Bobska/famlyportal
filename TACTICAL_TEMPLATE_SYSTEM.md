# Tactical Template System - Modular Architecture

## Overview
The tactical theme has been refactored into a fully modular, component-based architecture. This allows for easy reuse of UI elements across multiple pages and simplified maintenance.

## Folder Structure

```
bank/templates/tactical/
├── tactical_base.html              # Base template for all tactical pages
├── dashboard.html                  # Refactored dashboard (uses components)
├── components/                     # Reusable UI components
│   ├── header.html                # Tactical header with stats
│   ├── footer.html                # System status footer
│   ├── bottom_panels.html         # 3-panel bottom info section
│   ├── panel.html                 # Generic panel wrapper
│   ├── panel_financial_status.html # Financial status sidebar
│   ├── panel_quick_access.html    # Quick access sidebar
│   ├── transaction_list.html      # Reusable transaction list
│   ├── transaction_filters.html   # Filter controls
│   └── empty_state.html           # Empty state component
```

## Component Usage

### 1. Base Template (`tactical_base.html`)

All tactical pages should extend this base:

```django
{% extends 'tactical/tactical_base.html' %}

{% block title %}My Page Title{% endblock %}

{% block content %}
    <!-- Your page content here -->
{% endblock %}
```

**Features:**
- Automatic inclusion of tactical CSS and JS
- Header, footer, and bottom panels included by default
- URL data attributes for JavaScript
- Extensible blocks for customization

**Available Blocks:**
- `title` - Page title (appends "- Bank Dashboard")
- `extra_css` - Additional stylesheets
- `content` - Main page content (inside dashboard-grid)
- `bottom_panels` - Override bottom info panels
- `url_data` - Override URL data attributes
- `extra_js` - Additional JavaScript

### 2. Header Component

**File:** `components/header.html`

**Usage:**
```django
{% include 'tactical/components/header.html' %}
```

**Features:**
- Logo and subtitle (can be overridden with blocks)
- Current balance display
- Monthly net display
- System init button

**Customizable Blocks:**
- `header_title` - Change "FINANCIAL COMMAND"
- `header_subtitle` - Change subtitle text
- `header_action` - Replace system init button

**Required Context:**
- `current_balance`
- `monthly_balance`

### 3. Footer Component

**File:** `components/footer.html`

**Usage:**
```django
{% include 'tactical/components/footer.html' %}
```

**Features:**
- System status indicator
- Version number
- User information
- Auth level display

**Required Context:**
- `request.user` (automatic from Django)

### 4. Bottom Panels Component

**File:** `components/bottom_panels.html`

**Usage:**
```django
{% include 'tactical/components/bottom_panels.html' %}
```

**Features:**
- 3 equal-width panels
- System metrics panel
- Activity summary panel
- Financial status panel

**Optional Context:**
- `uptime_days`
- `today_transaction_count`
- `week_transaction_count`
- `last_activity`
- `category_count`
- `balance_trend`

### 5. Generic Panel Component

**File:** `components/panel.html`

**Usage:**
```django
{% include 'tactical/components/panel.html' with panel_title="My Panel" panel_class="custom-class" panel_id="myPanel" %}
```

**Parameters:**
- `panel_title` (required) - Title displayed in panel header
- `panel_class` (optional) - Additional CSS classes
- `panel_id` (optional) - HTML id attribute

**Features:**
- Tactical corners (bottom-left and bottom-right)
- Panel header with title
- Content wrapper

### 6. Financial Status Panel

**File:** `components/panel_financial_status.html`

**Usage:**
```django
{% include 'tactical/components/panel_financial_status.html' %}
```

**Features:**
- Large balance display
- Color-coded balance (green/red)
- Monthly income/expenses stats
- Transaction count
- Payee count
- Category count

**Required Context:**
- `current_balance`
- `monthly_income`
- `monthly_expenses`
- `transaction_count`
- `payee_count`
- `category_count`

### 7. Quick Access Panel

**File:** `components/panel_quick_access.html`

**Usage:**
```django
{% include 'tactical/components/panel_quick_access.html' %}
```

**Features:**
- Navigation buttons to key pages
- Optional top payees section

**Optional Context:**
- `top_payees` - QuerySet of payees with total_count

### 8. Transaction List Component

**File:** `components/transaction_list.html`

**Usage:**
```django
{% include 'tactical/components/transaction_list.html' with transactions=my_transactions show_category=True clickable=True %}
```

**Parameters:**
- `transactions` (required) - QuerySet or list of transactions
- `show_category` (optional, default: False) - Show category field
- `list_id` (optional) - HTML id for the container
- `clickable` (optional, default: False) - Enable selection onclick
- `list_full` (optional, default: False) - Add full-height class
- `empty_icon` (optional, default: "📭") - Icon for empty state
- `empty_title` (optional, default: "NO TRANSACTION DATA")
- `empty_text` (optional) - Text for empty state

**Features:**
- Transaction icon (▲ income, ▼ expense)
- Color-coded amounts
- Optional category display
- Optional click handlers for selection
- Automatic empty state

**Transaction Object Requirements:**
- `id` - Transaction ID
- `type` - "income" or "expense"
- `payee` - Payee name
- `date` - Transaction date
- `amount` - Transaction amount
- `category` (optional) - Category object with name

### 9. Transaction Filters Component

**File:** `components/transaction_filters.html`

**Usage:**
```django
{% include 'tactical/components/transaction_filters.html' %}
```

**Features:**
- Search input (by payee)
- Type filter (all/income/expense)
- Category filter
- Filter and Reset buttons
- Add transaction button

**Required Context:**
- `categories` - QuerySet of categories

**JavaScript Dependencies:**
- `applyTransactionFilters()`
- `clearTransactionFilters()`
- `showAddTransaction()`

### 10. Empty State Component

**File:** `components/empty_state.html`

**Usage:**
```django
{% include 'tactical/components/empty_state.html' with icon="📭" title="NO DATA" text="Add items to get started" %}
```

**Parameters:**
- `icon` (optional, default: "📭") - Emoji or icon
- `title` (optional, default: "NO DATA") - Title text
- `text` (optional) - Description text

## Creating New Tactical Pages

### Example: Simple Tactical Page

```django
{% extends 'tactical/tactical_base.html' %}

{% block title %}My Tactical Page{% endblock %}

{% block content %}
    <!-- Left sidebar -->
    <div class="tactical-panel">
        <div class="corner-bl"></div>
        <div class="corner-br"></div>
        
        <div class="panel-header">
            <div class="panel-title">Sidebar</div>
        </div>
        
        <div class="panel-content">
            <p>Sidebar content here</p>
        </div>
    </div>
    
    <!-- Main content -->
    <div class="tactical-panel">
        <div class="corner-bl"></div>
        <div class="corner-br"></div>
        
        <div class="panel-header">
            <div class="panel-title">Main Content</div>
        </div>
        
        <div class="panel-content">
            <p>Main content here</p>
        </div>
    </div>
{% endblock %}
```

### Example: Using Transaction Components

```django
{% extends 'tactical/tactical_base.html' %}

{% block title %}Transactions{% endblock %}

{% block content %}
    <!-- Filter panel -->
    {% include 'tactical/components/transaction_filters.html' %}
    
    <!-- Transaction list panel -->
    <div class="tactical-panel">
        <div class="corner-bl"></div>
        <div class="corner-br"></div>
        
        <div class="panel-header">
            <div class="panel-title">Transactions</div>
        </div>
        
        <div class="panel-content">
            {% include 'tactical/components/transaction_list.html' with transactions=all_transactions clickable=True show_category=True %}
        </div>
    </div>
{% endblock %}
```

## Customizing Components

### Override Header Text

```django
{% extends 'tactical/tactical_base.html' %}

{% block header_title %}PAYEE MANAGEMENT{% endblock %}
{% block header_subtitle %}TACTICAL OVERVIEW // PAYEE MODULE{% endblock %}
```

### Custom Bottom Panels

```django
{% block bottom_panels %}
    <div class="bottom-panels">
        <div class="bottom-panel">
            <div class="corner-bl"></div>
            <div class="corner-br"></div>
            <div class="info-panel-header">
                <span>CUSTOM PANEL</span>
            </div>
            <div class="info-panel-content">
                <!-- Custom content -->
            </div>
        </div>
    </div>
{% endblock %}
```

### Additional JavaScript

```django
{% block extra_js %}
    <script>
        // Your custom JavaScript
        console.log('Custom page loaded');
    </script>
{% endblock %}
```

## Benefits of Modular Architecture

### 1. Code Reusability
- Write once, use everywhere
- Consistent UI across all pages
- No code duplication

### 2. Easy Maintenance
- Update component once, applies everywhere
- Clear separation of concerns
- Easier to find and fix issues

### 3. Rapid Development
- Build new pages quickly using existing components
- Focus on business logic, not UI
- Consistent patterns reduce cognitive load

### 4. Flexibility
- Mix and match components as needed
- Easy to customize with parameters
- Override blocks for specific needs

### 5. Improved Testing
- Test components in isolation
- Easier to identify issues
- Smaller, focused templates

## Dashboard Comparison

### Before (dashboard_tactical.html)
- **Size:** 454 lines
- **Structure:** Monolithic template
- **Reusability:** None
- **Maintenance:** Difficult

### After (tactical/dashboard.html)
- **Size:** 130 lines
- **Structure:** Component-based
- **Reusability:** High (10 reusable components)
- **Maintenance:** Easy

**Reduction:** 71% smaller main template

## File Size Summary

| File | Lines | Purpose |
|------|-------|---------|
| `tactical_base.html` | 52 | Base template |
| `dashboard.html` | 130 | Dashboard page |
| `header.html` | 35 | Header component |
| `footer.html` | 24 | Footer component |
| `bottom_panels.html` | 84 | Bottom panels |
| `panel.html` | 25 | Generic panel |
| `panel_financial_status.html` | 50 | Financial status |
| `panel_quick_access.html` | 52 | Quick access |
| `transaction_list.html` | 52 | Transaction list |
| `transaction_filters.html` | 35 | Filters |
| `empty_state.html` | 17 | Empty state |
| **Total** | **556** | **Complete system** |

## Migration Guide

### Updating Existing Templates

1. **Change template path:**
   ```python
   # In views.py
   # Before:
   return render(request, 'bank/dashboard_tactical.html', context)
   
   # After:
   return render(request, 'tactical/dashboard.html', context)
   ```

2. **Ensure context variables:**
   - Check component documentation for required context
   - Add missing variables to view context

3. **Test functionality:**
   - Verify all components display correctly
   - Test JavaScript interactions
   - Check responsive behavior

### Creating New Pages

1. Create new template in `templates/tactical/`
2. Extend `tactical_base.html`
3. Use components from `components/`
4. Add custom content in `{% block content %}`
5. Update view to use new template

## Best Practices

### 1. Use Components Whenever Possible
Don't recreate UI elements that already exist as components.

### 2. Keep Components Generic
Make components flexible with parameters, not page-specific.

### 3. Document Required Context
Always document what context variables a component needs.

### 4. Follow Naming Conventions
- `panel_*` for sidebar/panel components
- `transaction_*` for transaction-related components
- Use descriptive names

### 5. Test With Different Data
Test components with:
- Empty data
- Minimal data
- Maximum data
- Edge cases

## Future Enhancements

### Planned Components
- Stats card component
- Action button group component
- Chart/graph components
- Form components (tactical styling)
- Modal/dialog components

### Planned Features
- Component library documentation
- Visual component gallery
- Interactive component playground
- Automated component tests

---

**Status:** Tactical template system complete  
**Version:** 2.0.0  
**Last Updated:** January 2025
