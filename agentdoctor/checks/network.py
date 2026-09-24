"""Network diagnostics: DNS, HTTP, connectivity."""

from __future__ import annotations

import socket
import time

from agentdoctor.core.models import DEFAULT_TIMEOUT, CheckResult, CheckSeverity, CheckStatus
from agentdoctor.core.registry import register_check

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


HTTP_PROBE_TIMEOUT = min(DEFAULT_TIMEOUT, 3.0)


def _check_dns(hostname: str, timeout: float = DEFAULT_TIMEOUT) -> tuple[bool, str]:
    """Check DNS resolution for a hostname."""
    start = time.time()
    try:
        result = socket.getaddrinfo(hostname, 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
        elapsed = time.time() - start
        if result:
            ip = result[0][4][0]
            return True, f"Resolved to {ip} ({elapsed:.2f}s)"
        return False, "No result"
    except socket.gaierror as e:
        return False, str(e)


def _check_tcp(host: str, port: int, timeout: float = DEFAULT_TIMEOUT) -> tuple[bool, str]:
    """Check TCP connectivity to a host:port."""
    start = time.time()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
        elapsed = time.time() - start
        sock.close()
        if result == 0:
            return True, f"Connected ({elapsed:.2f}s)"
        return False, f"Connection refused ({elapsed:.2f}s)"
    except TimeoutError:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


@register_check("network")
def check_network() -> list[CheckResult]:
    """Check network connectivity: DNS, HTTP, endpoints."""
    results = []

    endpoints = [
        ("github.com", "GitHub"),
        ("pypi.org", "PyPI"),
        ("registry.npmjs.org", "npm Registry"),
    ]

    # DNS checks
    for hostname, label in endpoints:
        ok, detail = _check_dns(hostname)
        if ok:
            results.append(
                CheckResult(
                    id=f"DNS_{label.replace(' ', '_').upper()}",
                    category="network",
                    name=f"DNS: {label}",
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.LOW,
                    summary=f"{label} DNS OK",
                    details=detail,
                )
            )
        else:
            results.append(
                CheckResult(
                    id=f"DNS_{label.replace(' ', '_').upper()}_FAIL",
                    category="network",
                    name=f"DNS: {label}",
                    status=CheckStatus.ERROR,
                    severity=CheckSeverity.HIGH,
                    summary=f"DNS resolution failed for {label}",
                    details=detail,
                    recommendation="Check DNS settings and network connectivity",
                )
            )

    # HTTP connectivity
    if HAS_HTTPX:
        http_endpoints = [
            ("https://github.com", "GitHub HTTPS"),
            ("https://pypi.org", "PyPI HTTPS"),
        ]
        for url, label in http_endpoints:
            try:
                start = time.time()
                with httpx.Client(timeout=HTTP_PROBE_TIMEOUT) as client:
                    resp = client.get(url)
                elapsed = time.time() - start
                if resp.status_code < 400:
                    status = CheckStatus.PASS
                    severity = CheckSeverity.LOW
                    summary = f"{label} {resp.status_code} ({elapsed:.2f}s)"
                elif resp.status_code < 500:
                    status = CheckStatus.WARNING
                    severity = CheckSeverity.LOW
                    summary = f"{label} reachable but returned {resp.status_code} ({elapsed:.2f}s)"
                else:
                    status = CheckStatus.WARNING
                    severity = CheckSeverity.MEDIUM
                    summary = f"{label} server error {resp.status_code} ({elapsed:.2f}s)"
                results.append(
                    CheckResult(
                        id=f"HTTP_{label.replace(' ', '_').upper()}",
                        category="network",
                        name=f"HTTP: {label}",
                        status=status,
                        severity=severity,
                        summary=summary,
                        detected_value=str(resp.status_code),
                    )
                )
            except Exception as e:
                results.append(
                    CheckResult(
                        id=f"HTTP_{label.replace(' ', '_').upper()}_FAIL",
                        category="network",
                        name=f"HTTP: {label}",
                        status=CheckStatus.ERROR,
                        severity=CheckSeverity.HIGH,
                        summary=f"{label} connection failed",
                        details=str(e),
                        recommendation="Check network connectivity and proxy settings",
                    )
                )
    else:
        results.append(
            CheckResult(
                id="HTTP_HTTPX_MISSING",
                category="network",
                name="HTTP check",
                status=CheckStatus.WARNING,
                severity=CheckSeverity.LOW,
                summary="httpx not installed, skipping HTTP checks",
                details="Install httpx for HTTP connectivity checks",
            )
        )

    if not any(r.id.startswith("HTTP_") for r in results):
        results.append(
            CheckResult(
                id="NET_OK",
                category="network",
                name="Network",
                status=CheckStatus.INFO,
                severity=CheckSeverity.LOW,
                summary="Network checks completed",
            )
        )

    return results
