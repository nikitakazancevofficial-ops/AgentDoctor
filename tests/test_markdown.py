"""Tests for markdown report."""

from agentdoctor.core.models import CheckResult, CheckSeverity, CheckStatus, HealthScore, SystemInfo
from agentdoctor.renderers.markdown_renderer import render_markdown


class TestMarkdownReport:
    def _create_test_data(self):
        results = {
            "system": [
                CheckResult(
                    id="SYS_OK",
                    category="system",
                    name="Python",
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.LOW,
                    summary="Python 3.12.0",
                ),
                CheckResult(
                    id="SYS_ERR",
                    category="system",
                    name="Disk",
                    status=CheckStatus.ERROR,
                    severity=CheckSeverity.HIGH,
                    summary="Low disk space",
                    details="Only 1 GB free",
                    recommendation="Free disk space",
                ),
            ],
            "network": [
                CheckResult(
                    id="NET_OK",
                    category="network",
                    name="Network",
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.LOW,
                    summary="OK",
                ),
            ],
        }
        health = HealthScore()
        for r in results["system"]:
            health.add_result(r)
        for r in results["network"]:
            health.add_result(r)
        sys_info = SystemInfo(
            platform="Windows",
            platform_version="11",
            architecture="x86_64",
            python_version="3.12.0",
            ram_total_gb=32.0,
            ram_available_gb=16.0,
            disk_free_gb=50.0,
            disk_total_gb=500.0,
            cpu_threads=8,
        )
        return results, health, sys_info

    def test_markdown_output(self):
        results, health, sys_info = self._create_test_data()
        output = render_markdown(results, health, sys_info, "0.1.0")
        assert "# AgentDoctor Report" in output
        assert "Health score:" in output
        assert "SYS_ERR" in output
        assert "Low disk space" in output

    def test_markdown_has_summary(self):
        results, health, sys_info = self._create_test_data()
        output = render_markdown(results, health, sys_info, "0.1.0")
        assert "## Summary" in output
        assert "Passed:" in output
        assert "Warnings:" in output
        assert "Errors:" in output

    def test_markdown_has_issues_section(self):
        results, health, sys_info = self._create_test_data()
        output = render_markdown(results, health, sys_info, "0.1.0")
        assert "## Issues" in output
        assert "SYS_ERR" in output

    def test_markdown_has_all_checks(self):
        results, health, sys_info = self._create_test_data()
        output = render_markdown(results, health, sys_info, "0.1.0")
        assert "## All Checks" in output
        assert "| SYS_OK |" in output
        assert "| SYS_ERR |" in output
        assert "| NET_OK |" in output

    def test_markdown_redacts_secrets(self):
        results, health, sys_info = self._create_test_data()
        # Add a result with a secret in details
        results["system"].append(
            CheckResult(
                id="SECRET_TEST",
                category="system",
                name="Secret test",
                status=CheckStatus.WARNING,
                severity=CheckSeverity.HIGH,
                summary="Secret found",
                details="api_key = sk-proj-abcdefghijklmnopqrstuvwxyz1234567890",
            )
        )
        health.add_result(results["system"][-1])
        output = render_markdown(results, health, sys_info, "0.1.0")
        assert "sk-proj-abcdefghijklmnopqrstuvwxyz" not in output
        assert "[REDACTED]" in output

    def test_markdown_no_issues(self):
        results = {
            "system": [
                CheckResult(
                    id="SYS_OK",
                    category="system",
                    name="Python",
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.LOW,
                    summary="OK",
                ),
            ],
        }
        health = HealthScore()
        for r in results["system"]:
            health.add_result(r)
        sys_info = SystemInfo(platform="Windows", architecture="x86_64", python_version="3.12.0")
        output = render_markdown(results, health, sys_info, "0.1.0")
        assert "No issues found" in output
