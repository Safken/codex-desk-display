# Selected display and supplied pin reference

Target: [Hosyond ESP32-S3, ASIN B0FKG7WRWV](https://www.amazon.com/dp/B0FKG7WRWV?th=1).

The pin reference is transcribed from the vendor's interface table and
[LCDWiki board documentation](https://www.lcdwiki.com/2.8inch_ESP32-S3_Display).
These are documented specifications, not measurements of a connected board.

## Documented configuration and development references

The vendor identifies the touch variant as **ES3C28P** (ES3N28P is non-touch),
with **ILI9341V** display control, **FT6336G** touch, **16 MB flash**, **8 MB OPI
PSRAM**, and **2.4 GHz Wi-Fi**. Match the delivered board revision before flashing.

The documentation hub links schematics, dimensional drawings, a 3D model,
initialization code, and the complete demo package. The cloud-package link
could not be retrieved through the research tool; no demo archive is downloaded
or tested yet.

The [Arduino demo instructions](https://www.lcdwiki.com/res/ES3C28P/2.8inch_ES3C28P_ES3N28P_arduino_Demo_Instructions.pdf)
specify Arduino IDE 2.3.4 and ESP32 core 3.2.0. They describe TFT_eSPI and
FT6336-arduino libraries; their LVGL examples require v8.x, not v9.x. Treat
these as the vendor's example baseline, not a validated project dependency set.
Review the package's board settings and library configuration before adopting it.

## MVP connections

| Function | Seller pin table |
|---|---|
| LCD chip select | GPIO10, active low |
| LCD command/data | GPIO46, high=data, low=command |
| LCD SPI clock | GPIO12 |
| LCD SPI write / MOSI | GPIO11 |
| LCD SPI read / MISO | GPIO13 |
| LCD reset | Shared with main ESP32-S3 reset; no separate GPIO specified |
| LCD backlight | GPIO45, high=on |
| Touch I2C data | GPIO16 |
| Touch I2C clock | GPIO15 |
| Touch reset | GPIO18, active low |
| Touch interrupt | GPIO17, active low |
| RGB LED | GPIO42 |
| Boot button | GPIO0 |
| Reset button | EN |

The screenshot describes USB-C for both module power and program download.
The microSD slot is optional expansion for fonts, pictures, audio, and large
data. The planned dashboard stores history on Ubuntu and needs no microSD.

## Initial hardware verification

An attached ESP32-S3 unit reported 16 MB flash and 8 MB embedded PSRAM.
Demo and release firmware uploads completed with device-side hash verification.
The user confirmed readable demo output and tap navigation between both pages.
The release application uses the same verified bootloader and partition map.

These results do not establish every board revision, swipe behavior, long-term
power stability, or SD-card functionality. The current firmware does not use the
microSD slot and does not format or modify an inserted card.

## Printed holder and monitor power

The [v6 holder](case/README.md) has been printed on a Bambu Lab P1S in PLA with
a 0.4 mm nozzle and fit-tested using four M3 x 4 mm screws. Double-sided tape
on two tabs attaches the holder beneath the monitor. A 90-degree USB-C cable
routes upward to a powered USB port. See [BOM.md](BOM.md) for the full parts list.
Monitor off/standby USB behavior must be checked for each installation.
The user has confirmed the black-background/white-text output after enabling
the IPS panel's required inversion setting.

## Remaining physical checks

- Board revision and agreement with the supplied pin table.
- Display initialization, orientation, color order, and usable SPI clock.
- FT6336G I2C address, reset sequence, and coordinate mapping on the delivered board.
- N16R8 flash/PSRAM build settings and supported firmware partition layout.
- USB upload behavior and stable power supply requirements.

The seller's peripheral descriptions contain confusing SPI/I2C wording.
Do not infer extra peripheral wiring from that prose. Use only the verified
MVP connections during bring-up. Firmware source is implemented and compiled in
`firmware/CodexDesk/`; the original fit-tested holder is in `case/stl/`.
