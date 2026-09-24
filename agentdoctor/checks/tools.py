"""Dev tool detection: Python, Node, Git, Docker, etc."""

from __future__ import annotations

from agentdoctor.core.models import SHORT_TIMEOUT, CheckResult, CheckSeverity, CheckStatus
from agentdoctor.core.registry import register_check
from agentdoctor.core.runner import run_command_sync


def _check_tool(name: str) -> tuple[bool, str]:
    """Check if a tool is available and get its version."""
    r = run_command_sync([name, "--version"], timeout=SHORT_TIMEOUT)
    if r.success and r.stdout.strip():
        version = r.stdout.strip().split("\n")[0].strip()
        return True, version
    return False, ""


@register_check("tools")
def check_tools() -> list[CheckResult]:
    """Check for installed development tools and AI coding tools."""
    results = []

    # Development tools
    tools = [
        ("python", "Python"),
        ("python3", "Python3"),
        ("pip", "pip"),
        ("node", "Node.js"),
        ("npm", "npm"),
        ("npx", "npx"),
        ("git", "Git"),
    ]

    for cmd, label in tools:
        found, version = _check_tool(cmd)
        if found:
            results.append(
                CheckResult(
                    id=f"TOOL_{label.upper().replace('.', '')}_OK",
                    category="tools",
                    name=label,
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.LOW,
                    summary=f"{label} {version}",
                    detected_value=version,
                )
            )
        else:
            results.append(
                CheckResult(
                    id=f"TOOL_{label.upper().replace('.', '')}_MISSING",
                    category="tools",
                    name=label,
                    status=CheckStatus.WARNING,
                    severity=CheckSeverity.MEDIUM,
                    summary=f"{label} not found",
                    detected_value="not installed",
                    expected_value="installed",
                )
            )

    # Optional tools
    optional_tools = [
        ("pipx", "pipx"),
        ("uv", "uv"),
        ("pnpm", "pnpm"),
        ("yarn", "yarn"),
        ("bun", "bun"),
        ("curl", "curl"),
        ("ssh", "ssh"),
        ("bash", "bash"),
        ("zsh", "zsh"),
    ]

    for cmd, label in optional_tools:
        found, version = _check_tool(cmd)
        if found:
            results.append(
                CheckResult(
                    id=f"TOOL_{label.upper()}_OK",
                    category="tools",
                    name=label,
                    status=CheckStatus.INFO,
                    severity=CheckSeverity.LOW,
                    summary=f"{label} {version}",
                    detected_value=version,
                )
            )

    return results
