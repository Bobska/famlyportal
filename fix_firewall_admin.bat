@echo off
echo ========================================
echo Gmail API Firewall Fix - FamlyPortal
echo ========================================
echo.
echo This script will add Windows Firewall rules to allow
echo Python to access Gmail API servers.
echo.
echo Administrator privileges required!
echo.
pause

echo.
echo Adding firewall rules...
echo.

PowerShell -Command "New-NetFirewallRule -DisplayName 'Python 3.10 - FamlyPortal Gmail' -Direction Outbound -Program 'C:\Users\Dmitry\AppData\Local\Programs\Python\Python310\python.exe' -Action Allow -Profile Domain,Private,Public -Protocol TCP -RemotePort 443,80 -Enabled True"

if %errorlevel% == 0 (
    echo.
    echo [SUCCESS] Firewall rule added successfully!
    echo.
    echo Next steps:
    echo 1. Restart Django server (Ctrl+C then: make run^)
    echo 2. Go to: http://127.0.0.1:8000/gmail/account/1/
    echo 3. Click "Sync Emails" button
    echo.
) else (
    echo.
    echo [ERROR] Failed to add firewall rule.
    echo.
    echo Make sure you ran this script as Administrator:
    echo 1. Right-click "fix_firewall_admin.bat"
    echo 2. Select "Run as administrator"
    echo.
)

pause
