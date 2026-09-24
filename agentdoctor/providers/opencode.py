"""OpenCode provider."""

from __future__ import annotations

import os
from pathlib import Path

from agentdoctor.providers.base import BaseProvider


class OpenCodeProvider(BaseProvider):
    name = "OpenCode"

    def detect(self) -> bool:
        import shutil

        return shutil.which("opencode") is not None

    def get_version(self) -> str | None:
        import shutil

        cmd = shutil.which("opencode")
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
            opencode_config = Path(home) / ".config" / "opencode.json"
            if opencode_config.exists():
                configs.append(opencode_config)
        return configs
