"""Desktop shortcut creator for Donkey Kong Bananza PC Recompiled."""

import os
import subprocess

def create_desktop_shortcut(game_dir: str, shortcut_name: str = "Donkey Kong Bananza", target_exe: str = None) -> bool:
    """Creates a Windows desktop shortcut pointing to DKBLauncher.exe (or dkb.exe) in game_dir."""
    try:
        desktop_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
        if not os.path.exists(desktop_dir):
            desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")

        shortcut_path = os.path.join(desktop_dir, f"{shortcut_name}.lnk")
        
        # Prefer DKBLauncher.exe if present
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
