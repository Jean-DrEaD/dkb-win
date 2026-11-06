# DKB Recomp Launcher Prototype

This Windows desktop launcher adapts the layout and feature set of the SteelTemple TotK launcher for the Donkey Kong Bananza PC Recomp fork. It is a local prototype for this fork and is not a game installer or a release package.

## English interface

The launcher interface and controller guide are in English. New settings use English for the game language and the in-game menu. The launcher only writes settings the current DKB runtime recognizes. The runtime still uses the inherited `totk.ini` filename and `TOTK_` environment-variable prefix internally; these are compatibility names, not user-facing game branding.

## Features

- Main menu with game launch, settings, digital extras, project link, and release status.
- Display selection, window and game render resolution, fullscreen, refresh-rate limit, presentation mode, aspect behavior, and camera field of view.
- Current runtime's FSR or bilinear upscaling, render scale, sharpness, device profile, pipeline policy, shader prebuild, and local Vulkan shader pre-warm.
- Color controls, supported DKB rendering fixes, controller prompts, motion, rumble, dead zone, mouse sensitivity, volume, and language.
- RomFS mod folder toggles and composition into the runtime's one mod overlay directory. Conflicts resolve by alphabetical mod-folder name, with later names taking precedence.
- Save snapshot and restore vault. Restoring first creates a safety snapshot.
- Monitor placement, optional UI sounds, and an English controller guide.

The current runtime does not provide DLSS, XeSS, frame generation, or Reflex settings, so the launcher does not invent those controls. DKB Recomp is experimental and some areas or effects may not work correctly.

## Use the prototype

1. Build DKB Recomp using the project instructions and your own game data.
2. Run `DKBLauncher.exe` from the install root next to the `jogo` folder, or run `python launcher/DKBLauncher.py` from this repository.
3. If the game is not found automatically, choose the folder that contains `dkb.exe`.
4. Select settings and use Play. Settings are saved beside the game executable in the inherited `totk.ini` file.

If `jogo/amigos/jogar-dk.ps1` exists, Play uses it so locally configured launch flags are preserved. Otherwise, Play runs `dkb.exe` directly. The launcher does not install or update the game.

## Build the standalone Windows launcher

Install Python 3.12+ and Pillow, PyInstaller, then from the repository root run:

```powershell
python -m pip install Pillow PyInstaller
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name DKBLauncher --icon launcher/assets/dkb.ico --add-data "launcher/assets;assets" launcher/DKBLauncher.py
```

The executable is written to `dist/`. The checked-in PyInstaller spec excludes unrelated scientific Python packages to keep the launcher smaller. Copy the executable next to the existing local `jogo` folder if you want automatic game discovery. Do not copy any game-derived data into this repository.

## User data and release status

`launcher_config.json` is created beside the launcher executable and stores the selected game directory, display, sound preference, and keep-open preference. Backups are saved under the game's profile folder. Release checking only checks GitHub for a published fork release and opens its page; it does not download or update files. No release is created by this prototype change.

## Attribution

The layout and interaction model are adapted from `TotKLauncher.py` in SteelTemple's TotK PC Recomp launcher. See [LICENSE-MIT.txt](LICENSE-MIT.txt) for the upstream MIT notice and attribution. Original DKB launcher artwork, icon, and UI chimes were created for this prototype.
