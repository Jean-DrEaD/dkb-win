## DKB v0.3.0

### New / Novidades
- **DKB Builder** (graphical installer): pick your game files, choose the folder and language, and it builds the game. Accepts .nup or romfs/exefs folders.
- **Update 3.2.0 support** (the installer detects the version automatically).
- **DLC (Emerald Rush)** is detected and mounted.
- Settings moved to `dkb.ini` (old `totk.ini` still read). Log: `logs\dkb.log`.
- The game window now opens in the foreground.
- New DKB icon and banner.

### Known issues / Problemas conhecidos
- 40-50 FPS in big scenes (limited by the CPU when preparing frames). Optimization is the next goal.
- The first launch shows black textures for a while (shader cache is empty). From the second launch on it loads normally.
- The version screen still shows 1.0.0 (only the text is wrong).

### Requirements
- Windows 10/11 x64, ~60 GB free, your own legal dump of the game. No game files are included.