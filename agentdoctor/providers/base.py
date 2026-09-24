"""Base class for AI tool providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from agentdoctor.core.models import CheckResult, CheckSeverity, CheckStatus


class BaseProvider(ABC):
    """Base class for AI tool providers."""

    name: str = ""
    category: str = "ai_tools"

    @abstractmethod
    def detect(self) -> bool:
        """Check if the tool is installed."""
        ...

    @abstractmethod
    def get_version(self) -> str | None:
        """Get the tool version."""
        ...

    def find_configs(self) -> list[Path]:
        """Find configuration files for this tool."""
        return []

    def validate_configs(self, configs: list[Path]) -> list[CheckResult]:
        """Validate configuration files."""
        return []

    def run_checks(self) -> list[CheckResult]:
        """Run all checks for this tool."""
        results = []
        if self.detect():
            version = self.get_version()
            results.append(
                CheckResult(
                    id=f"AI_{self.name.upper().replace(' ', '_')}_DETECTED",
                    category=self.category,
                    name=self.name,
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.LOW,
                    summary=f"{self.name} {version or 'installed'}",
                    detected_value=version or "installed",
                )
            )
        else:
            results.append(
                CheckResult(
                    id=f"AI_{self.name.upper().replace(' ', '_')}_MISSING",
                    category=self.category,
                    name=self.name,
                    status=CheckStatus.SKIPPED,
                    severity=CheckSeverity.LOW,
                    summary=f"{self.name} not installed",
                    detected_value="not installed",
                )
            )
        return results
