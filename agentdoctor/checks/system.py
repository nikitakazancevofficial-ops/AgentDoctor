"""System checks: OS, Python, RAM, disk, CPU, etc."""

from __future__ import annotations

import os
import platform
import sys

import psutil

from agentdoctor.core.models import (
    DISK_CRITICAL_GB,
    DISK_WARNING_GB,
    MIN_PYTHON_VERSION,
    SHORT_TIMEOUT,
    CheckResult,
    CheckSeverity,
    CheckStatus,
    SystemInfo,
)
from agentdoctor.core.registry import register_check
from agentdoctor.core.runner import run_command_sync


def _get_shell() -> str:
    return (
        os.environ.get("SHELL")
        or os.environ.get("COMSPEC")
        or os.environ.get("PROGRAMFILES", "").split("\\")[0]
        or "unknown"
    )


def _get_git_info(cwd: str) -> dict[str, str | bool]:
    result: dict[str, str | bool] = {"repo": "", "branch": "", "clean": True}
    r = run_command_sync(["git", "rev-parse", "--show-toplevel"], cwd=cwd, timeout=SHORT_TIMEOUT)
    if r.success:
        result["repo"] = r.stdout.strip()
        r2 = run_command_sync(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd, timeout=SHORT_TIMEOUT)
        if r2.success:
            result["branch"] = r2.stdout.strip()
        r3 = run_command_sync(["git", "status", "--porcelain"], cwd=cwd, timeout=SHORT_TIMEOUT)
        if r3.success and r3.stdout.strip():
            result["clean"] = False
    return result


def _get_wsl_info() -> dict[str, str | bool | list[str]]:
    result: dict[str, str | bool | list[str]] = {"installed": False, "version": "", "distros": []}
    r = run_command_sync(["wsl", "--version"], timeout=SHORT_TIMEOUT)
    if r.success and r.stdout.strip():
        result["installed"] = True
        result["version"] = r.stdout.strip()[:80]
    r2 = run_command_sync(["wsl", "--list", "--verbose"], timeout=SHORT_TIMEOUT)
    if r2.success:
        for line in r2.stdout.strip().split("\n"):
            line = line.strip()
            if line and "NAME" not in line.upper() and "<" not in line:
                parts = line.split()
                if parts and isinstance(result["distros"], list):
                    result["distros"].append(parts[0])
    return result


def _get_gpu_info() -> str:
    """Best-effort GPU detection."""
    info_parts = []

    if sys.platform == "win32":
        r = run_command_sync(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
            timeout=SHORT_TIMEOUT,
        )
        if r.success and r.stdout.strip():
            for line in r.stdout.strip().split("\n"):
                info_parts.append(f"NVIDIA: {line.strip()}")
        else:
            # Try AMD
            r2 = run_command_sync(["wmic", "path", "win32_VideoController", "get", "Name"], timeout=SHORT_TIMEOUT)
            if r2.success:
                for line in r2.stdout.strip().split("\n"):
                    line = line.strip()
                    if line and line != "Name":
                        info_parts.append(line)
    elif sys.platform == "darwin":
        r = run_command_sync(["system_profiler", "SPDisplaysDataType"], timeout=SHORT_TIMEOUT)
        if r.success:
            for line in r.stdout.split("\n"):
                if "Chipset Model" in line:
                    info_parts.append(line.strip())
                    break
    else:
        # Linux
        r = run_command_sync(["lspci"], timeout=SHORT_TIMEOUT)
        if r.success:
            for line in r.stdout.split("\n"):
                if "vga" in line.lower() or "3d" in line.lower() or "display" in line.lower():
                    info_parts.append(line.strip())

    return "\n".join(info_parts) if info_parts else ""


