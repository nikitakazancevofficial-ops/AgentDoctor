"""Claude Code provider."""

from __future__ import annotations

import os
from pathlib import Path

from agentdoctor.providers.base import BaseProvider


class ClaudeProvider(BaseProvider):
    name = "Claude Code"

    def detect(self) -> bool:
        import shutil

        return shutil.which("claude") is not None

    def get_version(self) -> str | None:
        import shutil

        cmd = shutil.which("claude")
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
            claude_dir = Path(home) / ".claude"
            if claude_dir.exists():
                for f in claude_dir.rglob("*.json"):
                    configs.append(f)
        return configs
