"""Tests for proxy detection."""

import os

from agentdoctor.checks.proxy import check_proxy


class TestProxyChecks:
    def test_proxy_check_runs(self):
        results = check_proxy()
        assert isinstance(results, list)

    def test_proxy_check_returns_valid_results(self):
        results = check_proxy()
        for r in results:
            assert hasattr(r, "id")
            assert hasattr(r, "category")
            assert hasattr(r, "status")


class TestProxyWithEnv:
    def test_proxy_detected_when_set(self):
        original = os.environ.get("HTTP_PROXY")
        try:
            os.environ["HTTP_PROXY"] = "http://proxy.example.com:8080"
            results = check_proxy()
            assert isinstance(results, list)
        finally:
            if original:
                os.environ["HTTP_PROXY"] = original
            else:
                os.environ.pop("HTTP_PROXY", None)

    def test_no_proxy_check(self):
        """Test NO_PROXY analysis."""
        original_http = os.environ.get("HTTP_PROXY")
        original_no = os.environ.get("NO_PROXY")
        try:
            os.environ["HTTP_PROXY"] = "http://proxy.example.com:8080"
            os.environ.pop("NO_PROXY", None)
            results = check_proxy()
            # Should have a warning about NO_PROXY
            warnings = [r for r in results if r.id == "PROXY_NO_MISSING"]
            assert len(warnings) == 1
        finally:
            if original_http:
                os.environ["HTTP_PROXY"] = original_http
            else:
                os.environ.pop("HTTP_PROXY", None)
            if original_no:
                os.environ["NO_PROXY"] = original_no
            else:
                os.environ.pop("NO_PROXY", None)
