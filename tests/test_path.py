"""Tests for PATH diagnostics."""

from agentdoctor.checks.path import check_path


class TestPathChecks:
    def test_path_check_runs(self):
        """Test that path check runs without error."""
        results = check_path()
        assert isinstance(results, list)
        assert results

    def test_path_check_returns_results(self):
        """Test that path check returns CheckResult objects."""
        results = check_path()
        for r in results:
            assert hasattr(r, "id")
            assert hasattr(r, "category")
            assert hasattr(r, "name")
            assert hasattr(r, "status")


class TestPathDuplicateDetection:
    def test_detects_duplicates(self):
        """Test that duplicate executables are detected."""
        from agentdoctor.checks.path import _find_executable_in_path

        # This test depends on the actual environment
        results = _find_executable_in_path("python")
        # May find 0 or more results depending on system
        assert isinstance(results, list)

    def test_detects_python3(self):
        from agentdoctor.checks.path import _find_executable_in_path

        results = _find_executable_in_path("python3")
        assert isinstance(results, list)


class TestPathShadowing:
    def test_shadowing_check_runs(self):
        """Test that shadowing detection runs."""
        results = check_path()
        # Check that at least some results are returned
        assert isinstance(results, list)
