param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_][A-Za-z0-9_.-]*@[A-Za-z0-9][A-Za-z0-9.-]*$')][string]$Target)
$ErrorActionPreference = 'Stop'
$Host.UI.RawUI.WindowTitle = 'Codex Usage Monitor - sign in on Ubuntu'
Write-Host 'Enter your Ubuntu SSH password, then follow the Codex browser/device-code instructions.'
Write-Host 'Use your main ChatGPT account. Do not paste the password or device code into chat.'
Write-Host 'Login output is shown only in this terminal and is not written to a project file.'
& ssh -t -o ConnectTimeout=10 $Target '~/.local/share/codex-usage-monitor/runtime/node_modules/.bin/codex login --device-auth'
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Codex login did not succeed. Leave the account probe for after login is resolved.'
    exit 1
}
Write-Host 'Login succeeded. Enter the Ubuntu SSH password once more for the read-only usage probe.'
& (Join-Path $PSScriptRoot 'Run-UbuntuProbe.ps1') -Target $Target
