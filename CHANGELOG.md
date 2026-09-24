# Changelog

## 0.1.0

### Added

- System diagnostics (OS, Python, RAM, disk, CPU, GPU)
- PATH diagnostics (duplicates, shadowing, non-existent entries)
- Dev tool detection (Python, Node.js, Git, Docker, Ollama)
- AI tool providers (Codex, Claude Code, Gemini CLI, OpenCode, Ollama)
- MCP configuration discovery and validation
- Secret scanning and redaction
- Network checks (DNS, HTTP, proxy)
- Port diagnostics
- Health score calculation
- Rich terminal, JSON, and Markdown output
- Cross-platform support (Windows, Linux, macOS)
- `agentdoctor` — Full diagnostics
- `agentdoctor check <type>` — Specific checks
- `agentdoctor --json` — JSON output for CI/CD
- `agentdoctor --output <file>` — Markdown report
- `agentdoctor --ci` — CI mode
- `agentdoctor explain <id>` — Issue explanations
- `agentdoctor self-check` — Self-diagnosis
- Issue knowledge base with 20+ known issues
