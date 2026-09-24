# 🩺 AgentDoctor

**Diagnose broken AI coding environments in one command.**

AgentDoctor checks your system, PATH, AI coding tools, MCP configuration, network, proxies, ports, Docker, Ollama, Git and common environment problems — without modifying your machine.

```console
$ agentdoctor

  🩺 AgentDoctor v0.1.0
  Diagnose broken AI coding environments in one command.

  Scanning your AI development environment...

  SYSTEM
  ✓ Operating system      Windows 11
  ✓ Architecture          AMD64
  ✓ Python                3.12.3
  ✓ RAM                   32.0 GB
  ✓ Disk                  500.0 GB
  ✓ Git                   2.x
  ✓ GPU                   detected

  AI TOOLS
  ✓ Claude Code           detected
  ○ Codex CLI             not installed
  ○ Gemini CLI            not installed
  ○ Ollama                not installed

  MCP
  ✓ 1 config discovered
  ⚠ github                token stored in config

  NETWORK
  ✓ DNS                   OK
  ✓ HTTP                  OK
  ✓ Proxy                 none

  Health score: 92/100

  1 warning
  18 checks passed

  Suggested actions:

  1. Secret in MCP config
    Variable: GITHUB_PERSONAL_ACCESS_TOKEN
    Recommendation: Use environment variables instead of hardcoding secrets
```

## What is AgentDoctor?

AgentDoctor is a cross-platform CLI tool that automatically diagnoses your AI development environment. It tells you what's installed, what's working, what's broken, and how to fix it — in one command.

## Why AgentDoctor?

AI coding tools (Claude Code, Codex CLI, Gemini CLI, Ollama, MCP servers, etc.) often fail silently or with cryptic errors. AgentDoctor helps you:

- **See what's installed** — Python, Node.js, Git, Docker, Ollama, AI tools
- **Find broken configs** — MCP server configs, invalid JSON, missing executables
- **Detect secrets** — API keys accidentally stored in config files
- **Check network** — DNS, HTTP connectivity, proxy issues
- **Inspect ports** — Common dev/AI ports and what's using them
- **Calculate health score** — A single number summarizing your environment

## Features

### System Checks
- OS, architecture, hostname
- Python version (requires 3.10+)
- Virtual environment detection
- CPU, RAM, disk space
- GPU detection (NVIDIA, AMD, Apple)
- WSL detection (Windows)

### PATH Diagnostics
- Non-existent directories
- Duplicate executables
- Shadowed executables
- Multiple Python/Node/Git installations

### AI Tool Detection
- OpenAI Codex CLI
- Claude Code
- Gemini CLI
- OpenCode
- Ollama

### MCP Configuration
- Auto-discovery in standard locations
- JSON validation
- Command availability checking
- Secret detection in env vars
- URL validation for SSE/Streamable HTTP
- Binary file exclusion (`.vscdb`, `.sqlite`, `.db`, etc.)

### Network Checks
- DNS resolution
- HTTP/HTTPS connectivity
- Proxy detection and NO_PROXY analysis
- Localhost reachability

### Port Diagnostics
- Common dev/AI ports (3000, 5173, 8000, 8080, 11434, etc.)
- Process identification for occupied ports

### Security
- Secret scanning in config files
- Credential redaction in all outputs (terminal, JSON, Markdown)
- No telemetry by default

### Output Formats
- **Rich terminal** — Color-coded with icons
- **JSON** — Machine-readable for CI/CD
- **Markdown** — Sanitized report for GitHub issues

## Supported Platforms

- **Windows 10/11** (primary target)
- **Linux** (Ubuntu, Debian, Fedora, etc.)
- **macOS** (Intel and Apple Silicon)

## Supported AI Tools

| Tool | Detection | Config Check |
|------|-----------|-------------|
| Claude Code | ✓ | ✓ |
| Codex CLI | ✓ | ✓ |
| Gemini CLI | ✓ | ✓ |
| OpenCode | ✓ | ✓ |
| Ollama | ✓ | ✓ |

## Installation

### From source (recommended for v0.1.0)

```bash
git clone https://github.com/nikitakazancevofficial-ops/AgentDoctor.git
cd AgentDoctor
pip install -e ".[dev]"
```

### pip (coming soon — PyPI)

```bash
pip install agentdoctor
```

## Quick Start

### Full diagnostics

```bash
agentdoctor
```

### Specific checks

```bash
agentdoctor check system
agentdoctor check tools
agentdoctor check network
agentdoctor check mcp
agentdoctor check ports
agentdoctor check proxy
agentdoctor check git
agentdoctor check docker
agentdoctor check ollama
agentdoctor check gpu
agentdoctor check secrets
```

