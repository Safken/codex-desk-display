# Validation status

This document records product behavior and technical validation only. It does
not publish account readings, user identities, server addresses, or hostnames.

## Software

- Windows and Linux Python test suites pass for account normalization, protocol
  errors/timeouts, SQLite persistence, retention, account changes, midnight/DST,
  reset timestamp drift, gaps, retry backoff, stale data, runway, and HTTP guards.
- JavaScript tests cover token expiry during outages and recovery behavior,
  safe Wi-Fi network rendering, duplicate removal, network selection, and
  visible save failures with retry enabled.
- Generic deployment configuration is tested for caller-provided network values,
  loopback defaults, validation, and preservation of existing settings.
- PowerShell syntax and documentation links are checked locally.
- A synthetic 370-day history at five-minute sampling measured about 21 MiB.

## Deployment

A user-service installation has passed live data checks before and after restart,
with persistence and LAN access verified. Measured idle memory was approximately
16 MiB; this is a sample, not a hard resource guarantee. The screen payload was
under 1 KiB in those checks, below the 16 KiB firmware limit.

The parameterized installation path is covered by local tests and shell syntax
checks; an additional fresh-server installation with arbitrary settings is not
claimed. Existing deployments retain their config and data on update.

## Firmware

Release and demo builds passed automated compilation for ESP32-S3, 16 MB flash,
8 MB OPI PSRAM, and the configured 3 MB application partition. Downloaded binary
checksums and an application image header have been verified; both upload-script
dry runs passed without opening a serial port. See repository Actions for the
latest run and downloadable artifacts. Artifacts expire after 14 days.

A local compiler is optional when using prebuilt artifacts and esptool. Static
RAM/compiler figures do not measure runtime allocations or physical stability.

## Initial device verification

A connected ESP32-S3 reported the expected 16 MB flash and 8 MB PSRAM.
Demo and release uploads passed device-side hash verification. The user
confirmed readable demo output and touch navigation between the two pages.
Release Wi-Fi provisioning and live-screen verification are in progress.
No microSD access or formatting was performed.

The Wi-Fi picker update passed release/demo compilation, 36 Python tests on
Windows and Linux, and three JavaScript tests. All eight downloaded binary
checksums passed. Matching bootloader and partition hashes allowed an
application-only update; the device verified the written application hash.
The USB setup command acknowledged saving and reading back a dashboard default.
The user subsequently confirmed successful setup and live dashboard operation.

## Credits at exhausted allowance

The collector now allowlists the main Codex bucket's credit balance and unlimited
flag, stores only the latest value with its account and observation time, and
includes it in both HTTP payloads. Existing database tables are unchanged.
All 38 Python tests and four JavaScript tests pass locally. Coverage includes
malformed/missing balances, bucket selection, persistence, account changes,
zero-versus-positive allowance, and offline suppression of the credit value.
The updated server returned fresh credit telemetry, and the live browser layout
was visually checked with the balance beside zero percent.
Windows/Linux CI and both firmware variants passed. Downloaded checksums and
unchanged bootloader/partition hashes were verified before flashing only the
release application. The device verified its written image and restarted;
physical confirmation of the new credit text remains user-observed.

## Typography and orientation

The smooth-font generator reproduces its committed header exactly. All 475
printable-ASCII glyphs across five sizes were checked for bitmap bounds and
metric storage limits; intermediate alpha coverage was verified. Bitmap data
totals 88,150 bytes in flash. Synthetic overview, credits, and detail layouts
were inspected at display resolution, and normal-row text widths were checked.
The existing 38 Python and four JavaScript tests still pass.
Release/demo compilation and Windows/Linux CI passed. All eight artifact hashes
were checked, and matching bootloader/partition hashes allowed an application-only
flash preserving device settings. The device verified the written image and
restarted. Physical readability and rotated gestures await user confirmation.

## Reset date label

Reset-date labels pass timezone, midnight/noon, and summer/winter offset tests.
The browser label is covered with and without the optional API field. All 39
Python and four JavaScript checks pass locally. Font metrics confirm the date
label and countdown fit together in the display row.
Windows/Linux CI and release/demo firmware builds passed. The updated live
collector returned a local reset label, and the browser row was visually checked.
All downloaded artifact hashes passed; the application-only USB update passed
device hash verification with the existing bootloader, partitions, and settings.

## Weekly heading

The weekly date-range heading passes local-time, year-boundary, and DST-boundary
tests. Browser tests cover missing and present date labels. All 40 Python and
four JavaScript tests pass locally; font metrics confirm the two-line heading
fits alongside the page indicator.
The updated live collector returned the expected full-week date range.
Windows/Linux CI and both firmware builds passed; all artifact hashes and the
unchanged bootloader/partition layout were verified. The application-only flash
passed device hash verification and restarted with saved settings preserved.

## Remaining physical and long-term checks

The black/white theme passed palette inspection, Windows/Linux checks, and both
firmware builds. Matching CSS was confirmed on the deployed server. Downloaded
firmware hashes and bootloader/partition compatibility passed before the
application-only flash, which passed device hash verification. The physical theme has since been confirmed by the user.
The user reported reversed black/white output. The manufacturer's published
ILI9341V initialization explicitly sends `0x21` (INVON), which the initial
firmware omitted. `DISPLAY_INVERT=true` now requests that mode on startup.
The user subsequently confirmed the intended black background and white text.
Both firmware variants and Windows/Linux CI passed. Artifact checksums and
bootloader/partition compatibility were verified; the application-only flash
passed device hash verification and restarted. The user subsequently confirmed black background and white text on the physical screen.

- Rotated display/font appearance, full touch-coordinate/swipe checks, reconnect, BOOT settings
  reset, power-cycle recovery, and mounted adhesive durability.
- Long-term authentication renewal, multi-day collection, and server reboot.
- Service-reported lifetime coverage and daily-bucket timezone.

Passing tests or compilation does not establish physical compatibility.

## Holder v6

The designer confirmed a working physical print using a Bambu Lab P1S, PLA,
and a 0.4 mm nozzle, fitted with four M3 x 4 mm screws. Double-sided tape on the
two tabs is the specified attachment method. The exact original STL is included
unchanged and verified by matching SHA-256 checksums. A structural mesh check
found 3,586 triangles, finite coordinates, and two faces per edge. Its bounding
box is approximately 109.64 x 56.00 x 18.34 in STL coordinate units (import as mm).
This does not establish all slicer profiles, adhesive durability, or monitor
USB off/sleep behavior. Those depend on the actual installation.

## Public preparation

The clean export passed all 40 Python and four JavaScript tests, and all local
Markdown links resolved. The GitHub STL blob matched the original file exactly.
After owner approval, main was replaced with an identical clean file tree and
public-safe commit identity. Twelve old workflow runs and ten artifacts were
removed. Repository visibility remains private because a direct old-SHA lookup
still succeeded; see PUBLIC_READINESS.md for the external retention blocker.
The clean-history release/demo firmware rebuild passed, with all eight binary
checksums verified and no identified private-value matches in the new artifacts.
A fresh remote clone passed the content/history scan and retained only the
public handle/noreply commit identities. A history-free source ZIP was checked
for the exact original STL and absence of local configuration/data directories.
