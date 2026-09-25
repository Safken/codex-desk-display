#!/usr/bin/env bash
set -euo pipefail
umask 077
base="$HOME/.local/share/codex-usage-monitor"
source_dir="$(cd "$(dirname "$0")/.." && pwd)"
runtime="$base/runtime/node_modules/.bin/codex"
test -x "$runtime" || { echo 'Missing isolated Codex runtime. Run Prepare-UbuntuRuntime.ps1 first.'; exit 1; }
"$runtime" --version
# Prove the complete package before replacing a running release.
(cd "$source_dir" && python3 -m unittest discover -s tests -q)
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
systemctl --user show-environment >/dev/null
if [[ "$(loginctl show-user "$(id -un)" -p Linger --value)" != yes ]]; then
  echo 'Enabling user-service startup without an open SSH session. Sudo may ask for your password.'
  sudo loginctl enable-linger "$(id -un)"
fi
mkdir -p "$base/releases" "$base/data" "$HOME/.config/systemd/user"
# Preserve existing installations. New installations default to loopback unless
# the caller explicitly supplies a bind address and allowed client network.
python3 "$source_dir/deploy/configure.py" "$base" "${1:-127.0.0.1}" "${2:-127.0.0.0/8}" "${3:-UTC}" "${4:-8790}"
release="$base/releases/$(date -u +%Y%m%dT%H%M%S)-$$"
mkdir "$release"
cp -R "$source_dir"/. "$release"/
previous="$(readlink "$base/current" || true)"
ln -sfn "$release" "$base/current"
cat > "$HOME/.config/systemd/user/codex-usage-monitor.service" <<EOF
[Unit]
Description=Codex account usage collector and LAN dashboard
After=network-online.target

[Service]
Type=simple
WorkingDirectory=$base/current
ExecStart=/usr/bin/python3 $base/current/monitor.py --config $base/config.json
Restart=on-failure
RestartSec=15
TimeoutStopSec=10
KillMode=control-group
Environment=PYTHONUNBUFFERED=1
Environment=PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin
UMask=0077
NoNewPrivileges=true
MemoryHigh=384M
MemoryMax=512M
CPUQuota=25%
TasksMax=128

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable codex-usage-monitor.service
started_at=$(date +%s)
systemctl --user restart codex-usage-monitor.service
echo 'Waiting for the first live reading...'
if ! python3 "$base/current/deploy/verify.py" --config "$base/config.json" --wait 100 --after "$started_at"; then
  echo 'Verification failed. Restoring the previous release if present.'
  if [[ -n "$previous" && -d "$previous" ]]; then
    ln -sfn "$previous" "$base/current"
    systemctl --user restart codex-usage-monitor.service
  else
    systemctl --user stop codex-usage-monitor.service
    systemctl --user disable codex-usage-monitor.service
  fi
  exit 1
fi
echo 'Checking persistence across a service restart...'
started_at=$(date +%s)
systemctl --user restart codex-usage-monitor.service
python3 "$base/current/deploy/verify.py" --config "$base/config.json" --wait 100 --after "$started_at"
systemctl --user show codex-usage-monitor.service -p ActiveState -p SubState -p MemoryCurrent -p CPUUsageNSec -p NRestarts
echo 'Dashboard address is recorded in the preserved server config.json.'
echo 'Readings continue when this SSH window closes.'
