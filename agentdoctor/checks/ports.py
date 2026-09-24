"""Port diagnostics: listening ports, common dev/AI ports."""

from __future__ import annotations

from typing import Any

import psutil

from agentdoctor.core.models import SUPPORTED_PORTS, CheckResult, CheckSeverity, CheckStatus
from agentdoctor.core.registry import register_check


def _get_process_name(pid: int) -> str:
    """Get process name by PID."""
    try:
        proc = psutil.Process(pid)
        return proc.name() or "unknown"
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return "unknown"


def _get_process_exe(pid: int) -> str:
    """Get process executable path by PID."""
    try:
        proc = psutil.Process(pid)
        return proc.exe() or ""
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return ""


@register_check("ports")
def check_ports() -> list[CheckResult]:
    """Check commonly used ports and listening sockets."""
    results = []

    # Get listening connections
    listening: dict[int, list[Any]] = {}
    try:
        conns = psutil.net_connections(kind="inet")
        for conn in conns:
            if conn.status == "LISTEN" and conn.laddr:
                port = conn.laddr.port
                if port not in listening:
                    listening[port] = []
                listening[port].append(conn)
    except (psutil.AccessDenied, Exception):
        results.append(
            CheckResult(
                id="PORTS_ACCESS_DENIED",
                category="ports",
                name="Port scan",
                status=CheckStatus.WARNING,
                severity=CheckSeverity.LOW,
                summary="Cannot scan ports (permission denied or OS limitation)",
                recommendation="Run with elevated privileges for full port diagnostics",
            )
        )
        return results

    # Check common ports
    for port in SUPPORTED_PORTS:
        if port in listening:
            conns = listening[port]
            for conn in conns:
                pid = conn.pid
                name = _get_process_name(pid) if pid else "unknown"
                exe = _get_process_exe(pid) if pid else ""
                results.append(
                    CheckResult(
                        id="PORT_IN_USE_001",
                        category="ports",
                        name=f"Port {port}",
                        status=CheckStatus.WARNING,
                        severity=CheckSeverity.LOW,
                        summary=f"Port {port} is {conn.status}",
                        details=f"Process: {name}\nPID: {pid}\nExecutable: {exe}",
                        detected_value=f"{name} (PID {pid})",
                        recommendation="Close the process if this port is not needed",
                        metadata={"port": port, "pid": pid, "process": name},
                    )
                )

    if not any(r.id == "PORT_IN_USE_001" for r in results):
        results.append(
            CheckResult(
                id="PORTS_OK",
                category="ports",
                name="Common ports",
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                summary="No conflicts on common ports",
            )
        )

    return results
