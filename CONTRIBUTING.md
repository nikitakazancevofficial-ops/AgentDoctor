# Contributing to AgentDoctor

Thank you for your interest in contributing to AgentDoctor!

## Prerequisites

- Python 3.10 or later
- pip (Python package manager)

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/<your-username>/agentdoctor.git
   cd agentdoctor
   ```
3. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # Linux/macOS
   ```
4. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Running Tests

```bash
pytest
pytest -v                        # Verbose
pytest --cov=agentdoctor         # With coverage
pytest --cov=agentdoctor --cov-report=term-missing
```

## Linting and Type Checking

```bash
ruff check agentdoctor tests     # Lint
ruff format agentdoctor tests    # Format
ruff check --fix agentdoctor tests  # Auto-fix
mypy agentdoctor                 # Type check
```

## Adding a New Check

1. Create a new file in `agentdoctor/checks/` (e.g., `my_check.py`)
2. Use the `@register_check` decorator:

```python
from agentdoctor.core.registry import register_check
from agentdoctor.core.models import CheckResult, CheckStatus, CheckSeverity

@register_check("my_category")
def check_my_thing() -> list[CheckResult]:
    results = []
    # Your check logic here
    results.append(CheckResult(
        id="MY_CHECK_001",
        category="my_category",
        name="My check",
        status=CheckStatus.PASS,
        severity=CheckSeverity.LOW,
        summary="Everything is OK",
    ))
    return results
```

3. Import the module in `agentdoctor/cli.py` so it gets registered
4. Add tests in `tests/`
5. Run `ruff check`, `ruff format`, `mypy`, and `pytest`

## Coding Standards

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints (Python 3.10+ syntax)
- Write tests for new functionality
- Keep functions small and focused
- Use `ruff` for formatting and linting

## Report an Issue

Use the GitHub issue tracker with:

- Bug reports: **Bug Report** template
- Feature requests: **Feature Request** template

**Important:** When reporting issues, DO NOT paste API keys, tokens, or secrets.
