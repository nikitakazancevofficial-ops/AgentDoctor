"""Core data models for AgentDoctor."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CheckStatus(str, Enum):
    PASS = "PASS"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class CheckSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(slots=True)
class CheckResult:
    """Result of a single diagnostic check."""

    id: str
    category: str
    name: str
    status: CheckStatus = CheckStatus.INFO
    severity: CheckSeverity = CheckSeverity.LOW
    summary: str = ""
    details: str = ""
    detected_value: str | None = None
    expected_value: str | None = None
    recommendation: str = ""
    commands: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0

    @property
    def is_pass(self) -> bool:
        return self.status in (CheckStatus.PASS, CheckStatus.INFO)

    @property
    def is_error(self) -> bool:
        return self.status in (CheckStatus.ERROR, CheckStatus.INTERNAL_ERROR)

    @property
    def is_warning(self) -> bool:
        return self.status == CheckStatus.WARNING


@dataclass
class SystemInfo:
    """Collected system information."""

    platform: str = ""
    platform_version: str = ""
    architecture: str = ""
    hostname: str = ""
    shell: str = ""
    username: str = ""
    python_executable: str = ""
    python_version: str = ""
    virtualenv: str = ""
    cpu: str = ""
    cpu_threads: int = 0
    ram_total_gb: float = 0.0
    ram_available_gb: float = 0.0
    swap_total_gb: float = 0.0
    swap_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    disk_free_gb: float = 0.0
    filesystem: str = ""
    cwd: str = ""
    git_repo: str = ""
    git_branch: str = ""
    git_clean: bool = True
    wsl_installed: bool = False
    wsl_version: str = ""
    wsl_distros: list[str] = field(default_factory=list)


@dataclass
class HealthScore:
    """Health score calculation."""

    score: int = 100
    passed: int = 0
    warnings: int = 0
    errors: int = 0
    skipped: int = 0
    info: int = 0
    details: list[str] = field(default_factory=list)

    def add_result(self, result: CheckResult) -> None:
        if result.status == CheckStatus.PASS:
            self.passed += 1
        elif result.status == CheckStatus.INFO:
            self.info += 1
        elif result.status == CheckStatus.WARNING:
            self.warnings += 1
            self.score -= self._severity_penalty(result.severity)
        elif result.status == CheckStatus.ERROR:
            self.errors += 1
            self.score -= self._severity_penalty(result.severity)
        elif result.status == CheckStatus.SKIPPED:
            self.skipped += 1

        self.score = max(0, self.score)
        penalty = self._severity_penalty(result.severity)
        if penalty > 0:
            status_label = result.status.value
            self.details.append(f"{status_label} {result.severity.value}: {result.summary}")

    def _severity_penalty(self, severity: CheckSeverity) -> int:
        mapping = {
            CheckSeverity.LOW: 5,
            CheckSeverity.MEDIUM: 10,
            CheckSeverity.HIGH: 15,
            CheckSeverity.CRITICAL: 25,
        }
        return mapping.get(severity, 0)

    @property
    def is_healthy(self) -> bool:
        return self.errors == 0


@dataclass
class CommandResult:
    """Result of a command execution."""

    command: str
    return_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration: float = 0.0
    timed_out: bool = False
    exception: str = ""

    @property
    def success(self) -> bool:
        return self.return_code == 0 and not self.timed_out and not self.exception


# Constants
DEFAULT_TIMEOUT = 10.0
SHORT_TIMEOUT = 3.0
LONG_TIMEOUT = 30.0

DISK_WARNING_GB = 5.0
DISK_CRITICAL_GB = 2.0

MIN_PYTHON_VERSION = (3, 10)

SUPPORTED_PORTS = [
    3000,
    3001,
    5173,
    8000,
    8080,
    8765,
    11434,
    5143,
    11435,
    3002,
    4000,
    4200,
    5000,
    8081,
    8082,
    8888,
    9000,
    9090,
    9200,
    9292,
]

STARTUP_COMMANDS = [
    "python",
    "-m",
    "agentdoctor",
]
