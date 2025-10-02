# Gmail OAuth Log Viewer
# Run this after attempting to connect Gmail account

Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "Gmail OAuth Callback Logs" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

$logFile = "logs\django.log"

if (-not (Test-Path $logFile)) {
    Write-Host "ERROR: Log file not found at $logFile" -ForegroundColor Red
    exit 1
}

Write-Host "Searching for OAuth callback entries..." -ForegroundColor Cyan
Write-Host ""

# Get the most recent OAuth Callback Started entry and show context
$results = Select-String -Path $logFile -Pattern "OAuth Callback Started" -Context 0,60

if ($results) {
    $lastResult = $results | Select-Object -Last 1
    
    Write-Host "Most Recent OAuth Attempt:" -ForegroundColor Green
    Write-Host "-" -ForegroundColor Gray -NoNewline; Write-Host ("-" * 79) -ForegroundColor Gray
    
    # Show the matched line and context
    Write-Host $lastResult.Line -ForegroundColor Yellow
    
    foreach ($contextLine in $lastResult.Context.PostContext) {
        # Color code based on log level
        if ($contextLine -match "ERROR") {
            Write-Host $contextLine -ForegroundColor Red
        }
        elseif ($contextLine -match "WARNING") {
            Write-Host $contextLine -ForegroundColor Yellow
        }
        elseif ($contextLine -match "INFO") {
            Write-Host $contextLine -ForegroundColor White
        }
        else {
            Write-Host $contextLine -ForegroundColor Gray
        }
    }
    
    Write-Host ""
    Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 79) -ForegroundColor Cyan
    
    # Check if any Gmail accounts were created
    Write-Host ""
    Write-Host "Checking database for Gmail accounts..." -ForegroundColor Cyan
    python test_gmail_accounts.py
    
} else {
    Write-Host "No OAuth callback attempts found in logs" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "This could mean:" -ForegroundColor White
    Write-Host "  1. Django server is not running" -ForegroundColor Gray
    Write-Host "  2. You haven't tried connecting Gmail yet" -ForegroundColor Gray
    Write-Host "  3. The updated code hasn't been loaded" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Please:" -ForegroundColor White
    Write-Host "  1. Start Django server: python manage.py runserver" -ForegroundColor Gray
    Write-Host "  2. Visit: http://127.0.0.1:8000/gmail/" -ForegroundColor Gray
    Write-Host "  3. Click 'Connect Gmail Account'" -ForegroundColor Gray
    Write-Host "  4. Complete OAuth flow" -ForegroundColor Gray
    Write-Host "  5. Run this script again" -ForegroundColor Gray
}

Write-Host ""
