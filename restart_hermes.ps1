# Restart Hermes gateway with new HERMES_HOME (P:\hermes)
$ErrorActionPreference = 'SilentlyContinue'
Start-Sleep -Seconds 15

# Kill old gateway processes (hermes gateway running from old C: home)
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*hermes.exe*"gateway"*' -or $_.CommandLine -like '*hermes.exe* gateway*' } | ForEach-Object {
    Write-Output ("Killing PID " + $_.ProcessId)
    Stop-Process -Id $_.ProcessId -Force
}
# Also kill the exact PIDs recorded in gateway.pid
Stop-Process -Id 1700 -Force
Stop-Process -Id 24196 -Force
Start-Sleep -Seconds 4

# Safety: kill anything still matching
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*hermes*gateway*' } | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force
}
Start-Sleep -Seconds 2

# Start new gateway with P: home
$env:HERMES_HOME = 'P:\hermes'
Set-Location 'D:\hermes-agent'
Start-Process -FilePath 'D:\hermes-agent\.venv\Scripts\hermes.exe' -ArgumentList 'gateway' -WindowStyle Hidden
Write-Output "New gateway started with HERMES_HOME=$env:HERMES_HOME"
