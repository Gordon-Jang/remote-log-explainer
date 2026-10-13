$ErrorActionPreference = "Stop"

$npx = (Get-Command npx.ps1 -CommandType ExternalScript -ErrorAction Stop | Select-Object -First 1).Source
$nodeDir = Split-Path $npx -Parent
$backup = Join-Path $nodeDir "npx.remote-log-backup.ps1"
$remoteCmd = Join-Path $nodeDir "remote.cmd"
$lockWhoCmd = Join-Path $nodeDir "lockwho.cmd"

$text = Get-Content $npx -Raw
$marker = "# Remote Log Explainer hook:"

# If npm/Node replaced npx.ps1, save the new pristine file as the uninstall backup.
if ($text -notmatch [regex]::Escape($marker)) {
    Copy-Item $npx $backup -Force
}

# Remove any older Remote Log Explainer hook before inserting the current one.
$oldHookPattern = '(?s)\r?\n?# Remote Log Explainer hook:.*?(?=\$NODE_EXE=)'
$text = [regex]::Replace($text, $oldHookPattern, '')

$hook = @'
# Remote Log Explainer hook: intercept only Desktop Commander Remote.
$REMOTE_LOG_PACKAGE = $null
foreach ($REMOTE_LOG_ARG in $args) {
  if ($REMOTE_LOG_ARG -match '^@wonderwhy-er/desktop-commander(?:@[^\s]+)?$') {
    $REMOTE_LOG_PACKAGE = $REMOTE_LOG_ARG
    break
  }
}

if (
  $REMOTE_LOG_PACKAGE -and
  $args.Count -ge 2 -and
  $args[$args.Count - 1] -eq 'remote'
) {
  $REMOTE_LOG_LAUNCHER = Join-Path $HOME '.remote-log-explainer\scripts\remote-with-monitor.ps1'
  if (Test-Path $REMOTE_LOG_LAUNCHER) {
    & $REMOTE_LOG_LAUNCHER -PackageSpec $REMOTE_LOG_PACKAGE
    exit $LASTEXITCODE
  }
}
'@

$firstNewline = $text.IndexOf([Environment]::NewLine)
if ($firstNewline -lt 0) {
    throw "Unexpected npx.ps1 format."
}
$header = $text.Substring(0, $firstNewline)
$body = $text.Substring($firstNewline + [Environment]::NewLine.Length).TrimStart()
$newText = $header + [Environment]::NewLine + [Environment]::NewLine +
    $hook.Trim() + [Environment]::NewLine + [Environment]::NewLine + $body
Set-Content -Path $npx -Value $newText -Encoding UTF8

$remoteText = @'
@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%USERPROFILE%\.remote-log-explainer\scripts\remote-with-monitor.ps1"
'@
Set-Content -Path $remoteCmd -Value $remoteText -Encoding ASCII

$lockWhoText = @'
@echo off
python.exe "%USERPROFILE%\.remote-log-explainer\src\lock_inspector.py" %*
'@
Set-Content -Path $lockWhoCmd -Value $lockWhoText -Encoding ASCII

Write-Host "Command hooks installed:"
Write-Host "  remote"
Write-Host "  lockwho <file-or-folder>"
Write-Host "  npx @wonderwhy-er/desktop-commander@latest remote"
Write-Host "  npx --yes @wonderwhy-er/desktop-commander@<version> remote"
Write-Host "All launch paths use npx --yes internally to avoid install-confirmation hangs."
