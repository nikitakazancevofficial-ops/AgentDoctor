"""Command-line interface for AgentDoctor."""

from __future__ import annotations

import shutil
import sys
import time
from importlib import import_module
from pathlib import Path
from typing import Any, cast

import typer

from agentdoctor import __version__
from agentdoctor.core.models import DEFAULT_TIMEOUT, CheckResult, CheckSeverity, CheckStatus, HealthScore, SystemInfo
from agentdoctor.core.redaction import sanitize_check_result
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
    no_args_is_help=False,
)
_g_debug = False


def _run_check(check_func: Any, category: str) -> list[CheckResult]:
    """Run one registered check and turn unexpected failures into diagnostics."""
    start = time.perf_counter()
    try:
        result = check_func()
        results = result[0] if isinstance(result, tuple) and isinstance(result[0], list) else result
        normalized = results if isinstance(results, list) else [results]
        for check_result in normalized:
            check_result.duration_ms = (time.perf_counter() - start) * 1000
        return normalized
    except Exception as exc:  # Third-party APIs must not abort a scan.
        return [
            CheckResult(
                id=f"{category.upper()}_INTERNAL_ERROR",
                category=category,
                name=f"{category} check",
                status=CheckStatus.INTERNAL_ERROR,
                severity=CheckSeverity.HIGH,
                summary=f"Internal error in {category} check",
                details=str(exc) if _g_debug else "Check failed with an error",
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        ]


def _collect_results(
    categories: list[str] | None = None, timeout: float = DEFAULT_TIMEOUT
) -> tuple[dict[str, list[CheckResult]], HealthScore, SystemInfo]:
    """Run requested checks in a deterministic order."""
    del timeout  # Individual checks own their documented command/network timeout.
    for module_name in (
        "docker",
        "git",
        "gpu",
        "mcp",
        "network",
        "ollama",
        "path",
        "ports",
        "proxy",
        "secrets",
        "system",
        "tools",
    ):
        import_module(f"agentdoctor.checks.{module_name}")
    from agentdoctor.checks import system

    results_by_category: dict[str, list[CheckResult]] = {}
    health = HealthScore()
    system_info = SystemInfo()
    if categories is None or "system" in categories:
        system_results, system_info = cast("tuple[list[CheckResult], SystemInfo]", system.check_system())
        results_by_category["system"] = system_results
        for result in system_results:
            health.add_result(result)
    for category, checks in sorted(get_registered_checks().items()):
        if category == "system" or (categories is not None and category not in categories):
            continue
        category_results: list[CheckResult] = []
        for check_func, _metadata in checks:
            category_results.extend(_run_check(check_func, category))
        results_by_category[category] = category_results
        for result in category_results:
            health.add_result(result)
    if categories is None or "tools" in categories:
        provider_results: list[CheckResult] = []
        for provider in get_providers():
            try:
                checked = provider.run_checks()
            except Exception as exc:
                checked = [
                    CheckResult(
                        id="AI_TOOLS_INTERNAL_ERROR",
                        category="ai_tools",
                        name=f"{provider.name} provider",
                        status=CheckStatus.INTERNAL_ERROR,
                        severity=CheckSeverity.HIGH,
                        summary=f"Internal error in {provider.name} provider",
                        details=str(exc) if _g_debug else "Provider check failed with an error",
                    )
                ]
            for result in checked:
                result.category = "ai_tools"
                provider_results.append(result)
                health.add_result(result)
        results_by_category["ai_tools"] = provider_results
    return results_by_category, health, system_info


def _exit_code(health: HealthScore) -> int:
    return 2 if health.errors else 1 if health.warnings else 0


def _render_ci(results: dict[str, list[CheckResult]], health: HealthScore) -> str:
    lines: list[str] = []
    for category, category_results in results.items():
        lines.append(f"[{category.upper()}]")
        for result in category_results:
            safe = sanitize_check_result(result)
            lines.append(f"{safe.status.value} | {safe.id} | {safe.name} | {safe.summary}")
    lines.append(
        f"Health: {health.score}/100 (passed={health.passed}, warnings={health.warnings}, errors={health.errors})"
    )
    return "\n".join(lines)


def _run_diagnostics(
    *,
    verbose: bool = False,
    debug: bool = False,
    json_output: bool = False,
    no_color: bool = False,
    only: str | None = None,
    skip: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    output: str | None = None,
    ci: bool = False,
) -> None:
    """Run and render a full scan; shared by the root command and ``doctor``."""
    del verbose, no_color
    global _g_debug
    _g_debug = debug
    categories = [item.strip() for item in only.split(",") if item.strip()] if only else None
    skipped = {item.strip() for item in skip.split(",") if item.strip()} if skip else set()
    results, health, system_info = _collect_results(categories, timeout)
    for category in sorted(skipped):
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
    if skipped:
        health = HealthScore()
        for category_results in results.values():
            for result in category_results:
                health.add_result(result)
    if output:
        content = (
            render_json(results, health, system_info, __version__)
            if Path(output).suffix.lower() == ".json"
            else render_markdown(results, health, system_info, __version__)
        )
        Path(output).write_text(content, encoding="utf-8")
        typer.echo(f"Report written to {output}")
    elif json_output:
        typer.echo(render_json(results, health, system_info, __version__))
    elif ci:
        typer.echo(_render_ci(results, health))
    else:
        typer.echo(render_header(__version__))
        typer.echo("\n[bold]Scanning your AI development environment...[/bold]\n")
        typer.echo(render_system_info(system_info))
        for category in [
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
        ]:
            if category in results:
                typer.echo(render_results(results[category], category))
        typer.echo(render_health(health))
        typer.echo(
            render_recommendations(
                [result for values in results.values() for result in values if result.is_error or result.is_warning]
            )
        )
    raise typer.Exit(_exit_code(health))


@app.command("doctor")
def doctor(
    json_output: bool = typer.Option(False, "--json", help="Output JSON."),
    ci: bool = typer.Option(False, "--ci", help="Output stable CI text."),
    output: str | None = typer.Option(None, "--output", "-O", help="Write a JSON or Markdown report."),
    timeout: float = typer.Option(DEFAULT_TIMEOUT, "--timeout", "-t", help="Check timeout in seconds."),
) -> None:
    """Run a full diagnostic scan (alias for ``agentdoctor``)."""
    _run_diagnostics(json_output=json_output, ci=ci, output=output, timeout=timeout)


@app.command("check")
def check(
    check_type: str = typer.Argument(..., help="Diagnostic category to run."),
    json_output: bool = typer.Option(False, "--json", help="Output JSON."),
    debug: bool = typer.Option(False, "--debug", "-d", help="Include diagnostic exception details."),
    timeout: float = typer.Option(DEFAULT_TIMEOUT, "--timeout", "-t", help="Check timeout in seconds."),
) -> None:
    """Run only one diagnostic category."""
    global _g_debug
    _g_debug = debug
    category = {"configs": "mcp"}.get(check_type.lower(), check_type.lower())
    known = {"system", "tools", "network", "mcp", "ports", "proxy", "git", "docker", "ollama", "gpu", "secrets"}
    if category not in known:
        typer.echo(f"Unknown check type: {check_type}. Available: {', '.join(sorted(known))}")
        raise typer.Exit(1)
    results, health, system_info = _collect_results([category], timeout)
    if json_output:
        typer.echo(render_json(results, health, system_info, __version__))
    else:
        for result_category, category_results in results.items():
            typer.echo(render_results(category_results, result_category))
        typer.echo(render_health(health))
    raise typer.Exit(_exit_code(health))


@app.command("explain")
def explain(issue_id: str = typer.Argument(..., help="Issue ID, for example NET_PROXY_001.")) -> None:
    """Explain a known diagnostic issue."""
    info = get_issue_info(issue_id)
    if not info:
        typer.echo(f"Issue '{issue_id}' not found in knowledge base.")
        raise typer.Exit(1)
    typer.echo(
        f"{info.title}\n\nID: {info.id}\n\nDescription:\n  {info.description}\n\nWhy it matters:\n  {info.why_it_matters}\n\nSuggested actions:"
    )
    for action in info.suggested_actions:
        typer.echo(f"  - {action}")


@app.command("self-check")
def self_check() -> None:
    """Check the AgentDoctor installation and required dependencies."""
    failures = 0
    typer.echo("AgentDoctor Self-Check")
    typer.echo(
        "OK | AgentDoctor executable found"
        if shutil.which("agentdoctor")
        else "INFO | AgentDoctor executable is not on PATH (module execution is available)"
    )
    for dependency in ("typer", "rich", "psutil", "pydantic", "httpx", "platformdirs"):
        try:
            __import__(dependency)
            typer.echo(f"OK | {dependency}")
        except ImportError:
            failures += 1
            typer.echo(f"ERROR | {dependency} is not installed")
    if sys.version_info < (3, 10):  # noqa: UP036 - retain an explicit runtime support check.
        failures += 1
        typer.echo("ERROR | Python 3.10+ is required")
    else:
        typer.echo(f"OK | Python {sys.version_info.major}.{sys.version_info.minor}")
    raise typer.Exit(2 if failures else 0)


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", help="Show version and exit."),
    json_output: bool = typer.Option(False, "--json", help="Output JSON."),
    ci: bool = typer.Option(False, "--ci", help="Output stable CI text."),
    output: str | None = typer.Option(None, "--output", "-O", help="Write a JSON or Markdown report."),
    timeout: float = typer.Option(DEFAULT_TIMEOUT, "--timeout", "-t", help="Check timeout in seconds."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output."),
    debug: bool = typer.Option(False, "--debug", "-d", help="Include diagnostic exception details."),
    only: str | None = typer.Option(None, "--only", "-o", help="Run only comma-separated categories."),
    skip: str | None = typer.Option(None, "--skip", "-s", help="Skip comma-separated categories."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colored output."),
) -> None:
    """Run the full diagnostic scan when no subcommand is selected."""
    if version:
        typer.echo(f"AgentDoctor {__version__}")
        raise typer.Exit(0)
    if ctx.invoked_subcommand is None:
        _run_diagnostics(
            verbose=verbose,
            debug=debug,
            json_output=json_output,
            ci=ci,
            output=output,
            timeout=timeout,
            only=only,
            skip=skip,
            no_color=no_color,
        )


if __name__ == "__main__":
    app()
