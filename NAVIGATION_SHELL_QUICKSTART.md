# Bank Navigation Shell - Quick Start Guide

## 🚀 Accessing the Navigation Shell

Visit: **`http://localhost:8000/bank/shell/`**

## 🎯 What Works Right Now

### ✅ Fully Implemented
- **Dashboard View** - Complete with analytics, recent transactions, and quick access
- **Accounts View** - Multi-account banking interface with transfers and history
- **Tab Navigation** - Click tabs for instant AJAX-loaded content
- **Faction Themes** - Switch between UN Navy, OPA, and Protomolecule
- **Audio System** - Toggle audio for hover/click sounds
- **Browser Navigation** - Back/forward buttons work perfectly
- **View Caching** - Last 3 views cached for instant switching
- **Loading States** - Faction-themed skeleton screens during load

### ⏳ Placeholder Views (Coming Soon)
- **Weekly View** - Shows "not yet implemented" message
- **Transactions View** - Shows "not yet implemented" message
- **Payees View** - Shows "not yet implemented" message
- **Categories View** - Shows "not yet implemented" message

## 🎨 Features You'll Notice

### Seamless Navigation
1. **Click any tab** → Content fades out
2. **Loading skeleton** → Faction-themed animation appears
3. **New content** → Fades in smoothly (300ms)
4. **No page reload** → URL updates, audio continues, theme persists

### Instant Caching
- First visit loads from server (~50-100ms)
- Subsequent visits load from memory (~200ms with transition)
- Hover over tabs to prefetch content before clicking

### Browser Integration
- Press **Back** button → Returns to previous view from cache
- Press **Forward** button → Advances to next view
- **Refresh** page → Reloads current view with new data

### Audio Feedback
- **Hover** over interactive elements → Subtle hover sound
- **Click** buttons/tabs → Tactical click sound
- **Toggle** audio anytime via header control

### Faction Themes
Select from dropdown in header:
- **UN Navy** - Blue tactical military aesthetic
- **OPA** - Orange belter rebellion styling
- **Protomolecule** - Cyan alien tech theme

## 🔍 Testing Checklist

### Basic Navigation (2 minutes)
1. Visit `/bank/shell/`
2. Click **Accounts** tab (should load smoothly)
3. Click **Dashboard** tab (should be instant from cache)
4. Click **Weekly** tab (should show "not yet implemented")
5. Press browser **Back** button twice (should return through history)

### Theme & Audio (1 minute)
6. Click **faction selector** dropdown
7. Choose different faction (UI should update instantly)
8. Click **audio toggle** button (enable if suspended)
9. Hover over tabs (should hear subtle sound if enabled)
10. Click tabs (should hear click sound)

### Performance (1 minute)
11. Click **Dashboard** → **Accounts** → **Dashboard** rapidly
12. Notice loading skeleton appears briefly
13. Notice cached loads are instant
14. Check browser console for errors (should be none)

### Mobile/Responsive (1 minute)
15. Resize browser window to mobile size
16. Notice tab labels hide on small screens
17. Navigation should still work
18. Faction selector should remain accessible

## 🐛 Known Issues / Limitations

### Current Limitations
- Only Dashboard and Accounts views are fully functional
- Weekly/Transactions/Payees/Categories show placeholder messages
- Add/Edit modals not yet tested in AJAX context
- Form submissions may cause page reloads (needs testing)

### Browser Compatibility
- **Chrome/Edge** - Full support including View Transitions API
- **Firefox** - Works (no View Transitions, uses CSS fallback)
- **Safari** - Works (no View Transitions, uses CSS fallback)

### Performance Notes
- First load fetches from server (~50-100ms)
- Cached loads are instant (~200ms transition time)
- View cache holds 3 views max (LRU eviction)
- Prefetch happens on tab hover (reduces perceived latency)

## 💡 Pro Tips

### For Best Experience
1. **Enable audio** - Makes navigation feel more immersive
2. **Hover before clicking** - Prefetches content for instant loads
3. **Use browser back/forward** - Works perfectly with cached views
4. **Choose a faction theme** - Personalizes the experience
5. **Keep developer console open** - See detailed logging

