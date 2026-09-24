"""Ollama provider."""

from __future__ import annotations

from agentdoctor.providers.base import BaseProvider


class OllamaProvider(BaseProvider):
    name = "Ollama"

    def detect(self) -> bool:
        import shutil

        return shutil.which("ollama") is not None

    def get_version(self) -> str | None:
        import shutil

        cmd = shutil.which("ollama")
        if not cmd:
            return None
        from agentdoctor.core.runner import run_command_sync

        r = run_command_sync([cmd, "--version"], timeout=3.0)
        if r.success and r.stdout.strip():
            return r.stdout.strip().split("\n")[0].strip()
        return None
