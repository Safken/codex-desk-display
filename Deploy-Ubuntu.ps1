param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_][A-Za-z0-9_.-]*@[A-Za-z0-9][A-Za-z0-9.-]*$')][string]$Target,
    [ValidatePattern('^[0-9.]+$')][string]$BindAddress = '127.0.0.1',
    [ValidatePattern('^[0-9./]+$')][string]$AllowedNetwork = '127.0.0.0/8',
    [ValidatePattern('^[A-Za-z0-9_+/-]+$')][string]$TimeZone = 'UTC',
    [ValidateRange(1024,65535)][int]$Port = 8790
)
$ErrorActionPreference = 'Stop'
$Host.UI.RawUI.WindowTitle = 'Codex Usage Monitor - deploy collector and dashboard'
Write-Host 'This installs the collector as a user service. Existing server configuration is preserved.'
Write-Host 'Enter SSH passwords locally. Sudo may ask once to enable startup without an open login session.'
& python (Join-Path $PSScriptRoot 'tools\package.py')
if ($LASTEXITCODE) { throw 'Packaging failed' }
& scp (Join-Path $PSScriptRoot 'dist\codex-usage-monitor.zip') "${Target}:codex-usage-monitor.zip"
if ($LASTEXITCODE) { throw 'Upload failed' }
$remote = 'mkdir -p "$HOME/.local/share/codex-usage-monitor/staging" && python3 -m zipfile -e "$HOME/codex-usage-monitor.zip" "$HOME/.local/share/codex-usage-monitor/staging" && bash "$HOME/.local/share/codex-usage-monitor/staging/deploy/install-ubuntu.sh"'
$remote += " $BindAddress $AllowedNetwork $TimeZone $Port"
# Do not capture terminal output: SSH/sudo authentication stays owner-operated.
& ssh -t -o ConnectTimeout=10 $Target $remote
Write-Host "Deployment exit code: $LASTEXITCODE"
Write-Host 'The installer verifies live data and restarts the service to check recovery.'
