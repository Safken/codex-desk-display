# Materials and equipment

Build one monitor-mounted Codex Usage Monitor. The STL is a holder, not a kit;
the display electronics and server are separate requirements.

| Qty | Item | Notes |
|---|---|---|
| 1 | Hosyond/LCDWiki ES3C28P display | 2.8-inch capacitive-touch ESP32-S3, 240 x 320, ILI9341V, FT6336G, 16 MB flash and 8 MB OPI PSRAM. Match this board, not just the screen size. |
| 1 | Printed screen holder v6 | [Original STL](case/stl/Screen%20holder-v6.stl); working print used a Bambu Lab P1S, PLA, and 0.4 mm nozzle. |
| 4 | M3 x 4 mm screws | Use a head that seats at the board holes; the pictured build uses socket-head screws. No nuts or heat-set inserts are specified. |
| As needed | Double-sided mounting tape | For the two mounting tabs; compatible with the monitor surface and printed PLA. |
| 1 | 90-degree USB-C power cable | USB-C at the screen; other connector matches the monitor's powered USB port. Select angle and length for your monitor. |
| 1 | USB data cable | Required for initial flashing; may be the same angled cable if data-capable. A power-only cable cannot flash firmware. |
| Access | FDM printer and PLA | P1S/0.4 mm nozzle print has been fit-tested; exact layer/infill/support profile is not supplied. |
| Access | Matching screwdriver/hex driver | For hand-tightening four screws. |
| 1 | Monitor with suitable mounting surface and USB power | A port that switches off with the monitor is needed for automatic display power-off. Verify standby/sleep behavior. |
| 1 | Ubuntu host | systemd, Python 3.12, isolated Codex runtime, internet and LAN access; an existing server can be used. |
| Access | 2.4 GHz Wi-Fi | Display must be able to reach the collector on the LAN. |
| Access | Setup computer and account | See [INSTALL.md](INSTALL.md); each owner authenticates their own eligible Codex account. |

No microSD card, battery, speaker, or separate API key is required. History lives
on Ubuntu, and the fonts are embedded in the display firmware. Collection reads
account telemetry and does not start model inference.

[Display product reference](https://www.amazon.com/dp/B0FKG7WRWV) (no tracking parameters)
| [Vendor documentation](https://www.lcdwiki.com/2.8inch_ESP32-S3_Display)

Follow the [print and assembly guide](case/README.md), then the
[software installation guide](INSTALL.md). No prices or print-time estimates are
provided because supplier pricing, slicer settings, and cable requirements vary.
