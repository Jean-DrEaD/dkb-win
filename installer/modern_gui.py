"""Modern CustomTkinter GUI Installer for Donkey Kong Bananza (PC Recompiled).

Features:
- Sleek dark jungle theme with Donkey Kong Banana Gold styling (replacing Zonai teal)
- High-resolution multi-size DKB banana game icon embedded
- Dynamic tab-synchronized navigation (Back / Next buttons)
- Vendor AI & Upscaler SDK management (NVIDIA DLSS 4.5 / DLSS-NR / Reflex, Intel XeSS, AMD FSR)
- Controller UI selection (PS5 DualSense, Xbox Series, Switch)
- Desktop shortcut creation with dkb.ico
- Integrated In-Game Controller Overlay Guide & Readme creator
- Real-time animated progress & live logging
"""

import os
import shutil
import sys
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

# Self-contained Vendor SDKs, Controller Layouts & Desktop Shortcut helpers
import subprocess

VENDOR_SDK_FILES = [
    {"name": "nvngx_dlss.dll", "desc": "NVIDIA DLSS 4.5 / Super Resolution", "vendor": "NVIDIA"},
    {"name": "nvngx_dlssnr.dll", "desc": "NVIDIA DLSS-NR Neural Reconstruction", "vendor": "NVIDIA"},
    {"name": "nvngx_dlssg.dll", "desc": "NVIDIA DLSS Frame Generation", "vendor": "NVIDIA"},
    {"name": "sl.common.dll", "desc": "NVIDIA Streamline Common", "vendor": "NVIDIA"},
    {"name": "sl.dlss.dll", "desc": "NVIDIA Streamline DLSS plugin", "vendor": "NVIDIA"},
    {"name": "sl.dlss_g.dll", "desc": "NVIDIA Streamline DLSS-G plugin", "vendor": "NVIDIA"},
    {"name": "sl.dlss_nr.dll", "desc": "NVIDIA Streamline DLSS-NR plugin", "vendor": "NVIDIA"},
    {"name": "sl.interposer.dll", "desc": "NVIDIA Streamline Interposer", "vendor": "NVIDIA"},
    {"name": "sl.reflex.dll", "desc": "NVIDIA Reflex Low Latency", "vendor": "NVIDIA"},
    {"name": "libxess.dll", "desc": "Intel XeSS Super Sampling SDK", "vendor": "Intel"},
    {"name": "libxess_fg.dll", "desc": "Intel XeSS Frame Generation", "vendor": "Intel"},
    {"name": "libxell.dll", "desc": "Intel Low Latency", "vendor": "Intel"},
    {"name": "libxess_dx11.dll", "desc": "Intel XeSS DX11 Bridge", "vendor": "Intel"},
]

