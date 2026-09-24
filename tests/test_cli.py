"""Integration tests for the installed CLI dispatch contract."""

from __future__ import annotations

import json
import os
import subprocess
import sys


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Execute the package entry point without relying on a shell alias."""
    return subprocess.run(
        [sys.executable, "-m", "agentdoctor", *args],
        capture_output=True,
        text=True,
        timeout=45,
        env=os.environ.copy(),
    )


def _expected_scan_exit(output: str) -> int:
    summary = json.loads(output)["summary"]
    return 2 if summary["errors"] else 1 if summary["warnings"] else 0


class TestCLI:
    def test_help(self) -> None:
        result = _run_cli(["--help"])
        assert result.returncode == 0
        assert "Diagnose broken AI coding environments" in result.stdout

    def test_version(self) -> None:
        result = _run_cli(["--version"])
        assert result.returncode == 0
        assert result.stdout.strip() == "AgentDoctor 0.1.0"

    def test_root_runs_full_scan(self) -> None:
        result = _run_cli(["--json"])
        payload = json.loads(result.stdout)
        assert result.returncode == _expected_scan_exit(result.stdout)
        assert "system" in payload["results"]
        assert "network" in payload["results"]

    def test_system_subcommand_only_runs_system_checks(self) -> None:
        result = _run_cli(["check", "system", "--json"])
        payload = json.loads(result.stdout)
        assert result.returncode == _expected_scan_exit(result.stdout)
        assert set(payload["results"]) == {"system"}

    def test_tools_subcommand_runs_tool_diagnostics(self) -> None:
        result = _run_cli(["check", "tools", "--json"])
        payload = json.loads(result.stdout)
        assert result.returncode == _expected_scan_exit(result.stdout)
        assert "ai_tools" in payload["results"]

    def test_explain_known_issue(self) -> None:
        result = _run_cli(["explain", "NET_PROXY_001"])
        assert result.returncode == 0
        assert "NET_PROXY_001" in result.stdout

    def test_self_check(self) -> None:
        result = _run_cli(["self-check"])
        assert result.returncode == 0
        assert "AgentDoctor Self-Check" in result.stdout

    def test_doctor_alias_json(self) -> None:
        result = _run_cli(["doctor", "--json"])
        payload = json.loads(result.stdout)
        assert result.returncode == _expected_scan_exit(result.stdout)
        assert "system" in payload["results"]

    def test_plain_default_command_dispatches_to_scan(self) -> None:
        result = _run_cli([])
        assert result.returncode in {0, 1, 2}
        assert "Scanning your AI development environment" in result.stdout
