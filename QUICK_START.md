# 🚀 Quick Start - Running FamlyPortal

## The Simple Answer

### For All Development (Just Use This! 👍)
```bash
make run
```
That's it! Open http://127.0.0.1:8000

✅ **Has auto-reload AND WebSocket support!**

---

## Wait, What About WebSockets?

**Good news!** Since Django Channels is installed, `make run` **automatically uses Daphne** with full WebSocket support. You get:

- ✅ **Auto-reload** - Code changes apply automatically
- ✅ **WebSocket support** - Live crew status works
- ✅ **Fast startup** - No collectstatic needed
- ✅ **All features enabled**

**There's no separate "WebSocket mode" anymore!** 🎉

---

## Alternative Commands

All of these work identically:

```powershell
# Recommended (default port 8000)
make run

# Alternative (explicit port 8000)
make dev

# Direct Django command
python manage.py runserver
```

---

## When to Use `make ws`

The `make ws` command is now only for **production-like testing**:

```powershell
make ws
```

**Use this when:**
- Testing static file collection for deployment
- Simulating production Daphne behavior
- Debugging deployment issues

**Trade-offs:**
- ❌ No auto-reload (must restart manually)
- ✅ More production-like
- ✅ Tests collectstatic process

**For daily development: Just use `make run`!**

---

## All Available Commands

```powershell
# Development
make run         # Start development server (recommended)
make dev         # Start development server on port 8000
make ws          # Production-like mode (no auto-reload)

# Database
make migrate     # Run migrations
make reset       # Reset database (WARNING: deletes data)

# Testing & Checks
make test        # Run all tests
make check       # Django system checks

# Utilities
make help        # Show all commands
make info        # Environment information
make clean       # Clean cache files
```

---

## Common Tasks

### First Time Setup
```powershell
make setup       # Install dependencies + migrations + superuser
```

### Daily Development
```powershell
make run         # Start server
# Edit code (auto-reloads automatically)
# Test in browser at http://127.0.0.1:8000
```

### After Pulling Changes
```powershell
make migrate     # Apply new migrations
make run         # Start server
```

### Before Deployment
```powershell
make ws          # Test production-like mode
make check       # Verify configuration
make test        # Run test suite
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'daphne'"
**Solution:** Make sure you're using the Makefile commands (they use the virtual environment):
```powershell
make run   # ✅ Uses .venv/Scripts/python.exe
```

Not:
```powershell
python manage.py runserver  # ❌ Might use system Python
```

### Server won't start
```powershell
# Check for errors
make check

# Check environment
make info

# Clean and retry
make clean
make run
```

### WebSocket features not working
**They should work automatically with `make run`!** If not:
1. Check browser console for connection errors
2. Verify Daphne is running (should say "Starting ASGI/Daphne")
3. Check that `channels` is in `requirements.txt`

---

## See Also

- **MAKEFILE_TEST_RESULTS.md** - Complete testing documentation
- **RUNNING_SERVER.md** - Detailed server documentation
- **Makefile** - All available commands (`make help`)

---

**TL;DR:** Just use `make run` - it has everything you need! 🎯
