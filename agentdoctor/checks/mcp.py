"""MCP configuration discovery and validation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from agentdoctor.core.models import SHORT_TIMEOUT, CheckResult, CheckSeverity, CheckStatus
from agentdoctor.core.paths import get_config_dirs, get_home_dir
from agentdoctor.core.registry import register_check
from agentdoctor.core.runner import run_command_sync

# Binary file extensions that should never be parsed as JSON
_BINARY_EXTENSIONS = frozenset(
    {
        ".vscdb",
        ".sqlite",
        ".sqlite3",
        ".db",
        ".wal",
        ".shm",
        ".log",
        ".dat",
        ".bin",
        ".idx",
    }
)


def _is_binary_file(path: Path) -> bool:
    """Check if a file is likely a binary file (not a text config)."""
    if path.suffix.lower() in _BINARY_EXTENSIONS:
        return True
    # Also check first bytes for binary content
    try:
        with open(path, "rb") as f:
            chunk = f.read(8192)
            if b"\x00" in chunk:
                return True
    except (OSError, PermissionError):
        pass
    return False


def _find_mcp_configs() -> list[Path]:
    """Find MCP configuration files across known locations."""
    configs: list[Path] = []
    seen = set()

    def add_if_new(p: Path) -> bool:
        resolved = p.resolve()
        if resolved not in seen:
            seen.add(resolved)
            configs.append(p)
            return True
        return False

    # Known config locations (specific paths, not recursive glob)
    home = get_home_dir()
    locations = [
        home / ".claude" / ".mcp.json",
        home / ".config" / "mcp.json",
        home / ".config" / "mcp_config.json",
        home / ".codex" / "config.json",
    ]

    # Windows-specific
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            locations.append(Path(appdata) / "Claude" / "claude_desktop_config.json")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if localappdata:
            locations.append(Path(localappdata) / "Programs" / "claude" / "resources" / "app" / "mcp.json")

    # Linux-specific
    else:
        locations.extend(
            [
                home / ".config" / "claude" / ".mcp.json",
                home / ".config" / "opencode.json",
            ]
        )

    # macOS-specific
    if sys.platform == "darwin":
        locations.extend(
            [
                home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
            ]
        )

    # Add specific locations
    for loc in locations:
        if loc.exists():
            add_if_new(loc)

    # Quick search in known config dirs (limit depth)
    config_dirs = get_config_dirs()
    for d in config_dirs[:3]:  # Limit to first 3 config dirs
        if not d.exists():
            continue
        try:
            for item in d.iterdir():
                if item.is_dir():
                    for sub in item.iterdir():
                        if sub.is_file() and "mcp" in sub.name.lower():
                            add_if_new(sub)
        except (PermissionError, OSError):
            pass

    return configs


def _parse_mcp_config(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Parse an MCP config file. Returns (parsed_data, error)."""
    if _is_binary_file(path):
        return None, "Binary file, not a text config"
    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"Line {e.lineno}, column {e.colno}: {e.msg}"
    except Exception as e:
        return None, str(e)


def _validate_mcp_server(server_name: str, server_config: dict[str, Any]) -> list[CheckResult]:
    """Validate a single MCP server configuration."""
    results = []

    # Check for command-based (stdio) server
    if "command" in server_config:
        cmd = server_config["command"]
        if isinstance(cmd, str):
            cmd_parts = [cmd]
        elif isinstance(cmd, list):
            cmd_parts = list(cmd)
        else:
            cmd_parts = [str(cmd)]

        base_cmd = cmd_parts[0] if cmd_parts else ""

        # Check if base command exists
        r = run_command_sync([base_cmd, "--version"], timeout=SHORT_TIMEOUT)
        if not r.success:
            # Try just checking if it exists on PATH
            import shutil

            if not shutil.which(base_cmd):
                results.append(
                    CheckResult(
                        id="MCP_COMMAND_001",
                        category="mcp",
                        name=f"MCP server: {server_name}",
                        status=CheckStatus.ERROR,
                        severity=CheckSeverity.HIGH,
                        summary=f"MCP command '{base_cmd}' not found on PATH",
                        details=f"Server '{server_name}' requires '{base_cmd}' but it is not available.",
                        detected_value="not found",
                        expected_value="command on PATH",
                        recommendation=f"Install '{base_cmd}' or update the MCP configuration",
                    )
                )

        # Check for secrets in env
        env = server_config.get("env", {})
        if isinstance(env, dict):
            for env_key, env_val in env.items():
                val_str = str(env_val)
                if (
                    any(kw in env_key.upper() for kw in ["KEY", "TOKEN", "SECRET", "PASSWORD", "AUTH"])
                    and val_str
                    and val_str not in ("", "${}", "${" + env_key + "}", "$" + env_key)
                ):
                    results.append(
                        CheckResult(
                            id="MCP_SECRET_001",
                            category="mcp",
                            name=f"Secret in {server_name} env",
                            status=CheckStatus.WARNING,
                            severity=CheckSeverity.HIGH,
                            summary=f"Secret found in {server_name} environment variable",
                            details=f"Variable: {env_key} = [REDACTED]",
                            recommendation="Use environment variables or a secrets manager instead of hardcoding",
                        )
                    )

    # Check for URL-based (SSE/Streamable HTTP) server
    elif "url" in server_config:
        url = server_config["url"]
        if isinstance(url, str) and url.startswith(("http://", "https://")) and "@" in url:
            results.append(
                CheckResult(
                    id="MCP_SECRET_001",
                    category="mcp",
                    name=f"Secret in {server_name} URL",
                    status=CheckStatus.WARNING,
                    severity=CheckSeverity.HIGH,
                    summary=f"Credentials in {server_name} URL",
                    details=f"URL contains credentials: {url[:30]}...[REDACTED]",
                    recommendation="Use a different authentication method",
                )
            )

    return results


