"""Controller UI Manager for Donkey Kong Bananza PC Recompiled Installer."""

import os
import shutil
from typing import List, Dict, Optional

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
    """Configures the selected controller layout in totk.ini / dkb.ini."""
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
