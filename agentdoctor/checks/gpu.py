"""GPU diagnostics."""

from __future__ import annotations

import sys

from agentdoctor.core.models import SHORT_TIMEOUT, CheckResult, CheckSeverity, CheckStatus
from agentdoctor.core.registry import register_check
from agentdoctor.core.runner import run_command_sync


@register_check("gpu")
def check_gpu() -> list[CheckResult]:
    """Detect and report GPU information."""
    results = []

    gpus = []

    if sys.platform == "win32":
        # NVIDIA
        r = run_command_sync(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
            timeout=SHORT_TIMEOUT,
        )
        if r.success and r.stdout.strip():
            for line in r.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    gpus.append(
                        {
                            "name": parts[0],
                            "driver": parts[1],
                            "vram": parts[2],
                        }
                    )

        if not gpus:
            # Try AMD/Intel via WMIC
            r2 = run_command_sync(
                ["wmic", "path", "win32_VideoController", "get", "Name", "/format:list"], timeout=SHORT_TIMEOUT
            )
            if r2.success:
                for line in r2.stdout.strip().split("\n"):
                    line = line.strip()
                    if line.startswith("Name=") and "Name=" in line:
                        name = line.split("=", 1)[1].strip()
                        if name:
                            gpus.append({"name": name, "driver": "unknown", "vram": "unknown"})

    elif sys.platform == "darwin":
        r = run_command_sync(["system_profiler", "SPDisplaysDataType"], timeout=SHORT_TIMEOUT)
        if r.success:
            for line in r.stdout.split("\n"):
                if "Chipset Model" in line:
                    name = line.split(":")[-1].strip()
                    if name:
                        gpus.append({"name": name, "driver": "unknown", "vram": "unknown"})

    else:
        # Linux
        r = run_command_sync(["lspci"], timeout=SHORT_TIMEOUT)
        if r.success:
            for line in r.stdout.split("\n"):
                if "vga" in line.lower() or "3d" in line.lower() or "display" in line.lower():
                    gpus.append({"name": line.strip(), "driver": "unknown", "vram": "unknown"})

        # NVIDIA on Linux
        r2 = run_command_sync(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
            timeout=SHORT_TIMEOUT,
        )
        if r2.success and r2.stdout.strip():
            gpus = []
            for line in r2.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    gpus.append(
                        {
                            "name": parts[0],
                            "driver": parts[1],
                            "vram": parts[2],
                        }
                    )

    if gpus:
        for gpu in gpus:
            results.append(
                CheckResult(
                    id="GPU_DETECTED",
                    category="gpu",
                    name="GPU",
                    status=CheckStatus.INFO,
                    severity=CheckSeverity.LOW,
                    summary=gpu["name"],
                    details=f"Driver: {gpu['driver']}\nVRAM: {gpu['vram']}",
                )
            )
    else:
        results.append(
            CheckResult(
                id="GPU_NOT_DETECTED_001",
                category="gpu",
                name="GPU",
                status=CheckStatus.INFO,
                severity=CheckSeverity.LOW,
                summary="No GPU detected",
                details="GPU acceleration not available for local AI models",
            )
        )

    return results
