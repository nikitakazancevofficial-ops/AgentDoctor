"""Docker diagnostics."""

from __future__ import annotations

from agentdoctor.core.models import DEFAULT_TIMEOUT, SHORT_TIMEOUT, CheckResult, CheckSeverity, CheckStatus
from agentdoctor.core.registry import register_check
from agentdoctor.core.runner import run_command_sync


@register_check("docker")
def check_docker() -> list[CheckResult]:
    """Check Docker installation and daemon status."""
    results = []

    # Check docker executable
    r = run_command_sync(["docker", "--version"], timeout=SHORT_TIMEOUT)
    if r.success and r.stdout.strip():
        docker_ver = r.stdout.strip().split("\n")[0].strip()
        results.append(
            CheckResult(
                id="DOCKER_OK",
                category="docker",
                name="Docker",
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                summary=docker_ver,
                detected_value=docker_ver,
            )
        )
    else:
        results.append(
            CheckResult(
                id="DOCKER_MISSING",
                category="docker",
                name="Docker",
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                summary="Docker not found",
                detected_value="not installed",
                expected_value="Docker installed",
                recommendation="Install Docker Desktop or Docker Engine",
            )
        )
        return results

    # Check docker info (daemon)
    r2 = run_command_sync(["docker", "info"], timeout=DEFAULT_TIMEOUT)
    if r2.success and "Server" in r2.stdout:
        results.append(
            CheckResult(
                id="DOCKER_DAEMON_OK",
                category="docker",
                name="Docker daemon",
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                summary="Docker daemon is running",
            )
        )
    else:
        results.append(
            CheckResult(
                id="DOCKER_DAEMON_001",
                category="docker",
                name="Docker daemon",
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                summary="Docker daemon is not responding",
                details=r2.stderr or r2.stdout or "Daemon not available",
                recommendation="Start Docker Desktop or the Docker service",
            )
        )

    # Check docker compose
    r3 = run_command_sync(["docker", "compose", "version"], timeout=SHORT_TIMEOUT)
    if r3.success and r3.stdout.strip():
        compose_ver = r3.stdout.strip().split("\n")[0].strip()
        results.append(
            CheckResult(
                id="DOCKER_COMPOSE_OK",
                category="docker",
                name="Docker Compose",
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                summary=compose_ver,
                detected_value=compose_ver,
            )
        )
    else:
        results.append(
            CheckResult(
                id="DOCKER_COMPOSE_MISSING",
                category="docker",
                name="Docker Compose",
                status=CheckStatus.WARNING,
                severity=CheckSeverity.LOW,
                summary="Docker Compose not available",
                recommendation="Install Docker Compose plugin",
            )
        )

    return results
