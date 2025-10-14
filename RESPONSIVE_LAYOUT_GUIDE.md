# Responsive Tactical Layout - Visual Guide

## Layout Transformations

### Desktop Mode (>1400px)
```
┌──────────────────────────────────────────────────────────────┐
│                    HEADER (Full Width)                       │
├──────────┬──────────────────────────────────┬────────────────┤
│          │                                  │                │
│  LEFT    │      CENTER PANEL (Main)        │     RIGHT      │
│  PANEL   │                                  │     PANEL      │
│  (300px) │        (Flexible 1fr)            │    (300px)     │
│          │                                  │                │
│ Always   │    Full information density      │    Always      │
│ Visible  │                                  │    Visible     │
│          │                                  │                │
└──────────┴──────────────────────────────────┴────────────────┘
```

### Tablet Narrow (1200px - 1400px)
```
┌──────────────────────────────────────────────────────────────┐
│                    HEADER (Full Width)                       │
├────────┬────────────────────────────────────┬────────────────┤
│        │                                    │                │
│ LEFT   │     CENTER PANEL (Main)           │     RIGHT      │
│ PANEL  │                                    │     PANEL      │
│(250px) │      (Flexible 1fr)                │    (250px)     │
│        │                                    │                │
│Smaller │  Optimized spacing                 │    Smaller     │
│        │                                    │                │
└────────┴────────────────────────────────────┴────────────────┘
```

### Tablet Wide (900px - 1200px)
```
Desktop view:
┌─────┬────────────────────────────────────────────────┬─────┐
│  ◄  │          CENTER PANEL (Full Width)             │  ►  │
│     │                                                │     │
│Toggle                                               Toggle│
│     │                                                │     │
└─────┴────────────────────────────────────────────────┴─────┘

Left panel expanded:
┌────────────┬──────────────────────────────────────────┐
│            │                                          │
│   LEFT     │         CENTER PANEL                     │
│   PANEL    │                                          │
│  (Overlay) │         (Dimmed backdrop)                │
│   280px    │                                          │
│            │    Click backdrop or toggle to close     │
│   [Close]  │                                          │
└────────────┴──────────────────────────────────────────┘

Right panel expanded:
┌──────────────────────────────────────────┬────────────┐
│                                          │            │
│         CENTER PANEL                     │   RIGHT    │
│                                          │   PANEL    │
│         (Dimmed backdrop)                │  (Overlay) │
│                                          │   280px    │
│    Click backdrop or toggle to close     │            │
│                                          │   [Close]  │
└──────────────────────────────────────────┴────────────┘
```

### Mobile (<768px)
```
┌────────────────────────────────────────────────────────┐
│               HEADER (Compact)                         │
├────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐     │
│  │  STATS ►                                     │     │
│  └──────────────────────────────────────────────┘     │
│  [ Left panel collapsed ]                             │
│                                                        │
├────────────────────────────────────────────────────────┤
│                                                        │
│           CENTER PANEL (Full Width)                   │
│                                                        │
│              Main content area                        │
│                                                        │
├────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐     │
│  │  ◄ ACTIONS                                   │     │
│  └──────────────────────────────────────────────┘     │
│  [ Right panel collapsed ]                            │
│                                                        │
└────────────────────────────────────────────────────────┘

When "STATS ►" is clicked:
┌────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────┐     │
│  │  STATS ▼                                     │     │
│  ├──────────────────────────────────────────────┤     │
│  │                                              │     │
│  │    LEFT PANEL CONTENT EXPANDED               │     │
│  │                                              │     │
│  │    • Financial Status                        │     │
│  │    • Stats Grid                              │     │
│  │    • Balance Display                         │     │
│  │                                              │     │
│  └──────────────────────────────────────────────┘     │
│                                                        │
│           CENTER PANEL                                │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## Interaction Patterns

### Desktop
- **Behavior**: Static layout, no interactions needed
- **Panels**: Always visible
- **User Action**: None required

### Tablet (900-1200px)
- **Behavior**: Slide-out overlay panels
- **Trigger**: Click toggle button (◄ or ►)
- **Animation**: Smooth slide from edge (300ms cubic-bezier)
- **Backdrop**: Semi-transparent overlay appears
- **Close**: Click backdrop, toggle button, or open other panel
- **Constraint**: Only one panel open at a time

### Mobile (<768px)
- **Behavior**: Accordion-style expansion
- **Trigger**: Click header bar ("STATS ►" or "◄ ACTIONS")
- **Animation**: Vertical expansion with max-height
- **Icon**: Changes from ► to ▼ when expanded
- **Backdrop**: None (not needed in stacked layout)
- **Constraint**: Multiple panels can be open

## Toggle Button States

### Tablet Vertical Buttons
```
Closed state:
┌───┐
│   │
│ ◄ │  (Left button)
│   │
└───┘

