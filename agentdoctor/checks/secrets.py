"""Secret scanner: detect potential secrets in config files."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from agentdoctor.core.models import CheckResult, CheckSeverity, CheckStatus
from agentdoctor.core.registry import register_check

# Common secret patterns
_SECRET_PATTERNS = [
    (re.compile(r'["\'](?:api[_-]?key|apikey)["\']\s*[:=]\s*["\']([^"\']{16,})["\']', re.IGNORECASE), "API key"),
    (
        re.compile(r'["\'](?:secret|token|password|auth)["\']\s*[:=]\s*["\']([^"\']{8,})["\']', re.IGNORECASE),
        "Secret/token",
    ),
    (
        re.compile(
            r'(?:OPENAI|ANTHROPIC|GOOGLE|GITHUB|AWS)[_]?API[_]?KEY["\']?\s*[:=]\s*["\']?([^"\',\s]{8,})', re.IGNORECASE
        ),
        "AI API key",
    ),
    (re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}"), "Bearer token"),
    (re.compile(r"-----BEGIN\s+(?:RSA\s+|EC\s+|OPENSSH\s+)?PRIVATE\s+KEY-----"), "Private key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS key"),
    (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GitHub personal token"),
    (re.compile(r"ghs_[a-zA-Z0-9]{36}"), "GitHub server token"),
    (re.compile(r"github_pat_[a-zA-Z0-9_]{20,}"), "GitHub PAT"),
]


def _scan_content(content: str, filepath: str) -> list[CheckResult]:
    """Scan file content for potential secrets."""
    results = []
    for pattern, label in _SECRET_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            for match in matches[:3]:  # Limit matches shown
                matched_str = str(match)
                results.append(
                    CheckResult(
                        id="SECRET_DETECTED",
                        category="secrets",
                        name=f"Secret in {os.path.basename(filepath)}",
                        status=CheckStatus.WARNING,
                        severity=CheckSeverity.HIGH,
                        summary=f"Potential {label} found in {filepath}",
                        details=f"Pattern: {matched_str[:30]}...",
                        recommendation="Remove the secret from the config file and use environment variables instead",
                    )
                )
    return results


def _scan_dict(data: dict[str, Any], path: str = "") -> list[CheckResult]:
    """Recursively scan a dictionary for secrets."""
    results = []
    for key, value in data.items():
        current_path = f"{path}.{key}" if path else key
        if isinstance(value, str):
            for pattern, label in _SECRET_PATTERNS:
                if pattern.search(value):
                    results.append(
                        CheckResult(
                            id="SECRET_DETECTED",
                            category="secrets",
                            name=f"Secret in {current_path}",
                            status=CheckStatus.WARNING,
                            severity=CheckSeverity.HIGH,
                            summary=f"Potential {label} in config path '{current_path}'",
                            details=f"Value: {value[:20]}...",
                            recommendation="Use environment variables instead of hardcoding secrets",
                        )
                    )
                    break
        elif isinstance(value, dict):
            results.extend(_scan_dict(value, current_path))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict | str):
                    results.extend(_scan_dict({str(i): item}, current_path))
    return results


@register_check("secrets")
def check_secrets() -> list[CheckResult]:
    """Scan known config locations for accidentally committed secrets."""
    results = []

    # Config locations to scan
    scan_dirs = []

    home = os.environ.get("HOME") or os.environ.get("USERPROFILE", "")
    if home:
        scan_dirs.append(Path(home) / ".config")
        scan_dirs.append(Path(home) / ".claude")
        scan_dirs.append(Path(home) / ".codex")

    if os.environ.get("APPDATA"):
        scan_dirs.append(Path(os.environ["APPDATA"]) / "Claude")
    if os.environ.get("LOCALAPPDATA"):
        scan_dirs.append(Path(os.environ["LOCALAPPDATA"]) / "Claude")

    # Also scan current working directory for .env files
    cwd = os.getcwd()
    for env_file in [".env", ".env.local", ".env.development"]:
        env_path = Path(cwd) / env_file
        if env_path.exists():
            try:
                content = env_path.read_text()
                secrets = _scan_content(content, str(env_path))
                results.extend(secrets)
            except Exception:
                pass

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        try:
            for config_file in scan_dir.rglob("*.json"):
                if "node_modules" in str(config_file):
                    continue
                try:
                    content = config_file.read_text(encoding="utf-8", errors="replace")
                    secrets = _scan_content(content, str(config_file))
                    results.extend(secrets)
                    # Also scan parsed JSON
                    try:
                        data = json.loads(content)
                        if isinstance(data, dict):
                            results.extend(_scan_dict(data))
                    except json.JSONDecodeError:
                        pass
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError):
            pass

    if not results:
        results.append(
            CheckResult(
                id="SECRETS_OK",
                category="secrets",
                name="Secret scan",
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                summary="No obvious secrets found in scanned configs",
            )
        )

    return results
