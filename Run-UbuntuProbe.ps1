param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_][A-Za-z0-9_.-]*@[A-Za-z0-9][A-Za-z0-9.-]*$')][string]$Target)
$ErrorActionPreference = 'Stop'
$Host.UI.RawUI.WindowTitle = 'Codex Usage Monitor - read-only account probe'
Write-Host 'Enter your Ubuntu SSH password at the prompt. It is not saved.'
Write-Host 'The Python probe is streamed to Ubuntu and runs without installing project files.'
Write-Host 'It reads usage only; no model turn or credit reset is requested.'
Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'discovery.py') | & ssh -o ConnectTimeout=10 $Target 'python3 - --codex ~/.local/share/codex-usage-monitor/runtime/node_modules/.bin/codex --include-tokens --diagnostics' | Tee-Object -FilePath (Join-Path $PSScriptRoot 'ubuntu-probe.txt')
$probeExit = $LASTEXITCODE
Write-Host "SSH/probe exit code: $probeExit"
Write-Host 'You can close this window after the probe finishes.'
