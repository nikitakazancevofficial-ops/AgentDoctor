"""OpenAI Codex CLI provider."""

from __future__ import annotations

import os
from pathlib import Path

from agentdoctor.providers.base import BaseProvider


class CodexProvider(BaseProvider):
    name = "Codex CLI"

    def detect(self) -> bool:
        import shutil

        return shutil.which("codex") is not None

    def get_version(self) -> str | None:
        import shutil

        cmd = shutil.which("codex")
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
            codex_dir = Path(home) / ".codex"
            if codex_dir.exists():
                for f in codex_dir.rglob("*.json"):
                    configs.append(f)
        return configs
