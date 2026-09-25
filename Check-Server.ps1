param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_][A-Za-z0-9_.-]*@[A-Za-z0-9][A-Za-z0-9.-]*$')][string]$Target)
$ErrorActionPreference = 'Stop'
$Host.UI.RawUI.WindowTitle = 'Codex Usage Monitor - Ubuntu access check'
Write-Host 'Enter your Ubuntu SSH password at the SSH prompt. It is not saved.'
Write-Host 'This check only reads hostname, OS, and installed tool versions.'
$serverCheck = 'printf "HOST: "; hostname; uname -sr; printf "PYTHON: "; python3 --version 2>/dev/null; printf "NODE: "; node --version 2>/dev/null; printf "CODEX: "; if command -v codex >/dev/null 2>&1; then codex --version; else printf "not on PATH\n"; fi'
& ssh -o ConnectTimeout=10 $Target $serverCheck | Tee-Object -FilePath (Join-Path $PSScriptRoot 'server-preflight.txt')
$checkExit = $LASTEXITCODE
Write-Host "SSH exit code: $checkExit"
Write-Host 'You can close this window after the check finishes.'
