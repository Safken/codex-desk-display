param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_][A-Za-z0-9_.-]*@[A-Za-z0-9][A-Za-z0-9.-]*$')][string]$Target)
$ErrorActionPreference = 'Stop'
$Host.UI.RawUI.WindowTitle = 'Codex Usage Monitor - Codex login check'
Write-Host 'Enter the Ubuntu SSH password locally. This checks login status without exposing credentials.'
$loginCheck = @'
import json, subprocess, pathlib
binary = str(pathlib.Path.home()/'.local/share/codex-usage-monitor/runtime/node_modules/.bin/codex')
result = subprocess.run([binary, 'login', 'status'], capture_output=True, text=True, timeout=20)
message = (result.stdout + result.stderr).lower()
if 'chatgpt' in message and 'logged in' in message:
    state = 'chatgpt_login_present'
elif 'api key' in message and 'logged in' in message:
    state = 'api_key_login_present_not_subscription'
elif 'not logged in' in message:
    state = 'not_logged_in'
else:
    state = 'unrecognized_login_status'
help_result = subprocess.run([binary, 'login', '--help'], capture_output=True, text=True, timeout=10)
print(json.dumps({'login_state': state, 'login_status_exit': result.returncode,
    'device_auth_option_available': '--device-auth' in help_result.stdout}, indent=2))
'@
$loginCheck | & ssh -o ConnectTimeout=10 $Target 'python3 -' | Tee-Object -FilePath (Join-Path $PSScriptRoot 'ubuntu-login-check.txt')
Write-Host 'You can close this window after the check finishes.'
