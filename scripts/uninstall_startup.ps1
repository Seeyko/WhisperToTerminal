# Remove WhisperVoice from Windows Startup
# Run this script to stop WhisperVoice from starting automatically

$ShortcutPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\WhisperVoice.lnk"

if (Test-Path $ShortcutPath) {
    Remove-Item $ShortcutPath
    Write-Host "Startup shortcut removed." -ForegroundColor Green
    Write-Host "WhisperVoice will no longer start automatically."
} else {
    Write-Host "No startup shortcut found." -ForegroundColor Yellow
}
