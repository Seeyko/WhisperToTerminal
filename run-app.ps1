# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'User') + ';' + [System.Environment]::GetEnvironmentVariable('Path', 'Machine')
$env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"

# Enable logging
$env:RUST_LOG = "info"

Set-Location "C:\Users\andri\IdeaProjects\WhisperToTerminal\whispervoice-native"

# Run the app
bun run tauri dev 2>&1
