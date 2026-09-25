# Install, connect, and update the Codex Usage Monitor

This is the end-to-end guide for the Ubuntu collector and the ESP32 desk screen.
Use [PROJECT_STATUS.md](PROJECT_STATUS.md) and [VALIDATION.md](VALIDATION.md)
for actual progress and test evidence; instructions below are not proof that a
physical board has been tested.

For an existing installation, skip the fresh-server steps and use the screen
or update sections. All usernames, IP addresses, ports, and values in this guide
are examples. Replace them with settings for your own environment.

## What you need

For the printable monitor mount, use the [complete materials list](BOM.md) and
[print/assembly guide](case/README.md). Print the original v6 STL, secure the
screen with four M3 x 4 mm screws, and tape its two tabs under the monitor.
Complete flashing and Wi-Fi setup before final mounting. A right-angle USB-C
cable can use monitor USB power; test whether the port switches off in the
monitor's off/sleep modes before relying on it to turn the display off.

| Component | Requirement |
|---|---|
| Display | Hosyond/LCDWiki **ES3C28P**, 2.8-inch **capacitive-touch** ESP32-S3, 240 x 320 |
| Board memory | 16 MB flash, 8 MB OPI PSRAM (N16R8) |
| Controllers | ILI9341V display and FT6336G touch |
| USB | USB-C **data** cable for flashing; USB power afterward |
| Wi-Fi | 2.4 GHz home network, with access to the collector's LAN address |
| Collector | Ubuntu server with systemd, Python 3.12, Node.js/npm, SSH access, and internet access |
| Setup computer | Windows with Git, Python 3.12, OpenSSH client, and GitHub CLI (`gh`) |
| Account | Each owner signs in to their own eligible ChatGPT/Codex account on Ubuntu |

No microSD, battery, speaker, API key, or model inference is required for this
configuration. History is stored on Ubuntu, not on the screen. Keep the
collector's LAN address stable so the screen can reconnect after power loss.

