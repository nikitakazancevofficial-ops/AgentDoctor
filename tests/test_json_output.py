"""Tests for JSON output."""

import json

from agentdoctor.core.models import CheckResult, CheckSeverity, CheckStatus, HealthScore, SystemInfo
from agentdoctor.renderers.json_renderer import render_json


class TestJSONOutput:
    def _create_test_results(self):
        results = {
            "system": [
                CheckResult(
                    id="SYS_TEST",
                    category="system",
                    name="Test",
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.LOW,
                    summary="Python 3.12.0",
                    detected_value="3.12.0",
                ),
                CheckResult(
                    id="SYS_ERROR",
                    category="system",
                    name="Test Error",
                    status=CheckStatus.ERROR,
                    severity=CheckSeverity.HIGH,
                    summary="Disk space low",
                    details="Only 1 GB free",
                    recommendation="Free disk space",
                    commands=["df -h"],
                    metadata={"key": "value", "api_key": "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890"},
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

    def test_json_output_valid(self):
        results, health, sys_info = self._create_test_results()
        output = render_json(results, health, sys_info, "0.1.0")
        parsed = json.loads(output)
        assert parsed["version"] == "0.1.0"
        assert "schema_version" in parsed
        assert "timestamp" in parsed
        assert "health_score" in parsed
        assert "summary" in parsed
        assert "results" in parsed

    def test_json_health_score(self):
        results, health, sys_info = self._create_test_results()
        output = render_json(results, health, sys_info, "0.1.0")
        parsed = json.loads(output)
        assert parsed["health_score"] < 100  # Due to error

    def test_json_summary(self):
        results, health, sys_info = self._create_test_results()
        output = render_json(results, health, sys_info, "0.1.0")
        parsed = json.loads(output)
        assert parsed["summary"]["passed"] >= 1
        assert parsed["summary"]["errors"] >= 1

    def test_json_redacts_secrets(self):
        results, health, sys_info = self._create_test_results()
        output = render_json(results, health, sys_info, "0.1.0")
        parsed = json.loads(output)
        # Check that the secret in metadata is redacted
        sys_results = parsed["results"]["system"]
        for r in sys_results:
            if r["id"] == "SYS_ERROR":
                meta = r["metadata"]
                # The api_key value should be redacted
                assert "sk-proj-secret123" not in str(meta)

    def test_json_structure(self):
        results, health, sys_info = self._create_test_results()
        output = render_json(results, health, sys_info, "0.1.0")
        parsed = json.loads(output)
        # Check result structure
        for cat_results in parsed["results"].values():
            for r in cat_results:
                assert "id" in r
                assert "category" in r
                assert "name" in r
                assert "status" in r
                assert "severity" in r
                assert "summary" in r
                assert "details" in r
                assert "detected_value" in r
                assert "expected_value" in r
                assert "recommendation" in r
                assert "commands" in r
                assert "metadata" in r
                assert "duration_ms" in r
