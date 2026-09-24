"""Fast CLI dispatch tests that do not inspect the host environment."""

from __future__ import annotations

import json

from pytest import MonkeyPatch
from typer.testing import CliRunner

from agentdoctor import cli
from agentdoctor.core.models import CheckResult, CheckSeverity, CheckStatus, HealthScore, SystemInfo


def _result_set(
    categories: list[str] | None, timeout: float
) -> tuple[dict[str, list[CheckResult]], HealthScore, SystemInfo]:
    del timeout
    result = CheckResult(
        id="TEST_OK",
        category=(categories or ["system"])[0],
        name="Test check",
        status=CheckStatus.PASS,
        severity=CheckSeverity.LOW,
        summary="safe",
    )
    health = HealthScore()
    health.add_result(result)
    return {result.category: [result]}, health, SystemInfo(platform="Test", python_version="3.12")


def test_root_json_dispatches_full_scan(monkeypatch: MonkeyPatch) -> None:
    calls: list[tuple[list[str] | None, float]] = []

    def collect(
        categories: list[str] | None, timeout: float
    ) -> tuple[dict[str, list[CheckResult]], HealthScore, SystemInfo]:
        calls.append((categories, timeout))
        return _result_set(categories, timeout)

    monkeypatch.setattr(cli, "_collect_results", collect)
    result = CliRunner().invoke(cli.app, ["--json", "--timeout", "0.5"])
    assert result.exit_code == 0
    assert calls == [(None, 0.5)]
    assert json.loads(result.stdout)["results"]["system"][0]["id"] == "TEST_OK"


def test_check_subcommand_does_not_run_full_scan(monkeypatch: MonkeyPatch) -> None:
    calls: list[list[str] | None] = []

    def collect(
        categories: list[str] | None, timeout: float
    ) -> tuple[dict[str, list[CheckResult]], HealthScore, SystemInfo]:
        calls.append(categories)
        return _result_set(categories, timeout)

    monkeypatch.setattr(cli, "_collect_results", collect)
    result = CliRunner().invoke(cli.app, ["check", "system", "--json"])
    assert result.exit_code == 0
    assert calls == [["system"]]
    assert set(json.loads(result.stdout)["results"]) == {"system"}


def test_doctor_is_full_scan_alias(monkeypatch: MonkeyPatch) -> None:
    calls: list[list[str] | None] = []

    def collect(
        categories: list[str] | None, timeout: float
    ) -> tuple[dict[str, list[CheckResult]], HealthScore, SystemInfo]:
        calls.append(categories)
        return _result_set(categories, timeout)

    monkeypatch.setattr(cli, "_collect_results", collect)
    result = CliRunner().invoke(cli.app, ["doctor", "--json"])
    assert result.exit_code == 0
    assert calls == [None]
    assert "TEST_OK" in result.stdout


def test_skip_recomputes_exit_status(monkeypatch: MonkeyPatch) -> None:
    warning = CheckResult(
        id="WARN",
        category="network",
        name="Network",
        status=CheckStatus.WARNING,
        severity=CheckSeverity.HIGH,
        summary="warning",
    )
    health = HealthScore()
    health.add_result(warning)
    monkeypatch.setattr(cli, "_collect_results", lambda *_args: ({"network": [warning]}, health, SystemInfo()))
    result = CliRunner().invoke(cli.app, ["--json", "--skip", "network"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["results"]["network"][0]["status"] == "SKIPPED"
    assert payload["summary"]["warnings"] == 0
