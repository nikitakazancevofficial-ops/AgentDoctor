"""PATH diagnostics: duplicates, shadowing, non-existent entries, etc."""

from __future__ import annotations

import os
import sys
from collections import defaultdict

from agentdoctor.core.models import CheckResult, CheckSeverity, CheckStatus
from agentdoctor.core.registry import register_check


def _find_executable_in_path(name: str) -> list[str]:
    """Find all occurrences of an executable in PATH."""
    results = []
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    extensions = [""]
    if sys.platform == "win32":
        extensions = [".exe", ".bat", ".cmd", ".com"]

    for d in path_dirs:
        if not d:
            continue
        for ext in extensions:
            candidate = os.path.join(d, name + ext)
            if os.path.isfile(candidate):
                results.append(os.path.normpath(candidate))
    return results


@register_check("path")
def check_path() -> list[CheckResult]:
    """Check PATH for issues: empty entries, non-existent dirs, duplicates, shadowing."""
    results = []
    path_str = os.environ.get("PATH", "")
    path_dirs = [d for d in path_str.split(os.pathsep) if d]

    # Empty entries in PATH
    if "" in path_str.split(os.pathsep):
        results.append(
            CheckResult(
                id="PATH_EMPTY_ENTRY_001",
                category="path",
                name="Empty PATH entry",
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                summary="Empty entry found in PATH (current directory)",
                details="An empty PATH entry means the current directory is searched for executables.",
                recommendation="Remove empty entries from PATH",
            )
        )

    # Non-existent directories
    nonexist = [d for d in path_dirs if not os.path.isdir(d)]
    if nonexist:
        results.append(
            CheckResult(
                id="PATH_NONEXISTENT_001",
                category="path",
                name="Non-existent PATH entries",
                status=CheckStatus.WARNING,
                severity=CheckSeverity.LOW,
                summary=f"{len(nonexist)} non-existent directory{'s' if len(nonexist) != 1 else ''} in PATH",
                details="\n".join(nonexist[:10]),
                recommendation="Remove non-existent directories from PATH",
            )
        )

    # Find executables and detect duplicates/shadowing
    exe_map: dict[str, list[str]] = defaultdict(list)
    for d in path_dirs:
        if not d or not os.path.isdir(d):
            continue
        try:
            for entry in os.listdir(d):
                full = os.path.join(d, entry)
                if os.path.isfile(full):
                    exe_map[entry].append(os.path.normpath(full))
        except PermissionError:
            continue

    # Duplicate executables (same name in multiple dirs)
    for name, locations in sorted(exe_map.items()):
        if len(locations) > 1:
            results.append(
                CheckResult(
                    id="PATH_DUPLICATE_001",
                    category="path",
                    name=f"Duplicate: {name}",
                    status=CheckStatus.WARNING,
                    severity=CheckSeverity.LOW,
                    summary=f"{name} found in {len(locations)} locations",
                    details="\n".join(locations[:5]),
                    recommendation=f"Review {name} installations",
                )
            )

    # Common tool shadowing check
    common_tools = ["python", "python3", "node", "npm", "git", "pip", "npx"]
    for tool in common_tools:
        locations = _find_executable_in_path(tool)
        if len(locations) > 1:
            results.append(
                CheckResult(
                    id="PATH_SHADOW_001",
                    category="path",
                    name=f"Shadowed: {tool}",
                    status=CheckStatus.WARNING,
                    severity=CheckSeverity.MEDIUM,
                    summary=f"{tool} may be shadowed by multiple installations",
                    details=f"First: {locations[0]}\nOther: {'; '.join(locations[1:])}",
                    recommendation=f"Check which {tool} is being used and remove unnecessary installations",
                )
            )

    if not results:
        results.append(
            CheckResult(
                id="PATH_OK",
                category="path",
                name="PATH integrity",
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                summary="PATH looks clean",
            )
        )

    return results
