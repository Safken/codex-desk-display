param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_][A-Za-z0-9_.-]*@[A-Za-z0-9][A-Za-z0-9.-]*$')][string]$Target)
$ErrorActionPreference = 'Stop'
$Host.UI.RawUI.WindowTitle = 'Codex Usage Monitor - server preflight and daily token check'
Write-Host 'Enter your SSH password locally. Read-only check of ports, service support, and token data.'
$source = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((Get-Content -Raw (Join-Path $PSScriptRoot 'discovery.py'))))
$code = @'
import asyncio, base64, getpass, json, os, pathlib, socket, subprocess
namespace = {'__name__': 'discovery_import'}
exec(base64.b64decode('SOURCE_BASE64'), namespace)
binary = pathlib.Path.home()/'.local/share/codex-usage-monitor/runtime/node_modules/.bin/codex'
result = asyncio.run(namespace['probe']([str(binary), 'app-server'], include_tokens=True, diagnostics=True, track_account=True))
result.pop('account_fingerprint', None)
print(json.dumps({'probe': result}, indent=2))
config_path = pathlib.Path.home()/'.local/share/codex-usage-monitor/config.json'
if config_path.exists():
    config = json.loads(config_path.read_text())
    print(json.dumps({'configured_host': config['host'], 'configured_port': config['port']}))
else:
    print(json.dumps({'configuration': 'not_installed'}))
for command in [['systemctl', '--user', 'is-system-running'], ['loginctl', 'show-user', getpass.getuser(), '-p', 'Linger']]:
    response = subprocess.run(command, capture_output=True, text=True, timeout=10)
    print(json.dumps({'check': command[0:2], 'result': response.stdout.strip(), 'exit': response.returncode}))
'@
$code.Replace('SOURCE_BASE64', $source) | & ssh -o ConnectTimeout=10 $Target 'python3 -' | Tee-Object -FilePath (Join-Path $PSScriptRoot 'ubuntu-inspection.txt')
Write-Host 'Inspection complete. You can close this window.'
