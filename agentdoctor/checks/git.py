"""Git diagnostics."""

from __future__ import annotations

import os

from agentdoctor.core.models import SHORT_TIMEOUT, CheckResult, CheckSeverity, CheckStatus
from agentdoctor.core.registry import register_check
from agentdoctor.core.runner import run_command_sync


@register_check("git")
def check_git() -> list[CheckResult]:
    """Check Git installation and repository state."""
    results = []

    # Check git executable
    r = run_command_sync(["git", "--version"], timeout=SHORT_TIMEOUT)
    if r.success and r.stdout.strip():
        git_ver = r.stdout.strip().split("\n")[0].strip()
        results.append(
            CheckResult(
                id="GIT_OK",
                category="git",
                name="Git",
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                summary=git_ver,
                detected_value=git_ver,
            )
        )
    else:
        results.append(
            CheckResult(
                id="GIT_NOT_INSTALLED_001",
                category="git",
                name="Git",
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                summary="Git not found on PATH",
                detected_value="not installed",
                expected_value="Git installed",
                recommendation="Install Git from https://git-scm.com",
            )
        )
        return results

    # Check if current directory is in a git repo
    cwd = os.getcwd()
    r2 = run_command_sync(["git", "rev-parse", "--show-toplevel"], cwd=cwd, timeout=SHORT_TIMEOUT)
    if r2.success:
        repo = r2.stdout.strip()
        results.append(
            CheckResult(
                id="GIT_REPO",
                category="git",
                name="Repository",
                status=CheckStatus.INFO,
                severity=CheckSeverity.LOW,
                summary="Git repository detected",
                details=f"Path: {repo}",
            )
        )

        # Branch
        r3 = run_command_sync(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd, timeout=SHORT_TIMEOUT)
        if r3.success:
            branch = r3.stdout.strip()
            results.append(
                CheckResult(
                    id="GIT_BRANCH",
                    category="git",
                    name="Branch",
                    status=CheckStatus.INFO,
                    severity=CheckSeverity.LOW,
                    summary=branch,
                    detected_value=branch,
                )
            )

        # Working tree status
        r4 = run_command_sync(["git", "status", "--porcelain"], cwd=cwd, timeout=SHORT_TIMEOUT)
        if r4.success and r4.stdout.strip():
            results.append(
                CheckResult(
                    id="GIT_DIRTY",
                    category="git",
                    name="Working tree",
                    status=CheckStatus.WARNING,
                    severity=CheckSeverity.LOW,
                    summary="Working tree has uncommitted changes",
                    details=f"{len(r4.stdout.strip().splitlines())} change(s)",
                )
            )
        else:
            results.append(
                CheckResult(
                    id="GIT_CLEAN",
                    category="git",
                    name="Working tree",
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.LOW,
                    summary="Working tree is clean",
                )
            )
    else:
        results.append(
            CheckResult(
                id="GIT_NOT_REPO",
                category="git",
                name="Repository",
                status=CheckStatus.INFO,
                severity=CheckSeverity.LOW,
                summary="Not in a Git repository",
            )
        )

    return results
