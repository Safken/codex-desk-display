param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_][A-Za-z0-9_.-]*@[A-Za-z0-9][A-Za-z0-9.-]*$')][string]$Target)
$ErrorActionPreference = 'Stop'
$Host.UI.RawUI.WindowTitle = 'Codex Usage Monitor - isolated runtime and probe'
Write-Host 'Enter your Ubuntu SSH password locally.'
Write-Host 'Installs Codex 0.144.3 into ~/.local/share/codex-usage-monitor/runtime, then runs two usage reads.'
Write-Host 'The existing global Codex installation and PATH are not changed.'
$probeSource = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'discovery.py')
$probeEncoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($probeSource))
$runtimeSetup = @'
import asyncio, base64, json, pathlib, subprocess, sys
runtime = pathlib.Path.home() / '.local/share/codex-usage-monitor/runtime'
binary = runtime / 'node_modules/.bin/codex'
try:
    install = subprocess.run(['npm', 'install', '--prefix', str(runtime),
        '--no-audit', '--no-fund', '--fetch-retries=1', '--fetch-timeout=30000',
        '@openai/codex@0.144.3'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, timeout=180)
    if install.returncode:
        print(json.dumps({'status': 'runtime_install_failed', 'exit_code': install.returncode}))
        sys.exit(1)
    version = subprocess.run([str(binary), '--version'], capture_output=True, text=True, timeout=15)
    if version.returncode or version.stdout.strip() != 'codex-cli 0.144.3':
        print(json.dumps({'status': 'runtime_version_check_failed'}))
        sys.exit(1)
except (OSError, subprocess.TimeoutExpired):
    print(json.dumps({'status': 'runtime_setup_failed_or_timed_out'}))
    sys.exit(1)
namespace = {'__name__': 'discovery_import'}
exec(base64.b64decode('PROBE_BASE64'), namespace)
results = []
for attempt in range(2):
    results.append(asyncio.run(namespace['probe']([str(binary), 'app-server'],
        timeout=30, include_tokens=True, diagnostics=True)))
print(json.dumps({'runtime_version': '0.144.3', 'observations': results}, indent=2))
sys.exit(0 if all(r['status'] == 'ok' for r in results) else 1)
'@
$runtimeSetup = $runtimeSetup.Replace('PROBE_BASE64', $probeEncoded)
$runtimeSetup | & ssh -o ConnectTimeout=10 $Target 'python3 -' | Tee-Object -FilePath (Join-Path $PSScriptRoot 'ubuntu-runtime-probe.txt')
$runtimeExit = $LASTEXITCODE
Write-Host "SSH/runtime probe exit code: $runtimeExit"
Write-Host 'You can close this window when the check finishes.'
