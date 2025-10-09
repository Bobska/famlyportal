# WebSocket Presence System Testing Guide

## Overview
The presence system tracks real-time online/offline status for family members using Django Channels and WebSocket connections.

## Prerequisites

### 1. Install Redis
Redis is required as the channel layer backend for Django Channels.

**Windows Installation:**
1. Download Redis for Windows from: https://github.com/microsoftarchive/redis/releases
2. Extract to `C:\Redis` (or your preferred location)
3. Run `redis-server.exe` from the extracted folder
4. Redis will start on default port `6379`

**Alternative - Windows Subsystem for Linux (WSL):**
```bash
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

**macOS (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

### 2. Verify Redis is Running
```bash
redis-cli ping
```
Expected output: `PONG`

## Running the Application

### 1. Start Redis (if not already running)
```bash
# Windows: Run redis-server.exe
# Linux/macOS:
redis-server
```

### 2. Run Django with Daphne (ASGI Server)
**Option A: Using Daphne directly**
```bash
C:/dev-projects/famlyportal/.venv/Scripts/python.exe -m daphne -b 127.0.0.1 -p 8000 famlyportal.asgi:application
```

**Option B: Using Django runserver (WebSocket support limited)**
```bash
C:/dev-projects/famlyportal/.venv/Scripts/python.exe manage.py runserver
```

**Note:** For full WebSocket functionality, use Daphne (Option A).

### 3. Access the Dashboard
1. Open browser and go to: http://127.0.0.1:8000
2. Log in with your user account
3. Navigate to the dashboard

## Testing Checklist

### ✅ Connection Tests
- [ ] Connection status shows "CONNECTING" on page load (yellow with blink animation)
- [ ] Connection status changes to "CONNECTED" within 2-3 seconds (green)
- [ ] Browser console shows: `[Presence] Connected to presence server`
- [ ] Connection sound plays when connected (if audio is enabled)

### ✅ Crew List Population
- [ ] "CONNECTING..." placeholder disappears after connection
- [ ] All family members appear in the crew list
- [ ] Each member shows:
  - Online/offline status indicator (green dot with pulse = online, gray dot = offline)
  - Name with role icon
  - Role label (ADMIN, PARENT, CHILD, MEMBER)
  - Last seen timestamp (e.g., "Online now", "5m ago", "2h ago")

### ✅ Real-Time Updates (Multi-Browser Test)
1. Open dashboard in Browser A (User 1)
2. Open dashboard in Browser B (User 2) or Incognito window with different user
3. Verify:
   - [ ] Both browsers show both users as online
   - [ ] Green status dots with pulse animation for online users
   - [ ] "Online now" text for online users
   - [ ] Status change sound plays when user goes online/offline (if audio enabled)

4. Close Browser B
5. Verify in Browser A:
   - [ ] User 2 status changes to offline (gray dot, no pulse)
   - [ ] Last seen timestamp updates (e.g., "Just now", "1m ago")
   - [ ] Brief glow animation on status change

### ✅ Heartbeat System
- [ ] Connection stays alive for 5+ minutes
- [ ] Browser console shows periodic: `[Presence] Heartbeat acknowledged` (every 30 seconds)
- [ ] Connection doesn't drop during idle periods

### ✅ Reconnection Tests
1. Stop Redis server
2. Verify:
   - [ ] Connection status changes to "DISCONNECTED" (red with blink)
   - [ ] Browser console shows: `[Presence] Disconnected`
   - [ ] Automatic reconnection attempts: `[Presence] Reconnecting in Xms`

3. Restart Redis server
4. Verify:
   - [ ] Connection automatically re-establishes
   - [ ] Status changes back to "CONNECTED"
   - [ ] Crew list repopulates

### ✅ Page Visibility Tests
1. Switch to different browser tab for 1 minute
2. Switch back to dashboard
3. Verify:
   - [ ] Connection is still active OR automatically reconnects
   - [ ] Crew statuses are up-to-date
   - [ ] Browser console shows: `[Presence] Page visible`

### ✅ Family Data Isolation
1. Create/join multiple families
2. Open dashboard for Family A
3. Open dashboard for Family B (different browser/user)
4. Verify:
   - [ ] Family A dashboard only shows Family A members
   - [ ] Family B dashboard only shows Family B members
   - [ ] No cross-family presence data leaks

### ✅ Faction Theme Integration
1. Switch between factions (UN Navy, Belter, Protomolecule)
2. Verify:
   - [ ] Status indicators use faction colors
   - [ ] Crew member hover shows faction-colored borders
   - [ ] Status change animation uses faction colors

### ✅ UI/UX Polish
- [ ] Status indicators are clearly visible
- [ ] Pulse animation is smooth (no jank)
- [ ] Status changes have brief highlight effect
- [ ] Last seen timestamps are readable
- [ ] Connection status fits in header without overflow
- [ ] Works on different screen sizes (responsive)

## Debugging Tools

### Browser Console Commands
```javascript
// Check presence manager status
ExpansePresence.isConnected

