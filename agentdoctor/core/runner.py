"""Safe command execution runner with timeout."""

from __future__ import annotations

import asyncio
import contextlib
import subprocess
from collections.abc import Sequence

from agentdoctor.core.models import DEFAULT_TIMEOUT, CommandResult

_timeout_cap: float | None = None


class CommandTimeoutError(Exception):
    """Raised when a command exceeds its timeout."""


def configure_timeout(timeout: float | None) -> None:
    """Cap command timeouts for the current diagnostic invocation.

    Individual checks can still request shorter deadlines; this setting never
    lengthens a built-in check's timeout.
    """
    global _timeout_cap
    if timeout is not None and timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    _timeout_cap = timeout


def _effective_timeout(timeout: float) -> float:
    return min(timeout, _timeout_cap) if _timeout_cap is not None else timeout


async def _run_async(
    cmd: Sequence[str],
    timeout: float = DEFAULT_TIMEOUT,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> CommandResult:
    timeout = _effective_timeout(timeout)
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return CommandResult(
                command=" ".join(cmd),
                return_code=proc.returncode,
                stdout=stdout_bytes.decode("utf-8", errors="replace"),
                stderr=stderr_bytes.decode("utf-8", errors="replace"),
            )
        except asyncio.TimeoutError:
            with contextlib.suppress(ProcessLookupError):
                proc.kill()
            return CommandResult(
                command=" ".join(cmd),
                timed_out=True,
                exception="Command timed out",
            )
    except Exception as e:
        return CommandResult(
            command=" ".join(cmd),
            exception=str(e),
        )


def run_command(
    cmd: Sequence[str],
    timeout: float = DEFAULT_TIMEOUT,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> CommandResult:
    """Run a command safely with timeout.

    Returns a CommandResult with stdout, stderr, return_code, etc.
    Never hangs indefinitely.
    """
    if not cmd:
        return CommandResult(
            command="",
            return_code=1,
            exception="Empty command",
        )

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run_async(cmd, timeout=timeout, cwd=cwd, env=env))
    finally:
        loop.close()


def run_command_sync(
    cmd: Sequence[str],
    timeout: float = DEFAULT_TIMEOUT,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> CommandResult:
    """Run a command using subprocess with timeout (synchronous)."""
    timeout = _effective_timeout(timeout)
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
            text=True,
        )
        return CommandResult(
            command=" ".join(cmd),
            return_code=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
        )
    except subprocess.TimeoutExpired:
        return CommandResult(
            command=" ".join(cmd),
            timed_out=True,
            exception="Command timed out",
        )
    except FileNotFoundError:
        return CommandResult(
            command=" ".join(cmd),
            return_code=127,
            exception="Command not found",
        )
    except Exception as e:
        return CommandResult(
            command=" ".join(cmd),
            exception=str(e),
        )
