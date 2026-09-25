# MakerWorld listing draft

Status: copy-ready description draft; not published. Upload the exact original
STL from `case/stl/Screen holder-v6.stl`. Do not substitute a repaired or scaled
export. Select CC BY-NC 4.0 for the model. Source, build instructions, and the
original STL are available in the public project repository linked below.

## Title

Codex Usage Monitor - Under-Monitor ESP32-S3 Screen Holder

## Short description

Keep your weekly Codex usage in view with a printable holder for a 2.8-inch
ESP32-S3 touchscreen. Mount it under your monitor with double-sided tape and
route USB power upward through a right-angle USB-C cable.

## Description

A small usage dashboard that sits just below your monitor, with the cable tucked
up toward the monitor's rear USB port. This v6 holder fits the Hosyond/LCDWiki
ES3C28P 2.8-inch capacitive-touch ESP32-S3 board and secures it with four M3 x 4 mm
screws. Two tabs attach to the monitor using double-sided mounting tape.

The companion firmware and Ubuntu collector turn the display into a Wi-Fi Codex
usage monitor. The black-and-white dashboard shows weekly allowance remaining,
credits left when the weekly allowance reaches zero, the weekly percentage used
today, observed token counts, estimated allowance runway, and the reset date/time.
Tap to see the weekly date range, daily readings, and lifetime tokens.

A 90-degree USB-C cable routes power out of the top of the holder to the back of
the monitor. If your monitor switches USB power off when it turns off, the screen
turns off with it and wakes when power returns. Verify your monitor's USB behavior:
some ports stay powered during sleep or standby. The Ubuntu collector remains on
and continues keeping history even while the screen is off.

### Tested print

- Bambu Lab P1S
- PLA
- 0.4 mm nozzle
- Holder v6 physically printed and fitted to the specified display
- Four M3 x 4 mm screws used successfully

Import the STL in millimeters at 100% scale. Overall mesh dimensions are about
109.64 x 56.00 x 18.34 mm. Exact layer height, infill, walls, supports, print time,
and filament weight are not supplied, and no tested 3MF print profile is included.
Review the slicer preview before printing, particularly the tabs and screw features.

### What you need

- One Hosyond/LCDWiki ES3C28P 2.8-inch capacitive ESP32-S3 display
- One printed v6 holder
- Four M3 x 4 mm screws and a matching hand driver
- Double-sided mounting tape for the two tabs
- A 90-degree USB-C cable with a monitor-compatible connector at the other end
- A USB data cable for flashing, if the angled cable is power-only
- A monitor with a suitable mounting surface and USB power
- An Ubuntu host, 2.4 GHz Wi-Fi, a setup computer, and your own Codex account

No microSD card or battery is needed. This is a holder and DIY software project;
electronics are not included with the STL.

### Assembly

1. Print and clean up the holder, then check the board fit.
2. Flash and configure the display before mounting it. Keep USB-C at the top.
3. Start all four M3 x 4 mm screws by hand. A little initial pressure may be
   needed for the threads to catch in the printed plastic. Tighten evenly until
   snug; do not overtighten, bend the board, or force a binding screw.
4. Connect the angled USB-C cable and test clearance under your monitor.
5. Put double-sided mounting tape on the two tabs and secure them to a clean,
   compatible surface. Follow the tape manufacturer's preparation instructions.
6. Route the cable with slack to the monitor's USB power port. Keep vents and
   buttons clear, and prevent the exposed board from touching conductive parts.
7. Test display startup, Wi-Fi reconnection, and monitor off/sleep power behavior.

### Software and build guide

https://github.com/Safken/codex-desk-display

The repository contains the Ubuntu installation guide, firmware setup, parts
list, and assembly instructions. Each user signs into their own Codex account;
credentials stay on their server. Usage totals are observed and may be partial.
Runway estimates concern the weekly allowance, not purchased-credit duration.
This is an independent community project, not an official OpenAI or Bambu Lab product.

### License

CC BY-NC 4.0. Noncommercial sharing and remixes are welcome with attribution to
Safken, a link to the license, and an indication of changes.
https://creativecommons.org/licenses/by-nc/4.0/

The companion software is MIT-licensed. That does not change the holder model's
noncommercial license. The included Manrope font retains its SIL OFL license.

## Suggested tags

ESP32, ESP32-S3, touchscreen, monitor mount, screen holder, desk accessory,
Codex, usage monitor, cable management, electronics

## Before publishing

- Finish repository history/artifact cleanup and verify the linked repository is
  available to readers before relying on it as the software download.
- Use the original STL. Only upload a print profile after slicing and testing it;
  do not claim the draft's unspecified settings were validated.
- Use fresh photos with demo data or the display off, on a neutral background.
  Suggested images: assembled front, back with four screws, mounted under monitor,
  and close-up of tape tabs/cable routing. The supplied reference photos contain
  personal account readings and background details and are not bundled for upload.
- Select the model license above; choose an appropriate electronics/monitor
  accessory category in the current MakerWorld uploader.
