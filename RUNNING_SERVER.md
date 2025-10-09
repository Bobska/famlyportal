# FamlyPortal - Running the Development Server

## Quick Start Guide

### 🚀 Option 1: Simple Development (No WebSockets)
**Best for:** General development, testing non-WebSocket features

**Windows:**
```bash
# Double-click this file or run in terminal:
start_server_simple.bat

# OR use the virtual environment directly:
.venv\Scripts\activate
python manage.py runserver
```

**Mac/Linux:**
```bash
source .venv/bin/activate
python manage.py runserver
```

**Using Makefile:**
```bash
make run
```

**Access at:** http://127.0.0.1:8000

⚠️ **Note:** Live crew status and real-time features won't work with this option.

---

### 📡 Option 2: Full Development (With WebSockets)
**Best for:** Testing real-time features (live crew status, collaborative viewing, chat)

**Windows:**
```bash
# Double-click this file or run in terminal:
start_server.bat

# OR manually:
.venv\Scripts\activate
python manage.py collectstatic --noinput
python -m daphne -b 127.0.0.1 -p 8000 famlyportal.asgi:application
```

**Mac/Linux:**
```bash
source .venv/bin/activate
python manage.py collectstatic --noinput
python -m daphne -b 127.0.0.1 -p 8000 famlyportal.asgi:application
```

**Using Makefile:**
```bash
make ws
```

**Access at:** http://127.0.0.1:8000

✅ **Includes:** Live crew presence, WebSocket connections, real-time updates

---

## 📝 Understanding the Difference

### Standard Django Server (`runserver`)
- ✅ Fast startup
- ✅ Auto-reload on code changes
- ✅ Built-in static file serving
- ❌ No WebSocket support
- ❌ Real-time features disabled

### Daphne ASGI Server (WebSocket Support)
- ✅ Full WebSocket support
- ✅ Real-time features enabled
- ✅ Production-like environment
- ❌ Manual static file collection needed
- ❌ No auto-reload (must restart after code changes)

---

## 🔄 Development Workflow

### Regular Feature Development
1. Use **standard server** for most development:
   ```bash
   python manage.py runserver
   ```
2. Code changes auto-reload
3. No need to collect static files

### Testing Real-Time Features
1. Switch to **Daphne server** when testing WebSocket features:
   ```bash
   make ws
   # or
   start_server.bat
   ```
2. Test live crew status, collaborative features
3. Remember to restart server after code changes

### Before Committing
1. Test with **Daphne server** to ensure WebSocket features work
2. Run system check:
   ```bash
   python manage.py check
   ```
3. Run tests:
   ```bash
   python manage.py test
   ```

---

## 🛠️ Common Commands

### Static Files
```bash
# Collect all static files (required for Daphne)
python manage.py collectstatic --noinput

# Clear and re-collect static files
python manage.py collectstatic --noinput --clear
```

### Database
```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Testing
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts
python manage.py test timesheet

# System check
python manage.py check
```

---

## 🐛 Troubleshooting

### Issue: "No module named daphne"
**Solution:**
```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: Static files not loading (404 errors)
**Solution:**
```bash
python manage.py collectstatic --noinput --clear
```

### Issue: WebSocket connection fails
**Causes:**
1. Using standard `runserver` instead of Daphne
2. Wrong URL (should be `ws://` not `http://`)

**Solution:**
- Use Daphne server: `make ws` or `start_server.bat`
- Check browser console for WebSocket errors

### Issue: "Port 8000 already in use"
**Solution:**
```bash
# Kill existing process (Windows)
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Or use different port
python manage.py runserver 8001
python -m daphne -b 127.0.0.1 -p 8001 famlyportal.asgi:application
```

---

## 📦 Available Scripts

### Windows Batch Files
- `start_server_simple.bat` - Standard Django server
- `start_server.bat` - Daphne with WebSocket support
- `start_redis.bat` - Start Redis (for production-like testing)

### Makefile Commands
```bash
make help        # Show all available commands
make run         # Standard development server
make ws          # WebSocket-enabled server
make dev         # Development server on port 8000
make check       # Run Django system checks
make test        # Run all tests
make migrate     # Run database migrations
```

---

## 🌐 Production Deployment

For production, you'll want to:
1. Use Redis instead of InMemoryChannelLayer
2. Use a proper ASGI server (Daphne, Uvicorn)
3. Use a reverse proxy (Nginx)
4. Enable SSL/TLS for secure WebSockets (WSS)
5. Set up systemd/supervisor for process management

See `WEBSOCKET_TESTING_GUIDE.md` for more details.

---

## 💡 Quick Reference

| Feature | Standard Server | Daphne Server |
|---------|----------------|---------------|
| **Command** | `python manage.py runserver` | `python -m daphne ...` |
| **Shortcut** | `make run` | `make ws` |
| **Port** | 8000 | 8000 |
| **Auto-reload** | ✅ Yes | ❌ No |
| **Static files** | Auto-served | Must collect |
| **WebSockets** | ❌ No | ✅ Yes |
| **Real-time features** | ❌ Disabled | ✅ Enabled |
| **Development speed** | ⚡ Fast | 🐌 Slower |
| **Production-like** | ❌ No | ✅ Yes |

---

**Recommendation:** Use `python manage.py runserver` for day-to-day development, and switch to `make ws` when testing real-time features!
