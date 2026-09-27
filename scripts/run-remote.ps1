param(
    [Parameter(Mandatory = $true)]
    [string]$SessionId,
    [string]$InstallRoot = (Join-Path $HOME ".remote-log-explainer")
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
try { chcp 65001 | Out-Null } catch {}
$Host.UI.RawUI.WindowTitle = "Desktop Commander Remote"
& (Join-Path $InstallRoot "scripts\console-style.ps1") -ScrollbackLines 1000

$runner = Join-Path $InstallRoot "src\remote_runner.py"
$streamDir = Join-Path $InstallRoot "runtime\streams"
$log = Join-Path $streamDir ($SessionId + ".log")
$meta = Join-Path $streamDir ($SessionId + ".json")

New-Item -ItemType Directory -Force -Path $streamDir | Out-Null

Write-Host "Desktop Commander Remote"
Write-Host "Session: $SessionId"
Write-Host "Log: $log"
Write-Host ("-" * 60)

python $runner --log $log --meta $meta
$code = $LASTEXITCODE
Write-Host ("Remote exited with code " + $code)
exit $code
