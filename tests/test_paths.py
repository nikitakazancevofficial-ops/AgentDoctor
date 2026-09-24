"""Tests for Windows-style and Unix-style paths."""

import ntpath
import os
from pathlib import Path, PureWindowsPath


class TestPathHandling:
    def test_windows_style_path(self):
        p = PureWindowsPath("C:\\Users\\test\\AppData\\Local\\Programs\\Python\\Python312\\python.exe")
        assert p.name == "python.exe"

    def test_unix_style_path(self):
        p = Path("/usr/local/bin/python3")
        # Just test that Path handles it
        assert p.name == "python3"

    def test_path_normpath(self):
        result = ntpath.normpath("C:\\Users\\test\\AppData\\..\\test")
        assert "AppData" not in result

    def test_path_with_spaces(self):
        """Test that paths with spaces are handled correctly."""
        p = PureWindowsPath("C:\\Program Files\\Python312\\python.exe")
        assert " " in str(p)
        # normpath should preserve spaces
        assert " " in os.path.normpath(str(p))
