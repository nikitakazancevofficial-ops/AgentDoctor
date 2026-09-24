"""Ollama diagnostics."""

from __future__ import annotations

import socket
import time

from agentdoctor.core.models import SHORT_TIMEOUT, CheckResult, CheckSeverity, CheckStatus
from agentdoctor.core.registry import register_check
from agentdoctor.core.runner import run_command_sync


def _check_endpoint(host: str, port: int, timeout: float = SHORT_TIMEOUT) -> tuple[bool, str]:
    """Check TCP connectivity to an endpoint."""
    start = time.time()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
        elapsed = time.time() - start
        if result == 0:
            return True, f"Connected ({elapsed:.2f}s)"
        return False, f"Connection refused ({elapsed:.2f}s)"
    except TimeoutError:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


@register_check("ollama")
def check_ollama() -> list[CheckResult]:
    """Check Ollama installation and server status."""
    results = []

    # Check ollama executable
    r = run_command_sync(["ollama", "--version"], timeout=SHORT_TIMEOUT)
    if r.success and r.stdout.strip():
        ollama_ver = r.stdout.strip().split("\n")[0].strip()
        results.append(
            CheckResult(
                id="OLLAMA_OK",
                category="ollama",
                name="Ollama",
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                summary=ollama_ver,
                detected_value=ollama_ver,
            )
        )
    else:
        results.append(
            CheckResult(
                id="OLLAMA_MISSING",
                category="ollama",
                name="Ollama",
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                summary="Ollama not found",
                detected_value="not installed",
                expected_value="Ollama installed",
                recommendation="Install Ollama from https://ollama.ai",
            )
        )
        return results

    # Check Ollama server
    ok, detail = _check_endpoint("127.0.0.1", 11434)
    if ok:
        results.append(
            CheckResult(
                id="OLLAMA_SERVER_OK",
                category="ollama",
                name="Ollama server",
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                summary="Ollama server is running",
                details=detail,
            )
        )
        # Try to get models list (safe, read-only)
        try:
            import httpx

            try:
                with httpx.Client(timeout=SHORT_TIMEOUT) as client:
                    resp = client.get("http://127.0.0.1:11434/api/tags")
                    if resp.status_code == 200:
                        data = resp.json()
                        models = data.get("models", [])
                        if models:
                            results.append(
                                CheckResult(
                                    id="OLLAMA_MODELS",
                                    category="ollama",
                                    name="Ollama models",
                                    status=CheckStatus.INFO,
                                    severity=CheckSeverity.LOW,
                                    summary=f"{len(models)} model{'s' if len(models) != 1 else ''} available",
                                    details=", ".join(m.get("name", "unknown") for m in models[:5]),
                                )
                            )
            except Exception:
                pass
        except ImportError:
            pass
    else:
        results.append(
            CheckResult(
                id="OLLAMA_SERVER_001",
                category="ollama",
                name="Ollama server",
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                summary="Ollama server is not responding",
                details=f"Expected: http://127.0.0.1:11434\n{detail}",
                recommendation="Run: ollama serve",
            )
        )

    return results
