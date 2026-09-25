# Account discovery client

`discovery.py` is a one-shot read-only probe using Python and a local Codex App
Server subprocess. It initializes stdio and reads account limits, with optional
token summaries. It does not request a model turn, buy credits, consume resets,
install a service, or open a listener.

## Preparation

Follow [INSTALL.md](INSTALL.md) to install the isolated runtime and sign in on
your Ubuntu server. Each user authenticates their own account interactively.
The project pins Codex 0.144.3 under
`~/.local/share/codex-usage-monitor/runtime/node_modules/.bin/codex`.
It does not require replacing a global Codex installation.

## Run from Windows

The SSH target below is an example; substitute your username and server IP.

```powershell
.\Run-UbuntuProbe.ps1 -Target user@192.168.1.100
.\Check-UbuntuLogin.ps1 -Target user@192.168.1.100
```

Probe output is written to ignored local files. Do not commit those files or
copy account authentication files into the project.

## Run directly on Ubuntu

From a checkout containing discovery.py:

```sh
python3 discovery.py --codex ~/.local/share/codex-usage-monitor/runtime/node_modules/.bin/codex --include-tokens --diagnostics
```

Requests include explicit parameter objects. Diagnostics allow only the auth
category, recognized numeric error codes, and fixed hints; raw errors and
upstream stderr are suppressed. Output contains normalized weekly values and
optional numeric token fields. Exit code 0 means a weekly reading was obtained;
1 means unavailable or failed. A failed optional token read does not invalidate
a successful weekly read. Do not present a failed or missing value as zero.

Select the main Codex bucket and weekly window by duration, not by assuming
primary or secondary. Compare results privately against the account UI near the
same time. Token coverage, service date-bucket timezone, and long-term renewal
require separate validation.

[Tests and validation](VALIDATION.md) · [Installation](INSTALL.md)
