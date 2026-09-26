$ErrorActionPreference = "SilentlyContinue"

$npx = (Get-Command npx.ps1 -CommandType ExternalScript -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if ($npx) {
    $nodeDir = Split-Path $npx -Parent
    $backup = Join-Path $nodeDir "npx.remote-log-backup.ps1"
    $remoteCmd = Join-Path $nodeDir "remote.cmd"

    if (Test-Path $backup) {
        Copy-Item $backup $npx -Force
        Remove-Item $backup -Force
        Write-Host "Restored original npx.ps1"
    }

    if (Test-Path $remoteCmd) {
        $remoteText = Get-Content $remoteCmd -Raw
        if ($remoteText -match 'remote-log-explainer') {
            Remove-Item $remoteCmd -Force
            Write-Host "Removed remote.cmd"
        }
    }
}
