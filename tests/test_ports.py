"""Tests for port output formatting."""

from agentdoctor.checks.ports import check_ports


class TestPortChecks:
    def test_ports_check_runs(self):
        results = check_ports()
        assert isinstance(results, list)

    def test_ports_check_returns_valid_results(self):
        results = check_ports()
        for r in results:
            assert hasattr(r, "id")
            assert hasattr(r, "category")
            assert hasattr(r, "status")


class TestSupportedPorts:
    def test_supported_ports_list(self):
        from agentdoctor.core.models import SUPPORTED_PORTS

        assert isinstance(SUPPORTED_PORTS, list)
        assert 3000 in SUPPORTED_PORTS
        assert 5173 in SUPPORTED_PORTS
        assert 11434 in SUPPORTED_PORTS