### JSON output (for CI/CD)

```bash
agentdoctor --json
```

### Markdown report (for GitHub issues)

```bash
agentdoctor --output report.md
```

### CI mode (stable, machine-readable output)

```bash
agentdoctor --ci
```

### Explain a specific issue

```bash
agentdoctor explain NET_PROXY_001
agentdoctor explain MCP_COMMAND_001
```

### CLI Options

| Flag | Description |
|------|-------------|
| `--help`, `-h` | Show help |
| `--version`, `-V` | Show version |
| `--verbose`, `-v` | Enable verbose output |
| `--debug`, `-d` | Enable debug output |
| `--json` | Output in JSON format |
| `--no-color` | Disable colored output |
| `--only <checks>` | Run only specific checks (comma-separated) |
| `--skip <checks>` | Skip specific checks (comma-separated) |
| `--timeout <s>` | Timeout for individual checks (default: 10s) |
| `--output <file>` | Write report to file (.json or .md) |
| `--ci` | CI mode: stable, machine-readable output |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | No actionable problems |
| 1 | Warnings found |
| 2 | Errors found |
| 3 | Internal AgentDoctor failure |

## JSON Contract

`agentdoctor --json` outputs **only** valid JSON to stdout:

```json
{
  "schema_version": "1",
  "version": "0.1.0",
  "timestamp": "2026-09-24T11:30:30+00:00",
  "system": { ... },
  "health_score": 92,
  "summary": {
    "passed": 18,
    "warnings": 1,
    "errors": 0,
    "skipped": 3,
    "info": 5
  },
  "results": {
    "system": [...],
    "ai_tools": [...],
    ...
  }
}
```

Diagnostic/debug text goes to stderr, never stdout.

## Sanitized Reports

Reports written via `--output report.md` are sanitized:

- Secrets in config files are **redacted** (replaced with `[REDACTED]`)
- No API keys or tokens appear in output
- No authentication credentials are logged

## Privacy

AgentDoctor runs **entirely locally**. No telemetry, no data collection, no network uploads by default.

- Secrets in config files are **redacted** from all outputs
- No API keys are logged or transmitted
- No user data is collected

## Security

- All external commands run with **timeouts**
- No `shell=True` by default
- Secrets are **never** printed (even in debug mode)
- Config files are read **read-only**
- No system modifications are made

## How AgentDoctor Works

```
agentdoctor/
├── cli.py              # CLI entry point (typer)
├── core/
│   ├── models.py       # CheckResult, HealthScore, SystemInfo
│   ├── runner.py       # Safe command execution with timeout
│   ├── registry.py     # Check registration system
│   ├── redaction.py    # Secret redaction utilities
│   └── paths.py        # Platform config directory discovery
├── checks/
│   ├── system.py       # OS, Python, RAM, disk, GPU
│   ├── path.py         # PATH diagnostics
│   ├── tools.py        # Dev tool detection
│   ├── network.py      # DNS, HTTP checks
│   ├── proxy.py        # Proxy detection
│   ├── ports.py        # Port inspection
│   ├── mcp.py          # MCP config discovery/validation
│   ├── secrets.py      # Secret scanning
│   ├── docker.py       # Docker checks
│   ├── ollama.py       # Ollama checks
│   ├── gpu.py          # GPU detection
│   └── git.py          # Git checks
├── providers/
│   ├── base.py         # Base provider class
│   ├── codex.py        # Codex CLI
│   ├── claude.py       # Claude Code
│   ├── gemini.py       # Gemini CLI
│   ├── opencode.py     # OpenCode
│   └── ollama.py       # Ollama
├── renderers/
│   ├── rich_renderer.py    # Terminal output
│   ├── json_renderer.py    # JSON output
│   └── markdown_renderer.py # Markdown report
└── knowledge/
    └── issues.py         # Known issues database
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on:

- Forking and cloning the repo
- Setting up a development environment
- Running tests (`pytest`)
- Running linter (`ruff check`)
- Running type checker (`mypy`)
- Adding a new check
- Submitting a pull request

## Roadmap

- [ ] `agentdoctor fix` — Safe auto-fixes for common issues
- [ ] GUI mode
- [ ] More AI tool providers (Cline, Roo Code, Continue)
- [ ] WSL-enhanced diagnostics
- [ ] Plugin system for custom checks
- [ ] Windows-specific deep diagnostics

## License

MIT License — see [LICENSE](LICENSE) file.

---

**Diagnose your AI dev environment before debugging the AI.**
