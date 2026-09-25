[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^COM[1-9][0-9]*$')][string]$Port,
    [ValidateSet('release','demo')][string]$Variant = 'demo'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$relative = "firmware/build/$Variant/CodexDesk.ino.merged.bin"
$binary = Join-Path $root $relative
$manifest = Join-Path $root 'firmware/build/SHA256SUMS.txt'
if (!(Test-Path -LiteralPath $binary) -or !(Test-Path -LiteralPath $manifest)) {
    throw 'Download the esp32-firmware artifact from a successful GitHub Actions run first. See firmware/README.md.'
}
$entry = Get-Content -LiteralPath $manifest | Where-Object { ($_ -split '\s+',2)[1] -eq $relative }
if (@($entry).Count -ne 1) { throw 'Missing or ambiguous firmware checksum' }
$expected = ($entry -split '\s+',2)[0]
$hasher = [Security.Cryptography.SHA256]::Create()
$stream = [IO.File]::OpenRead($binary)
try { $actual = [BitConverter]::ToString($hasher.ComputeHash($stream)).Replace('-', '') }
finally { $stream.Dispose(); $hasher.Dispose() }
if ($actual -ine $expected) { throw 'Firmware checksum mismatch; refusing to flash' }
$python = Join-Path $root '.venv/Scripts/python.exe'
if (!(Test-Path -LiteralPath $python)) { $python = 'python' }
if ($PSCmdlet.ShouldProcess($Port, "Write verified $Variant full-flash image (replaces saved device settings)")) {
    & $python -m esptool --chip esp32s3 --port $Port --baud 460800 write_flash 0x0 $binary
    if ($LASTEXITCODE) { throw 'Firmware upload failed' }
}
