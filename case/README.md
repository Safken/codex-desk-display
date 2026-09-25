# Under-monitor screen holder v6

Print [Screen holder-v6.stl](stl/Screen%20holder-v6.stl) for the Hosyond/LCDWiki
ES3C28P 2.8-inch capacitive-touch ESP32-S3 display. The designer has printed and
fit-tested this revision with four M3 x 4 mm screws. The source STL is included
byte-for-byte, with its original filename; it has not been repaired, scaled,
reoriented, or had metadata removed.

[Open the MakerWorld model and print profile](https://makerworld.com/en/models/3353225-codex-usage-monitor-under-monitor-screen-holder#profileId-3811349). The published profile lists
0.2 mm layers, two walls, and 15% infill. These are published profile settings;
they do not establish the exact settings used for the original fit-tested print.

## Confirmed print information

| Setting | Used for the working print |
|---|---|
| Printer | Bambu Lab P1S |
| Material | PLA |
| Nozzle | 0.4 mm |
| Model | Screen holder-v6.stl, one piece |
| Scale | Import as millimeters at 100%; check the dimensions below |
| Layer height, walls, infill, supports | Exact successful settings were not supplied |

The mesh envelope is approximately **109.64 x 56.00 x 18.34 mm**, assuming
millimeter units. STL does not encode units. It contains 3,586 triangles; an
edge check found two faces per edge. This is a mesh check, not a guarantee of
slicer behavior. Use the original STL, inspect it in your slicer, and do not
scale it to compensate for screw fit.

Start with your printer's PLA profile. Place the broad, flat front face against
the build plate and inspect the layer preview around the mounting tabs and
screw features. This orientation is assembly guidance, not a supplied tested
print profile. Select supports as needed after inspecting the preview. A tested
3MF, print time, material weight, and exact support settings are not included.

## Assemble and mount

1. Print one holder. Remove support remnants and loose plastic before fitting
   electronics. Dry-fit the board and ensure the screen opening and four holes
   align. Use the exact ES3C28P board; a different 2.8-inch display may not fit.
2. Complete [firmware flashing and Wi-Fi setup](../INSTALL.md) before mounting.
   Firmware is oriented with the USB-C port at the top.
3. Seat the screen in the holder and start **four M3 x 4 mm screws** by hand.
   The working print needed a little initial pressure for the threads to catch.
   Keep the screws straight, start all four loosely, then tighten evenly until
   snug. Do not force a binding screw or flex the circuit board; stop if a screw
   bottoms out. The design uses screws directly in the printed features, with
   no heat-set inserts or nuts specified.
4. With power disconnected, connect a **90-degree USB-C cable** that routes
   upward and clears the monitor. Match the other end to the monitor's powered
   USB port. Check the direction of the angled plug before buying the cable.
5. Dry-fit under the monitor. Apply **double-sided mounting tape to the two
   tabs**. Follow the tape maker's surface preparation and cure instructions.
   Choose a compatible flat area that does not cover monitor vents, buttons,
   sensors, or connectors. Keep the exposed board clear of conductive surfaces.
6. Support the holder while pressing both tabs into position. Route the cable
   to the USB power port at the back of the monitor, leaving slack so the cable
   does not pull on the board or peel the tabs loose.
7. Turn the monitor on and verify the screen reconnects and receives data.
   Turn the monitor off and test sleep/standby separately. Some monitors keep
   USB power on in those modes; check the monitor's USB charging/standby settings.
   When that port switches off with the monitor, the display powers down too,
   so this arrangement does not need a software screen saver.

The Ubuntu collector stays running independently when the screen has no power.
It continues keeping history; the screen reconnects when power returns. Monitor
USB behavior, adhesive performance, and long-term mounted use vary by installation.
Avoid placing the PLA holder against a hot surface.

## Parts, files, and sharing

- [Full materials list](../BOM.md)
- [Ubuntu and firmware installation](../INSTALL.md)
- [MakerWorld listing draft](../publishing/MAKERWORLD_LISTING.md)
- [Model license and attribution](LICENSE.md): CC BY-NC 4.0

Original STL SHA-256:
`4ac897e66814f2c85b72ef47bc12714f729d4d683889a6ec6ddd4e6085f9ffc6`
