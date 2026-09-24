# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in AgentDoctor:

1. **Do not** open a public issue
2. Use GitHub's private vulnerability reporting if available
   - Navigate to Security > Code scanning > Private vulnerability reporting
3. If private reporting is not available, open a regular issue **without** revealing the vulnerability details
4. Allow time for a fix before public disclosure

## Security Principles

- **No telemetry** by default
- **No secrets** in output (even debug mode)
- **No system modifications** — read-only diagnostics
- **Timeouts** on all external commands
- **Safe defaults** — never execute potentially harmful commands

## Current Security Measures

- Secret redaction in all outputs (terminal, JSON, Markdown)
- Command timeout protection (default 10s)
- No `shell=True` for subprocess calls
- Config files read-only
- No API key transmission
- Binary file detection prevents `.vscdb`, `.sqlite`, `.db` files from being parsed as JSON
