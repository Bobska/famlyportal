# Email Label Tracking - Prevent Double-Marking

## Overview
Added visual indicators and protection to prevent re-labeling emails that have already been manually labeled in the training data.

## Features Implemented

### 1. Visual Indicators for Labeled Emails

#### Color-Coded Rows
- **Green background** with left border: Emails labeled as "NOT INVOICE"
- **Orange background** with left border: Emails labeled as "INVOICE"
- Provides instant visual feedback about which emails have been labeled

#### Badge System
- **Prominent label badge** in subject column:
  - 🟨 `INVOICE` (yellow/warning badge with invoice icon)
  - 🟩 `NOT INVOICE` (green/success badge with X icon)
- **"Labeled" badge** in Info column with checkmark icon
- Hover tooltips show:
  - When labeled (e.g., "2 hours ago")
  - Who labeled it (e.g., "by admin")
  - Source (manual, auto_confirmed, etc.)

### 2. Checkbox Protection
- **Disabled checkboxes** for already-labeled emails
- Tooltip on hover: "Already labeled as [label_type]"
- Prevents accidental re-selection and re-labeling
- Only unlabeled emails can be selected

### 3. Enhanced Email Enrichment
The view now enriches each email with label information:
- Label type (daycare_invoice or not_invoice)
- Created timestamp
- Created by user
- Label source (manual, auto_confirmed, etc.)

## Implementation Details

### Backend Changes (ai/views.py)

#### Updated `manual_selection_view()`:
```python
# Enrich emails with their label information
enriched_emails = []
for email in page_obj:
    # Check if this email has been labeled and get its label
    email_samples = TrainingSample.objects.filter(
        content_type=email_content_type,
        object_id=email.id
    )
    
    label_info = None
    if email_samples.exists():
        latest_sample = email_samples.order_by('-created_at').first()
        label_info = {
            'label': latest_sample.label,
            'created_at': latest_sample.created_at,
            'created_by': latest_sample.created_by,
            'source': latest_sample.source,
            'is_invoice': latest_sample.label == 'daycare_invoice'
        }
    
    enriched_emails.append({
        'email': email,
        'label_info': label_info
    })
```

**Context Update**:
- Added `enriched_emails` to context (replaces direct `page_obj` usage in template)
- Contains email object + label information for each email

### Frontend Changes (ai/templates/ai/manual_selection.html)

#### New CSS Classes:
```css
.email-row.labeled {
    background-color: #f0f9f0;  /* Light green */
    border-left: 4px solid #28a745;  /* Green left border */
}

.email-row.labeled-invoice {
    background-color: #fff3e0;  /* Light orange */
    border-left: 4px solid #ff9800;  /* Orange left border */
}

.label-badge {
    font-size: 0.85em;
    font-weight: 600;
}
```

#### Updated Email Rows:
```django
{% for item in enriched_emails %}
<tr class="email-row {% if item.label_info %}{% if item.label_info.is_invoice %}labeled-invoice{% else %}labeled{% endif %}{% endif %}">
    <td onclick="event.stopPropagation()">
        {% if item.label_info %}
        <input type="checkbox" class="email-checkbox" 
               disabled title="Already labeled as {{ item.label_info.label }}">
        {% else %}
        <input type="checkbox" class="email-checkbox" name="email_ids" 
               value="{{ item.email.id }}" form="labelForm" 
               onchange="updateCount()">
        {% endif %}
    </td>
    <td>
        {% if item.label_info %}
        <span class="label-badge badge {% if item.label_info.is_invoice %}bg-warning text-dark{% else %}bg-success{% endif %} me-2" 
              title="Labeled {{ item.label_info.created_at|timesince }} ago{% if item.label_info.created_by %} by {{ item.label_info.created_by.username }}{% endif %}">
            <i class="fas {% if item.label_info.is_invoice %}fa-file-invoice{% else %}fa-times-circle{% endif %}"></i>
            {% if item.label_info.is_invoice %}INVOICE{% else %}NOT INVOICE{% endif %}
        </span>
        {% endif %}
        <!-- Email subject and link -->
    </td>
    <!-- Other columns -->
    <td>
        <!-- View button, attachments -->
        {% if item.label_info %}
        <span class="badge bg-light text-dark border" title="Source: {{ item.label_info.source }}">
            <i class="fas fa-check-circle text-success"></i> Labeled
        </span>
        {% endif %}
    </td>
</tr>
{% endfor %}
```

