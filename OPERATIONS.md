# Running and maintaining the monitor

For first-time Ubuntu installation and screen setup, use [INSTALL.md](INSTALL.md).

## Preview locally

On Windows, the project virtual environment supplies timezone data:

```powershell
.\.venv\Scripts\python.exe monitor.py --config config.demo.json
```

Open `http://127.0.0.1:8791`. It is explicitly marked **DEMO** and uses synthetic
data in a separate database. Ubuntu uses the operating system's timezone
database and otherwise needs only Python 3.10+; the service has no pip dependencies.

## Deploy on an Ubuntu host

Run `Deploy-Ubuntu.ps1 -Target user@server` in a local PowerShell terminal. Enter the SSH password
locally for upload and installation. If requested, enter the sudo password
locally to enable user-service startup after logout and reboot.

The installer runs the test suite on Ubuntu, verifies the selected port on the
first installation, writes a user service, waits for a fresh account reading,
restarts the service, and checks recovery. A failed initial verification stops
and disables the new service or restores the previous release when available.

The dashboard URL is `http://SERVER_IP:PORT/`, using the configured bind
address and port. See INSTALL.md for first-install LAN parameters.

The server listens only on its supplied LAN IP. Source-address and Host checks
restrict access to the configured home subnet/hostnames. It serves only public
dashboard fields and static assets. HTTP is used on the trusted home LAN;
OpenAI authentication remains on Ubuntu. There is no remote command endpoint,
browser mutation endpoint, CORS grant, router change, or internet port forwarding.
Devices on the allowed LAN can read the usage statistics.

## Files on Ubuntu

Under the installing user's `~/.local/share/codex-usage-monitor/`:

| Path | Purpose |
|---|---|
| `runtime/` | Isolated pinned Codex CLI 0.144.3 |
| `releases/` | Versioned application copies |
| `current` | Symlink to the selected application copy |
| `config.json` | Bind address, poll interval, runtime path, database, timezone |
| `data/usage.sqlite` | Private SQLite history; sidecar WAL files may be present |

Unit: `~/.config/systemd/user/codex-usage-monitor.service`.
The collector runs as the installing user and uses that user's authorized login.
No account credentials are copied into the application or onto the display.
User-service lingering allows it to run without a connected PC.

## Service commands (Ubuntu shell)

```sh
systemctl --user status codex-usage-monitor.service
systemctl --user restart codex-usage-monitor.service
journalctl --user -u codex-usage-monitor.service -n 40 --no-pager
systemctl --user show codex-usage-monitor.service -p MemoryCurrent -p CPUUsageNSec -p NRestarts
```

Polling is five minutes, with bounded backoff on failure. Reads have timeouts.
The service retains the last successful observation; a failed request does not
advance its freshness timestamp. Quota-reset expiry also makes it stale.
No scheduled Codex task or model invocation is involved.

## Reauthentication

If account reads fail, stop the collector temporarily and run the supported
owner-operated login flow using the isolated binary:

```sh
systemctl --user stop codex-usage-monitor.service
~/.local/share/codex-usage-monitor/runtime/node_modules/.bin/codex login --device-auth
systemctl --user start codex-usage-monitor.service
```

Do not paste device codes, passwords, or tokens into chat or source files.
Read-only diagnostics: `Run-UbuntuProbe.ps1 -Target user@server` from Windows. Normal managed token
renewal is delegated to Codex; long-term renewal needs observation over time.

## Backup, retention, and rollback

History is retained for 370 days. The database stores normalized observations,
an internal hash to separate account identities, sanitized attempt states, and
allowlisted daily token buckets. No transcripts or raw account responses are stored.
The identity hash is not returned by the dashboard API.

For a consistent backup, use SQLite's backup API (not a bare file copy while
the WAL is active):

```sh
python3 - <<'PY'
import pathlib, sqlite3
p=pathlib.Path.home()/'.local/share/codex-usage-monitor/data'
with sqlite3.connect(p/'usage.sqlite') as source, sqlite3.connect(p/'usage-backup.sqlite') as target:
    source.backup(target)
PY
```

To roll back a release, stop the service, repoint `current` to a known prior
directory under `releases`, then start it. Preserve `config.json` and `data`.
No automatic cleanup deletes old releases. Do not copy demo data into production.

To disable monitoring without changing any other server services:

```sh
systemctl --user disable --now codex-usage-monitor.service
```

## Calculations and limits

- Percent remaining is 100 minus the reported used percentage for the seven-day
  main Codex bucket; it is never inferred from tokens.
- Daily allowance is the sum of nonnegative differences between consecutive
  comparable readings on that local date. Intervals over fifteen minutes,
  changes of account/reset, counter decreases, and midnight-crossing intervals
  are not assigned to a daily total.
- Reset timestamps within 120 seconds are grouped into the same contiguous
  window to tolerate upstream timestamp rounding. A real weekly rollover still
  starts a new period.
- Tokens today/current period are observed positive changes in the reported
  lifetime counter over comparable intervals. Delayed service updates can shift
  when tokens appear. These are always labeled observed/partial, not exact
  event-time totals. API-platform token usage is a separate system.
- Service daily buckets are stored and shown separately with a scope label;
  their timezone and completeness have not been assumed.
- Runway uses the latest uninterrupted segment in the last 24 hours, requires
  at least six hours, and divides remaining percentage points by measured pace.
  Zero observed pace is unavailable, not infinity. Stale readings suppress it.
- No extrapolation reconstructs activity before installation or through outages.
- Lifetime totals are the service's reported values, with unverified full coverage.
- Failed optional token reads do not erase successful weekly data. Stale token
  values are hidden on the display while historical rows remain labeled observations.

## Hardware arrival

Follow `firmware/README.md` for flashing and the physical test checklist.
Firmware compilation alone does not prove display initialization, touch mapping,
Wi-Fi provisioning, or power behavior on the actual board.
