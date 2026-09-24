"""Markdown report renderer for AgentDoctor output."""

from __future__ import annotations

import datetime

from agentdoctor.core.models import CheckResult, HealthScore, SystemInfo
from agentdoctor.core.redaction import sanitize_check_result


def render_markdown(
    results: dict[str, list[CheckResult]],
    health: HealthScore,
    system_info: SystemInfo,
    version: str,
) -> str:
    """Render all results as a sanitized Markdown report."""
    lines = [
        "# AgentDoctor Report",
        "",
        f"Generated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"AgentDoctor version: {version}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"**Health score:** {health.score}/100",
        "",
        f"- Passed: {health.passed}",
        f"- Warnings: {health.warnings}",
        f"- Errors: {health.errors}",
        f"- Skipped: {health.skipped}",
        f"- Info: {health.info}",
        "",
    ]

    # System info
    lines.extend(
        [
            "## System",
            "",
            f"- **OS:** {system_info.platform} {system_info.platform_version}",
            f"- **Architecture:** {system_info.architecture}",
            f"- **Python:** {system_info.python_version}",
            f"- **RAM:** {system_info.ram_total_gb:.1f} GB total, {system_info.ram_available_gb:.1f} GB available",
            f"- **Disk:** {system_info.disk_free_gb:.1f} GB free of {system_info.disk_total_gb:.1f} GB",
            f"- **CPU:** {system_info.cpu or 'Unknown'} ({system_info.cpu_threads} threads)",
            "",
        ]
    )

    # Issues
    all_issues = []
    for _category, category_results in results.items():
        for r in category_results:
            r = sanitize_check_result(r)
            if r.is_error or r.is_warning:
                all_issues.append(r)

    if all_issues:
        lines.extend(
            [
                "## Issues",
                "",
            ]
        )
        for issue in all_issues:
            lines.extend(
                [
                    f"### {issue.id}",
                    "",
                    f"**{issue.name}**: {issue.summary}",
                    "",
                ]
            )
            if issue.details:
                lines.append(f"```\n{issue.details}\n```")
                lines.append("")
            if issue.recommendation:
                lines.append(f"**Recommendation:** {issue.recommendation}")
                lines.append("")
            if issue.commands:
                lines.append("**Suggested commands:**")
                for cmd in issue.commands:
                    lines.append(f"- `{cmd}`")
                lines.append("")
    else:
        lines.extend(
            [
                "## Issues",
                "",
                "No issues found. Your environment looks healthy!",
                "",
            ]
        )

    # All results
    lines.extend(
        [
            "## All Checks",
            "",
            "| ID | Category | Name | Status | Summary |",
            "|----|----------|------|--------|---------|",
        ]
    )

    for _category, category_results in results.items():
        for r in category_results:
            safe = sanitize_check_result(r)
            lines.append(f"| {safe.id} | {safe.category} | {safe.name} | {safe.status.value} | {safe.summary} |")

    lines.append("")
    return "\n".join(lines)
