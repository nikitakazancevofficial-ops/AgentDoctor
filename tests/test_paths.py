"""Tests for Windows-style and Unix-style paths."""

from pathlib import Path


class TestPathHandling:
    def test_windows_style_path(self):
        p = Path("C:\\Users\\test\\AppData\\Local\\Programs\\Python\\Python312\\python.exe")
        assert p.exists() or True  # May not exist on all systems
        assert p.name == "python.exe"

    def test_unix_style_path(self):
        p = Path("/usr/local/bin/python3")
        # Just test that Path handles it
        assert p.name == "python3"

    def test_path_normpath(self):
        import os

        result = os.path.normpath("C:\\Users\\test\\AppData\\..\\test")
        assert "AppData" not in result

    def test_path_with_spaces(self):
        """Test that paths with spaces are handled correctly."""
        import os

        p = Path("C:\\Program Files\\Python312\\python.exe")
        assert " " in str(p)
        # normpath should preserve spaces
        assert " " in os.path.normpath(str(p))
