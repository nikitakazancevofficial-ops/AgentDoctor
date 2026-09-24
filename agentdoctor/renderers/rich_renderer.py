"""Rich terminal renderer for AgentDoctor output."""

from __future__ import annotations

import os
import sys

from agentdoctor.core.models import (
    CheckResult,
    CheckStatus,
    HealthScore,
    SystemInfo,
)


def _has_unicode_support() -> bool:
    """Check if terminal supports Unicode."""
    term = os.environ.get("TERM", "")
    if "dumb" in term.lower():
        return False
    if os.environ.get("WT_SESSION"):  # Windows Terminal
        return True
    if os.environ.get("TERM_PROGRAM") == "vscode":
        return True
    encoding = sys.stdout.encoding or ""
    return "utf" in encoding.lower() or "ansi" in encoding.lower()


def _get_symbols() -> dict[str, str]:
    """Get display symbols based on terminal capabilities."""
    if _has_unicode_support():
        return {
            "pass": "\u2713",
            "warn": "\u26a0",
            "error": "\u2717",
            "info": "\u24d8",
            "sep": "\u2500",
            "tl": "\u256d",
            "tr": "\u256e",
            "bl": "\u2570",
            "br": "\u256f",
            "header_bg": "\u2550",
        }
    return {
        "pass": "[OK]",
        "warn": "[WARN]",
        "error": "[ERR]",
        "info": "[INFO]",
        "sep": "-",
        "tl": "+",
        "tr": "+",
        "bl": "+",
        "br": "+",
        "header_bg": "=",
    }


def _get_status_color(status: CheckStatus) -> str:
    """Get ANSI color for status."""
    colors = {
        CheckStatus.PASS: "green",
        CheckStatus.INFO: "cyan",
        CheckStatus.WARNING: "yellow",
        CheckStatus.ERROR: "red",
        CheckStatus.SKIPPED: "blue",
        CheckStatus.INTERNAL_ERROR: "magenta",
    }
    return colors.get(status, "white")


def render_header(version: str) -> str:
    """Render the tool header."""
    sym = _get_symbols()
    width = 40
    lines = [
        f"{sym['tl']}{sym['header_bg'] * (width - 2)}{sym['tr']}",
        f"{'AgentDoctor':<{width - 2}}",
        f"{'Diagnose broken AI coding environments in one command.':<{width - 2}}",
        f"{'v' + version:<{width - 2}}",
        f"{sym['bl']}{sym['header_bg'] * (width - 2)}{sym['br']}",
    ]
    return "\n".join(lines)


def render_results(results: list[CheckResult], title: str) -> str:
    """Render a section of check results."""
    lines = [f"\n{title}"]
    lines.append("-" * max(len(title), 30))

    for r in results:
        sym = _get_symbols()
        status_sym = {
            CheckStatus.PASS: f"[green]{sym['pass']}[/green]",
            CheckStatus.INFO: f"[cyan]{sym['info']}[/cyan]",
            CheckStatus.WARNING: f"[yellow]{sym['warn']}[/yellow]",
            CheckStatus.ERROR: f"[red]{sym['error']}[/red]",
            CheckStatus.SKIPPED: "[blue]○[/blue]",
            CheckStatus.INTERNAL_ERROR: "[magenta]![/magenta]",
        }.get(r.status, "[white]?[/white]")

        name = f"{r.name:<25}"
        value = r.detected_value or r.summary or ""
        lines.append(f"  {status_sym} {name} {value}")

    return "\n".join(lines)


def render_health(score: HealthScore) -> str:
    """Render health score and summary."""
    lines = []
    color = "green"
    if score.score < 50:
        color = "red"
    elif score.score < 75:
        color = "yellow"

    lines.append(f"\n[bold]Health score: [{color}]{score.score}/100[/{color}][/bold]")
    lines.append(f"\n  {score.passed} checks passed")
    if score.warnings:
        lines.append(f"  {score.warnings} warnings")
    if score.errors:
        lines.append(f"  {score.errors} errors")
    if score.skipped:
        lines.append(f"  {score.skipped} skipped")
    if score.info:
        lines.append(f"  {score.info} info")

    if score.details:
        lines.append("\n  [bold]Issues:[/bold]")
        for detail in score.details[:10]:
            lines.append(f"    - {detail}")

    return "\n".join(lines)


def render_recommendations(results: list[CheckResult]) -> str:
    """Render suggested actions for errors and warnings."""
    issues = [r for r in results if r.is_error or r.is_warning]
    if not issues:
        return "\n[bold green]No issues found. Your environment looks healthy![/bold green]"

    lines = ["\n[bold]Suggested actions:[/bold]"]
    for i, issue in enumerate(issues, 1):
        lines.append(f"\n  [bold]{i}. {issue.summary}[/bold]")
        if issue.details:
            lines.append(f"    {issue.details}")
        if issue.recommendation:
            lines.append(f"    [bold]Recommendation:[/bold] {issue.recommendation}")
        if issue.commands:
            for cmd in issue.commands:
                lines.append(f"    [bold]Command:[/bold] {cmd}")
        if issue.id:
            lines.append(f"    [bold]ID:[/bold] {issue.id}")

    return "\n".join(lines)


def render_system_info(sys_info: SystemInfo) -> str:
    """Render system info section."""
    lines = ["\n[bold]System:[/bold]"]
    lines.append(f"  [cyan]OS:[/cyan] {sys_info.platform} {sys_info.platform_version}")
    lines.append(f"  [cyan]Architecture:[/cyan] {sys_info.architecture}")
    lines.append(f"  [cyan]Python:[/cyan] {sys_info.python_version}")
    lines.append(
        f"  [cyan]RAM:[/cyan] {sys_info.ram_total_gb:.1f} GB total, {sys_info.ram_available_gb:.1f} GB available"
    )
    lines.append(f"  [cyan]Disk:[/cyan] {sys_info.disk_free_gb:.1f} GB free of {sys_info.disk_total_gb:.1f} GB")
    lines.append(f"  [cyan]CPU:[/cyan] {sys_info.cpu or 'Unknown'} ({sys_info.cpu_threads} threads)")
    if sys_info.virtualenv:
        lines.append(f"  [cyan]Virtual env:[/cyan] {sys_info.virtualenv}")
    if sys_info.git_repo:
        lines.append(f"  [cyan]Git repo:[/cyan] {sys_info.git_repo}")
        lines.append(f"  [cyan]Branch:[/cyan] {sys_info.git_branch or 'unknown'}")
    if sys_info.wsl_installed:
        lines.append("  [cyan]WSL:[/cyan] installed")
    return "\n".join(lines)