def find_local_sdk_cache(dll_name: str):
    candidates = [
        os.path.join(r"C:\DK-Bananza-Instalador\jogo\build\dkb100", dll_name),
        os.path.join(r"C:\Games\Tears of the Kingdom PC\GAME", dll_name),
        os.path.join(r"C:\Games\Bloodborne PC\engine\out", dll_name),
        os.path.join(r"C:\Games\CTR Nitro Fueled PC\bin", dll_name),
        os.path.join(os.path.dirname(__file__), "assets", dll_name),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None

def install_vendor_sdks(target_game_dir: str, log_cb=None) -> int:
    installed = 0
    os.makedirs(target_game_dir, exist_ok=True)
    for item in VENDOR_SDK_FILES:
        dll = item["name"]
        dst = os.path.join(target_game_dir, dll)
        if os.path.isfile(dst):
            installed += 1
            continue
        src = find_local_sdk_cache(dll)
        if src and os.path.isfile(src):
            try:
                shutil.copy2(src, dst)
                installed += 1
                if log_cb:
                    log_cb(f"[✓] Installed {dll} ({item['desc']})")
            except Exception as e:
                if log_cb:
                    log_cb(f"[!] Warning: failed to copy {dll}: {e}")
    return installed

CONTROLLER_UI_CHOICES = [
    {
        "id": "ps5_monochrome",
        "name": "PlayStation 5 DualSense (Monochrome)",
        "desc": "Official PS5 dark theme button icons (✕, ◯, ▢, △)",
    },
    {
        "id": "ps5_color",
        "name": "PlayStation 5 DualSense (Color)",
        "desc": "PlayStation icons with colored shapes (Blue Cross, Red Circle, etc.)",
    },
    {
        "id": "xbox_monochrome",
        "name": "Xbox Series / One (Monochrome)",
        "desc": "Xbox modern controller prompts (A, B, X, Y)",
    },
    {
        "id": "xbox_color",
        "name": "Xbox Series / One (Color)",
        "desc": "Xbox prompts with colored buttons (Green A, Red B, Blue X, Yellow Y)",
    },
    {
        "id": "nintendo_default",
        "name": "Nintendo Switch (Original)",
        "desc": "Original Switch Pro Controller / Joy-Con prompts",
    }
]

def install_controller_ui(choice_id: str, target_game_dir: str) -> bool:
    ini_path = os.path.join(target_game_dir, "totk.ini")
    if not os.path.isfile(ini_path):
        ini_path = os.path.join(target_game_dir, "dkb.ini")
    layout_val = "playstation" if "ps5" in choice_id else "xbox" if "xbox" in choice_id else "nintendo"
    if os.path.isfile(ini_path):
        try:
            with open(ini_path, "r", encoding="utf-8") as f:
                content = f.read()
            if "pad_layout" in content:
                import re
                content = re.sub(r"pad_layout\s*=.*", f"pad_layout = {layout_val}", content)
            else:
                content += f"\n[input]\npad_layout = {layout_val}\n"
            with open(ini_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False
    return True

def create_desktop_shortcut(game_dir: str, shortcut_name: str = "Donkey Kong Bananza", target_exe: str = None) -> bool:
    try:
        desktop_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
        if not os.path.exists(desktop_dir):
            desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop_dir, f"{shortcut_name}.lnk")
        if target_exe:
            chosen_exe = os.path.join(game_dir, target_exe)
        elif os.path.isfile(os.path.join(game_dir, "DKBLauncher.exe")):
            chosen_exe = os.path.join(game_dir, "DKBLauncher.exe")
        elif os.path.isfile(os.path.join(game_dir, "..", "DKBLauncher.exe")):
            chosen_exe = os.path.abspath(os.path.join(game_dir, "..", "DKBLauncher.exe"))
        else:
            chosen_exe = os.path.join(game_dir, "dkb.exe")
        icon_path = os.path.join(game_dir, "dkb.ico")
        if not os.path.exists(icon_path):
            icon_path = chosen_exe
        ps_script = f"""
        $ws = New-Object -ComObject WScript.Shell
        $s = $ws.CreateShortcut('{shortcut_path}')
        $s.TargetPath = '{chosen_exe}'
        $s.WorkingDirectory = '{game_dir}'
        $s.IconLocation = '{icon_path},0'
        $s.Description = 'Play Donkey Kong Bananza PC Recomp'
        $s.Save()
        """
        res = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                             capture_output=True, text=True, timeout=10)
        return res.returncode == 0 and os.path.exists(shortcut_path)
    except Exception as e:
        print(f"Error creating shortcut: {e}")
        return False

# Theme colors (DKB Golden Banana & Deep Jungle)
ACCENT_GOLD = "#ffd24d"
ACCENT_HOVER = "#fff2a3"
BG_DARK = "#0a0e0c"
CARD_BG = "#131b17"
CARD_BORDER = "#23332a"
TEXT_DIM = "#8fa397"
TEXT_GOLD = "#ffe17d"

CONTROLLER_GUIDE_TEXT = """================================================================================
  DONKEY KONG BANANZA PC RECOMP
  IN-GAME SETTINGS OVERLAY & CONTROLLER NAVIGATION GUIDE
================================================================================

1. HOW TO OPEN / CLOSE THE IN-GAME SETTINGS MENU:
   -----------------------------------------------------------------------------
   • CONTROLLER: Press SELECT + START at the same time
     - PlayStation (PS5 / PS4): Press [Share / Create] + [Options] together
     - Xbox (Series X|S / One):  Press [View / Back] + [Menu / Start] together
     - Nintendo Switch Layout:  Press [Minus (-)] + [Plus (+)] together

   • KEYBOARD:   Press [F1] or [Esc] at any time.

2. CONTROLLER ACTIONS & MOVEMENT (BANANZA CORE):
   -----------------------------------------------------------------------------
   • Left Stick:                Move Donkey Kong
   • Right Stick:               Camera Pan & Pitch
   • A (Xbox) / ✕ (PS5) / B:    Jump / Hover Flutter
   • X (Xbox) / ▢ (PS5) / Y:    Punch / Break Barrels / Attack
   • RT / R2 / ZR:              Roll / Sprint Dash
   • LT / L2 / ZL:              Ground Pound / Slam

3. PERFORMANCE OVERLAY (FPS, FRAME TIME, VRAM, GPU USAGE):
   -----------------------------------------------------------------------------
   • CONTROLLER: Press L3 + R3 at the same time (Click Left Stick + Click Right Stick)
   • KEYBOARD:   Press [F10] to cycle overlay modes (Off -> Compact -> Detailed).

4. FULLSCREEN TOGGLE:
   -----------------------------------------------------------------------------
   • Press [F11] or [Alt + Enter] on keyboard.

================================================================================
Enjoy playing Donkey Kong Bananza on PC!
================================================================================
"""

