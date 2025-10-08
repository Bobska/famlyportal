# The Expanse Dashboard - Theme Visual Reference

## Quick Access
**URL**: http://localhost:8000/accounts/dashboard/  
**Keyboard Shortcuts**:
- `Alt + 1` → Earth Defense (Blue)
- `Alt + 2` → Mars Congressional Republic (Red)
- `Alt + 3` → OPA Belter (Cyan/Yellow)

---

## Theme 1: Earth Defense (UN Military)

### Visual Identity
```
███████ EARTH DEFENSE COALITION ███████
        UNITED NATIONS COMMAND
═══════════════════════════════════════
```

**Primary Color**: `#4a9eff` (Professional Blue)  
**Accent**: `#6db4ff` (Bright Blue)  
**Status Active**: `#00d4aa` (Teal)  
**Typography**: Rajdhani (clean sans-serif)

### Design Characteristics
- **Aesthetic**: Clean, organized, professional military command
- **Borders**: Sharp, straight lines with subtle rounded corners (2px)
- **Panels**: Clean backgrounds with blue accent top borders
- **Lighting**: Cool blue glow effects on active elements
- **Layout**: Precise grid alignment, symmetric organization
- **Feel**: Authoritative, trustworthy, efficient

### Visual Elements
- Hexagonal logo with double border
- Straight accent lines across panels
- Clean status indicators with blue glow
- Organized three-column status displays
- Professional military card layouts

### Use Case
Default theme. Best for users who prefer professional, clean interfaces. Represents United Nations naval command aesthetic from The Expanse series.

---

## Theme 2: Mars Congressional Republic (Industrial Military)

### Visual Identity
```
▓▓▓▓▓▓▓ MARS CONGRESSIONAL REPUBLIC ▓▓▓▓▓▓▓
           MILITARY OPERATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Primary Color**: `#ff6b4a` (Industrial Red-Orange)  
**Accent**: `#ff8866` (Bright Orange)  
**Status Active**: `#00ff88` (Green)  
**Typography**: Rajdhani (industrial sans-serif)

### Design Characteristics
- **Aesthetic**: Industrial, rugged, exposed-tech military
- **Borders**: Red-orange with lower opacity (0.28)
- **Panels**: Darker backgrounds with diagonal pattern overlays (45deg stripes)
- **Lighting**: Warm red-orange accent lighting
- **Layout**: Slightly asymmetric, industrial construction feel
- **Feel**: Powerful, determined, no-nonsense

### Visual Elements
- Hexagonal logo with red-orange double border and gradient fill
- Diagonal repeating patterns (8px intervals) suggesting industrial construction
- Heavier panel backgrounds (darker browns/reds)
- Exposed-tech appearance with visible panel seams
- Industrial gradient treatments (145deg angles)

### Use Case
For users who prefer bold, industrial aesthetics. Represents Martian Congressional Republic Navy military vessels - functional, powerful, industrial design philosophy.

---

## Theme 3: OPA Belter (Makeshift Resistance)

### Visual Identity
```
╔═══════════════════════════════════════╗
║   OUTER PLANETS ALLIANCE NETWORK     ║
║   ⚠ IMPROVISED SYSTEMS ACTIVE ⚠      ║
╚═══════════════════════════════════════╝
```

**Primary Color**: `#00d4cc` (Cyan)  
**Accent**: `#00fff2` (Bright Cyan)  
**Warning**: `#ffcc00` / `#ffee00` (Yellow)  
**Status Active**: `#ffee00` (Yellow)  
**Typography**: Share Tech Mono (monospace terminal font)

### Design Characteristics
- **Aesthetic**: Improvised, jury-rigged, makeshift industrial
- **Borders**: Cyan with yellow warning accents
- **Panels**: Grid patterns (3px intervals) suggesting modular construction
- **Lighting**: Dual cyan-yellow lighting system
- **Layout**: More visible panel separation, cobbled-together modules
- **Feel**: Resourceful, scrappy, functional warning systems

### Visual Elements
- Hexagonal logo with cyan border and yellow inner border (dual-color system)
- Grid-based background patterns (both horizontal and vertical)
- Yellow warning stripe accents at panel tops (1px height)
- Monospace terminal-style typography (Share Tech Mono)
- Cyan text glow effects on readouts
- Visible panel afterglow effects suggesting improvised lighting
- More prominent panel borders showing modular construction

### Use Case
For users who prefer cyberpunk/terminal aesthetics. Represents OPA Belter improvised technology - resourceful, makeshift, warning-system heavy design from The Expanse series.

---

## Component Breakdown

### Command Bar (Header)
All themes include:
- Hexagonal logo (faction-colored)
- Organization name in Orbitron font
- Live mission clock (HH:MM:SS)
- User profile with avatar and role
- Theme selector dropdown

