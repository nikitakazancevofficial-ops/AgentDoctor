"""CLI definition for AgentDoctor."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, cast

import typer

from agentdoctor import __version__
from agentdoctor.core.models import (
    DEFAULT_TIMEOUT,
    CheckResult,
    CheckSeverity,
    CheckStatus,
    HealthScore,
    SystemInfo,
)
from agentdoctor.core.registry import get_registered_checks
from agentdoctor.knowledge.issues import get_issue_info
from agentdoctor.providers.registry import get_providers
from agentdoctor.renderers.json_renderer import render_json
from agentdoctor.renderers.markdown_renderer import render_markdown
from agentdoctor.renderers.rich_renderer import (
    render_header,
    render_health,
    render_recommendations,
    render_results,
    render_system_info,
)

app = typer.Typer(
    name="agentdoctor",
    help="Diagnose broken AI coding environments in one command.",
    add_completion=False,
    no_args_is_help=True,
)

# Global state
_g_results: dict[str, list[CheckResult]] = {}
_g_health = HealthScore()
_g_system_info = SystemInfo()
_g_verbose = False
_g_debug = False


def _run_check(check_func: Any, category: str, timeout: float) -> list[CheckResult]:
    """Run a check function with error handling."""
    start = time.time()
    try:
        result = check_func()
        if isinstance(result, tuple):
            results = result[0] if isinstance(result[0], list) else [result[0]]
        else:
            results = result if isinstance(result, list) else [result]
        for r in results:
            r.duration_ms = (time.time() - start) * 1000
        return results
    except Exception as e:
        duration = (time.time() - start) * 1000
        return [
            CheckResult(
                id=f"{category.upper()}_INTERNAL_ERROR",
                category=category,
                name=f"{category} check",
                status=CheckStatus.INTERNAL_ERROR,
                severity=CheckSeverity.HIGH,
                summary=f"Internal error in {category} check",
                details=str(e) if _g_debug else "Check failed with an error",
                duration_ms=duration,
            )
        ]


def _collect_results(
    categories: list[str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> tuple[dict[str, list[CheckResult]], HealthScore, SystemInfo]:
    """Run all checks and collect results."""
    global _g_results, _g_health, _g_system_info
    _g_results = {}
    _g_health = HealthScore()
    _g_system_info = SystemInfo()

    # Import all check modules to register them
    from agentdoctor.checks import system

    all_checks = get_registered_checks()
    results: list[CheckResult] = []

    # Run system checks first
    if not categories or "system" in categories:
        _sys_result = system.check_system()
        _sys_results, _sys_info = cast("tuple[list[CheckResult], SystemInfo]", _sys_result)
        results = _sys_results
        _g_results["system"] = results
        for r in results:
            _g_health.add_result(r)

    # Run all other checks
    for category in sorted(all_checks.keys()):
        if category == "system":
            continue
        if categories and category not in categories:
            continue
        checks = all_checks[category]
        for check_func, _meta in checks:
            results = _run_check(check_func, category, timeout)
            if category not in _g_results:
                _g_results[category] = []
            _g_results[category].extend(results)
            for r in results:
                _g_health.add_result(r)

    # Run AI tool providers
    if not categories or "tools" in categories:
        for provider in get_providers():
            try:
                results = provider.run_checks()
                for r in results:
                    r.category = "ai_tools"
                    if "ai_tools" not in _g_results:
                        _g_results["ai_tools"] = []
                    _g_results["ai_tools"].append(r)
                    _g_health.add_result(r)
            except Exception:
                pass

    return _g_results, _g_health, _g_system_info


@app.command()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug output"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colored output"),
    only: str | None = typer.Option(None, "--only", "-o", help="Run only specific check categories (comma-separated)"),
    skip: str | None = typer.Option(None, "--skip", "-s", help="Skip specific check categories (comma-separated)"),
    timeout: float = typer.Option(10.0, "--timeout", "-t", help="Timeout for individual checks in seconds"),
    output: str | None = typer.Option(
        None, "--output", "-O", help="Output file path (supports .json and .md extensions)"
    ),
    ci: bool = typer.Option(False, "--ci", help="CI mode: stable, machine-readable output"),
) -> None:
    """AgentDoctor - Diagnose your AI dev environment before debugging the AI."""
    global _g_verbose, _g_debug, _g_results, _g_health, _g_system_info

    _g_verbose = verbose
    _g_debug = debug

    # Parse only/skip
    categories: list[str] | None = None
    if only:
        categories = [c.strip() for c in only.split(",")]
    skip_categories: set[str] = set()
    if skip:
        skip_categories = {c.strip() for c in skip.split(",")}

    # Collect all results
    results, health, sys_info = _collect_results(categories, timeout)

    # Add skip markers
    if skip_categories:
        for category in skip_categories:
            if category in results:
                results[category] = [
                    CheckResult(
                        id=f"{category.upper()}_SKIPPED",
                        category=category,
                        name=f"{category} checks",
                        status=CheckStatus.SKIPPED,
                        severity=CheckSeverity.LOW,
                        summary=f"Skipped by user (--skip {category})",
                    )
                ]
                health.add_result(results[category][-1])

    _g_results = results
    _g_health = health
    _g_system_info = sys_info

    # Determine output mode
    if output:
        ext = Path(output).suffix.lower()
        if ext == ".json":
            content = render_json(results, health, sys_info, __version__)
        elif ext == ".md":
            content = render_markdown(results, health, sys_info, __version__)
        else:
            content = render_markdown(results, health, sys_info, __version__)
        Path(output).write_text(content, encoding="utf-8")
        typer.echo(f"Report written to {output}")
        sys.exit(1 if health.errors > 0 else 0)

    if json_output:
        content = render_json(results, health, sys_info, __version__)
        typer.echo(content)
        sys.exit(1 if health.errors > 0 else 0)

    if ci:
        # CI mode: plain text output
        for category, category_results in results.items():
            typer.echo(f"\n[{category.upper()}]")
            for r in category_results:
                status_str = r.status.value
                typer.echo(f"  {status_str} | {r.id} | {r.name} | {r.summary}")
        typer.echo(
            f"\nHealth: {health.score}/100 (passed={health.passed}, warnings={health.warnings}, errors={health.errors})"
        )
        sys.exit(1 if health.errors > 0 else 0)

    # Rich output
    typer.echo(render_header(__version__))
    typer.echo("\n[bold]Scanning your AI development environment...[/bold]\n")

    # System info
    typer.echo(render_system_info(sys_info))

    # Each category
    ordered_categories = [
        "system",
        "path",
        "ai_tools",
        "tools",
        "mcp",
        "network",
        "proxy",
        "ports",
        "docker",
        "ollama",
        "gpu",
        "git",
        "secrets",
    ]
    for cat in ordered_categories:
        if cat in results:
            typer.echo(render_results(results[cat], cat))

    # Health score
    typer.echo(render_health(health))

    # Recommendations
    typer.echo(
        render_recommendations(
            [r for cat_results in results.values() for r in cat_results if r.is_error or r.is_warning]
        )
    )

    # Exit code
    if health.errors > 0:
        sys.exit(2)
    elif health.warnings > 0:
        sys.exit(1)
    else:
        sys.exit(0)


@app.command("check")
def check(
    check_type: str = typer.Argument(
        "", help="Check type: system, tools, network, mcp, ports, proxy, git, docker, ollama, gpu, secrets, configs"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug output"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    timeout: float = typer.Option(10.0, "--timeout", "-t", help="Timeout in seconds"),
) -> None:
    """Run specific diagnostic checks."""
    global _g_verbose, _g_debug

    _g_verbose = verbose
    _g_debug = debug

    if not check_type:
        typer.echo("Usage: agentdoctor check <type>")
        typer.echo(
            "Available checks: system, tools, network, mcp, ports, proxy, git, docker, ollama, gpu, secrets, configs"
        )
        raise typer.Exit(1)

    type_map = {
        "system": "system",
        "tools": "tools",
        "network": "network",
        "mcp": "mcp",
        "ports": "ports",
        "proxy": "proxy",
        "git": "git",
        "docker": "docker",
        "ollama": "ollama",
        "gpu": "gpu",
        "secrets": "secrets",
        "configs": "mcp",
    }

    category = type_map.get(check_type.lower())
    if not category:
        typer.echo(f"Unknown check type: {check_type}")
        typer.echo(f"Available: {', '.join(type_map.keys())}")
        raise typer.Exit(1)

    results, health, sys_info = _collect_results([category], timeout)

    if json_output:
        typer.echo(render_json(results, health, sys_info, __version__))
        return

    for cat, cat_results in results.items():
        typer.echo(render_results(cat_results, cat))

    typer.echo(render_health(health))


@app.command("doctor")
def doctor(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug output"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colored output"),
    timeout: float = typer.Option(10.0, "--timeout", "-t", help="Timeout in seconds"),
    output: str | None = typer.Option(None, "--output", "-O", help="Output file (.json or .md)"),
) -> None:
    """Run a full diagnostic analysis (alias for main command)."""
    main(
        verbose=verbose,
        debug=debug,
        json_output=json_output,
        no_color=no_color,
        timeout=timeout,
        output=output,
    )


@app.command("explain")
def explain(
    issue_id: str = typer.Argument(..., help="Issue ID to explain (e.g., NET_PROXY_001)"),
) -> None:
    """Explain a known diagnostic issue and suggest fixes."""
    info = get_issue_info(issue_id)
    if not info:
        typer.echo(f"Issue '{issue_id}' not found in knowledge base.")
        typer.echo("Available issue IDs:")
        for id_key in [
            "SYS_PYTHON_001",
            "SYS_DISK_LOW_001",
            "PATH_DUPLICATE_001",
            "PATH_SHADOW_001",
            "NET_DNS_001",
            "NET_PROXY_001",
            "NET_PROXY_NOLOCALHOST_001",
            "MCP_CONFIG_001",
            "MCP_COMMAND_001",
            "MCP_ENDPOINT_001",
            "MCP_SECRET_001",
            "PORT_IN_USE_001",
            "DOCKER_DAEMON_001",
            "OLLAMA_SERVER_001",
            "GIT_NOT_INSTALLED_001",
            "GPU_NOT_DETECTED_001",
        ]:
            info = get_issue_info(id_key)
            if info:
                typer.echo(f"  {info.id} - {info.title}")
        raise typer.Exit(1)

    typer.echo(f"\n[bold]{info.title}[/bold]")
    typer.echo(f"\nID: {info.id}")
    typer.echo("\nDescription:")
    typer.echo(f"  {info.description}")
    typer.echo("\nWhy it matters:")
    typer.echo(f"  {info.why_it_matters}")
    typer.echo("\nSuggested actions:")
    for action in info.suggested_actions:
        typer.echo(f"  - {action}")
    typer.echo()


@app.command("self-check")
def self_check() -> None:
    """Check AgentDoctor's own installation and environment."""
    import shutil

    lines = ["[bold]AgentDoctor Self-Check[/bold]\n"]

    # Check executable
    exe = shutil.which("agentdoctor") or shutil.which("agentdoctor", path=os.environ.get("PATH", ""))
    if exe:
        lines.append(f"[green]OK[/green] AgentDoctor executable: {exe}")
    else:
        lines.append("[red]ERR[/red] AgentDoctor executable not found on PATH")

    # Check dependencies
    deps = ["typer", "rich", "psutil", "pydantic", "httpx", "platformdirs"]
    for dep in deps:
        try:
            __import__(dep)
            lines.append(f"[green]OK[/green] {dep}")
        except ImportError:
            lines.append(f"[red]ERR[/red] {dep} - not installed")

    # Check Python version
    py_ver = sys.version_info
    if (py_ver.major, py_ver.minor) >= (3, 10):
        lines.append(f"[green]OK[/green] Python {py_ver.major}.{py_ver.minor}.{py_ver.micro}")
    else:
        lines.append(f"[red]ERR[/red] Python {py_ver.major}.{py_ver.minor}.{py_ver.micro} (need 3.10+)")

    typer.echo("\n".join(lines))


