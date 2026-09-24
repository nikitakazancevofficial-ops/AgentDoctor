"""JSON renderer for AgentDoctor output."""

from __future__ import annotations

import datetime
import json
from enum import Enum
from typing import Any

from agentdoctor.core.models import CheckResult, HealthScore, SystemInfo
from agentdoctor.core.redaction import sanitize_check_result


class _EnumEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles enums."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


def render_json(
    results: dict[str, list[CheckResult]],
    health: HealthScore,
    system_info: SystemInfo,
    version: str,
) -> str:
    """Render all results as a JSON string."""
    output = {
        "schema_version": "1",
        "version": version,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "system": {
            "platform": system_info.platform,
            "platform_version": system_info.platform_version,
            "architecture": system_info.architecture,
            "python_version": system_info.python_version,
            "ram_total_gb": system_info.ram_total_gb,
            "ram_available_gb": system_info.ram_available_gb,
            "disk_free_gb": system_info.disk_free_gb,
            "disk_total_gb": system_info.disk_total_gb,
            "cpu_threads": system_info.cpu_threads,
            "git_repo": system_info.git_repo,
            "git_branch": system_info.git_branch,
            "wsl_installed": system_info.wsl_installed,
        },
        "health_score": health.score,
        "summary": {
            "passed": health.passed,
            "warnings": health.warnings,
            "errors": health.errors,
            "skipped": health.skipped,
            "info": health.info,
        },
        "results": {},
    }
    results_out: dict[str, list[dict[str, Any]]] = {}
    output["results"] = results_out

    for category, category_results in results.items():
        results_out[category] = []
        for r in category_results:
            r = sanitize_check_result(r)
            entry: dict[str, Any] = {
                "id": r.id,
                "category": r.category,
                "name": r.name,
                "status": r.status.value if isinstance(r.status, Enum) else r.status,
                "severity": r.severity.value if isinstance(r.severity, Enum) else r.severity,
                "summary": r.summary,
                "details": r.details,
                "detected_value": r.detected_value,
                "expected_value": r.expected_value,
                "recommendation": r.recommendation,
                "commands": r.commands,
                "metadata": r.metadata,
                "duration_ms": r.duration_ms,
            }
            results_out[category].append(entry)

    return json.dumps(output, indent=2, ensure_ascii=False, cls=_EnumEncoder)
