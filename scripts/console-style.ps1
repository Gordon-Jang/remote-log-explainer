$ErrorActionPreference = "SilentlyContinue"

try {
    $raw = $Host.UI.RawUI
    $raw.BackgroundColor = "Black"
    $raw.ForegroundColor = "Gray"

    Clear-Host

    $raw.BackgroundColor = "Black"
    $raw.ForegroundColor = "Gray"
} catch {
    try {
        $Host.PrivateData.ErrorForegroundColor = "Red"
        $Host.PrivateData.WarningForegroundColor = "Yellow"
    } catch {}
}
