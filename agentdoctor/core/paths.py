"""Path discovery utilities for platform-specific config directories."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def get_config_dirs() -> list[Path]:
    """Get platform-specific config directories to search."""
    dirs: list[Path] = []

    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA", "")
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if app_data:
            dirs.append(Path(app_data))
        if local_app_data:
            dirs.append(Path(local_app_data))
    elif sys.platform == "darwin":
        home = os.environ.get("HOME", "")
        if home:
            dirs.append(Path(home) / "Library" / "Application Support")
    else:
        # Linux
        xdg_config = os.environ.get("XDG_CONFIG_HOME", "")
        if xdg_config:
            dirs.append(Path(xdg_config))
        home = os.environ.get("HOME", "")
        if home:
            dirs.append(Path(home) / ".config")

    return dirs


def get_home_dir() -> Path:
    """Get the user's home directory."""
    home = os.environ.get("HOME") or os.environ.get("USERPROFILE") or str(Path.home())
    return Path(home)


def find_config_files(name: str, dirs: list[Path] | None = None) -> list[Path]:
    """Find config files with a given name in config directories."""
    if dirs is None:
        dirs = get_config_dirs()

    results: list[Path] = []
    for d in dirs:
        if not d.exists():
            continue
        # Check direct
        candidate = d / name
        if candidate.exists():
            results.append(candidate)
        # Check subdirectories
        try:
            for sub in d.iterdir():
                if sub.is_dir() and not sub.name.startswith("."):
                    candidate = sub / name
                    if candidate.exists():
                        results.append(candidate)
        except PermissionError:
            pass

    return results
