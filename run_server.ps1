# FamlyPortal Development Server Launcher
# PowerShell script for Windows

param(
    [switch]$WebSocket = $false,
    [switch]$Simple = $false,
    [switch]$Help = $false
)

function Show-Help {
    Write-Host ""
    Write-Host "FamlyPortal Development Server" -ForegroundColor Cyan
    Write-Host "===============================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\run_server.ps1              # Standard server (no WebSockets)"
    Write-Host "  .\run_server.ps1 -WebSocket   # Server with WebSocket support"
    Write-Host "  .\run_server.ps1 -Simple      # Same as no arguments"
    Write-Host "  .\run_server.ps1 -Help        # Show this help"
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -WebSocket   Enable WebSocket support (real-time features)"
    Write-Host "  -Simple      Standard Django server (faster, no real-time)"
    Write-Host "  -Help        Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  Quick development:"
    Write-Host "    .\run_server.ps1"
    Write-Host ""
    Write-Host "  Testing real-time features:"
    Write-Host "    .\run_server.ps1 -WebSocket"
    Write-Host ""
}

if ($Help) {
    Show-Help
    exit 0
}

# Check if virtual environment exists
if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FamlyPortal Development Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1

if ($WebSocket) {
    Write-Host "📡 WebSocket Support: ENABLED" -ForegroundColor Green
    Write-Host ""
    Write-Host "Collecting static files..." -ForegroundColor Yellow
    python manage.py collectstatic --noinput
    
    Write-Host ""
    Write-Host "🚀 Starting Daphne ASGI server..." -ForegroundColor Green
    Write-Host "Server will be available at: http://127.0.0.1:8000" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""
    
    python -m daphne -b 127.0.0.1 -p 8000 famlyportal.asgi:application
} else {
    Write-Host "⚡ Quick Development Mode" -ForegroundColor Green
    Write-Host "WebSocket features will not work in this mode" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🚀 Starting Django development server..." -ForegroundColor Green
    Write-Host "Server will be available at: http://127.0.0.1:8000" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""
    
    python manage.py runserver
}
