param(
    [Parameter(Mandatory = $true)]
    [int]$RemotePid,
    [string]$InstallRoot = (Join-Path $HOME ".remote-log-explainer")
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
try { chcp 65001 | Out-Null } catch {}
$Host.UI.RawUI.WindowTitle = "Remote Monitor"
& (Join-Path $InstallRoot "scripts\console-style.ps1")

$script = Join-Path $InstallRoot "src\remote_log.py"
$status = Join-Path $InstallRoot "runtime\status.json"

if (-not (Test-Path $script)) {
    Write-Host "Remote Log Explainer not installed: $script"
    exit 1
}

python $script --follow --session-pid $RemotePid --replay 3 --status $status
