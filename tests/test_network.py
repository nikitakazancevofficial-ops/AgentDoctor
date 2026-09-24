"""Unit tests for network diagnostics; no test contacts the internet."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx

from agentdoctor.checks.network import _check_tcp, check_network
from agentdoctor.core.models import CheckStatus


def _mock_dns() -> list[tuple[object, object, object, object, tuple[str, int]]]:
    return [(0, 0, 0, "", ("203.0.113.1", 443))]


def test_tcp_socket_is_closed() -> None:
    socket_instance = MagicMock()
    socket_instance.__enter__.return_value = socket_instance
    socket_instance.connect_ex.return_value = 0
    with patch("agentdoctor.checks.network.socket.socket", return_value=socket_instance):
        ok, _detail = _check_tcp("example.test", 443)
    assert ok
    socket_instance.__exit__.assert_called_once()


def test_https_uses_certificate_verification_and_classifies_statuses() -> None:
    response = MagicMock(status_code=503)
    client = MagicMock()
    client.__enter__.return_value = client
    client.get.return_value = response
    with (
        patch("agentdoctor.checks.network.socket.getaddrinfo", side_effect=lambda *_args: _mock_dns()),
        patch("agentdoctor.checks.network.httpx.Client", return_value=client) as client_factory,
    ):
        results = check_network()
    assert all(call.kwargs.get("verify", True) is not False for call in client_factory.call_args_list)
    http_results = [result for result in results if result.id.startswith("HTTP_")]
    assert http_results
    assert all(result.status == CheckStatus.WARNING for result in http_results)


def test_tls_failure_becomes_diagnostic() -> None:
    client = MagicMock()
    client.__enter__.return_value = client
    client.get.side_effect = httpx.ConnectError("certificate verify failed")
    with (
        patch("agentdoctor.checks.network.socket.getaddrinfo", side_effect=lambda *_args: _mock_dns()),
        patch("agentdoctor.checks.network.httpx.Client", return_value=client),
    ):
        results = check_network()
    failures = [result for result in results if result.id.startswith("HTTP_") and result.status == CheckStatus.ERROR]
    assert len(failures) == 2
    assert all("connection failed" in result.summary for result in failures)
