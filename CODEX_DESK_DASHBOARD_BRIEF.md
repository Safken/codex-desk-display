# Codex Desk Dashboard — Product Brief

## Goal

Provide a small always-on desk display for a user's weekly Codex allowance,
observed token activity, consumption pace, and reset countdown. Values must be
labeled by source and freshness; missing data must remain unavailable.

## Architecture

An Ubuntu collector reads account telemetry through an isolated Codex App Server,
stores normalized SQLite observations, and serves a read-only LAN API. A browser
dashboard and ESP32-S3 screen render that API. Collection requires no model
inference. Account credentials remain on the server; Wi-Fi settings stay on the
device. The server is not a router, DNS server, or network dependency.

## Hardware

Hosyond/LCDWiki ES3C28P 2.8-inch capacitive-touch ESP32-S3, 240 x 320,
16 MB flash and 8 MB OPI PSRAM. USB-C supplies power and initial flashing;
Wi-Fi is 2.4 GHz. No microSD, battery, or speaker is required.
See [HARDWARE.md](HARDWARE.md) for pin assignments and vendor references.

## Primary page

1. Weekly allowance remaining percentage and bar.
2. Weekly Used Today, displayed as a percentage of the weekly allowance.
3. Observed tokens today.
4. Estimated remaining runway.
5. Time until the weekly reset.
6. Freshness or offline/stale indication.

## Secondary page

Observed period token total, average consumption pace, daily observed percentage
and token rows, and service-reported lifetime tokens. Tap to change page; swipe
vertically on the statistics page for additional daily rows.

## Data rules

- Locate the weekly window by duration and main bucket identity.
- Percentages come from account limits, not an invented token quota.
- Daily and period totals represent observed intervals and are always partial.
- Do not bridge account changes, large gaps, counter decreases, or actual resets.
- Allow small reset timestamp rounding drift within the same contiguous window.
- Runway requires six continuous hours with measurable usage; stale data hides it.
- Preserve last known values on failures, but do not advance freshness.
- Lifetime coverage and daily service-bucket timezone remain unverified.
- API prepaid balance is deferred until a supported source is established;
  subscription credits are not API dollars.

## Storage and deployment

Keep 370 days of compact observations at five-minute sampling and prune older
readings. Require explicit SSH and LAN settings; default new installs to
loopback and UTC. Preserve existing config/history on updates. Do not embed a
specific user's identity, network, account readings, or credentials in defaults,
demos, or public documentation.

## Acceptance

Software tests, service restart recovery, and firmware compilation are separate
from physical display, touch, power, Wi-Fi, and enclosure acceptance. See
[PROJECT_STATUS.md](PROJECT_STATUS.md), [VALIDATION.md](VALIDATION.md), and
[INSTALL.md](INSTALL.md) for current progress and setup instructions.
