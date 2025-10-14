# Transaction List Progressive Responsive Layout

## Overview
Transaction list now properly squeezes, adapts, and stacks as screen width decreases. No overlapping, clean transitions.

## Progressive Layout Stages

### Stage 1: Full Width (>1150px)
```
┌────┬──────────────┬──────────────────────┬───────────────┬───────────┐
│ ▲  │ MON, 14 OCT  │ Amazon.com           │ SHOPPING      │  +$150.00 │
└────┴──────────────┴──────────────────────┴───────────────┴───────────┘
     90px           100-300px (flex)       110px (flex)    90px
     [Icon]         [Date]                 [Payee]         [Category]  [Amount]
```
**Behavior**: 
- All elements visible
- Category has full 110px width
- Payee flexible between 100-300px
- 8px gap between elements

### Stage 2: Squeezing (1000px - 1150px)
```
┌────┬─────────────┬──────────────────────────┬──────────┬───────────┐
│ ▲  │ MON, 14 OCT │ Amazon.com               │ SHOP     │  +$150.00 │
└────┴─────────────┴──────────────────────────┴──────────┴───────────┘
     90px          100-250px (flex)          80px        90px
     [Icon]        [Date]                    [Payee]     [Cat...]    [Amount]
```
**Behavior**:
- Category shrinks to 80px (flex: 0 1 80px)
- Category font size: 8px (from 9px)
- Payee max-width: 250px
- Gap: 6px
- **Category shows ellipsis** if text too long

### Stage 3: Category Hidden (800px - 1000px)
```
┌────┬─────────────┬────────────────────────────────────┬──────────┐
│ ▲  │ MON, 14 OCT │ Amazon.com - Long Store Name Here  │ +$150.00 │
└────┴─────────────┴────────────────────────────────────┴──────────┘
     80px          120px+ (flexible)                     80px
     [Icon]        [Date]                                [Payee]     [Amount]
```
**Behavior**:
- **Category removed** (display: none)
- Payee expands to fill space (flex: 1 1 auto)
- Payee no max-width restriction
- Date: 80px min-width
- Amount: 80px min-width
- Font sizes slightly reduced

### Stage 4: Stacked Layout (768px - 800px)
```
┌────┬──────────────────────────────────────────────────┬──────────┐
│    │ MON, 14 OCT                                      │          │
│ ▲  │ Amazon.com - Very Long Store Name                │ +$150.00 │
└────┴──────────────────────────────────────────────────┴──────────┘
     [Icon]  [Date on top]                               [Amount]
             [Payee below]
```
**Behavior**:
- **transaction-info becomes column** (flex-direction: column)
- Date on top, payee below
- Stacked vertically with 3px gap
- Payee takes full width
- Amount stays right-aligned
- Icon: 30x30px
- Padding: 10px 8px

### Stage 5: Mobile Compact (<768px)
```
┌───┬──────────────────────────────────────────────┬─────────┐
│   │ MON, 14                                      │         │
│ ▲ │ Amazon.com...                                │ +$150.0 │
└───┴──────────────────────────────────────────────┴─────────┘
    [Icon]  [Date]                                  [Amount]
            [Payee]
```
**Behavior**:
- Very compact stacked layout
- Date font: 9px
- Payee font: 11px
- Amount: 70px min-width
- Icon: 30x30px
- Tight spacing (2px gap)
- Padding: 10px 8px

## Key CSS Properties

### Flexbox Configuration

```css
/* Container */
.split-left .transaction-info {
    flex: 1;
    display: flex;
    flex-direction: row;  /* Becomes 'column' on narrow */
    gap: 8px;             /* Reduces to 2-3px on narrow */
    flex-wrap: nowrap;
    overflow: hidden;
}

/* Date - Fixed width */
.split-left .transaction-date {
    flex-shrink: 0;       /* Never shrinks */
    min-width: 90px;      /* Minimum space */
}

/* Payee - Flexible */
.split-left .transaction-payee {
    flex: 1 1 auto;       /* Grows and shrinks */
    min-width: 100px;     /* Minimum readable width */
    max-width: 300px;     /* Maximum to prevent sprawl */
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Category - Squeezable then removable */
.split-left .transaction-category {
    flex: 0 1 110px;      /* Can shrink from 110px basis */
    min-width: 0;         /* Can shrink to nothing */
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Amount - Fixed width */
.split-left .transaction-amount {
    flex-shrink: 0;       /* Never shrinks */
    min-width: 90px;      /* Minimum space */
    margin-left: auto;    /* Push to right */
}
```

## Responsive Breakpoints Summary

