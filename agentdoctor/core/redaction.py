"""Secret redaction utilities."""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Any, cast

from agentdoctor.core.models import CheckResult

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
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            re.IGNORECASE | re.DOTALL,
        ),
        "[REDACTED PRIVATE KEY]",
    ),
    (
        re.compile(r"(https?://)([^:/@\s]+):([^@\s]+)@"),
        r"\1[REDACTED]:[REDACTED]@",
    ),
]


def redact_secret(text: str | None) -> str:
    """Redact potential secrets from text.

    Never exposes actual secret values.
    """
    if not text:
        return text or ""

    result = text
    for pattern, replacement in _SECRET_PATTERNS:
        result = pattern.sub(replacement, result)

    return result


_SENSITIVE_KEY = re.compile(r"(?:api[_.-]?key|token|secret|password|authorization|auth)", re.IGNORECASE)


def _redact_value(value: Any, key: str | None = None) -> Any:
    """Recursively redact report data while preserving JSON-compatible structure."""
    if key and _SENSITIVE_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(child_key): _redact_value(child_value, str(child_key)) for child_key, child_value in value.items()}
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_value(item) for item in value)
    if isinstance(value, str):
        return redact_secret(value)
    return value


def redact_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively redact secrets from a dictionary and nested collections."""
    return cast("dict[str, Any]", _redact_value(d))


def sanitize_check_result(result: CheckResult) -> CheckResult:
    """Return a copy of a result safe to serialize or display publicly.

    Check producers should avoid storing credentials in the first place.  This is
    a defense-in-depth boundary for every renderer and CLI output path.
    """
    return replace(
        result,
        id=redact_secret(result.id),
        category=redact_secret(result.category),
        name=redact_secret(result.name),
        summary=redact_secret(result.summary),
        details=redact_secret(result.details),
        detected_value=redact_secret(result.detected_value) if result.detected_value is not None else None,
        expected_value=redact_secret(result.expected_value) if result.expected_value is not None else None,
        recommendation=redact_secret(result.recommendation),
        commands=[redact_secret(command) for command in result.commands],
        metadata=redact_dict(result.metadata),
    )


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