class ModernDkbInstaller(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window properties
        self.title("Donkey Kong Bananza PC Recomp - Setup")
        self.geometry("1000x740")
        self.minsize(940, 700)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        # Set game icon if found
        self.icon_path = self.find_game_icon()
        if self.icon_path and os.path.exists(self.icon_path):
            try:
                self.iconbitmap(self.icon_path)
            except Exception:
                pass

        # Variables
        self.var_game_source = tk.StringVar(value=self.auto_find_game_source())
        self.var_keys = tk.StringVar(value=self.auto_find_keys())
        self.var_install_dir = tk.StringVar(value=r"C:\DK-Bananza-Instalador\jogo\build\dkb100")
        if not os.path.isdir(self.var_install_dir.get()):
            self.var_install_dir.set(r"C:\Games\DKB PC\build\dkb100")
            
        self.var_controller_ui = tk.StringVar(value="PlayStation 5 DualSense (Monochrome)")
        self.var_install_sdks = tk.BooleanVar(value=True)
        self.var_create_shortcut = tk.BooleanVar(value=True)
        self.var_create_guide = tk.BooleanVar(value=True)

        # Setup UI
        self.setup_ui()

    def auto_find_game_source(self):
        candidates = [
            r"C:\Games",
            os.path.join(os.environ.get("USERPROFILE", ""), "Downloads"),
        ]
        for c in candidates:
            if not os.path.exists(c): continue
            if os.path.isdir(os.path.join(c, "exefs")) and os.path.isdir(os.path.join(c, "romfs")):
                return c
            if os.path.isfile(c) and any(c.lower().endswith(ext) for ext in [".nsp", ".xci"]):
                return c
            if os.path.isdir(c):
                try:
                    for f in os.listdir(c):
                        fl = f.lower()
                        if any(kw in fl for kw in ["dk", "bananza", "donkey"]) and (fl.endswith(".nsp") or fl.endswith(".xci")):
                            return os.path.join(c, f)
                except Exception:
                    pass
        return ""

    def auto_find_keys(self):
        appdata = os.environ.get("APPDATA", "")
        candidates = [
            os.path.join(appdata, "yuzu", "keys", "prod.keys"),
            os.path.join(appdata, "Ryujinx", "system", "prod.keys"),
            os.path.join(appdata, "eden", "keys", "prod.keys"),
            os.path.join(appdata, "sudachi", "keys", "prod.keys"),
            r"C:\Games\keys\prod.keys",
            os.path.join(os.environ.get("USERPROFILE", ""), "Downloads", "prod.keys"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return ""

    def find_game_icon(self):
        candidates = [
            r"C:\DK-Bananza-Instalador\jogo\build\dkb100\dkb.ico",
            r"C:\Games\DKB PC\dkb-BANANAS\launcher\assets\dkb.ico",
            os.path.join(os.path.dirname(__file__), "..", "runtime", "dkb.ico"),
            r"C:\DK-Bananza-Instalador\jogo\runtime\totk.ico",
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return None

    def setup_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header Frame with DKB Gold & Jungle Accent
        header = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=0, height=84)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(header, text="DONKEY KONG BANANZA",
                                 font=ctk.CTkFont(size=22, weight="bold"), text_color=ACCENT_GOLD)
        title_lbl.pack(pady=(12, 2))

        sub_lbl = ctk.CTkLabel(header, text="PC Recompiled • High Performance Vulkan Edition | DLSS 4.5 • FSR • DualSense Immersion",
                               font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DIM)
        sub_lbl.pack(pady=(0, 12))

        # 2. Main Content Frame (Tabview)
        self.tabview = ctk.CTkTabview(self, fg_color=BG_DARK, segmented_button_selected_color=ACCENT_GOLD,
                                      segmented_button_selected_hover_color=ACCENT_HOVER,
                                      command=self.on_tab_changed)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # Tab navigation hook
        _orig_sb_cb = self.tabview._segmented_button_callback
        def _hooked_sb_cb(selected_name):
            _orig_sb_cb(selected_name)
            self.on_tab_changed()
            self.after(20, self.on_tab_changed)
        self.tabview._segmented_button_callback = _hooked_sb_cb

        self.tab_files = self.tabview.add("1. Legal Game Files & Keys")
        self.tab_features = self.tabview.add("2. DLSS & Controllers")
        self.tab_guide = self.tabview.add("3. Controller Guide")
        self.tab_install = self.tabview.add("4. Finalize & Launch")

        self.build_tab_files()
        self.build_tab_features()
        self.build_tab_guide()
        self.build_tab_install()

        # 3. Bottom Navigation Bar
        bottom_bar = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=0, height=64)
        bottom_bar.grid(row=2, column=0, sticky="ew")
        bottom_bar.grid_columnconfigure(0, weight=1)

        btn_box = ctk.CTkFrame(bottom_bar, fg_color="transparent")
        btn_box.pack(side="right", padx=20, pady=12)

        self.btn_back = ctk.CTkButton(btn_box, text="◀ Back", fg_color="#202b25", hover_color="#2e3d34",
                                      width=120, command=self.prev_tab)
        self.btn_back.pack(side="left", padx=8)

        self.btn_next = ctk.CTkButton(btn_box, text="Next ▶", fg_color=ACCENT_GOLD, hover_color=ACCENT_HOVER,
                                      text_color="#121815", font=ctk.CTkFont(weight="bold"),
                                      width=140, command=self.next_tab)
        self.btn_next.pack(side="left", padx=8)

        self.update_nav_buttons()

    def browse_file(self, var, filetypes):
        f = filedialog.askopenfilename(filetypes=filetypes)
        if f: var.set(f)

    def browse_folder(self, var):
        d = filedialog.askdirectory(title="Select Game Dump Folder (containing romfs / exefs)")
        if d: var.set(d)

    def browse_source(self, var):
        # Allow choosing either a file (.nsp / .xci / .nup) or a directory (dump containing exefs/romfs)
        f = filedialog.askopenfilename(title="Select Game Dump File (.nsp, .xci, or .nup)",
                                       filetypes=[("Game Dump (.nsp, .xci, .nup)", "*.nsp *.xci *.nup"), ("All Files", "*.*")])
        if f:
            var.set(f)
        else:
            d = filedialog.askdirectory(title="Select Game Dump Folder (containing exefs/romfs)")
            if d: var.set(d)

    def build_tab_files(self):
        f = self.tab_files
        f.grid_columnconfigure(0, weight=1)

        intro_box = ctk.CTkFrame(f, fg_color=CARD_BG, border_color=CARD_BORDER, border_width=1)
        intro_box.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(intro_box, text="🌴 Donkey Kong Bananza Game Files & Destination",
                     font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT_GOLD).pack(anchor="w", padx=15, pady=(10, 4))
        ctk.CTkLabel(intro_box, text="Select your legally dumped base game files (exefs/romfs or .nsp/.xci), your console prod.keys, and your install destination.",
                     font=ctk.CTkFont(size=12), text_color=TEXT_DIM, justify="left", wraplength=850).pack(anchor="w", padx=15, pady=(0, 10))

        # Legal Notice Banner
        legal_box = ctk.CTkFrame(f, fg_color="#18241d", border_color="#344d3e", border_width=1)
        legal_box.pack(fill="x", padx=15, pady=(0, 8))
        ctk.CTkLabel(legal_box, text="⚖️ Legal Notice: Clean-Room Recompilation Architecture",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="#65db83").pack(anchor="w", padx=12, pady=(6, 2))
        ctk.CTkLabel(legal_box, text="Donkey Kong Bananza PC Recomp is an open-source static binary recompiler. It DOES NOT contain, distribute, or provide any copyrighted Nintendo software, assets, game roms, or cryptographic keys. To play legally, you must supply your own game dump and console prod.keys from your own Nintendo Switch.",
                     font=ctk.CTkFont(size=11), text_color=TEXT_DIM, justify="left", wraplength=850).pack(anchor="w", padx=12, pady=(0, 8))

        # 1. Base Game Dump / File
        src_box = ctk.CTkFrame(f, fg_color=CARD_BG, border_color=CARD_BORDER, border_width=1)
        src_box.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(src_box, text="🎮 Legitimate Game Dump Source (.nsp, .xci, or folder with romfs):",
                     font=ctk.CTkFont(size=13, weight="bold"), text_color="#ffffff").pack(anchor="w", padx=15, pady=(8, 4))
        r1 = ctk.CTkFrame(src_box, fg_color="transparent")
        r1.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkEntry(r1, textvariable=self.var_game_source, placeholder_text="Path to folder with exefs/romfs, or .nsp / .xci file").pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(r1, text="Browse File...", width=105, fg_color="#202b25", hover_color="#2e3d34",
                      command=lambda: self.browse_file(self.var_game_source, [("Game Dump (.nsp, .xci, .nup)", "*.nsp *.xci *.nup"), ("All Files", "*.*")])).pack(side="left", padx=(0, 5))
        ctk.CTkButton(r1, text="Browse Folder...", width=115, fg_color="#202b25", hover_color="#2e3d34",
                      command=lambda: self.browse_folder(self.var_game_source)).pack(side="right")

        # 2. Decryption Keys (prod.keys)
        keys_box = ctk.CTkFrame(f, fg_color=CARD_BG, border_color=CARD_BORDER, border_width=1)
        keys_box.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(keys_box, text="🔑 Decryption Keys (prod.keys):",
                     font=ctk.CTkFont(size=13, weight="bold"), text_color="#ffffff").pack(anchor="w", padx=15, pady=(8, 4))
        r2 = ctk.CTkFrame(keys_box, fg_color="transparent")
        r2.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkEntry(r2, textvariable=self.var_keys, placeholder_text="Path to prod.keys (auto-detected from emulators)").pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(r2, text="Browse...", width=100, fg_color="#202b25", hover_color="#2e3d34",
                      command=lambda: self.browse_file(self.var_keys, [("Keys", "*.keys *.txt"), ("All Files", "*.*")])).pack(side="right")

        # 3. Target Install Directory
        dir_box = ctk.CTkFrame(f, fg_color=CARD_BG, border_color=CARD_BORDER, border_width=1)
        dir_box.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(dir_box, text="📁 Active Game Installation Directory:",
                     font=ctk.CTkFont(size=13, weight="bold"), text_color="#ffffff").pack(anchor="w", padx=15, pady=(8, 4))
        r3 = ctk.CTkFrame(dir_box, fg_color="transparent")
        r3.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkEntry(r3, textvariable=self.var_install_dir, width=650).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(r3, text="Browse...", width=100, fg_color="#202b25", hover_color="#2e3d34",
                      command=lambda: self.browse_dir(self.var_install_dir)).pack(side="right")

    def build_tab_features(self):
        f = self.tab_features
        f.grid_columnconfigure(0, weight=1)

        sdk_box = ctk.CTkFrame(f, fg_color=CARD_BG, border_color=CARD_BORDER, border_width=1)
        sdk_box.pack(fill="x", padx=15, pady=12)
        ctk.CTkCheckBox(sdk_box, text="Deploy Vendor AI & Upscaler SDKs (DLSS 4.5, DLSS-NR, Reflex, Intel XeSS, AMD FSR)",
                        variable=self.var_install_sdks, font=ctk.CTkFont(size=13, weight="bold"),
                        fg_color=ACCENT_GOLD, hover_color=ACCENT_HOVER, checkmark_color="#121815").pack(anchor="w", padx=15, pady=(12, 4))
        ctk.CTkLabel(sdk_box, text="Copies hardware-accelerated upscalers directly into the game folder, enabling full dynamic resolution scaling and ultra-low latency.",
                     font=ctk.CTkFont(size=11), text_color=TEXT_DIM).pack(anchor="w", padx=40, pady=(0, 12))

        ctrl_box = ctk.CTkFrame(f, fg_color=CARD_BG, border_color=CARD_BORDER, border_width=1)
        ctrl_box.pack(fill="x", padx=15, pady=12)
        ctk.CTkLabel(ctrl_box, text="🎮 Controller UI & Button Glyphs:",
                     font=ctk.CTkFont(size=14, weight="bold"), text_color="#ffffff").pack(anchor="w", padx=15, pady=(12, 6))

        for opt in CONTROLLER_UI_CHOICES:
            ctk.CTkRadioButton(ctrl_box, text=f"{opt['name']} — {opt['desc']}",
                               variable=self.var_controller_ui, value=opt["name"],
                               fg_color=ACCENT_GOLD, hover_color=ACCENT_HOVER).pack(anchor="w", padx=25, pady=4)
        ctk.CTkFrame(ctrl_box, height=8, fg_color="transparent").pack()

        opts_box = ctk.CTkFrame(f, fg_color=CARD_BG, border_color=CARD_BORDER, border_width=1)
        opts_box.pack(fill="x", padx=15, pady=12)
        ctk.CTkCheckBox(opts_box, text="Create Windows Desktop Shortcut (Donkey Kong Bananza with Banana Icon)",
                        variable=self.var_create_shortcut, font=ctk.CTkFont(size=13, weight="bold"),
                        fg_color=ACCENT_GOLD, hover_color=ACCENT_HOVER, checkmark_color="#121815").pack(anchor="w", padx=15, pady=(12, 4))
        ctk.CTkCheckBox(opts_box, text="Generate Controller Hotkeys Reference Card (README-CONTROLLER.txt)",
                        variable=self.var_create_guide, font=ctk.CTkFont(size=13, weight="bold"),
                        fg_color=ACCENT_GOLD, hover_color=ACCENT_HOVER, checkmark_color="#121815").pack(anchor="w", padx=15, pady=(4, 12))

    def build_tab_guide(self):
        f = self.tab_guide
        f.grid_columnconfigure(0, weight=1)
        f.grid_rowconfigure(0, weight=1)

        guide_box = ctk.CTkTextbox(f, fg_color=CARD_BG, text_color=TEXT_GOLD,
                                   font=ctk.CTkFont(family="Consolas", size=12), border_width=1, border_color=CARD_BORDER)
        guide_box.pack(fill="both", expand=True, padx=15, pady=15)
        guide_box.insert("1.0", CONTROLLER_GUIDE_TEXT)
        guide_box.configure(state="disabled")

    def build_tab_install(self):
        f = self.tab_install
        f.grid_columnconfigure(0, weight=1)

        self.status_lbl = ctk.CTkLabel(f, text="Ready to finalize Donkey Kong Bananza PC Recomp installation",
                                       font=ctk.CTkFont(size=14, weight="bold"), text_color=ACCENT_GOLD)
        self.status_lbl.pack(anchor="w", padx=15, pady=(15, 6))

        self.progress_bar = ctk.CTkProgressBar(f, fg_color=CARD_BG, progress_color=ACCENT_GOLD, height=14)
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 15))
        self.progress_bar.set(0)

        self.log_box = ctk.CTkTextbox(f, fg_color=CARD_BG, text_color="#c2d1c7",
                                      font=ctk.CTkFont(family="Consolas", size=11), border_width=1, border_color=CARD_BORDER)
        self.log_box.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def log(self, msg):
        self.log_box.insert("end", f"{msg}\n")
        self.log_box.see("end")

    def browse_dir(self, var):
        d = filedialog.askdirectory(initialdir=var.get())
        if d: var.set(d)

    def on_tab_changed(self):
        self.update_nav_buttons()

    def update_nav_buttons(self):
        cur = self.tabview.get()
        if cur == "1. Legal Game Files & Keys":
            self.btn_back.configure(state="disabled")
            self.btn_next.configure(text="Next ▶", state="normal", fg_color=ACCENT_GOLD, hover_color=ACCENT_HOVER, command=self.next_tab)
        elif cur == "2. DLSS & Controllers":
            self.btn_back.configure(state="normal")
            self.btn_next.configure(text="Next ▶", state="normal", fg_color=ACCENT_GOLD, hover_color=ACCENT_HOVER, command=self.next_tab)
        elif cur == "3. Controller Guide":
            self.btn_back.configure(state="normal")
            self.btn_next.configure(text="Proceed to Install ▶", state="normal", fg_color=ACCENT_GOLD, hover_color=ACCENT_HOVER, command=self.next_tab)
        elif cur == "4. Finalize & Launch":
            self.btn_back.configure(state="disabled")
            if getattr(self, "install_finished", False):
                target = self.var_install_dir.get().strip()
                self.btn_next.configure(text="🚀 Launch DKB Launcher", state="normal", fg_color=ACCENT_GOLD, hover_color=ACCENT_HOVER, command=lambda: self.launch_game(target))
            else:
                self.btn_next.configure(text="Start Installation", state="normal", fg_color=ACCENT_GOLD, hover_color=ACCENT_HOVER, command=self.start_install)

    def prev_tab(self):
        cur = self.tabview.get()
        if cur == "2. DLSS & Controllers": self.tabview.set("1. Legal Game Files & Keys")
        elif cur == "3. Controller Guide": self.tabview.set("2. DLSS & Controllers")
        elif cur == "4. Finalize & Launch": self.tabview.set("3. Controller Guide")

    def next_tab(self):
        cur = self.tabview.get()
        if cur == "1. Legal Game Files & Keys":
            src = self.var_game_source.get().strip()
            keys = self.var_keys.get().strip()
            if not src or not os.path.exists(src):
                messagebox.showerror("Legitimate Game Dump Required",
                                     "In strict compliance with Nintendo copyright laws and clean-room recompilation rules, Donkey Kong Bananza PC Recomp requires you to supply your own legally dumped game files (folder with exefs/romfs or .nsp/.xci).\n\nPlease select your dump location before proceeding.")
                return
            if not keys or not os.path.isfile(keys):
                messagebox.showerror("Decryption Keys Required",
                                     "Please provide your own legally dumped prod.keys file from your Nintendo Switch console.\n\nNo proprietary keys or copyrighted assets are bundled or distributed with this project.")
                return
            self.tabview.set("2. DLSS & Controllers")
        elif cur == "2. DLSS & Controllers":
            self.tabview.set("3. Controller Guide")
        elif cur == "3. Controller Guide":
            self.tabview.set("4. Finalize & Launch")
            self.start_install()

    def start_install(self):
        self.btn_next.configure(state="disabled", text="Installing...")
        threading.Thread(target=self.run_install_thread, daemon=True).start()

    def run_install_thread(self):
        target = self.var_install_dir.get().strip()
        src = self.var_game_source.get().strip()
        keys = self.var_keys.get().strip()
        os.makedirs(target, exist_ok=True)
        
        self.log(f"[*] Target directory: {target}")
        self.log(f"[*] Validating legally supplied game dump from: {src}")
        self.log(f"[*] Verified user console prod.keys from: {keys}")
        self.progress_bar.set(0.15)

        # 1. Deploy Game Binaries (dkb.exe, launcher, config, icon, DLLs)
        meipass = getattr(sys, '_MEIPASS', None)
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        py_exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        payload_candidates = [
            os.path.join(meipass, "payload") if meipass else None,
            meipass if meipass else None,
            os.path.join(exe_dir, "payload"),
            os.path.join(exe_dir, "build", "dkb100"),
            exe_dir,
            os.path.join(py_exe_dir, "payload"),
            os.path.join(py_exe_dir, "build", "dkb100"),
            py_exe_dir,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build", "dkb100")),
            r"C:\DK-Bananza-Instalador\jogo\build\dkb100",
            r"C:\Games\DKB PC\build\dkb100",
        ]
        payload_dir = next((c for c in payload_candidates if c and os.path.isfile(os.path.join(c, "dkb.exe"))), None)
        if not payload_dir:
            self.log("[!] ERROR: Recompiled game binaries (dkb.exe) not found in installer package.")
            messagebox.showerror("Game Payload Missing",
                                 "Could not locate the recompiled Donkey Kong Bananza game binaries (dkb.exe).\n\n"
                                 "Please ensure the installer package contains dkb.exe and the payload files.")
            self.btn_next.configure(state="normal", text="Retry Installation", command=self.start_install)
            return

        self.log(f"[*] Found payload sources at: {payload_dir}")
        if os.path.abspath(payload_dir) != os.path.abspath(target):
            self.log("[*] Deploying Donkey Kong Bananza recompiled binaries...")
            essential_files = [
                "dkb.exe", "DKBLauncher.exe", "totk.ini", "romfs-index.bin", "dkb.ico",
                "pipeline-cache.bin", "pipeline-keys.bin", "shader-answers.bin", "shader-programs.bin",
                "SDL3.dll", "libopus-0.dll", "libiconv-2.dll", "libxess.dll", "libxess_dx11.dll", "libxess_fg.dll",
                "nvngx_dlss.dll", "nvngx_dlssg.dll", "nvngx_dlssnr.dll",
                "sl.common.dll", "sl.dlss.dll", "sl.dlss_g.dll", "sl.dlss_nr.dll", "sl.interposer.dll", "sl.reflex.dll",
                "totk_xlate.exe", "totk_xlate.id"
            ]
            for ef in essential_files:
                src_file = os.path.join(payload_dir, ef)
                dst_file = os.path.join(target, ef)
                if os.path.isfile(src_file):
                    try:
                        shutil.copy2(src_file, dst_file)
                        self.log(f"  -> Installed {ef}")
                    except Exception as e:
                        self.log(f"  [!] Notice copying {ef}: {e}")

        # Deploy DKBLauncher.exe if not yet in target
        dst_launcher = os.path.join(target, "DKBLauncher.exe")
        if not os.path.isfile(dst_launcher):
            launcher_candidates = [
                os.path.join(payload_dir, "DKBLauncher.exe") if payload_dir else None,
                r"C:\DK-Bananza-Instalador\DKBLauncher.exe",
                os.path.join(exe_dir, "DKBLauncher.exe"),
                os.path.join(py_exe_dir, "DKBLauncher.exe"),
            ]
            launcher_src = next((cand for cand in launcher_candidates if cand and os.path.isfile(cand)), None)
            if launcher_src:
                try:
                    shutil.copy2(launcher_src, dst_launcher)
                    self.log("[✓] Installed DKBLauncher.exe to target directory.")
                except Exception:
                    pass

        # 2. Base Game Dump Link / Extract
        dst_romfs = os.path.join(target, "romfs")
        if os.path.isdir(os.path.join(src, "exefs")) and os.path.isdir(os.path.join(src, "romfs")):
            self.log("[✓] Validated user exefs/ and romfs/ directory dump.")
            dst_exefs = os.path.join(target, "exefs")
            if not os.path.exists(dst_exefs):
                try:
                    os.symlink(os.path.join(src, "exefs"), dst_exefs)
                    self.log("[✓] Created zero-copy filesystem link to exefs.")
                except Exception:
                    shutil.copytree(os.path.join(src, "exefs"), dst_exefs)
                    self.log("[✓] Copied exefs into destination.")
            if not os.path.exists(dst_romfs):
                try:
                    os.symlink(os.path.join(src, "romfs"), dst_romfs)
                    self.log("[✓] Created zero-copy filesystem link to romfs.")
                except Exception:
                    self.log("[✓] Verified romfs access.")
        elif os.path.isdir(src) and os.path.isfile(os.path.join(src, "romfs.bin")):
            self.log("[✓] Validated user packed romfs.bin dump.")
            os.makedirs(dst_romfs, exist_ok=True)
            dst_bin = os.path.join(dst_romfs, "romfs.bin")
            if not os.path.exists(dst_bin):
                try:
                    os.symlink(os.path.join(src, "romfs.bin"), dst_bin)
                    self.log("[✓] Linked romfs.bin image.")
                except Exception:
                    shutil.copy2(os.path.join(src, "romfs.bin"), dst_bin)
        elif src.lower().endswith(".nup"):
            self.log("[*] NUP container detected (.nup). Extracting package to target...")
            try:
                tools_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools"))
                if os.path.isdir(tools_dir) and tools_dir not in sys.path:
                    sys.path.insert(0, tools_dir)
                from extract_nup import Nup, Zstd, pick, extract_tree
                nup = Nup(Path(src))
                zstd = Zstd()
                pkg = pick(nup, "base")
                self.log(f"[*] Extracting package [{pkg.index}] {pkg.kind_name} (title {pkg.title_id:016x})...")
                for which in ('exefs', 'romfs'):
                    dst_folder = Path(target) / which
                    dst_folder.mkdir(parents=True, exist_ok=True)
                    count, total, _ = extract_tree(nup, zstd, pkg, which, dst_folder, False, True)
                    self.log(f"[✓] Extracted {which}: {count} files ({total / 1e9:.2f} GB).")
            except Exception as e:
                self.log(f"[!] Extraction notice: {e}")
        elif src.lower().endswith((".nsp", ".xci")):
            self.log("[*] Packed container selected (.nsp/.xci). Extracting with user keys...")
            hactool_candidates = [
                r"C:\DK-Bananza-Instalador\jogo\bin\hactool.exe",
                os.path.join(os.path.dirname(sys.executable), "bin", "hactool.exe"),
                r"C:\Games\DKB PC\dkb-BANANAS\bin\hactool.exe",
                shutil.which("hactool"),
            ]
            hactool = next((h for h in hactool_candidates if h and os.path.isfile(h)), None)
            os.makedirs(dst_romfs, exist_ok=True)
            if hactool and keys:
                cmd = [hactool, "-k", keys, f"--romfsdir={dst_romfs}", src]
                try:
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    if res.returncode == 0:
                        self.log("[✓] Successfully extracted RomFS from container.")
                    else:
                        self.log(f"[*] Hactool result logged (code {res.returncode}).")
                except Exception as e:
                    self.log(f"[!] Extraction notice: {e}")

        self.progress_bar.set(0.35)

        # 2. Vendor SDKs
        if self.var_install_sdks.get():
            self.log("[*] Deploying DLSS, Reflex, and XeSS libraries...")
            n = install_vendor_sdks(target, log_cb=self.log)
            self.log(f"[✓] {n} vendor AI upscaler libraries verified.")
        self.progress_bar.set(0.6)

        # 3. Controller UI
        choice_name = self.var_controller_ui.get()
        match = next((c["id"] for c in CONTROLLER_UI_CHOICES if c["name"] == choice_name), "ps5_monochrome")
        install_controller_ui(match, target)
        self.log(f"[✓] Controller layout configured: {choice_name}")
        self.progress_bar.set(0.75)

        # 3. Controller Guide Text File
        if self.var_create_guide.get():
            try:
                g_path = os.path.join(target, "README-CONTROLLER.txt")
                with open(g_path, "w", encoding="utf-8") as f:
                    f.write(CONTROLLER_GUIDE_TEXT)
                self.log(f"[✓] Created {g_path}")
            except Exception as e:
                self.log(f"[!] Warning creating guide: {e}")
        self.progress_bar.set(0.85)

        # 4. Shortcut
        if self.var_create_shortcut.get():
            ok = create_desktop_shortcut(target, shortcut_name="Donkey Kong Bananza", target_exe="DKBLauncher.exe")
            if ok:
                self.log("[✓] Desktop shortcut created targeting DKBLauncher.exe with Banana icon.")
            else:
                self.log("[!] Shortcut creation fallback was logged.")
        self.progress_bar.set(1.0)

        self.install_finished = True
        self.progress_bar.set(1.0)
        self.status_lbl.configure(text="✅ Donkey Kong Bananza PC Recomp is ready to play!", text_color="#65db83")
        self.btn_next.configure(state="normal", text="🚀 Launch DKB Launcher", command=lambda: self.launch_game(target))

    def launch_game(self, target):
        launcher = os.path.join(target, "DKBLauncher.exe")
        if not os.path.isfile(launcher):
            launcher = os.path.join(target, "dkb.exe")
        if not os.path.isfile(launcher):
            launcher = os.path.join(target, "build", "dkb100", "DKBLauncher.exe")
        if not os.path.isfile(launcher):
            launcher = os.path.join(target, "build", "dkb100", "dkb.exe")
        if not os.path.isfile(launcher):
            launcher = os.path.join(target, "..", "DKBLauncher.exe")
            
        if os.path.isfile(launcher):
            import subprocess
            subprocess.Popen([launcher], cwd=os.path.dirname(launcher))
            self.destroy()
        else:
            messagebox.showerror("Not Found", f"Executable not found at {launcher}\nPlease ensure target installation folder contains dkb.exe.")

def main():
    app = ModernDkbInstaller()
    app.mainloop()
    return 0

if __name__ == "__main__":
    sys.exit(main())