[Hardware reference and pin mapping](HARDWARE.md) ·
[Selected product](https://www.amazon.com/dp/B0FKG7WRWV?th=1) ·
[Vendor documentation](https://www.lcdwiki.com/2.8inch_ESP32-S3_Display)

The source repository is public. Downloading Actions artifacts through GitHub CLI
requires GitHub sign-in. Each user authenticates their own Codex account separately.

## Build sequence

1. Download/clone the project and collect the [parts](BOM.md).
2. Print the [original holder](case/README.md) and dry-fit it at 100% scale.
3. Install/authenticate the Ubuntu collector using the fresh-server steps below.
4. Confirm the live browser dashboard works from another LAN device.
5. Download a clean successful firmware artifact or build locally.
6. Flash demo, check display/touch, then flash release and configure Wi-Fi.
7. Follow the holder guide to secure the screen with four screws, tape the two
   tabs under the monitor, and route the right-angle power cable.
8. Test power cycling and monitor off/sleep USB behavior before relying on it.

## Get the project on Windows

In PowerShell, authenticate to GitHub through the normal interactive flow if
needed, then clone the repository. Skip cloning if you already have this checkout.

```powershell
gh auth login
# Use this public repository, or substitute your fork.
gh repo clone Safken/codex-desk-display
Set-Location codex-desk-display
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install tzdata==2025.2 esptool==4.8.1
```

Alternatively, use GitHub **Code > Download ZIP**, extract it, and open PowerShell
in the extracted directory containing `INSTALL.md`. Run the same virtual-environment
commands above. A source ZIP does not include firmware binaries or Git history.
For ZIP users, specify `-R Safken/codex-desk-display` on `gh run list` and
`gh run download` commands so GitHub CLI knows which repository to use. Example:

```powershell
gh run list -R Safken/codex-desk-display --workflow verify.yml --status success --limit 5
gh run download RUN_ID -R Safken/codex-desk-display -n esp32-firmware -D firmware/build
```

If artifacts have expired, a repository owner can rerun the workflow. Other users
can fork the repository, enable Actions, and run it in their fork, or follow the
local build instructions in [firmware/README.md](firmware/README.md).

Run subsequent Windows commands from the repository root. These dependencies
stay in `.venv`; do not commit it. To update an existing clean checkout, use
`git pull --ff-only`. Preserve any local edits before pulling.

## Fresh Ubuntu installation

### 1. Choose the server and network settings

Set these example values in your Windows PowerShell session:

```powershell
$Target = 'user@192.168.1.100'
$BindAddress = '192.168.1.100'
$AllowedNetwork = '192.168.1.0/24'
$TimeZone = 'UTC'
$Port = 8790
```

Replace `user` with the Ubuntu login, the IP with the server's actual private
IPv4 address, the subnet with the clients allowed to read the dashboard, and
UTC with an IANA timezone if you want local-day statistics. The allowed subnet
must also include the server itself for restart verification.

All SSH helpers require `-Target`; none has a built-in destination. New service
installations default to loopback unless you explicitly supply LAN settings.
Existing `config.json` settings are preserved when updating. No source edits
are needed for a different user or network. `config.example.json` is a generic
loopback example; `/home/user/` is a placeholder, not an auto-detected path.

### 2. Prepare Ubuntu prerequisites

SSH into the intended Ubuntu machine:

```powershell
ssh $Target
```

On a fresh Ubuntu 24.04 system, install missing prerequisites with Ubuntu's
package manager. Skip packages already managed by your server administrator:

```sh
sudo apt update
sudo apt install python3 nodejs npm ca-certificates tzdata
python3 --version
node --version
npm --version
systemctl --user is-system-running
```

The pinned Codex package declares Node >=16; this project's live deployment
was tested with Node 24.21.0 and Python 3.12.3. Use an OS-supported Node version
or your existing maintained Node installation. The service PATH includes
`~/.local/bin`, `/usr/local/bin`, and `/usr/bin`; a shell-only version-manager
installation needs adjustment to the service PATH before deployment.

SSH must already be available. If this is a new server without SSH, install
and enable `openssh-server` locally before attempting the Windows SSH commands.
The guide does not change router, firewall, DNS, or internet forwarding settings.

Exit back to Windows when prerequisite checks are complete:

```sh
exit
```

### 3. Install the isolated Codex runtime

From the Windows repository directory:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Check-Server.ps1 -Target $Target
powershell -NoProfile -ExecutionPolicy Bypass -File .\Prepare-UbuntuRuntime.ps1 -Target $Target
```

Enter passwords in the terminal only. The runtime is installed at
`~/.local/share/codex-usage-monitor/runtime/node_modules/.bin/codex` on Ubuntu;
the server's global Codex CLI is not replaced.

On a brand-new account installation, the runtime helper's final account probe
can fail because sign-in has not happened yet. Confirm installation succeeded,
then perform the next step. An npm installation failure is a separate issue
and must be resolved first.

### 4. Sign in on Ubuntu

Use the isolated executable explicitly, especially on a server without a
global Codex installation:

```powershell
ssh -t $Target '~/.local/share/codex-usage-monitor/runtime/node_modules/.bin/codex login --device-auth'
```

Follow the displayed browser/device-code sign-in instructions using the account
whose usage should appear on the display. If device authorization is disabled,
enable **device code authorization for Codex** in that account's security settings
and retry. Do not put passwords, device codes, authentication files, or API keys
in this repository or send them to somebody else.

Then check account access and the intended server port:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run-UbuntuProbe.ps1 -Target $Target
powershell -NoProfile -ExecutionPolicy Bypass -File .\Inspect-Ubuntu.ps1 -Target $Target
```

Look for `status: ok` and an available weekly window. The installer checks the
selected bind address and port when creating the first configuration. If another
application owns the port, select a free `-Port` and use it in the display URL;
do not stop the unrelated application. Existing deployments retain their port.

### 5. Install the persistent collector

From Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Deploy-Ubuntu.ps1 -Target $Target -BindAddress $BindAddress -AllowedNetwork $AllowedNetwork -TimeZone $TimeZone -Port $Port
```

The helper packages source only, uploads it, runs the Ubuntu tests, installs a
user service, and verifies a new successful reading both before and after a
service restart. Expect two SSH password prompts. Sudo may be requested once
to enable user-service lingering so the collector continues after logout.

Success means **Deployment exit code: 0**, two `verification: ok` results,
`demo: false`, and `ActiveState=active` / `SubState=running`. Open
`http://SERVER_IP:PORT/` (for example, `http://192.168.1.100:8790/`) from another device on the same network. A local
verification alone does not establish LAN reachability.

The service is `codex-usage-monitor.service`. Configuration and history live in:

```text
~/.local/share/codex-usage-monitor/config.json
~/.local/share/codex-usage-monitor/data/usage.sqlite
```

The installer preserves these on subsequent deployments. It collects every
five minutes, keeps 370 days, and uses no model inference for polling. Data is
readable by devices on the allowed LAN. Do not expose this unauthenticated LAN
dashboard through public port forwarding.

## Prepare the screen

### 1. Download a successful firmware build

In the repository's GitHub **Actions** tab, open a successful **Verify software
and firmware** run and download the **esp32-firmware** artifact. Extract it so
`release/`, `demo/`, and `SHA256SUMS.txt` are directly inside `firmware/build/`.
Alternatively, from Windows PowerShell:

```powershell
gh run list --workflow verify.yml --status success --limit 5
# Replace RUN_ID with the selected successful run's numeric ID.
gh run download RUN_ID -n esp32-firmware -D firmware/build
```

Use a new/empty destination or move aside the previous build before downloading
another artifact into that directory. Do not mix binaries and checksum manifests
from different runs. Artifacts expire after 14 days. If necessary, run the
workflow again through Actions or `gh workflow run verify.yml`, and wait for
success. Local source-build instructions are in [firmware/README.md](firmware/README.md).

Verified prebuilt binaries need only the esptool uploader; a compiler
installation is optional.

### 2. Identify the board and serial port

Confirm **ES3C28P capacitive touch**, N16R8 memory, and the board revision.
Connect the USB-C data cable. In Windows Device Manager, check **Ports (COM &
LPT)** and identify the port that appears when this board is plugged in. Do not
guess a port belonging to another device. Close any serial monitor using it.

The examples below use `COM7`; replace it with the board's actual port.

### 3. Flash the demo first

```powershell
# Optional: validate the artifact/checksum without connecting to the device.
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Flash-Firmware.ps1 -Port COM7 -Variant demo -WhatIf
# Actual upload:
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Flash-Firmware.ps1 -Port COM7 -Variant demo
```

The script checks the SHA256 before uploading the full image. This overwrites
saved device settings. The demo should show clearly marked synthetic values
without Wi-Fi. Check colors, portrait orientation, both pages, taps, and swipes.
If automatic download mode fails, use the vendor's BOOT/RESET sequence: hold
BOOT, press/release RESET, release BOOT, and retry on the newly enumerated port.

### 4. Flash the release and configure Wi-Fi

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Flash-Firmware.ps1 -Port COM7 -Variant release
```

After upload, reset/power-cycle if necessary. The screen should display a
`Codex-Setup-...` Wi-Fi name and generated setup password.

1. Join that Wi-Fi from a phone or laptop. It has no internet connection;
   remain connected long enough to finish setup.
2. Open **http://192.168.4.1** in the browser.
3. Select your **2.4 GHz Wi-Fi** from the scanned list and enter its password.
   Use **Find Wi-Fi networks** to rescan, or type a hidden network name manually.
4. Enter the collector address, **http://192.168.1.100:8790** in this example.
   Substitute your server IP and port.
   Use a private IPv4 address and port, without an extra path. A trailing slash
   is accepted. A previously saved dashboard address is filled in automatically.
5. Save; the screen restarts. Rejoin your normal Wi-Fi on the setup phone/laptop.

The current firmware supports password-protected home Wi-Fi with 8-63 character
passwords; it does not implement enterprise or open-network setup. Preferences
stay on the screen. Do not enter ChatGPT/OpenAI credentials into this form.

The screen polls the collector every 30 seconds. Compare it with the browser:
weekly remaining, **Weekly Used Today**, tokens today, estimated runway, reset,
and freshness on page one; observed period/daily statistics and lifetime tokens
on page two. Daily values are partial from the collector's start time. Runway
requires at least six hours of continuous observations and a measurable pace.

## Updating later

### Ubuntu application update

Pull the desired repository revision on Windows and run `Deploy-Ubuntu.ps1 -Target $Target`
again. Existing server settings take precedence over first-install defaults. The existing config and
SQLite history are preserved; the installer selects a new versioned release
and repeats first-read/restart verification. It does not upgrade the pinned
Codex runtime automatically. See [OPERATIONS.md](OPERATIONS.md) for backups,
service commands, reauthentication, and release rollback.

### Screen firmware update

Download a successful artifact from the desired revision, verify the selected
COM port, and run the release flashing command above. **The full-image helper
overwrites device settings**, so repeat Wi-Fi provisioning afterward. There
is no OTA updater in this version; firmware updates use a USB data connection.

For local builds, the Arduino CLI application-upload alternative is documented
in [firmware/README.md](firmware/README.md). Do not assume settings survive an
update that changes partition layout or the settings format. Keep a copy of a
known-working artifact if you want an immediate firmware rollback.

Changing only server software normally needs no screen flash while API schema
version 1 remains compatible. Coordinate firmware and server updates if the
API schema changes; the device rejects incompatible schema versions.

## Troubleshooting and acceptance

| Symptom | Check |
|---|---|
| No serial port / upload timeout | Data-capable cable, correct device port, closed serial monitor, vendor BOOT/RESET sequence |
| Blank screen or wrong colors/touch | Exact board variant/pins and `firmware/CodexDesk/board_config.h`; hardware validation is still required |
| Wrong Wi-Fi / collector address | Hold BOOT for five seconds **while firmware is running** to clear settings and reopen setup; do not hold it through reset for this action |
| Server offline | Browser can reach collector URL, same reachable LAN, server service active, no guest-network client isolation |
| Data stale but server reachable | Account authentication, upstream connectivity, latest attempt status, Ubuntu service journal |
| Daily totals missing / zero | Two comparable readings are needed; token counters may update late; no pre-install history is invented |
| Runway says Collecting | Needs six continuous hours and measured usage; unavailable during stale/offline states |
| Checksum mismatch | Download a complete artifact and its matching manifest; do not bypass verification |

After first installation, test a screen power cycle, Wi-Fi reconnection, server
restart recovery, stale/offline indication, and several hours of stable use.
Actual server reboot and long-term authentication renewal remain separate
checks; do not reboot a shared server solely for setup without planning for its
other services.

Use the fit-tested **[original holder STL](case/stl/Screen%20holder-v6.stl)** and
[assembly guide](case/README.md). Confirm your board matches the specified model
and leave USB-C, BOOT, and RESET accessible.
