"""Provider registry."""

from __future__ import annotations

from agentdoctor.providers.base import BaseProvider
from agentdoctor.providers.claude import ClaudeProvider
from agentdoctor.providers.codex import CodexProvider
from agentdoctor.providers.gemini import GeminiProvider
from agentdoctor.providers.ollama import OllamaProvider
from agentdoctor.providers.opencode import OpenCodeProvider

_PROVIDERS: list[type[BaseProvider]] = [
    CodexProvider,
    ClaudeProvider,
    GeminiProvider,
    OpenCodeProvider,
    OllamaProvider,
]


def get_providers() -> list[BaseProvider]:
    """Get all registered AI tool providers."""
    return [p() for p in _PROVIDERS]


def get_provider_by_name(name: str) -> BaseProvider | None:
    """Get a provider by tool name."""
    for p in _PROVIDERS:
        if p.name.lower() == name.lower():
            return p()
    return None