@app.callback(invoke_without_command=True)
def callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output in JSON format.",
    ),
    ci_mode: bool = typer.Option(
        False,
        "--ci",
        help="CI mode: stable, machine-readable output.",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-O",
        help="Output file path (supports .json and .md extensions).",
    ),
    timeout: float = typer.Option(
        10.0,
        "--timeout",
        "-t",
        help="Timeout for individual checks in seconds.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug output.",
    ),
    only: str | None = typer.Option(
        None,
        "--only",
        "-o",
        help="Run only specific check categories (comma-separated).",
    ),
    skip: str | None = typer.Option(
        None,
        "--skip",
        "-s",
        help="Skip specific check categories (comma-separated).",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colored output.",
    ),
) -> None:
    """AgentDoctor - Diagnose broken AI coding environments in one command."""
    if version:
        typer.echo(f"AgentDoctor {__version__}")
        raise typer.Exit()

    # If no subcommand, run diagnostics
    global _g_verbose, _g_debug, _g_results, _g_health, _g_system_info
    _g_verbose = verbose
    _g_debug = debug

    # Parse only/skip
    categories: list[str] | None = None
    if only:
        categories = [c.strip() for c in only.split(",")]
    skip_categories: set[str] = set()
    if skip:
        skip_categories = {c.strip() for c in skip.split(",")}

    # Collect all results
    results, health, sys_info = _collect_results(categories, timeout)

    # Add skip markers
    if skip_categories:
        for category in skip_categories:
            if category in results:
                results[category] = [
                    CheckResult(
                        id=f"{category.upper()}_SKIPPED",
                        category=category,
                        name=f"{category} checks",
                        status=CheckStatus.SKIPPED,
                        severity=CheckSeverity.LOW,
                        summary=f"Skipped by user (--skip {category})",
                    )
                ]
                health.add_result(results[category][-1])

    _g_results = results
    _g_health = health
    _g_system_info = sys_info

    # Determine output mode
    if output:
        ext = Path(output).suffix.lower()
        if ext == ".json":
            content = render_json(results, health, sys_info, __version__)
        elif ext == ".md":
            content = render_markdown(results, health, sys_info, __version__)
        else:
            content = render_markdown(results, health, sys_info, __version__)
        Path(output).write_text(content, encoding="utf-8")
        typer.echo(f"Report written to {output}")
        sys.exit(1 if health.errors > 0 else 0)

    if json_output:
        content = render_json(results, health, sys_info, __version__)
        typer.echo(content)
        sys.exit(1 if health.errors > 0 else 0)

    if ci_mode:
        # CI mode: plain text output
        for category, category_results in results.items():
            typer.echo(f"\n[{category.upper()}]")
            for r in category_results:
                status_str = r.status.value
                typer.echo(f"  {status_str} | {r.id} | {r.name} | {r.summary}")
        typer.echo(
            f"\nHealth: {health.score}/100 (passed={health.passed}, warnings={health.warnings}, errors={health.errors})"
        )
        sys.exit(1 if health.errors > 0 else 0)

    # Rich output (default)
    typer.echo(render_header(__version__))
    typer.echo("\n[bold]Scanning your AI development environment...[/bold]\n")

    # System info
    typer.echo(render_system_info(sys_info))

    # Each category
    ordered_categories = [
        "system",
        "path",
        "ai_tools",
        "tools",
        "mcp",
        "network",
        "proxy",
        "ports",
        "docker",
        "ollama",
        "gpu",
        "git",
        "secrets",
    ]
    for cat in ordered_categories:
        if cat in results:
            typer.echo(render_results(results[cat], cat))

    # Health score
    typer.echo(render_health(health))

    # Recommendations
    typer.echo(
        render_recommendations(
            [r for cat_results in results.values() for r in cat_results if r.is_error or r.is_warning]
        )
    )

    # Exit code
    if health.errors > 0:
        sys.exit(2)
    elif health.warnings > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    app()
