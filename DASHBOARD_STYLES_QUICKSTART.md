# Quick Reference: Three Dashboard Styles

## How to Switch Styles

### Using Dropdown
Click the **"DASHBOARD STYLE"** selector in the top-right corner

### Using Keyboard
- **Ctrl + 1** → Quantum Glass
- **Ctrl + 2** → Terminal Matrix  
- **Ctrl + 3** → Neon Synthwave

### Automatic
Your choice is saved and will persist across sessions!

---

## Style 1: Quantum Glass 🌟

**When to use**: Daily productivity, professional feel

### What You'll See
- Floating frosted glass cards
- Purple-blue gradient background
- Animated colorful blobs
- Smooth hover effects
- Modern, clean design

### Perfect for
- Users who like Apple/iOS aesthetics
- Professional/business environments
- Clean, distraction-free interface
- Elegant, premium feel

---

## Style 2: Terminal Matrix 💻

**When to use**: Developer/tech enthusiast mode

### What You'll See
- Black background with green text
- ASCII art logo
- CRT scanline effects
- Live terminal clock
- Command-line style interface
- Numbered app list

### Perfect for
- Developers and programmers
- Retro computing fans
- Matrix/hacker aesthetic lovers
- Minimalist, text-focused users

---

## Style 3: Neon Synthwave 🌆

**When to use**: Fun, energetic, cyberpunk vibe

### What You'll See
- Dark background with 3D grid
- Pink/cyan neon colors
- Pulsing gradient sun
- Glowing text effects
- Flickering neon lights
- 80s retrowave aesthetic

### Perfect for
- Creative users
- Cyberpunk/sci-fi fans
- High-energy visual experience
- Outrun/synthwave enthusiasts

---

## At a Glance Comparison

| Feature | Quantum | Terminal | Neon |
|---------|---------|----------|------|
| **Vibe** | 😌 Calm | 🤓 Technical | 🎮 Energetic |
| **Colors** | Purple/Blue | Green/Black | Pink/Cyan |
| **Layout** | Cards | List | Grid |
| **Best Time** | All day | Late night | Weekends |
| **Energy** | Relaxed | Focused | High |

---

## Tips & Tricks

### Quantum Glass
- Move your mouse over app cards to see the glow follow your cursor
- Cards lift when you hover for a 3D effect
- Perfect for long work sessions

### Terminal Matrix
- Watch the scanlines for authentic CRT monitor feel
- Live clock updates every second
- Great for coding sessions

### Neon Synthwave
- Notice the flickering effect on the title
- Cards have dual-colored shadows on hover
- The sun pulses in the background
- Best experienced in a dark room!

---

## Troubleshooting

**Style not changing?**
- Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
- Check browser console for errors
- Clear localStorage and try again

**Performance issues?**
- Quantum's blur effects work best on modern browsers
- Terminal is the most lightweight
- Disable animations in browser settings if needed

**Visual glitches?**
- Update your browser to the latest version
- Some effects require modern CSS support
- Try a different style if one has issues

---

## Quick Start Guide

1. **Open Dashboard**: http://localhost:8000/accounts/dashboard/
2. **See the selector**: Top-right corner (black box)
3. **Pick a style**: Quantum, Terminal, or Neon
4. **Explore**: Each style has unique features!
5. **It's saved**: Your choice persists automatically

---

## Developer Notes

### File Locations
- Template: `templates/accounts/dashboard.html`
- CSS: `static/css/multi_dashboard.css` (27KB)
- JS: `static/js/multi_dashboard.js` (7.5KB)

### Storage
- Key: `dashboard_style`
- Values: `quantum`, `terminal`, `neon`
- Location: localStorage

### Adding New Styles
1. Add new `<div class="layout layout-yourname">` in template
2. Create CSS classes with `.layout-yourname` prefix
3. Add initialization function in JavaScript
4. Update style selector dropdown

---

**Need Help?** See full documentation in `MULTI_DASHBOARD_IMPLEMENTATION.md`
