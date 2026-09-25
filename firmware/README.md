# ES3C28P display firmware

For the complete Ubuntu-to-screen walkthrough, start with [INSTALL.md](../INSTALL.md).

Target: Hosyond/LCDWiki 2.8-inch ESP32-S3 N16R8 capacitive-touch board.
See `../HARDWARE.md` for the documented pin mapping and source links.

## What is implemented

- Wi-Fi configuration through a password-protected setup access point.
- Available-network scanning and selection, plus manual entry for hidden SSIDs.
- Saved dashboard address prefilled on setup; explicit validation/storage errors.
- Wi-Fi credentials and LAN endpoint saved in local Preferences/NVS.
- Automatic Wi-Fi reconnect and thirty-second LAN polling with timeouts.
- Primary page: weekly remaining, observed allowance today, observed tokens
  today, estimated runway, reset countdown, freshness.
- Secondary page: observed period tokens, average pace, four daily rows at a
  time, lifetime tokens. Tap to switch pages; swipe vertically on statistics
  to switch between newer and older rows.
- Locally aged stale/offline states and countdowns even if server requests fail.
- Standalone demo build, which requires no network and is always marked DEMO.
- Hold BOOT for five seconds while running to erase device settings and restart
  into setup. Do not hold BOOT through reset unless intentionally entering the
  ROM download mode.

No OpenAI credential, transcript, or API-platform key belongs on this board.
Wi-Fi settings reside in ordinary device NVS; physical flash security is not
configured. No microSD, audio hardware, or battery is required.

## Build on this Windows workspace

For a local compiler installation, place Arduino CLI 1.2.2 under
`.tools/arduino/`. Download
the Windows 64-bit archive from Arduino's official releases and extract there.
Toolchain data and libraries stay under `.tools/`; no global Arduino install is
required. Run from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\Setup-Firmware.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools\Build-Firmware.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools\Build-Firmware.ps1 -Demo
```

Pinned core: ESP32 Arduino 3.2.0. Libraries: Adafruit ILI9341 1.6.1,
Adafruit GFX 1.11.11, Adafruit BusIO 1.17.0, ArduinoJson 7.4.2.
The project uses the Adafruit SPI display driver and a minimal I2C touch reader,
not the vendor's LVGL examples. No LVGL dependency is needed for these two pages.

Build target: ESP32-S3, 16 MB flash, OPI PSRAM, 16 MB partitions with a 3 MB application slot,
hardware USB CDC enabled at boot. Confirm these match the delivered revision.
Outputs are under `firmware/build/release` and `firmware/build/demo`.
Consult `../VALIDATION.md` for actual build outcomes, not just these commands.

## Prebuilt firmware (no compiler installation needed)

GitHub Actions compiles both variants and uploads `esp32-firmware` artifacts.
They are retained for 14 days; rerun the workflow to produce a fresh artifact.
Download a successful run into `firmware/build/`:

```powershell
gh run download RUN_ID -n esp32-firmware -D firmware/build
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install esptool==4.8.1
```

The checked script verifies the full-image SHA256 before touching a serial port.
After the board arrives, replace COM_PORT with its actual Windows port:

```powershell
.\tools\Flash-Firmware.ps1 -Port COM_PORT -Variant demo
.\tools\Flash-Firmware.ps1 -Port COM_PORT -Variant release
```

These full-flash images overwrite saved device settings. Use them for initial
bring-up; provision Wi-Fi after the release flash. `-WhatIf` checks the file and
checksum without opening the serial port. Arduino CLI upload below is an
alternative for local builds and later application updates.

## First flash and setup (requires the board)

1. Connect a data-capable USB-C cable. Confirm the board revision and serial port.
2. Compile and upload the demo first; verify colors, orientation, text, and touch.
3. Upload the release build with the same board options and correct port:

   ```powershell
   .\.tools\arduino\arduino-cli.exe upload --config-file .tools\arduino-cli.json --fqbn "esp32:esp32:esp32s3:FlashSize=16M,PSRAM=opi,PartitionScheme=app3M_fat9M_16MB,USBMode=hwcdc,CDCOnBoot=cdc" --port COM_PORT --input-dir firmware\build\release firmware\CodexDesk
   ```

4. Join the `Codex-Setup-...` Wi-Fi shown on the display, using its generated
   eight-character setup password. Open `http://192.168.4.1`.
5. Enter your home 2.4 GHz Wi-Fi and `http://192.168.1.100:8790` as an example server address; substitute your collector IP and port.
   Credentials stay on the device; setup does not contact OpenAI.
6. The device restarts, joins Wi-Fi, and fetches the read-only dashboard payload.

Use a known correct COM port in place of `COM_PORT`. Upload may require the
vendor BOOT/RESET procedure. See `../VALIDATION.md` for completed device checks and remaining acceptance tests.

## Physical acceptance checklist

- Confirm board markings, N16R8 memory, LCD controller, and FT6336G address 0x38.
- Verify shared LCD reset behavior, backlight polarity, portrait orientation,
  color order, and reliable operation at the conservative 20 MHz SPI clock.
- Check touch x/y, corner coordinates, taps, and vertical swipes. Adjust only
  documented transforms in `board_config.h` after measuring the actual board.
- Compare both screen pages against live `/api/display`; confirm large token
  counts, 0%/100% states, null data, and long reset/runway values fit.
- Test wrong Wi-Fi details and recovery via BOOT; test power-cycle auto-reconnect.
- Stop/restart the server and disconnect Wi-Fi; ensure cached readings show
  stale/offline, never an invented fresh percentage or reset replenishment.
- Run a several-hour stability test and measure power/temperature before
  finalizing a printed enclosure.

The server can run and collect history before any of these hardware tests.

## Setup convenience over USB

While the setup portal is active, the USB serial interface at 115200 baud accepts
`server http://192.168.1.100:8790` followed by a newline. Substitute the collector
address. A successful write returns `Dashboard default saved`; reload the phone
setup page to prefill it. This stores only the address on that device, never a
network-specific value in the source. Wi-Fi passwords are entered in the setup
form and are never returned by the settings endpoint. A BOOT settings reset
clears this saved address too.

## Orientation and typography

This IPS panel requires `DISPLAY_INVERT=true` to reproduce the intended colors.
The manufacturer's [initialization sequence](https://www.lcdwiki.com/res/ES3C28P/ILI9341V_Init.txt)
sends `0x21` (INVON). Omitting it can make the black theme appear white with
black text. This is a panel setting, independent of the theme's RGB values.

The display defaults to 180-degree portrait rotation so USB power exits at the top. Touch coordinates rotate with the display. DISPLAY_ROTATION in board_config.h accepts 0 or 2.

The screen uses antialiased Manrope fonts, proportional alignment, and a larger lifetime counter. See fonts/README.md for the font license and asset regeneration instructions. Font assets are embedded in flash; the microSD is not needed.
