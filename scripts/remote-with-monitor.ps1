param(
    [string]$InstallRoot = (Join-Path $HOME ".remote-log-explainer")
)

$ErrorActionPreference = "Stop"

$existing = Get-CimInstance Win32_Process | Where-Object {
    $c = $_.CommandLine
    $c -and (
        $c -match '(?i)@wonderwhy-er[/\\]desktop-commander(@latest)?\s+remote' -or
        $c -match '(?i)desktop-commander(?:\.cmd)?\s+remote'
    )
} | Sort-Object ProcessId | Select-Object -First 1

if ($existing) {
    Write-Host "Remote is already running (PID $($existing.ProcessId)); attaching monitor."
    & (Join-Path $InstallRoot "scripts\attach-monitor.ps1") -InstallRoot $InstallRoot
    exit $LASTEXITCODE
}

$sessionId = (Get-Date -Format "yyyyMMdd-HHmmss") + "-" + ([Guid]::NewGuid().ToString("N").Substring(0, 6))
$streamDir = Join-Path $InstallRoot "runtime\streams"
$log = Join-Path $streamDir ($sessionId + ".log")
$runScript = Join-Path $InstallRoot "scripts\run-remote.ps1"
$monitorScript = Join-Path $InstallRoot "scripts\start-stream-monitor.ps1"

New-Item -ItemType Directory -Force -Path $streamDir | Out-Null

$wt = Get-Command wt.exe -ErrorAction SilentlyContinue
if ($wt) {
    & $wt.Source -w new new-tab powershell.exe -NoExit -NoProfile -ExecutionPolicy Bypass -File $runScript -SessionId $sessionId -InstallRoot $InstallRoot
    Start-Sleep -Milliseconds 500
    & $wt.Source -w new new-tab powershell.exe -NoProfile -ExecutionPolicy Bypass -File $monitorScript -LogPath $log -InstallRoot $InstallRoot
    Write-Host "Opened Desktop Commander Remote + Remote Monitor in Windows Terminal."
} else {
    $remoteArgs = '-NoExit -NoProfile -ExecutionPolicy Bypass -File "' + $runScript +
        '" -SessionId "' + $sessionId + '" -InstallRoot "' + $InstallRoot + '"'
    $monitorArgs = '-NoProfile -ExecutionPolicy Bypass -File "' + $monitorScript +
        '" -LogPath "' + $log + '" -InstallRoot "' + $InstallRoot + '"'

    Start-Process -FilePath "powershell.exe" -ArgumentList $remoteArgs | Out-Null
    Start-Sleep -Milliseconds 400
    Start-Process -FilePath "powershell.exe" -ArgumentList $monitorArgs | Out-Null
    Write-Host "Windows Terminal was not found; using classic console fallback."
}

Write-Host "Session: $sessionId"