@register_check("mcp")
def check_mcp() -> list[CheckResult]:
    """Discover and validate MCP configurations."""
    results = []
    configs = _find_mcp_configs()

    if not configs:
        results.append(
            CheckResult(
                id="MCP_NOT_FOUND",
                category="mcp",
                name="MCP configs",
                status=CheckStatus.INFO,
                severity=CheckSeverity.LOW,
                summary="No MCP configurations found",
                details="No MCP server configurations were discovered in standard locations.",
            )
        )
        return results

    results.append(
        CheckResult(
            id="MCP_FOUND",
            category="mcp",
            name="MCP configs discovered",
            status=CheckStatus.INFO,
            severity=CheckSeverity.LOW,
            summary=f"{len(configs)} MCP config file{'s' if len(configs) != 1 else ''} found",
            details="\n".join(str(c) for c in configs[:5]),
        )
    )

    for config_path in configs:
        data, error = _parse_mcp_config(config_path)

        if error:
            results.append(
                CheckResult(
                    id="MCP_CONFIG_001",
                    category="mcp",
                    name=f"Config: {config_path.name}",
                    status=CheckStatus.ERROR,
                    severity=CheckSeverity.HIGH,
                    summary=f"Invalid JSON in {config_path.name}",
                    details=f"File: {config_path}\n{error}",
                    expected_value="valid JSON",
                    recommendation=f"Fix JSON syntax in {config_path}",
                )
            )
            continue

        if not isinstance(data, dict):
            results.append(
                CheckResult(
                    id="MCP_CONFIG_001",
                    category="mcp",
                    name=f"Config: {config_path.name}",
                    status=CheckStatus.ERROR,
                    severity=CheckSeverity.HIGH,
                    summary=f"Invalid MCP config structure in {config_path.name}",
                    details=f"Expected a JSON object, got {type(data).__name__}",
                    recommendation=f"Fix config structure in {config_path}",
                )
            )
            continue

        # Find server definitions
        servers = {}
        # Check various MCP config formats
        for key in ["mcpServers", "servers", "server", "commands"]:
            if key in data and isinstance(data[key], dict):
                servers = data[key]
                break

        if not servers:
            # Try nested mcpServers
            for key in ["mcp", "configuration", "config"]:
                if key in data and isinstance(data[key], dict):
                    nested = data[key]
                    if "mcpServers" in nested:
                        servers = nested["mcpServers"]
                        break

        if servers:
            for server_name, server_config in servers.items():
                if isinstance(server_config, dict):
                    results.extend(_validate_mcp_server(server_name, server_config))
            results.append(
                CheckResult(
                    id=f"MCP_SERVERS_{len(servers)}",
                    category="mcp",
                    name=f"Servers in {config_path.name}",
                    status=CheckStatus.INFO,
                    severity=CheckSeverity.LOW,
                    summary=f"{len(servers)} server{'s' if len(servers) != 1 else ''} defined",
                    details=", ".join(servers.keys()),
                )
            )
        else:
            results.append(
                CheckResult(
                    id="MCP_NO_SERVERS",
                    category="mcp",
                    name=f"Config: {config_path.name}",
                    status=CheckStatus.WARNING,
                    severity=CheckSeverity.LOW,
                    summary=f"No server definitions in {config_path.name}",
                    details="Config file exists but contains no server definitions.",
                    recommendation="Add server definitions to the config file",
                )
            )

    return results
