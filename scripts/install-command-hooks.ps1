$ErrorActionPreference = "Stop"

$npx = (Get-Command npx.ps1 -CommandType ExternalScript -ErrorAction Stop | Select-Object -First 1).Source
$nodeDir = Split-Path $npx -Parent
$backup = Join-Path $nodeDir "npx.remote-log-backup.ps1"
$remoteCmd = Join-Path $nodeDir "remote.cmd"

$text = Get-Content $npx -Raw
$marker = "# Remote Log Explainer hook"

if ($text -notmatch [regex]::Escape($marker)) {
    Copy-Item $npx $backup -Force
    $needle = "#!/usr/bin/env pwsh" + [Environment]::NewLine
    $hook = @'
#!/usr/bin/env pwsh

# Remote Log Explainer hook: only intercept Desktop Commander Remote.
if (
  $args.Count -eq 2 -and
  $args[0] -match '^@wonderwhy-er/desktop-commander(?:@latest)?$' -and
  $args[1] -eq 'remote'
) {
  $REMOTE_LOG_LAUNCHER = Join-Path $HOME '.remote-log-explainer\scripts\remote-with-monitor.ps1'
  if (Test-Path $REMOTE_LOG_LAUNCHER) {
    & $REMOTE_LOG_LAUNCHER
    exit $LASTEXITCODE
  }
}
'@
    $body = $text.Substring($text.IndexOf([Environment]::NewLine) + [Environment]::NewLine.Length).TrimStart()
    Set-Content -Path $npx -Value ($hook.TrimEnd() + [Environment]::NewLine + [Environment]::NewLine + $body) -Encoding UTF8
}

$remoteText = @'
@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%USERPROFILE%\.remote-log-explainer\scripts\remote-with-monitor.ps1" %*
'@
Set-Content -Path $remoteCmd -Value $remoteText -Encoding ASCII

Write-Host "Command hooks installed:"
Write-Host "  npx @wonderwhy-er/desktop-commander@latest remote"
Write-Host "  remote"
Write-Host "Both now start Desktop Commander Remote + Remote Monitor."
