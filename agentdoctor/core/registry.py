"""Check registry for discoverable diagnostic checks."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from agentdoctor.core.models import CheckResult

logger = logging.getLogger(__name__)

# Registry of check functions: category -> list of (check_func, check_meta)
_REGISTRY: dict[str, list[tuple[Callable[..., list[CheckResult]], dict[str, Any]]]] = {}


def register_check(
    category: str, **meta: Any
) -> Callable[[Callable[..., list[CheckResult]]], Callable[..., list[CheckResult]]]:
    """Decorator to register a check function in the registry."""

    def decorator(func: Callable[..., list[CheckResult]]) -> Callable[..., list[CheckResult]]:
        if category not in _REGISTRY:
            _REGISTRY[category] = []
        _REGISTRY[category].append((func, meta))
        return func

    return decorator


def get_registered_checks(
    category: str | None = None,
) -> dict[str, list[tuple[Callable[..., list[CheckResult]], dict[str, Any]]]]:
    """Get all registered checks, optionally filtered by category."""
    if category:
        return {category: _REGISTRY.get(category, [])}
    return dict(_REGISTRY)


def list_check_ids() -> list[str]:
    """List all registered check categories."""
    return sorted(_REGISTRY.keys())


def get_all_check_metadata() -> dict[str, list[dict[str, Any]]]:
    """Get metadata for all registered checks."""
    result = {}
    for category, checks in _REGISTRY.items():
        result[category] = [meta for _, meta in checks]
    return result
