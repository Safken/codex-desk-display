# Embedded typography

Manrope variable font, distributed under the SIL Open Font License in OFL.txt.
Source: https://github.com/google/fonts/tree/main/ofl/manrope

The firmware uses proportional glyphs at native pixel sizes with 16 alpha levels
blended into the framebuffer. It does not scale the default bitmap font.
Font pixels and metrics are embedded in flash; no SD card or network font is
needed. The original font and license are retained for reproducibility.

To regenerate `firmware/CodexDesk/smooth_fonts.h` from the repository root:

```sh
python -m pip install Pillow==11.3.0
python tools/generate_fonts.py
```

The renderer supports printable ASCII and substitutes `?` for unsupported bytes.
Firmware font assets are generated ahead of time; normal CI builds use the
committed header and do not require Pillow.