### Keyboard Navigation
- **Tab** key - Navigate between interactive elements
- **Enter** - Activate focused tab
- **Arrows** - Navigate dropdowns
- **Escape** - Close modals (when implemented)

### Developer Features
Browser console shows detailed logs:
```
🚀 Bank Navigation Shell initializing...
✅ Bank Navigation Shell ready
📂 Loading view: accounts
💾 Loading from cache
✅ View loaded: accounts
🎯 Initializing Accounts View
✅ Accounts View initialized
```

## 📊 Performance Expectations

| Action | Time | Notes |
|--------|------|-------|
| Initial shell load | ~100ms | One-time server fetch |
| First view load | ~50-100ms | Server + render time |
| Cached view switch | ~200ms | Memory + transition |
| Prefetched view | ~200ms | Already loaded on hover |
| Faction change | Instant | CSS variable update |
| Audio toggle | Instant | localStorage update |

## 🔧 Troubleshooting

### Tab Not Loading
**Symptom:** Click tab but nothing happens  
**Solution:** Open browser console, check for JavaScript errors, refresh page

### Audio Not Working
**Symptom:** No hover/click sounds  
**Solution:** Click audio toggle button in header to enable

### Theme Not Changing
**Symptom:** Faction selector doesn't update colors  
**Solution:** Clear browser localStorage, refresh page

### Loading Forever
**Symptom:** Skeleton screen stays visible  
**Solution:** Check network tab for failed AJAX requests, refresh page

### Browser Back Broken
**Symptom:** Back button reloads page  
**Solution:** Ensure you're using `/bank/shell/` URL, not individual page URLs

## 📍 URL Structure

### Navigation Shell URLs
- `/bank/shell/` - Main shell entry point (loads dashboard by default)
- State stored in browser history (invisible to user)

### AJAX Endpoints (Background)
- `/bank/ajax/dashboard/` - Returns dashboard HTML in JSON
- `/bank/ajax/accounts/` - Returns accounts HTML in JSON
- `/bank/ajax/weekly/` - Placeholder (not yet implemented)
- `/bank/ajax/transactions/` - Placeholder (not yet implemented)
- `/bank/ajax/payees/` - Placeholder (not yet implemented)
- `/bank/ajax/categories/` - Placeholder (not yet implemented)

### Traditional URLs (Still work)
- `/bank/` - Old-style dashboard page (full page load)
- `/bank/accounts/` - Old-style accounts page (full page load)
- `/bank/weekly-expanse/` - Old-style weekly page (full page load)
- Use these if you need to bypass the shell system

## 🎬 Demo Sequence

**For showing to others:**

1. **Start** at `/bank/shell/`
2. "Notice the Expanse tactical interface with faction theming"
3. **Click Accounts tab** - "See the smooth transition without page reload"
4. **Click Dashboard tab** - "This loads instantly from cache"
5. **Change faction** - "Entire UI updates with new color scheme"
6. **Enable audio** - "Adds immersive sound effects"
7. **Hover over tabs** - "Hear subtle feedback and see prefetch in console"
8. **Click browser back** - "Previous view loads instantly from cache"
9. **Resize window** - "Responsive design adapts to mobile"
10. **Click Weekly tab** - "Placeholder shows this view is coming soon"

## 📞 Support

### Questions?
- Check `NAVIGATION_SHELL_IMPLEMENTATION.md` for full technical details
- Review browser console for detailed logging
- Check network tab to see AJAX requests/responses

### Reporting Issues
When reporting bugs, include:
- Browser version
- Console error messages
- Network tab showing failed requests
- Steps to reproduce

### Feature Requests
For next phase implementation:
1. Weekly view conversion (Priority: HIGH)
2. Transactions view conversion (Priority: HIGH)
3. Payees view conversion (Priority: MEDIUM)
4. Categories view conversion (Priority: MEDIUM)
5. Modal integration testing
6. Form submission handling

---

**Version:** 1.0  
**Last Updated:** October 10, 2025  
**Status:** Phase 1 Complete (Dashboard + Accounts)
