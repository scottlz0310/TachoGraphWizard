param(
    [ValidateSet("copy", "symlink")]
    [string]$Mode,
    [string]$PluginBase,
    [string]$Target,
    [string]$Source,
    [switch]$NonInteractive,
    [switch]$Yes
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "install_plugin.py"

$args = @()
if ($Mode) {
    $args += "--mode"
    $args += $Mode
}
if ($PluginBase) {
    $args += "--plugin-base"
    $args += $PluginBase
}
if ($Target) {
    $args += "--target"
    $args += $Target
}
if ($Source) {
    $args += "--source"
    $args += $Source
}
if ($NonInteractive) {
    $args += "--non-interactive"
}
if ($Yes) {
    $args += "--yes"
}

if (Get-Command uv -ErrorAction SilentlyContinue) {
    & uv run python $pythonScript @args
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python $pythonScript @args
    exit $LASTEXITCODE
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $pythonScript @args
    exit $LASTEXITCODE
}

Write-Error "uv / python / py が見つかりません。"
exit 1
