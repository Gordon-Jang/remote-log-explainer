param(
    [string]$InstallRoot = (Join-Path $HOME ".remote-log-explainer")
)

$ErrorActionPreference = "Stop"

function Get-RemoteProcess {
    $items = Get-CimInstance Win32_Process | Where-Object {
        $c = $_.CommandLine
        $c -and (
            $c -match '(?i)@wonderwhy-er[/\\]desktop-commander(@latest)?\s+remote' -or
            $c -match '(?i)desktop-commander[/\\]dist[/\\]index\.js[" ]+\s*remote' -or
            $c -match '(?i)desktop-commander(?:\.cmd)?\s+remote'
        )
    }
    return $items | Sort-Object ProcessId | Select-Object -First 1
}

$remote = Get-RemoteProcess
if (-not $remote) {
    Write-Host "No running Desktop Commander Remote session was found."
    exit 2
}

$monitorScript = Join-Path $InstallRoot "src\remote_log.py"
$existing = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and
    $_.CommandLine -match [Regex]::Escape($monitorScript) -and
    $_.CommandLine -match '(--follow|--stream-log)'
} | Select-Object -First 1

if ($existing) {
    Write-Host "Remote Monitor is already running (PID $($existing.ProcessId))."
    exit 0
}

$startScript = Join-Path $InstallRoot "scripts\start-monitor.ps1"
if (-not (Test-Path $startScript)) {
    Write-Host "Missing monitor launcher: $startScript"
    exit 3
}

$wt = Get-Command wt.exe -ErrorAction SilentlyContinue
if ($wt) {
    & $wt.Source -w new new-tab powershell.exe -NoProfile -ExecutionPolicy Bypass -File $startScript -RemotePid $remote.ProcessId -InstallRoot $InstallRoot
} else {
    $argLine = '-NoProfile -ExecutionPolicy Bypass -File "' + $startScript + '" -RemotePid ' +
        [string]$remote.ProcessId + ' -InstallRoot "' + $InstallRoot + '"'
    Start-Process -FilePath "powershell.exe" -ArgumentList $argLine | Out-Null
}

Write-Host "Opened Remote Monitor for Remote PID $($remote.ProcessId)."
