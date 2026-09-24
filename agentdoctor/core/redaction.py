"""Secret redaction utilities."""

from __future__ import annotations

import re
from typing import Any

# Patterns for detecting secrets
_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"(sk-proj-[a-zA-Z0-9]{20,})", re.IGNORECASE),
        r"sk-proj-[REDACTED]",
    ),
    (
        re.compile(r"(sk-ant-[a-zA-Z0-9]{20,})", re.IGNORECASE),
        r"sk-ant-[REDACTED]",
    ),
    (
        re.compile(r"(sk-[a-zA-Z0-9]{20,})", re.IGNORECASE),
        r"sk-[REDACTED]",
    ),
    (
        re.compile(r"(ghp_[a-zA-Z0-9]{36,})", re.IGNORECASE),
        r"ghp_[REDACTED]",
    ),
    (
        re.compile(r"(gho_[a-zA-Z0-9]{36,})", re.IGNORECASE),
        r"gho_[REDACTED]",
    ),
    (
        re.compile(r"(ghs_[a-zA-Z0-9]{36,})", re.IGNORECASE),
        r"ghs_[REDACTED]",
    ),
    (
        re.compile(r"(github_pat_[a-zA-Z0-9_]{20,})", re.IGNORECASE),
        r"github_pat_[REDACTED]",
    ),
    (
        re.compile(r"(glpat-[a-zA-Z0-9_\-]{20,})", re.IGNORECASE),
        r"glpat-[REDACTED]",
    ),
    (
        re.compile(r"(AKIA[0-9A-Z]{16})", re.IGNORECASE),
        r"AKIA-[REDACTED]",
    ),
    (
        re.compile(r"((?:Bearer|token)[\s:=]+)[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"(password[\"':=\s]+)([^\s\"'&,}{\n]+)"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"(secret[\"':=\s]+)([^\s\"'&,}{\n]+)"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"(api.?key[\"':=\s]+)([^\s\"'&,}{\n]+)"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"(-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"),
        r"\1",
    ),
    (
        re.compile(r"(https?://)([^:/@\s]+):([^@\s]+)@"),
        r"\1[REDACTED]:[REDACTED]@",
    ),
]


def redact_secret(text: str) -> str:
    """Redact potential secrets from text.

    Never exposes actual secret values.
    """
    if not text:
        return text or ""

    result = text
    for pattern, replacement in _SECRET_PATTERNS:
        result = pattern.sub(replacement, result)

    return result


def redact_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively redact secrets from a dictionary."""
    result: dict[str, Any] = {}
    for key, value in d.items():
        if isinstance(value, dict):
            result[key] = redact_dict(value)
        elif isinstance(value, list):
            result[key] = [redact_secret(str(v)) if isinstance(v, str) else v for v in value]
        elif isinstance(value, str):
            result[key] = redact_secret(value)
        else:
            result[key] = value
    return result


def redact_url(url: str) -> str:
    """Redact credentials from a URL."""
    if not url:
        return url or ""

    # Redact user:password from URLs
    url = re.sub(
        r"(https?://)([^:@/]+):([^@/]+)@([^@/]+)",
        r"\1[REDACTED]:[REDACTED]@\4",
        url,
    )
    return url


def mask_token(token: str | None, visible_chars: int = 4) -> str:
    """Mask a token showing only the first few characters."""
    if not token:
        return "NOT SET"
    if len(token) <= visible_chars:
        return "[REDACTED]"
    return token[:visible_chars] + "..." + token[-4:] if len(token) > 8 else token[:visible_chars] + "***"