| Width Range | Layout | Date | Payee | Category | Amount | Gap |
|------------|--------|------|-------|----------|--------|-----|
| >1150px | Row | 90px | 100-300px | 110px | 90px | 8px |
| 1000-1150px | Row | 90px | 100-250px | 80px | 90px | 6px |
| 800-1000px | Row | 80px | Flex | Hidden | 80px | 6px |
| 768-800px | Column | Auto | 100% | Hidden | 75px | 3px |
| <768px | Column | Auto | 100% | Hidden | 70px | 2px |

## Visual Transition Examples

### Squeeze Animation (1200px → 1000px)
```
Full:     [▲][MON, 14 OCT][Amazon.com              ][SHOPPING   ][$150]
            ↓ Screen narrows ↓
Squeezed: [▲][MON, 14 OCT][Amazon.com              ][SHOP       ][$150]
            ↓ Screen narrows more ↓
Compact:  [▲][MON, 14 OCT][Amazon.com - Store Name Here          ][$150]
            ↓ Category gone ↓
```

### Stack Transition (900px → 700px)
```
Row:      [▲][MON, 14 OCT][Amazon Store Name Here                ][$150]
            ↓ Screen narrows ↓
Stack:    [▲][MON, 14 OCT                                        ][$150]
             [Amazon Store Name Here                             ]
            ↓ Two-line layout ↓
```

### Mobile Compact (<768px)
```
Compact:  [▲][MON, 14                                           ][$150]
             [Amazon Store Name...                              ]
            ↓ Very tight layout ↓
```

## User Experience Benefits

### No Overlapping
- Elements never overlap or collide
- Clean transitions at every breakpoint
- Readable at all screen sizes

### Progressive Disclosure
1. **Wide**: Show everything (date, payee, category, amount)
2. **Medium**: Squeeze category (still visible but smaller)
3. **Narrower**: Remove category (not critical info)
4. **Narrow**: Stack payee under date (two-line layout)
5. **Mobile**: Compact stack (minimal but readable)

### Maintained Hierarchy
- **Date**: Always prominent (bold cyan)
- **Payee**: Always visible (primary identifier)
- **Category**: Sacrificed first (secondary info)
- **Amount**: Always visible (financial data)

## Testing at Each Breakpoint

### 1400px (Desktop)
```
[▲] [MON, 14 OCT 2025] [Amazon Web Services       ] [TECH SERVICE] [+$150.00]
```
✓ All visible, spacious, easy to scan

### 1100px (Laptop/Narrow Desktop)
```
[▲] [MON, 14 OCT] [Amazon Web Services       ] [TECH SER] [+$150.00]
```
✓ Category squeezed but still visible

### 900px (Tablet Portrait)
```
[▲] [MON, 14 OCT] [Amazon Web Services - Cloud Platform     ] [+$150.00]
```
✓ Category gone, payee expanded, still single line

### 750px (Large Phone / Narrow Tablet)
```
[▲] [MON, 14 OCT                                            ] [+$150.00]
    [Amazon Web Services - Cloud Platform                   ]
```
✓ Stacked layout, date on top, payee below

### 375px (Standard Phone)
```
[▲] [MON, 14                                     ] [+$150]
    [Amazon Web Services - Clou...               ]
```
✓ Compact, readable, no horizontal scroll

## Implementation Details

### Files Modified
- `tactical.css`: Lines ~1177-1230 (main layout)
- `tactical.css`: Lines ~1998-2080 (responsive breakpoints)
- `tactical.css`: Lines ~2167-2210 (mobile optimizations)

### Key CSS Features Used
- Flexbox with flex-basis for squeezing
- flex-direction switch (row → column)
- min-width and max-width constraints
- text-overflow: ellipsis for truncation
- Progressive font-size reduction
- gap property for spacing
- display: none for category removal

### Performance
- Pure CSS solution (no JavaScript)
- Hardware accelerated (flexbox)
- Smooth transitions
- No layout thrashing
- Minimal repaints

## Testing Checklist

Progressive Squeezing:
- [x] Category shrinks from 110px → 80px (1150px)
- [x] Category shows ellipsis when text too long
- [x] Payee stays readable while category squeezes
- [x] No overlapping at any width

Category Removal:
- [x] Category disappears cleanly at 1000px
- [x] Payee expands to fill space smoothly
- [x] No layout jump or flash

Stacking Behavior:
- [x] Switches to vertical at 800px
- [x] Date stays on top
- [x] Payee below date
- [x] Amount stays right-aligned
- [x] Clean two-line layout

Mobile Optimization:
- [x] Very compact at <768px
- [x] Still readable
- [x] Touch targets adequate
- [x] No horizontal scroll

Edge Cases:
- [x] Very long payee names truncate properly
- [x] Very short payee names don't cause gaps
- [x] Empty categories don't break layout
- [x] Single-word payees display correctly

---

**Status**: ✅ Complete - Progressive responsive layout
**Impact**: Smooth adaptation from desktop to mobile
**UX**: Clean, readable, no overlapping at any width
