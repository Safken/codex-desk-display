# Codex Usage Monitor

A small Wi-Fi desk display for weekly Codex allowance, daily observed usage,
token counts, estimated runway, and time until reset. An Ubuntu collector
stores history and serves a browser dashboard and an ESP32 display endpoint.
Collection uses account telemetry; it does not request model inference.

Public project: https://github.com/Safken/codex-desk-display

Start with the [installation guide](INSTALL.md) to build your own.

## Project status

Collector, SQLite history, browser dashboard, deployment helpers, and firmware
source are implemented. 40 Python tests and four JavaScript tests pass.
An Ubuntu deployment and fresh reads after restart have been verified with
isolated Codex 0.144.3. Release and demo firmware compile successfully. A physical
display has passed setup, live readings, tap navigation, and black/white color
confirmation. The v6 holder has been printed and fit-tested.
The browser demo uses clearly labeled synthetic readings.

## Hardware and printable case

- **Hosyond 2.8-inch ESP32-S3 capacitive touchscreen**, LCDWiki **ES3C28P**.
- 240 x 320 display, ILI9341V controller, FT6336G touch, 16 MB flash,
  8 MB OPI PSRAM, and 2.4 GHz Wi-Fi.
- USB-C power; use a data-capable USB cable for initial flashing.
- An Ubuntu server runs the collector. No microSD or battery is required.
- [Selected product](https://www.amazon.com/dp/B0FKG7WRWV?th=1)
- [Vendor documentation](https://www.lcdwiki.com/2.8inch_ESP32-S3_Display)
- [Hardware pinout and verification notes](HARDWARE.md)

Print the **[original Screen holder-v6.stl](case/stl/Screen%20holder-v6.stl)**.
The working build used a Bambu Lab P1S, PLA, a 0.4 mm nozzle, and four M3 x 4 mm
screws. Double-sided tape on two tabs mounts it under a monitor; a 90-degree
USB-C cable routes power to the monitor's rear USB port. Automatic screen
power-off requires a monitor port that actually switches off.

- [Materials list](BOM.md)
- [Printing and assembly](case/README.md)
- [MakerWorld listing draft](publishing/MAKERWORLD_LISTING.md)
- [Model license: CC BY-NC 4.0](case/LICENSE.md)
- [Public-release audit](PUBLIC_READINESS.md)

## Local preview

With Python 3.12 or newer, run from the repository root:

```sh
python -m pip install tzdata  # needed on Windows if system timezone data is absent
python monitor.py --config config.demo.json
```

Open http://127.0.0.1:8791/. Run checks with:

```sh
python -m unittest discover -s tests -v
```

## Build and deployment documentation

**Start with [INSTALL.md](INSTALL.md)** for Ubuntu installation, screen flashing,
Wi-Fi provisioning, troubleshooting, and future updates.

- [Operations](OPERATIONS.md): collector setup, retention, recovery, and deployment.
- [Firmware](firmware/README.md): build, flash, and device provisioning.
- [API](API.md): display payload and metric semantics.
- [Validation](VALIDATION.md): what has and has not been verified.
- [Project status](PROJECT_STATUS.md): implementation handoff and prior evidence.
- [Discovery](DISCOVERY.md): account telemetry compatibility and diagnostics.
- [Project brief](CODEX_DESK_DASHBOARD_BRIEF.md): scope and decisions.

## Before using on another network

SSH helpers require an explicit `-Target user@server`. New deployments accept
`-BindAddress`, `-AllowedNetwork`, `-TimeZone`, and `-Port`; their defaults are
loopback and UTC. Existing server configuration is preserved on updates.
Examples use fictitious usernames and example LAN addresses. Each user signs
in to their own account. Keep credentials, usage databases, and machine-specific
`config.local.json` files out of version control.

The collector retains 370 days of compact readings at a five-minute interval;
a synthetic full-year database measured approximately 21 MiB. Old readings
are pruned automatically. Daily totals reflect observed intervals and can be
partial. Lifetime token coverage is service-reported and unverified.

## Licenses

The holder STL is licensed CC BY-NC 4.0; see [case/LICENSE.md](case/LICENSE.md).
Manrope retains its [SIL Open Font License](firmware/fonts/OFL.txt).
Software and project-authored documentation use the [MIT License](LICENSE).
The STL and third-party font are excluded from that grant and retain their
separate licenses above, including SIL OFL for the generated Manrope glyph data.