// Check stored family presence data
ExpansePresence.familyPresence

// Manually trigger reconnection
ExpansePresence.connect()

// Disconnect
ExpansePresence.disconnect()

// Send test heartbeat
ExpansePresence.send({type: 'heartbeat', page: '/test'})
```

### Django Admin
1. Go to: http://127.0.0.1:8000/admin/
2. Navigate to: Accounts → User Presences
3. View real-time presence data:
   - Is online status
   - Last seen timestamp
   - Last heartbeat
   - Current page
   - Channel name

### Redis CLI Monitoring
```bash
# Monitor all Redis commands
redis-cli monitor

# Check active channels
redis-cli PUBSUB CHANNELS

# Check channel subscribers
redis-cli PUBSUB NUMSUB family_1
```

## Common Issues

### Issue: Connection Status Stuck on "CONNECTING"
**Causes:**
- Redis not running
- Daphne not used (using runserver instead)
- ASGI configuration error

**Solutions:**
1. Verify Redis: `redis-cli ping` → should return `PONG`
2. Use Daphne: `python -m daphne famlyportal.asgi:application`
3. Check browser console for WebSocket errors

### Issue: WebSocket Connection Fails
**Error:** `WebSocket connection to 'ws://127.0.0.1:8000/ws/presence/' failed`

**Solutions:**
1. Ensure using Daphne ASGI server (not Django runserver)
2. Check `ASGI_APPLICATION` in settings.py
3. Verify accounts/routing.py exists and is imported in asgi.py
4. Check CHANNEL_LAYERS configuration in settings.py

### Issue: Users Not Appearing in Crew List
**Causes:**
- User not part of a family
- WebSocket not connected
- JavaScript error

**Solutions:**
1. Verify user has FamilyMember record
2. Check browser console for errors
3. Verify family_presence message received in console

### Issue: Status Not Updating
**Causes:**
- Heartbeat not working
- Multiple browser tabs (same user)
- Redis connection lost

**Solutions:**
1. Check browser console for heartbeat acknowledgments
2. Close duplicate tabs
3. Restart Redis server

## Performance Monitoring

### Expected Behavior
- **Connection Time:** < 2 seconds
- **Status Update Latency:** < 500ms
- **Heartbeat Frequency:** Every 30 seconds
- **Reconnection Attempts:** Up to 10 times with exponential backoff
- **Memory Usage:** ~2-5MB per WebSocket connection

### Metrics to Track
- Active WebSocket connections: Check Daphne logs
- Redis memory usage: `redis-cli info memory`
- Browser memory: Chrome DevTools → Memory tab
- Network traffic: Chrome DevTools → Network → WS tab

## Production Considerations

### Before Deploying to Production:
1. [ ] Set up Redis with persistence enabled
2. [ ] Configure Redis password authentication
3. [ ] Use SSL/TLS for WebSocket connections (WSS)
4. [ ] Set up Redis cluster for high availability
5. [ ] Implement rate limiting for WebSocket messages
6. [ ] Add monitoring and alerting for Redis/Daphne
7. [ ] Test with expected user load
8. [ ] Configure proper ALLOWED_HOSTS in Django settings
9. [ ] Use production ASGI server (Daphne with systemd/supervisor)
10. [ ] Set up log rotation for Daphne logs

## Next Steps
After successful testing, implement:
1. Real-time sync indicators for module updates
2. Collaborative viewing features (show who's viewing what)
3. Live chat panel for family communication
4. Notification system for important events

---

**Last Updated:** January 9, 2025
**Version:** 1.0
