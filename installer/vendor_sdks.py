"""Vendor SDK Manager for Donkey Kong Bananza PC Recompiled.

Handles deployment and optional downloading of vendor-specific AI and upscaler libraries:
- NVIDIA: DLSS (Super Resolution), DLSS-NR (Neural Reconstruction), DLSS-FG (Frame Generation)
- Intel: XeSS (Super Sampling & Frame Generation)
- AMD: FSR 3 / FidelityFX SDK
"""

import os
import shutil
from typing import Callable, Optional, Dict, List

VENDOR_SDK_FILES = [
    # NVIDIA AI / DLSS stack
    {"name": "nvngx_dlss.dll", "desc": "NVIDIA DLSS 4.5 / Super Resolution", "vendor": "NVIDIA"},
    {"name": "nvngx_dlssnr.dll", "desc": "NVIDIA DLSS-NR Neural Reconstruction", "vendor": "NVIDIA"},
    {"name": "nvngx_dlssg.dll", "desc": "NVIDIA DLSS Frame Generation", "vendor": "NVIDIA"},
    {"name": "sl.common.dll", "desc": "NVIDIA Streamline Common", "vendor": "NVIDIA"},
    {"name": "sl.dlss.dll", "desc": "NVIDIA Streamline DLSS plugin", "vendor": "NVIDIA"},
    {"name": "sl.dlss_g.dll", "desc": "NVIDIA Streamline DLSS-G plugin", "vendor": "NVIDIA"},
    {"name": "sl.dlss_nr.dll", "desc": "NVIDIA Streamline DLSS-NR plugin", "vendor": "NVIDIA"},
    {"name": "sl.interposer.dll", "desc": "NVIDIA Streamline Interposer", "vendor": "NVIDIA"},
    {"name": "sl.reflex.dll", "desc": "NVIDIA Reflex Low Latency", "vendor": "NVIDIA"},
    
    # Intel XeSS stack
    {"name": "libxess.dll", "desc": "Intel XeSS Super Sampling SDK", "vendor": "Intel"},
    {"name": "libxess_fg.dll", "desc": "Intel XeSS Frame Generation", "vendor": "Intel"},
    {"name": "libxell.dll", "desc": "Intel Low Latency", "vendor": "Intel"},
    {"name": "libxess_dx11.dll", "desc": "Intel XeSS DX11 Bridge", "vendor": "Intel"},
]

def find_local_sdk_cache(dll_name: str) -> Optional[str]:
    """Finds vendor SDK DLL in system caches or prior installations."""
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

def install_vendor_sdks(target_game_dir: str, log_cb: Optional[Callable[[str], None]] = None) -> int:
    """Installs all available vendor AI/upscaler DLLs into target_game_dir."""
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