**Theme Variations**:
- Earth: Clean blue hexagon with single border gradient
- Mars: Red-orange hexagon with diagonal gradient fill
- OPA: Cyan outer border, yellow inner border, dual-color gradient

### Status Panels (Information Display)
All themes include:
- Panel designation label (small caps)
- Panel title
- Status readouts with labels and values
- Border accents

**Theme Variations**:
- Earth: Blue top accent, clean backgrounds
- Mars: Red diagonal pattern overlay, industrial gradients
- OPA: Yellow warning stripe top, cyan-yellow gradient accents, visible grid overlay

### Operations Grid (App Cards)
All themes include:
- Status indicator (ACTIVE/DEVELOPMENT/OFFLINE)
- Operation icon (Bootstrap Icons)
- Operation title (Orbitron font)
- Description text
- Metadata (clearance level, integration status)

**Theme Variations**:
- Earth: Clean cards with blue accent hover
- Mars: Industrial cards with red diagonal patterns
- OPA: Modular cards with yellow warning accents, cyan glow on text

### Mission Brief (Section Header)
All themes include:
- Section designation
- Large heading (Orbitron)
- Current stardate (YYYY.DDD format)

**Theme Variations**:
- Same structure, themed colors via CSS custom properties

---

## Color Palettes (Complete Reference)

### Earth Defense
```css
--expanse-accent: #4a9eff           /* Primary blue */
--expanse-accent-bright: #6db4ff    /* Bright blue */
--expanse-accent-dim: rgba(74, 158, 255, 0.25)
--expanse-panel-border: rgba(74, 158, 255, 0.35)
--expanse-status-active: #00d4aa    /* Teal green */
--expanse-status-dev: #ffaa00       /* Orange */
--expanse-status-offline: #666      /* Gray */
--expanse-bg-primary: #0a0e14       /* Deep space black */
--expanse-bg-secondary: #0d1117     /* Slightly lighter black */
--expanse-surface: rgba(16, 24, 38, 0.95)
--expanse-surface-elevated: rgba(22, 32, 48, 0.98)
--expanse-text-primary: #e8f0ff     /* Near white */
--expanse-text-secondary: rgba(200, 220, 255, 0.75)
--expanse-text-dim: rgba(160, 180, 210, 0.6)
```

### Mars Congressional Republic
```css
--expanse-accent: #ff6b4a           /* Industrial red-orange */
--expanse-accent-bright: #ff8866    /* Bright orange */
--expanse-accent-dim: rgba(255, 107, 74, 0.25)
--expanse-panel-border: rgba(255, 107, 74, 0.35)
--expanse-status-active: #00ff88    /* Bright green */
--expanse-status-dev: #ffcc00       /* Yellow */
--expanse-status-offline: #555      /* Darker gray */
--expanse-surface: rgba(28, 16, 16, 0.95)      /* Warm dark brown */
--expanse-surface-elevated: rgba(38, 22, 22, 0.98)
/* Text colors inherited from base */
```

### OPA Belter
```css
--expanse-accent: #00d4cc           /* Cyan */
--expanse-accent-bright: #00fff2    /* Bright cyan */
--expanse-accent-dim: rgba(0, 212, 204, 0.25)
--expanse-panel-border: rgba(0, 212, 204, 0.32)
--expanse-warning: #ffcc00          /* Warning yellow */
--expanse-status-active: #ffee00    /* Bright yellow */
--expanse-status-dev: #ff8800       /* Orange */
--expanse-status-offline: #555      /* Darker gray */
--expanse-surface: rgba(12, 20, 22, 0.95)      /* Dark cyan-tinted */
--expanse-surface-elevated: rgba(18, 28, 30, 0.98)
/* Text colors inherited from base */
```

---

## Typography Scale

### Font Families
```css
/* Primary Body Text */
font-family: 'Rajdhani', 'Segoe UI', sans-serif;
Weights: 400, 500, 600, 700

/* Headers & Titles */
font-family: 'Orbitron', sans-serif;
Weights: 500, 600, 700, 900

/* Monospace (Clock, Terminal) */
font-family: 'Share Tech Mono', monospace;
Weight: 400

/* OPA Theme Override */
font-family: 'Share Tech Mono', 'Rajdhani', monospace;
```