## User Experience Flow

### Before (Problem)
1. User labels email as "INVOICE"
2. Email remains in unlabeled list
3. User might accidentally label same email again
4. Creates duplicate training samples
5. No visual feedback about what's been labeled

### After (Solution)
1. User labels email as "INVOICE"
2. Email gets visual indicators:
   - 🟨 Orange background with left border
   - 🟨 `INVOICE` badge in subject
   - ✅ "Labeled" badge in info column
   - ⬜ Disabled checkbox
3. User can't accidentally re-label it
4. Clear visual confirmation of labeled status
5. Can toggle to "Labeled" view to review all labeled emails

## Filter Behavior

### "Unlabeled" View (Default)
- Shows only emails **without** training samples
- All checkboxes enabled
- Ready for labeling

### "Labeled" View
- Shows only emails **with** training samples
- All checkboxes disabled
- Visual indicators displayed
- Review-only mode

## Benefits

### 1. Prevents Data Duplication
- No duplicate training samples created
- More efficient training data

### 2. Visual Clarity
- Instant feedback on labeled status
- Color-coding for quick scanning
- Badge system for detailed information

### 3. User Protection
- Disabled checkboxes prevent accidents
- Clear tooltips explain status
- Can't waste time re-labeling

### 4. Audit Trail
- Shows who labeled each email
- Shows when it was labeled
- Shows labeling source (manual vs auto)

## Testing Checklist

- [x] Backend enriches emails with label info
- [x] Labeled emails show visual indicators
- [x] Checkboxes disabled for labeled emails
- [x] Tooltip shows "Already labeled as X"
- [x] Color coding: green for NOT INVOICE, orange for INVOICE
- [x] Badge system displays correctly
- [x] Labeled/Unlabeled filter toggle works
- [x] Pagination preserves enriched data
- [x] No duplicate training samples created

## Example Scenarios

### Scenario 1: Labeling New Emails
```
User on "Unlabeled" view
├─> Sees 100 unlabeled emails
├─> Selects 20 emails
├─> Marks as "NOT INVOICE"
└─> Result:
    ├─> 20 emails disappear from unlabeled view
    ├─> 20 emails appear in labeled view
    └─> All 20 show green background + badges
```

### Scenario 2: Reviewing Labeled Emails
```
User switches to "Labeled" view
├─> Sees all 250 labeled emails
├─> Green backgrounds: 200 NOT INVOICE
├─> Orange backgrounds: 50 INVOICE
├─> All checkboxes disabled
└─> Can review but not re-label
```

### Scenario 3: Trying to Re-Label
```
User tries to check labeled email
├─> Checkbox is grayed out (disabled)
├─> Tooltip: "Already labeled as daycare_invoice"
├─> Cannot select it
└─> Cannot accidentally duplicate
```

## Files Modified

1. **ai/views.py** (lines 396-425)
   - Added email enrichment logic
   - Queries TrainingSample for each email
   - Builds label_info dictionary
   - Passes enriched_emails to template

2. **ai/templates/ai/manual_selection.html**
   - Added CSS for labeled row styling
   - Updated checkbox logic (disabled if labeled)
   - Added badge system in subject column
   - Added "Labeled" badge in info column
   - Updated row classes for color coding
   - Changed loop to use enriched_emails

## Performance Considerations

### Database Queries
- One additional query per email to check training samples
- Mitigated by:
  - Only checking current page (25 emails max)
  - Using exists() for quick checks
  - Ordering to get latest sample only

### Optimization Opportunities (Future)
- Could use select_related/prefetch_related
- Could cache label info for frequent pages
- Could add database index on content_type + object_id

## Status
✅ **COMPLETE** - Visual indicators implemented, checkboxes protected, double-marking prevented.

---
**Implemented**: October 2, 2025
**Branch**: feature/email-classification
**Impact**: Prevents duplicate training samples, improves UX clarity
