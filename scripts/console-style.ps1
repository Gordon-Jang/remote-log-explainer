param(
    [int]$ScrollbackLines = 1000
)

$ErrorActionPreference = "SilentlyContinue"

try {
    $raw = $Host.UI.RawUI
    $raw.BackgroundColor = "Black"
    $raw.ForegroundColor = "Gray"

    Clear-Host

    $window = $raw.WindowSize
    $buffer = $raw.BufferSize
    $targetHeight = [Math]::Max([int]$window.Height, $ScrollbackLines)

    $buffer.Width = [Math]::Max([int]$buffer.Width, [int]$window.Width)
    $buffer.Height = $targetHeight
    $raw.BufferSize = $buffer

    $raw.BackgroundColor = "Black"
    $raw.ForegroundColor = "Gray"
} catch {
    try {
        $Host.PrivateData.ErrorForegroundColor = "Red"
        $Host.PrivateData.WarningForegroundColor = "Yellow"
    } catch {}
}