### Size Scale
```css
/* Logo */
logo-text: 1.15rem (letter-spacing: 0.18em)
logo-designation: 0.6rem (letter-spacing: 0.25em)

/* Clock */
mission-time__label: 0.65rem
mission-time__value: 1.5rem

/* User Profile */
user-name: 0.85rem
user-designation: 0.65rem

/* Panel Headers */
panel-designation: 0.65rem (letter-spacing: 0.28em)
panel-title: 0.95rem (letter-spacing: 0.18em)

/* Status Readouts */
readout-label: 0.72rem
readout-value: 0.85rem

/* Mission Brief */
brief-designation: 0.65rem
brief-heading: clamp(1.6rem, 2vw, 2.2rem)

/* Operation Cards */
status-text: 0.62rem (letter-spacing: 0.24em)
operation-icon: 2.4rem
operation-title: 1.05rem (letter-spacing: 0.15em)
operation-desc: 0.8rem
meta-item: 0.65rem
```

---

## Animation Effects

### Theme Switching
```javascript
// Viewport fade transition
opacity: 0.8 → 1 (150ms ease-in-out)
```

### Status Indicator Pulse (on hover)
```css
@keyframes pulse-glow {
    0%, 100%: box-shadow: 0 0 12px, scale(1)
    50%: box-shadow: 0 0 20px, scale(1.1)
}
Duration: 1.5s ease-in-out infinite
```

### Operation Card Hover
```css
transform: translateY(-3px)
border-color: var(--expanse-accent)
box-shadow: 0 8px 32px -8px var(--expanse-accent-dim)
Duration: 220ms ease
```

### Clock Update
```javascript
Interval: 1000ms (every second)
Format: HH:MM:SS (24-hour)
```

---

## Responsive Behavior

### Desktop (1200px+)
- 3-column command bar layout
- 3-column status panels
- Auto-fit operations grid (300px minimum)

### Tablet (768px - 1200px)
- Single-column command bar (stacked)
- 2-column or auto-fit status panels
- 2-column operations grid

### Mobile (< 768px)
- All single-column layouts
- Reduced padding (1rem)
- Hidden secondary info (logo designation, user info text)
- Smaller font sizes

### Small Mobile (< 480px)
- Minimal layout
- Hide user info entirely (keep avatar only)
- Smaller clock display
- Single-column everything

---

## Developer Reference

### Theme Switching Code
```javascript
// Apply theme programmatically
function applyTheme(themeName) {
    document.body.className = `expanse-shell expanse-${themeName}`;
    document.querySelector('[data-expanse-theme]')
        .setAttribute('data-expanse-theme', themeName);
}

// Get current theme
const currentTheme = localStorage.getItem('expanse_theme') || 'earth';

// Save theme preference
localStorage.setItem('expanse_theme', 'mars');
```

### CSS Custom Property Usage
```css
/* Define theme colors */
body.expanse-earth {
    --expanse-accent: #4a9eff;
}

/* Use in components */
.operation-card {
    border-color: var(--expanse-accent);
}
/* Automatically inherits theme colors */
```

---

## Testing Checklist

### Visual Tests
- [ ] All three themes render correctly
- [ ] Theme switching is instant (no page reload)
- [ ] Colors match reference palette
- [ ] Typography is consistent
- [ ] Icons display properly (Bootstrap Icons)
- [ ] Layouts are aligned

### Functional Tests
- [ ] Clock updates every second
- [ ] Stardate calculates correctly
- [ ] Theme persists after page reload
- [ ] Keyboard shortcuts work (Alt+1/2/3)
- [ ] Hover effects trigger properly
- [ ] Status indicators glow on hover
- [ ] Theme selector dropdown works
- [ ] Weather data displays (if available)
- [ ] App permissions filter correctly

### Responsive Tests
- [ ] Desktop layout (1920px, 1366px)
- [ ] Tablet layout (1024px, 768px)
- [ ] Mobile layout (375px, 414px)
- [ ] Small mobile (320px)
- [ ] Landscape orientation
- [ ] Portrait orientation

### Browser Tests
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest, if available)

---

## Quick Reference: What's Different Between Themes?

| Feature | Earth Defense | Mars Republic | OPA Belter |
|---------|--------------|---------------|------------|
| **Primary Color** | Blue (#4a9eff) | Red-Orange (#ff6b4a) | Cyan (#00d4cc) |
| **Secondary Color** | - | - | Yellow (#ffee00) |
| **Font** | Rajdhani | Rajdhani | Share Tech Mono |
| **Background Pattern** | Subtle blue radial gradients | 45° diagonal stripes | 3px grid overlay |
| **Border Style** | Clean straight lines | Industrial red borders | Cyan + yellow dual borders |
| **Panel Accent** | Blue top line | Red gradient line | Yellow warning stripe |
| **Logo Treatment** | Blue single border | Red gradient fill | Cyan outer + yellow inner |
| **Text Glow** | Subtle blue | None | Cyan glow on values |
| **Overall Feel** | Professional military | Industrial powerful | Makeshift terminal |

---

**Implementation Date**: October 9, 2025  
**Version**: 1.0  
**Status**: Production Ready (Pending Final Testing)
