"""Gemini CLI provider."""

from __future__ import annotations

import os
from pathlib import Path

from agentdoctor.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    name = "Gemini CLI"

    def detect(self) -> bool:
        import shutil

        return shutil.which("gemini") is not None

    def get_version(self) -> str | None:
        import shutil

        cmd = shutil.which("gemini")
        if not cmd:
            return None
        from agentdoctor.core.runner import run_command_sync

        r = run_command_sync([cmd, "--version"], timeout=3.0)
        if r.success and r.stdout.strip():
            return r.stdout.strip().split("\n")[0].strip()
        return None

    def find_configs(self) -> list[Path]:
        home = os.environ.get("HOME") or os.environ.get("USERPROFILE", "")
        configs = []
        if home:
            gemini_dir = Path(home) / ".config" / "gemini"
            if gemini_dir.exists():
                for f in gemini_dir.rglob("*.json"):
                    configs.append(f)
        return configs
