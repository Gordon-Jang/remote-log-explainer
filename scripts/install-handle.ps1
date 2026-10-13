param(
    [string]$InstallRoot = (Join-Path $HOME ".remote-log-explainer")
)

$ErrorActionPreference = "Stop"
$tools = Join-Path $InstallRoot "tools"
$target = Join-Path $tools "handle64.exe"
New-Item -ItemType Directory -Force -Path $tools | Out-Null

function Test-MicrosoftHandle([string]$Path) {
    if (-not (Test-Path $Path)) { return $false }
    try {
        $sig = Get-AuthenticodeSignature $Path
        return (
            $sig.Status -eq "Valid" -and
            $sig.SignerCertificate -and
            $sig.SignerCertificate.Subject -match "Microsoft Corporation"
        )
    } catch {
        return $false
    }
}

if (Test-MicrosoftHandle $target) {
    Write-Host "Sysinternals Handle already installed and signature is valid."
    exit 0
}

$tempRoot = Join-Path $env:TEMP ("remote-log-handle-" + [Guid]::NewGuid().ToString("N"))
$zip = Join-Path $tempRoot "Handle.zip"
$extract = Join-Path $tempRoot "extract"

try {
    New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
    Write-Host "Downloading Microsoft Sysinternals Handle..."
    Invoke-WebRequest -UseBasicParsing -Uri "https://download.sysinternals.com/files/Handle.zip" -OutFile $zip
    Expand-Archive -Path $zip -DestinationPath $extract -Force

    $source = Join-Path $extract "handle64.exe"
    if (-not (Test-MicrosoftHandle $source)) {
        throw "Downloaded handle64.exe did not pass Microsoft Authenticode verification."
    }

    Copy-Item $source $target -Force
    Copy-Item (Join-Path $extract "Eula.txt") (Join-Path $tools "Handle-Eula.txt") -Force
    Write-Host "Installed verified Sysinternals Handle: $target"
} catch {
    Write-Warning ("Sysinternals Handle was not installed: " + $_.Exception.Message)
    Write-Warning "File lock checks still work for files; folder deep-scan may be slower."
} finally {
    Remove-Item $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
