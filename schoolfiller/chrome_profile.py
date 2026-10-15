"""Locate Google Chrome and a named Chrome profile on Windows and macOS."""

import json
import os
import platform
import shutil
import subprocess
from pathlib import Path


def chrome_user_data_dir():
    system = platform.system()
    if system == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "User Data"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
    return Path.home() / ".config" / "google-chrome"


def chrome_executable():
    system = platform.system()
    candidates = []
    if system == "Windows":
        for env in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            base = os.environ.get(env)
            if base:
                candidates.append(Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe")
    elif system == "Darwin":
        candidates.append(Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))
        candidates.append(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    for path in candidates:
        if path.exists():
            return str(path)
    for name in ("google-chrome", "google-chrome-stable", "chrome", "chromium"):
        found = shutil.which(name)
        if found:
            return found
    return None


def list_profiles(user_data_dir=None):
    """Return {directory_name: display_name} from Chrome's Local State file."""
    user_data_dir = Path(user_data_dir) if user_data_dir else chrome_user_data_dir()
    local_state = user_data_dir / "Local State"
    try:
        data = json.loads(local_state.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    cache = data.get("profile", {}).get("info_cache", {})
    return {directory: info.get("name", "") for directory, info in cache.items()}


def find_profile(name="school", user_data_dir=None):
    """Return the profile directory (e.g. "Profile 2") whose name matches, ignoring case."""
    wanted = name.strip().lower()
    for directory, display in list_profiles(user_data_dir).items():
        if display.strip().lower() == wanted:
            return directory
    return None


def open_in_profile(url, profile_directory):
    """Open url in a new tab of the given Chrome profile."""
    exe = chrome_executable()
    if not exe:
        raise RuntimeError("Google Chrome was not found on this computer.")
    subprocess.Popen([exe, f"--profile-directory={profile_directory}", url])
