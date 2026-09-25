#pragma once
// LCDWiki ES3C28P. Confirm board revision before flashing.
constexpr int LCD_CS=10, LCD_DC=46, LCD_SCK=12, LCD_MOSI=11, LCD_MISO=13;
constexpr int LCD_RST=-1, LCD_BL=45; // LCD reset is shared with CHIP_PU.
constexpr int TOUCH_SDA=16, TOUCH_SCL=15, TOUCH_RST=18, TOUCH_INT=17;
constexpr int BOOT_BUTTON=0;
constexpr uint8_t TOUCH_ADDR=0x38;
constexpr bool TOUCH_SWAP_XY=false, TOUCH_INVERT_X=false, TOUCH_INVERT_Y=false;
constexpr uint32_t DISPLAY_SPI_HZ=20000000;
constexpr uint8_t DISPLAY_ROTATION=2; // 180 degrees: USB power cable exits at top.
// Manufacturer ILI9341V_Init.txt explicitly sends INVON (0x21) for this IPS panel.
constexpr bool DISPLAY_INVERT=true;
static_assert(DISPLAY_ROTATION==0||DISPLAY_ROTATION==2,"Portrait rotations only");
