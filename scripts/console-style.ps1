$ErrorActionPreference = "SilentlyContinue"

try {
    $raw = $Host.UI.RawUI
    $raw.BackgroundColor = "Black"
    $raw.ForegroundColor = "Gray"

    # Windows Terminal uses a dynamic scrollback buffer. Set its default
    # colors with OSC so untouched cells are black too, without Clear-Host
    # and without creating blank scrollback rows.
    if ($env:WT_SESSION) {
        $esc = [char]27
        $bel = [char]7
        [Console]::Write($esc + "]11;#000000" + $bel)
        [Console]::Write($esc + "]10;#C0C0C0" + $bel)
    }

    $raw.BackgroundColor = "Black"
    $raw.ForegroundColor = "Gray"
} catch {
    try {
        $Host.PrivateData.ErrorForegroundColor = "Red"
        $Host.PrivateData.WarningForegroundColor = "Yellow"
    } catch {}
}
