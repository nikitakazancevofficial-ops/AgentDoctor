# Architecture

## Core Components

### CheckResult

The fundamental unit of diagnostic output. Each check returns one or more `CheckResult` objects containing:

- `id`: Stable issue ID (e.g., `SYS_PYTHON_001`)
- `category`: Check category (system, path, network, etc.)
- `status`: PASS, INFO, WARNING, ERROR, SKIPPED, INTERNAL_ERROR
- `severity`: LOW, MEDIUM, HIGH, CRITICAL
- `summary`: Brief description
- `details`: Additional context
- `recommendation`: Suggested fix

### CheckRegistry

The registry system allows checks to be discovered and run dynamically:

```python
@register_check("my_category")
def check_my_thing() -> list[CheckResult]:
    ...
```

### CommandRunner

Safe external command execution with:

- Configurable timeout
- Cross-platform compatibility
- Exception handling
- Never hangs indefinitely

### Redaction

Secret redaction system that:

- Detects API keys, tokens, passwords in any text
- Never exposes actual secret values
- Works on URLs, JSON, env vars, error messages
- Applied at all output layers

### HealthScore

Calculates a 0-100 health score based on:

- PASS/INFO: No penalty
- WARNING LOW: -5
- WARNING MEDIUM: -10
- WARNING HIGH: -15
- ERROR LOW: -5
- ERROR MEDIUM: -10
- ERROR HIGH: -15
- ERROR CRITICAL: -25

### Renderers

Three output renderers:

1. **RichRenderer**: Color-coded terminal output with icons
2. **JsonRenderer**: Machine-readable JSON output
3. **MarkdownRenderer**: Sanitized Markdown report

## Check Categories

| Category | Description |
|----------|-------------|
| system | OS, Python, RAM, disk, CPU, GPU |
| path | PATH integrity |
| tools | Dev tool detection |
| network | DNS, HTTP connectivity |
| proxy | Proxy configuration |
| ports | Port inspection |
| mcp | MCP config discovery/validation |
| secrets | Secret scanning |
| docker | Docker checks |
| ollama | Ollama checks |
| gpu | GPU detection |
| git | Git checks |
| ai_tools | AI coding tool detection |

## Provider System

AI tool providers follow a common interface:

```python
class BaseProvider(ABC):
    def detect(self) -> bool: ...
    def get_version(self) -> str | None: ...
    def find_configs(self) -> list[Path]: ...
    def run_checks(self) -> list[CheckResult]: ...
```

## Issue Knowledge Base

Each diagnostic issue has a stable ID with associated:

- Title
- Description
- Why it matters
- Suggested actions

Users can look up issues with: `agentdoctor explain <ISSUE_ID>`