┌───┐
│   │
│ ► │  (Right button)
│   │
└───┘

Open state:
Button hides/fades when panel is open
```

### Mobile Horizontal Buttons
```
Collapsed:
┌──────────────────────────────┐
│  STATS ►                     │
└──────────────────────────────┘

Expanded:
┌──────────────────────────────┐
│  STATS ▼                     │
└──────────────────────────────┘
```

## Visual Effects

### Panel Animations
- **Transform**: `translateX(-100%)` → `translateX(0)` (left panel)
- **Transform**: `translateX(100%)` → `translateX(0)` (right panel)
- **Duration**: 300ms
- **Easing**: cubic-bezier(0.4, 0, 0.2, 1)

### Backdrop
- **Background**: rgba(0, 0, 0, 0.7)
- **Transition**: Opacity fade 300ms
- **Z-index**: 998 (below panels)

### Toggle Buttons
- **Hover**: Glow effect (box-shadow: 0 0 15px cyan)
- **Background**: Gradient (cyan 20% → 10%)
- **Border**: 2px solid cyan (50% opacity)

### Panel Borders
- **Normal**: 1px solid cyan (25% opacity)
- **Active**: 2px solid cyan (100% opacity)
- **Shadow**: 0 0 30px cyan (50% opacity)

## Tactical Theme Elements Maintained

✅ Sharp corners (border-radius: 0)
✅ Cyan accent color (#00d9ff)
✅ Rajdhani font family
✅ Gradient backgrounds
✅ Scan line effects
✅ HUD-style corners
✅ Tactical terminology
✅ Military-inspired layout

## Testing Scenarios

1. **Desktop to Tablet**: Resize browser from 1500px → 1000px
   - Watch panels convert to overlays
   - Toggle buttons should appear
   - Layout should remain functional

2. **Tablet to Mobile**: Resize from 1000px → 700px
   - Overlays convert to accordions
   - Toggle buttons change orientation
   - Backdrop should disappear

3. **Toggle Interactions**:
   - Click left toggle → panel slides out
   - Click backdrop → panel slides in
   - Click right toggle → left closes, right opens
   - Smooth animations throughout

4. **Mobile Accordion**:
   - Tap "STATS ►" → expands vertically
   - Icon changes to "STATS ▼"
   - Tap again → collapses back
   - Multiple panels can be open

## Browser DevTools Testing

### Chrome DevTools
1. Press `F12`
2. Click device toolbar icon (or `Ctrl+Shift+M`)
3. Select "Responsive" mode
4. Drag to resize or enter specific widths:
   - 1920px (desktop)
   - 1300px (tablet narrow)
   - 1000px (tablet wide)
   - 375px (mobile)

### Test Checklist
- [ ] Panels visible on desktop
- [ ] Panels narrow on tablet-narrow
- [ ] Toggle buttons appear on tablet-wide
- [ ] Left panel slides out correctly
- [ ] Right panel slides out correctly
- [ ] Backdrop appears/disappears
- [ ] Only one panel open at a time (tablet)
- [ ] Accordion works on mobile
- [ ] Icons change on mobile
- [ ] Smooth animations everywhere
- [ ] No visual glitches
- [ ] Touch targets adequate

## Performance Notes

- **CSS Transforms**: Hardware-accelerated (60fps)
- **JavaScript**: Minimal overhead, event-driven
- **Memory**: Toggles/backdrop created once, reused
- **Cleanup**: Elements removed on desktop mode
- **Resize**: Debounced for performance

---

**Implementation Status**: ✅ Complete
**Commit**: `feat(bank): implement responsive tactical panel system`
**Files**: tactical.css, tactical.js, RESPONSIVE_TACTICAL_PANELS.md
