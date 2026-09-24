"""Proxy diagnostics: HTTP_PROXY, NO_PROXY analysis."""

from __future__ import annotations

import os

from agentdoctor.core.models import CheckResult, CheckSeverity, CheckStatus
from agentdoctor.core.redaction import redact_url
from agentdoctor.core.registry import register_check


def _mask_proxy_cred(url: str) -> str:
    """Mask credentials in proxy URL."""
    return redact_url(url)


@register_check("proxy")
def check_proxy() -> list[CheckResult]:
    """Check proxy environment variables and NO_PROXY configuration."""
    results = []
    proxy_vars = ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]

    proxy_values: dict[str, str] = {}
    for var in proxy_vars:
        val = os.environ.get(var, "")
        if val:
            proxy_values[var] = val

    if proxy_values:
        for var, val in proxy_values.items():
            masked = _mask_proxy_cred(val)
            results.append(
                CheckResult(
                    id=f"PROXY_{var}",
                    category="proxy",
                    name=f"Proxy: {var}",
                    status=CheckStatus.WARNING,
                    severity=CheckSeverity.LOW,
                    summary=f"Proxy set: {_mask_proxy_cred(val)}",
                    detected_value=masked,
                )
            )

        # Check NO_PROXY for localhost
        no_proxy = os.environ.get("NO_PROXY", "") or os.environ.get("no_proxy", "")
        if no_proxy:
            localhost_included = any(x in no_proxy.lower() for x in ["localhost", "127.0.0.1", "::1", ".local"])
            if not localhost_included:
                results.append(
                    CheckResult(
                        id="NET_PROXY_NOLOCALHOST_001",
                        category="proxy",
                        name="NO_PROXY missing localhost",
                        status=CheckStatus.WARNING,
                        severity=CheckSeverity.MEDIUM,
                        summary="NO_PROXY does not include localhost/127.0.0.1",
                        details=f"NO_PROXY={no_proxy}",
                        recommendation="Add localhost,127.0.0.1,::1 to NO_PROXY to prevent local connections going through proxy",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        id="PROXY_NO_PROXY_OK",
                        category="proxy",
                        name="NO_PROXY",
                        status=CheckStatus.PASS,
                        severity=CheckSeverity.LOW,
                        summary="NO_PROXY includes localhost",
                        detected_value=no_proxy,
                    )
                )
        else:
            results.append(
                CheckResult(
                    id="PROXY_NO_MISSING",
                    category="proxy",
                    name="NO_PROXY",
                    status=CheckStatus.WARNING,
                    severity=CheckSeverity.MEDIUM,
                    summary="NO_PROXY not set (proxy may intercept all connections)",
                    recommendation="Set NO_PROXY to exclude localhost and local networks",
                )
            )
    else:
        results.append(
            CheckResult(
                id="PROXY_NONE",
                category="proxy",
                name="Proxy",
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                summary="No proxy configured",
            )
        )

    return results
