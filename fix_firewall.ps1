# Gmail API Firewall Fix Script
# Run this as Administrator to allow Python through Windows Firewall

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "Gmail API Firewall Fix for FamlyPortal" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "To run as Administrator:" -ForegroundColor Yellow
    Write-Host "  1. Right-click PowerShell" -ForegroundColor Gray
    Write-Host "  2. Select 'Run as Administrator'" -ForegroundColor Gray
    Write-Host "  3. Navigate to project folder: cd C:\dev-projects\famlyportal" -ForegroundColor Gray
    Write-Host "  4. Run this script again: .\fix_firewall.ps1" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✓ Running as Administrator" -ForegroundColor Green
Write-Host ""

# Detect Python installation
$pythonPath = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python310\python.exe"
$pythonwPath = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python310\pythonw.exe"

Write-Host "Checking for Python installation..." -ForegroundColor Cyan

if (Test-Path $pythonPath) {
    Write-Host "✓ Found Python at: $pythonPath" -ForegroundColor Green
} else {
    Write-Host "❌ Python not found at expected location: $pythonPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please enter the full path to python.exe:" -ForegroundColor Yellow
    $pythonPath = Read-Host
    if (-not (Test-Path $pythonPath)) {
        Write-Host "❌ Invalid path. Exiting." -ForegroundColor Red
        exit 1
    }
    $pythonwPath = $pythonPath -replace "python.exe", "pythonw.exe"
}

Write-Host ""
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "Adding Firewall Rules..." -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

# Remove existing rules if they exist
Write-Host "Removing existing Python firewall rules (if any)..." -ForegroundColor Cyan
try {
    Remove-NetFirewallRule -DisplayName "Python 3.10 - FamlyPortal" -ErrorAction SilentlyContinue
    Remove-NetFirewallRule -DisplayName "Python 3.10 (windowed) - FamlyPortal" -ErrorAction SilentlyContinue
    Write-Host "✓ Cleaned up old rules" -ForegroundColor Green
} catch {
    Write-Host "⚠ No old rules to remove" -ForegroundColor Yellow
}

Write-Host ""

# Add new firewall rules
Write-Host "Adding firewall rule for python.exe..." -ForegroundColor Cyan
try {
    New-NetFirewallRule `
        -DisplayName "Python 3.10 - FamlyPortal" `
        -Description "Allow Python to access Gmail API for FamlyPortal" `
        -Direction Outbound `
        -Program $pythonPath `
        -Action Allow `
        -Profile Domain,Private,Public `
        -Protocol TCP `
        -RemotePort 443,80 `
        -Enabled True | Out-Null
    
    Write-Host "✓ Added rule for python.exe" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to add rule for python.exe: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

if (Test-Path $pythonwPath) {
    Write-Host "Adding firewall rule for pythonw.exe..." -ForegroundColor Cyan
    try {
        New-NetFirewallRule `
            -DisplayName "Python 3.10 (windowed) - FamlyPortal" `
            -Description "Allow Python (windowed) to access Gmail API for FamlyPortal" `
            -Direction Outbound `
            -Program $pythonwPath `
            -Action Allow `
            -Profile Domain,Private,Public `
            -Protocol TCP `
            -RemotePort 443,80 `
            -Enabled True | Out-Null
        
        Write-Host "✓ Added rule for pythonw.exe" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Failed to add rule for pythonw.exe (non-critical): $_" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "Verifying Firewall Rules..." -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

# Verify rules were added
$rules = Get-NetFirewallRule -DisplayName "*FamlyPortal*"
if ($rules) {
    Write-Host "✓ Firewall rules configured successfully!" -ForegroundColor Green
    Write-Host ""
    $rules | ForEach-Object {
        Write-Host "  • $($_.DisplayName)" -ForegroundColor Gray
        Write-Host "    Direction: $($_.Direction)" -ForegroundColor Gray
        Write-Host "    Action: $($_.Action)" -ForegroundColor Gray
        Write-Host "    Enabled: $($_.Enabled)" -ForegroundColor Gray
        Write-Host ""
    }
} else {
    Write-Host "❌ Failed to verify firewall rules" -ForegroundColor Red
    exit 1
}

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "Testing Network Connectivity..." -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

# Test network connectivity
Write-Host "Testing connection to Google APIs..." -ForegroundColor Cyan
$testScript = @"
import urllib.request
import sys

try:
    response = urllib.request.urlopen('https://www.googleapis.com', timeout=10)
    print(f'✓ Success! Status: {response.status}')
    sys.exit(0)
except Exception as e:
    print(f'✗ Failed: {e}')
    sys.exit(1)
"@

$testResult = & $pythonPath -c $testScript 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host $testResult -ForegroundColor Green
} else {
    Write-Host $testResult -ForegroundColor Red
    Write-Host ""
    Write-Host "⚠ Note: If test failed, you may need to:" -ForegroundColor Yellow
    Write-Host "  1. Restart your computer" -ForegroundColor Gray
    Write-Host "  2. Check your antivirus settings" -ForegroundColor Gray
    Write-Host "  3. Try using a different network (mobile hotspot)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Restart Django server (if running):" -ForegroundColor White
Write-Host "   • Press Ctrl+C in the terminal running 'make run'" -ForegroundColor Gray
Write-Host "   • Run: make run" -ForegroundColor Gray
Write-Host ""

Write-Host "2. Test Gmail sync in browser:" -ForegroundColor White
Write-Host "   • Open: http://127.0.0.1:8000/gmail/account/1/" -ForegroundColor Gray
Write-Host "   • Click 'Sync Emails' button" -ForegroundColor Gray
Write-Host "   • Should see: '✓ Sync completed! X new emails added'" -ForegroundColor Gray
Write-Host ""

Write-Host "3. If still not working, check:" -ForegroundColor White
Write-Host "   • Antivirus exclusions (see GMAIL_FIREWALL_FIX.md)" -ForegroundColor Gray
Write-Host "   • Try mobile hotspot to test if network-specific issue" -ForegroundColor Gray
Write-Host ""

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "✓ Firewall configuration complete!" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"
