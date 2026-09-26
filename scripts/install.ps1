$ErrorActionPreference = "Stop"
$SourceRoot = Split-Path $PSScriptRoot -Parent
$Dest = Join-Path $HOME ".remote-log-explainer"
$Startup = [Environment]::GetFolderPath("Startup")
$LegacyStartup = Join-Path $Startup "RemoteLogExplainer.vbs"

Write-Host "Installing Remote Log Explainer (transparent mode)..."

# Clean up the old hidden-watcher prototype if it exists.
Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and (
        $_.CommandLine -match '\\.remote-log-explainer\\watcher\.ps1' -or
        $_.CommandLine -match 'remote_log\.py.+--follow'
    )
} | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
if (Test-Path $LegacyStartup) {
    Remove-Item $LegacyStartup -Force
    Write-Host "Removed legacy Startup hook."
}
$LegacyWatcher = Join-Path $Dest "watcher.ps1"
if (Test-Path $LegacyWatcher) {
    Remove-Item $LegacyWatcher -Force
    Write-Host "Removed legacy hidden watcher file."
}

New-Item -ItemType Directory -Force -Path $Dest | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Dest "src") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Dest "scripts") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Dest "runtime") | Out-Null

Copy-Item (Join-Path $SourceRoot "src\*") (Join-Path $Dest "src") -Force
Copy-Item (Join-Path $PSScriptRoot "start-monitor.ps1") (Join-Path $Dest "scripts\start-monitor.ps1") -Force
Copy-Item (Join-Path $PSScriptRoot "start-stream-monitor.ps1") (Join-Path $Dest "scripts\start-stream-monitor.ps1") -Force
Copy-Item (Join-Path $PSScriptRoot "run-remote.ps1") (Join-Path $Dest "scripts\run-remote.ps1") -Force
Copy-Item (Join-Path $PSScriptRoot "attach-monitor.ps1") (Join-Path $Dest "scripts\attach-monitor.ps1") -Force
Copy-Item (Join-Path $PSScriptRoot "remote-with-monitor.ps1") (Join-Path $Dest "scripts\remote-with-monitor.ps1") -Force
Copy-Item (Join-Path $PSScriptRoot "install-command-hooks.ps1") (Join-Path $Dest "scripts\install-command-hooks.ps1") -Force
Copy-Item (Join-Path $PSScriptRoot "uninstall-command-hooks.ps1") (Join-Path $Dest "scripts\uninstall-command-hooks.ps1") -Force
Copy-Item (Join-Path $PSScriptRoot "uninstall.ps1") (Join-Path $Dest "scripts\uninstall.ps1") -Force
Copy-Item (Join-Path $SourceRoot "VERSION") (Join-Path $Dest "VERSION") -Force

& (Join-Path $Dest "scripts\install-command-hooks.ps1")

Write-Host "Installed: $Dest"
Write-Host "No Startup entry was created."
Write-Host "No hidden watcher was started."
Write-Host "Both 'remote' and the normal Desktop Commander npx command now open the monitor."
