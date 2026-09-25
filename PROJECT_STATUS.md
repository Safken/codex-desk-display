# Project progress

## Completed

- Read-only account collector with bounded requests and retry backoff.
- SQLite history with 370-day retention and account separation.
- Observed daily/period usage, runway estimation, and stale/offline handling.
- Browser dashboard and two-page ESP32 firmware; Wi-Fi setup and reconnect.
- Ubuntu user-service deployment with fresh-read and restart verification.
- GitHub Windows/Linux tests and release/demo firmware builds.
- Checksum-verified prebuilt firmware upload helper.
- Generic [installation guide](INSTALL.md), [operations guide](OPERATIONS.md),
  [hardware reference](HARDWARE.md), and [case STL folder](case/stl/).
- Explicit user-supplied SSH/network settings; no personal server defaults.

A deployment has passed installation and restart checks. This is project-level
validation, not a statement that the software is installed on any reader's server.
See [VALIDATION.md](VALIDATION.md) for tested behavior and remaining limits.

## Hardware bring-up

Initial USB flashing of demo and release firmware passed device-side verification.
The user confirmed readable demo output and touch page navigation on one unit.
The architecture remains the Ubuntu collector plus a read-only Wi-Fi display.
A microSD card is optional and currently unused.

The display now defaults to 180-degree portrait rotation for a top-exiting power
cable, with matching touch-coordinate rotation. Antialiased Manrope replaces
the fixed-width bitmap font. Text uses measured alignment and the detail page
emphasizes the lifetime counter. Font data is embedded in flash.
The display and browser dashboard use black backgrounds with white text and
dark gray dividers. Status wording continues to distinguish stale/offline data.
The ES3C28P IPS panel uses the manufacturer's INVON setting so the intended
black/white theme is not displayed with reversed polarity.
The overview reset row includes the local calendar date and time beside its
label, while retaining the countdown. The collector's timezone determines this
label, including the offset applicable on the reset date.
The statistics heading reads "Total Tokens used -" with the full weekly date
range beneath it. The start is seven days before the reported reset endpoint,
converted into the configured timezone. Totals retain their observed/partial note.

The setup portal now lists available Wi-Fi networks, retains manual entry for
hidden networks, prefills saved dashboard addresses, and reports save errors.
An application-only update has been flashed and verified, and the USB command
for a device-local dashboard default has passed its storage acknowledgment.

The user confirmed successful Wi-Fi provisioning and live display operation.
The overview now adds `(Credits Left: XXX)` beside zero remaining allowance;
positive allowance retains the percentage alone. Credits are Codex units, not
API dollars. The balance is hidden behind a missing-value marker when stale.
Remaining
checks include reconnect/power cycling, swipes, and BOOT/RESET behavior.
The v6 holder is included unchanged and has been printed and fit-tested with
four M3 x 4 mm screws. See [printing and assembly](case/README.md) and the
[materials list](BOM.md). The panel inversion correction is visually confirmed.
Under-monitor attachment uses tape on two tabs; power-off behavior depends on
the chosen monitor's USB settings and still needs installation-specific testing.

## Longer-term checks

Observe multi-day collection and authentication renewal. Actual server reboot
and physical stability remain separate checks. Lifetime-token coverage and
service daily-bucket timezone remain unverified. API prepaid balance is deferred;
Codex credits must not be presented as API dollars.

## Continuing development

Read README.md, INSTALL.md, VALIDATION.md, and firmware/README.md. Preserve an
existing installation's config and history. Run tests before deploying changes.
Each user authenticates interactively; keep credentials and personal telemetry
out of the repository. Do not replace an unrelated global Codex installation.
