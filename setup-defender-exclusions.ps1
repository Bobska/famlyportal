# Speed up VS Code and Django development by excluding from Windows Defender
# Run this script as Administrator in PowerShell

Write-Host "Adding Windows Defender exclusions for faster development..." -ForegroundColor Green

# Exclude the entire project folder from real-time scanning
Add-MpPreference -ExclusionPath "c:\dev-projects\famlyportal"
Write-Host "✓ Excluded project folder: c:\dev-projects\famlyportal" -ForegroundColor Cyan

# Exclude common development processes
$processes = @("Code.exe", "python.exe", "pythonw.exe", "node.exe", "git.exe")
foreach ($process in $processes) {
    Add-MpPreference -ExclusionProcess $process
    Write-Host "✓ Excluded process: $process" -ForegroundColor Cyan
}

Write-Host "`nDone! VS Code saves should be much faster now." -ForegroundColor Green
Write-Host "Restart VS Code to see the full effect." -ForegroundColor Yellow