<!-- banner -->
<p align="center"><img src="docs/banner.png" width="200" alt="DKB"></p>
<!-- /banner -->
# DKB Recomp

<!-- novidades -->
## What's new in v0.3.9
- Works on clean PCs: **no Git and no Visual Studio needed** (the shader translator is prebuilt and downloaded from the release).
- Run `Instalador.exe` from a normal folder (e.g. Downloads), not a read-only/network folder.
- The build takes about 1 hour and needs plenty of RAM (~24 GB incl. pagefile).

## What's new in v0.3.9
- Synced with upstream (67 commits): runtime, rendering and performance fixes.
- **Frame generation (experimental)** in the in-game menu, plus a `Frame gen` line in the full overlay.
- Fixed the game title showing `Ver. 0.0.0`, and the window now opens in the foreground.
- Full notes: [RELEASE_NOTES.md](RELEASE_NOTES.md)
<!-- /novidades -->

[![License: GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0--or--later-blue)](LICENSE)

**DKB Recomp** is a static recompilation of *Donkey Kong Bananza* (Nintendo Switch 2) into a native Windows x86-64
application with a Vulkan renderer. It is not an emulator: the game's ARM64 code is translated to C ahead of time and
compiled into one executable. Based on [DKB Recomp](https://github.com/Lucas-blip-png/dkb-pc-recomp) and
[TotK Recomp](https://github.com/valentderah/totk-pc-recomp).

> [!IMPORTANT]
> **No game files are included, and none ever will be.** You need your own copy of *Donkey Kong Bananza*, dumped
> from your own console. Instructions for obtaining those files will not be provided. There are no prebuilt
> executables: everyone builds the game from their own dump.

## Status

**Playable**

- Base 1.0.0 and update 3.2.0
- DLC
- Dumps as `.nup` or as `exefs` / `romfs` folders

## Requirements

- Windows 11, 64-bit
- GPU with Vulkan 1.3 or newer
- 16 GB of RAM
- About 25 GB of free space, on a path without accented characters

## Before building: shader cache

Shader preparation compiles ~34,000 variants (~18 min) and stores them in the driver cache. If that cache is too
small, the driver drops part of it and the first boot gets a **black screen or a frozen cutscene**.

- **NVIDIA:** NVIDIA Control Panel → Manage 3D settings → **Shader Cache Size → Unlimited** → Apply.
- **AMD (untested):** AMD Software (Adrenalin) → Gaming → Graphics → **Shader Cache: On**. Do not use "Reset Shader Cache" after building.

If the game was already built with a limited cache, change the setting and build again.

## How to use

1. Download `Instalador.exe` from the [latest release](../../releases/latest).
2. Run it. It installs the missing tools and keeps itself up to date.
3. Choose your game files and click **Build the game** (~45 min).
4. Start `dkb.exe` from the output folder.

## In-game menu

Press **F1** (or **Esc**) to open the menu.

### Frame generation (experimental)

*Graphics → Frame generation* (`off` / `2x`, off by default). It inserts one generated frame per real frame, but
drops the generated frames when twice the FPS exceeds the monitor refresh rate.

| Monitor | Game | Result |
|---|---|---|
| 60 Hz | 60 fps | no effect (`refresh cap`) |
| 60 Hz | ≤ 30 fps | ~60 shown, with more latency |
| 120/144 Hz | 60 fps | ~120 shown |

**On a 60 Hz monitor, leave it off.** The full overlay shows the state on the `Frame gen` line (real → shown fps).

## Credits

- [DKB Recomp](https://github.com/Lucas-blip-png/dkb-pc-recomp) and [TotK Recomp](https://github.com/valentderah/totk-pc-recomp), the base of everything here
- [Eglantine](https://git.eden-emu.dev/Franseven/PokeDinner-a-Eglantine-Fork) (Eden Emulator Project) for the Ampere-to-Maxwell shader lowering
- [GRAnimated/DKBananza](https://github.com/GRAnimated/DKBananza) for the game's symbols
- [libvpx](https://chromium.googlesource.com/webm/libvpx), [Switchbrew](https://switchbrew.org) and the others in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

## License

[GNU GPL v3 or later](LICENSE). Files that came from TotK Recomp keep their [MIT License](LICENSE-MIT); third-party code
keeps its own license. The license grants nothing for Nintendo's game.

Independent, non-commercial fan project, not affiliated with or endorsed by Nintendo. *Donkey Kong Bananza* and
*Nintendo Switch 2* are trademarks of Nintendo.