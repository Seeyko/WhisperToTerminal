# Install WhisperVoice to Windows Startup
# Run this script to make WhisperVoice start automatically when you log in

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$ExePath = Join-Path $ProjectDir "dist\WhisperVoice.exe"

if (-not (Test-Path $ExePath)) {
    Write-Host "Error: WhisperVoice.exe not found at $ExePath" -ForegroundColor Red
    Write-Host "Please build the application first with: pyinstaller WhisperVoice.spec"
    exit 1
}

$WshShell = New-Object -ComObject WScript.Shell
$StartupPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$ShortcutPath = "$StartupPath\WhisperVoice.lnk"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $ExePath
$Shortcut.WorkingDirectory = Join-Path $ProjectDir "dist"
$Shortcut.Description = "Whisper Voice-to-Text"
$Shortcut.Save()

Write-Host "Startup shortcut created at: $ShortcutPath" -ForegroundColor Green
Write-Host "WhisperVoice will now start automatically when you log in."
