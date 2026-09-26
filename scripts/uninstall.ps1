$ErrorActionPreference = "SilentlyContinue"
$Dest = Join-Path $HOME ".remote-log-explainer"
$Startup = [Environment]::GetFolderPath("Startup")
$LegacyStartup = Join-Path $Startup "RemoteLogExplainer.vbs"

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
}

if (Test-Path $Dest) {
    Remove-Item $Dest -Recurse -Force
}

Write-Host "Remote Log Explainer runtime removed."
Write-Host "Source repository was left untouched."