@register_check("system")  # type: ignore[arg-type]
def check_system(verbose: bool = False, cwd: str | None = None) -> tuple[list[CheckResult], SystemInfo]:
    """Collect system information and run system checks."""
    if not cwd:
        cwd = os.getcwd()

    sys_info = SystemInfo()
    sys_info.platform = platform.system()
    sys_info.platform_version = platform.version()
    sys_info.architecture = platform.machine()
    sys_info.hostname = platform.node() or ""
    sys_info.shell = _get_shell()
    sys_info.username = os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"

    sys_info.python_executable = sys.executable or ""
    sys_info.python_version = platform.python_version()

    # Virtualenv detection
    venv = os.environ.get("VIRTUAL_ENV") or os.environ.get("CONDA_PREFIX") or ""
    sys_info.virtualenv = venv

    cpu = platform.processor() or ""
    sys_info.cpu = cpu
    sys_info.cpu_threads = psutil.cpu_count(logical=True) or 0

    mem = psutil.virtual_memory()
    sys_info.ram_total_gb = mem.total / (1024**3)
    sys_info.ram_available_gb = mem.available / (1024**3)

    try:
        swap = psutil.swap_memory()
        sys_info.swap_total_gb = swap.total / (1024**3)
        sys_info.swap_used_gb = swap.used / (1024**3)
    except Exception:
        sys_info.swap_total_gb = 0.0
        sys_info.swap_used_gb = 0.0

    try:
        disk = psutil.disk_usage("/")
        sys_info.disk_total_gb = disk.total / (1024**3)
        sys_info.disk_free_gb = disk.free / (1024**3)
    except Exception:
        sys_info.disk_total_gb = 0.0
        sys_info.disk_free_gb = 0.0

    # Filesystem type
    try:
        mounts = psutil.disk_partitions()
        if mounts:
            sys_info.filesystem = mounts[0].fstype or ""
    except Exception:
        pass

    sys_info.cwd = cwd
    git_info = _get_git_info(cwd)
    sys_info.git_repo = str(git_info["repo"])
    sys_info.git_branch = str(git_info["branch"])
    sys_info.git_clean = bool(git_info["clean"])

    wsl = _get_wsl_info()
    sys_info.wsl_installed = bool(wsl["installed"])
    sys_info.wsl_version = str(wsl["version"])
    distros = wsl["distros"]
    sys_info.wsl_distros = distros if isinstance(distros, list) else []

    results = []

    # Python version check
    py_ver = sys.version_info
    if (py_ver.major, py_ver.minor) < MIN_PYTHON_VERSION:
        results.append(
            CheckResult(
                id="SYS_PYTHON_001",
                category="system",
                name="Python version",
                status=CheckStatus.ERROR,
                severity=CheckSeverity.HIGH,
                summary=f"Python {py_ver.major}.{py_ver.minor} is below minimum {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}",
                details=f"AgentDoctor requires Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+",
                detected_value=f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}",
                expected_value=f"{MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}.0+",
                recommendation="Upgrade Python to 3.10 or later",
            )
        )
    else:
        results.append(
            CheckResult(
                id="SYS_PYTHON_OK",
                category="system",
                name="Python version",
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                summary=f"Python {py_ver.major}.{py_ver.minor}.{py_ver.micro}",
                detected_value=sys_info.python_version,
                expected_value=f">= {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}",
            )
        )

    # Platform
    results.append(
        CheckResult(
            id="SYS_PLATFORM",
            category="system",
            name="Operating system",
            status=CheckStatus.INFO,
            severity=CheckSeverity.LOW,
            summary=f"{sys_info.platform} {sys_info.platform_version}",
            detected_value=sys_info.platform_version,
        )
    )

    # Architecture
    results.append(
        CheckResult(
            id="SYS_ARCH",
            category="system",
            name="Architecture",
            status=CheckStatus.INFO,
            severity=CheckSeverity.LOW,
            summary=sys_info.architecture,
            detected_value=sys_info.architecture,
        )
    )

    # CPU
    results.append(
        CheckResult(
            id="SYS_CPU",
            category="system",
            name="CPU",
            status=CheckStatus.INFO,
            severity=CheckSeverity.LOW,
            summary=f"{sys_info.cpu or 'Unknown'} ({sys_info.cpu_threads} threads)",
            detected_value=f"{sys_info.cpu_threads} logical threads",
        )
    )

    # RAM
    ram_status = CheckStatus.PASS
    ram_severity = CheckSeverity.LOW
    if sys_info.ram_total_gb < 4:
        ram_status = CheckStatus.ERROR
        ram_severity = CheckSeverity.CRITICAL
    elif sys_info.ram_total_gb < 8:
        ram_status = CheckStatus.WARNING
        ram_severity = CheckSeverity.MEDIUM
    results.append(
        CheckResult(
            id="SYS_RAM",
            category="system",
            name="RAM",
            status=ram_status,
            severity=ram_severity,
            summary=f"{sys_info.ram_total_gb:.1f} GB total, {sys_info.ram_available_gb:.1f} GB available",
            detected_value=f"{sys_info.ram_total_gb:.1f} GB",
            expected_value=">= 8 GB recommended",
            recommendation="Consider upgrading RAM if below 8 GB for AI development",
        )
    )

    # Disk space
    disk_status = CheckStatus.PASS
    disk_severity = CheckSeverity.LOW
    if sys_info.disk_free_gb < DISK_CRITICAL_GB:
        disk_status = CheckStatus.ERROR
        disk_severity = CheckSeverity.CRITICAL
    elif sys_info.disk_free_gb < DISK_WARNING_GB:
        disk_status = CheckStatus.WARNING
        disk_severity = CheckSeverity.MEDIUM
    results.append(
        CheckResult(
            id="SYS_DISK"
            if disk_status != CheckStatus.ERROR
            else "SYS_DISK_CRITICAL"
            if disk_status == CheckStatus.ERROR
            else "SYS_DISK_LOW",
            category="system",
            name="Disk space",
            status=disk_status,
            severity=disk_severity,
            summary=f"{sys_info.disk_free_gb:.1f} GB free of {sys_info.disk_total_gb:.1f} GB",
            detected_value=f"{sys_info.disk_free_gb:.1f} GB free",
            expected_value=f">= {DISK_WARNING_GB} GB free",
            recommendation=f"Free at least {DISK_WARNING_GB} GB of disk space"
            if disk_status == CheckStatus.WARNING
            else "",
        )
    )

    # Filesystem
    if sys_info.filesystem:
        results.append(
            CheckResult(
                id="SYS_FS",
                category="system",
                name="Filesystem",
                status=CheckStatus.INFO,
                severity=CheckSeverity.LOW,
                summary=sys_info.filesystem,
                detected_value=sys_info.filesystem,
            )
        )

    # Git
    git_r = run_command_sync(["git", "--version"], timeout=SHORT_TIMEOUT)
    if git_r.success and git_r.stdout.strip():
        git_ver = git_r.stdout.strip().split()[-1] if git_r.stdout.strip() else "unknown"
        results.append(
            CheckResult(
                id="SYS_GIT",
                category="system",
                name="Git",
                status=CheckStatus.PASS,
                severity=CheckSeverity.LOW,
                summary=git_ver,
                detected_value=git_ver,
            )
        )
        if sys_info.git_repo:
            clean_str = "clean" if sys_info.git_clean else "dirty"
            results.append(
                CheckResult(
                    id="SYS_GIT_REPO",
                    category="system",
                    name="Git repository",
                    status=CheckStatus.INFO,
                    severity=CheckSeverity.LOW,
                    summary=f"Branch: {sys_info.git_branch or 'unknown'}, Working tree: {clean_str}",
                    detected_value=sys_info.git_repo,
                )
            )
    else:
        results.append(
            CheckResult(
                id="SYS_GIT",
                category="system",
                name="Git",
                status=CheckStatus.WARNING,
                severity=CheckSeverity.MEDIUM,
                summary="Git not found",
                detected_value="not installed",
                expected_value="Git installed",
                recommendation="Install Git for AI coding tools that need version control",
            )
        )

    # GPU
    gpu = _get_gpu_info()
    if gpu:
        results.append(
            CheckResult(
                id="SYS_GPU",
                category="system",
                name="GPU",
                status=CheckStatus.INFO,
                severity=CheckSeverity.LOW,
                summary="GPU detected",
                details=gpu,
            )
        )
    else:
        results.append(
            CheckResult(
                id="SYS_GPU_NONE",
                category="system",
                name="GPU",
                status=CheckStatus.INFO,
                severity=CheckSeverity.LOW,
                summary="No GPU detected",
                details="GPU acceleration not available for local AI models",
            )
        )

    # WSL
    if sys_info.wsl_installed:
        results.append(
            CheckResult(
                id="SYS_WSL",
                category="system",
                name="WSL",
                status=CheckStatus.INFO,
                severity=CheckSeverity.LOW,
                summary=f"WSL installed ({sys_info.wsl_version.strip()[:40]})",
                details=f"Distros: {', '.join(sys_info.wsl_distros) if sys_info.wsl_distros else 'unknown'}",
            )
        )

    # Virtualenv
    if sys_info.virtualenv:
        results.append(
            CheckResult(
                id="SYS_VENV",
                category="system",
                name="Virtual environment",
                status=CheckStatus.INFO,
                severity=CheckSeverity.LOW,
                summary="Active",
                detected_value=sys_info.virtualenv,
            )
        )

    return results, sys_info
