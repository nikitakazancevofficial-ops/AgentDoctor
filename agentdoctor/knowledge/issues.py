"""Knowledge base for known issues and their explanations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IssueInfo:
    """Information about a known diagnostic issue."""

    id: str
    title: str
    description: str
    why_it_matters: str
    suggested_actions: list[str]


ISSUE_KNOWLEDGE: dict[str, IssueInfo] = {
    "SYS_PYTHON_001": IssueInfo(
        id="SYS_PYTHON_001",
        title="Python version below minimum",
        description="The installed Python version is below the minimum required version.",
        why_it_matters="AgentDoctor requires Python 3.10+ for compatibility with modern libraries and features.",
        suggested_actions=[
            "Install Python 3.10 or later from https://python.org",
            "Or use your system package manager: apt install python3.10, brew install python, etc.",
        ],
    ),
    "SYS_DISK_LOW_001": IssueInfo(
        id="SYS_DISK_LOW_001",
        title="Low disk space",
        description="Free disk space is below the warning threshold.",
        why_it_matters="Insufficient disk space can prevent AI models, containers, and development tools from working.",
        suggested_actions=[
            "Clean up temporary files and caches",
            "Remove unused Docker images: docker image prune",
            "Clear npm/yarn/pip caches",
            "Free at least 5 GB of disk space",
        ],
    ),
    "SYS_DISK_CRITICAL_001": IssueInfo(
        id="SYS_DISK_CRITICAL_001",
        title="Critically low disk space",
        description="Free disk space is critically low.",
        why_it_matters="The system may become unstable or unable to write files.",
        suggested_actions=[
            "Free disk space immediately",
            "Remove large unused files and directories",
        ],
    ),
    "PATH_EMPTY_ENTRY_001": IssueInfo(
        id="PATH_EMPTY_ENTRY_001",
        title="Empty PATH entry",
        description="A PATH entry is empty, which means the current directory is in PATH.",
        why_it_matters="An empty PATH entry can cause unexpected executable resolution and is a security concern.",
        suggested_actions=[
            "Review your PATH environment variable",
            "Remove empty entries from PATH",
        ],
    ),
    "PATH_NONEXISTENT_001": IssueInfo(
        id="PATH_NONEXISTENT_001",
        title="Non-existent PATH entry",
        description="A directory in PATH does not exist on the filesystem.",
        why_it_matters="Non-existent PATH entries slow down executable lookups and indicate cleanup is needed.",
        suggested_actions=[
            "Remove non-existent directories from PATH",
            "Reinstall the tool that created the PATH entry if needed",
        ],
    ),
    "PATH_DUPLICATE_001": IssueInfo(
        id="PATH_DUPLICATE_001",
        title="Duplicate executables in PATH",
        description="The same executable is found in multiple directories.",
        why_it_matters="Multiple installations can cause version conflicts and unpredictable behavior.",
        suggested_actions=[
            "Keep only the preferred installation",
            "Remove older or unnecessary installations from PATH",
        ],
    ),
    "PATH_SHADOW_001": IssueInfo(
        id="PATH_SHADOW_001",
        title="Executable shadowing",
        description="An executable in an earlier PATH entry shadows one in a later entry.",
        why_it_matters="The wrong version of a tool may be used unexpectedly.",
        suggested_actions=[
            "Reorder PATH entries to prefer the correct installation",
            "Remove duplicate installations",
        ],
    ),
    "NET_DNS_001": IssueInfo(
        id="NET_DNS_001",
        title="DNS resolution failure",
        description="Could not resolve a hostname via DNS.",
        why_it_matters="DNS issues prevent network connectivity to remote services.",
        suggested_actions=[
            "Check your DNS settings",
            "Try: nslookup <hostname> or dig <hostname>",
            "Check firewall/antivirus DNS settings",
        ],
    ),
    "NET_HTTP_001": IssueInfo(
        id="NET_HTTP_001",
        title="HTTP connection failed",
        description="Could not establish an HTTP/HTTPS connection.",
        why_it_matters="Network connectivity is required for AI tool API calls and package installation.",
        suggested_actions=[
            "Check your internet connection",
            "Check proxy settings",
            "Check firewall/antivirus settings",
        ],
    ),
    "NET_PROXY_001": IssueInfo(
        id="NET_PROXY_001",
        title="Proxy detected",
        description="A proxy environment variable is set, which may intercept connections.",
        why_it_matters="Proxies can slow down or block local AI tool communication.",
        suggested_actions=[
            "Verify proxy settings are correct",
            "Ensure localhost/127.0.0.1 is in NO_PROXY",
        ],
    ),
    "NET_PROXY_NOLOCALHOST_001": IssueInfo(
        id="NET_PROXY_NOLOCALHOST_001",
        title="NO_PROXY missing localhost",
        description="Proxy is set but NO_PROXY does not include localhost.",
        why_it_matters="Local AI tools and MCP servers may fail to connect.",
        suggested_actions=[
            "Add localhost,127.0.0.1,::1 to NO_PROXY",
            'Example: export NO_PROXY="localhost,127.0.0.1,::1,.local"',
        ],
    ),
    "MCP_CONFIG_001": IssueInfo(
        id="MCP_CONFIG_001",
        title="Invalid MCP configuration",
        description="An MCP config file contains invalid JSON or missing required fields.",
        why_it_matters="Invalid MCP configs prevent MCP servers from starting.",
        suggested_actions=[
            "Fix the JSON syntax in the config file",
            "Ensure 'command' or 'url' field is present",
        ],
    ),
    "MCP_COMMAND_001": IssueInfo(
        id="MCP_COMMAND_001",
        title="MCP command not found",
        description="The MCP server specifies a command that is not available on PATH.",
        why_it_matters="The MCP server cannot start without its base command.",
        suggested_actions=[
            "Install the required command",
            "Or update the MCP config to use an available command",
        ],
    ),
    "MCP_ENDPOINT_001": IssueInfo(
        id="MCP_ENDPOINT_001",
        title="MCP endpoint unreachable",
        description="The MCP server URL is not responding.",
        why_it_matters="The MCP server may be down or the URL may be incorrect.",
        suggested_actions=[
            "Check if the server is running",
            "Verify the URL is correct",
            "Check network connectivity",
        ],
    ),
    "MCP_SECRET_001": IssueInfo(
        id="MCP_SECRET_001",
        title="Secret stored in MCP config",
        description="A secret (API key, token, password) was found in an MCP config file.",
        why_it_matters="Storing secrets in config files is a security risk.",
        suggested_actions=[
            "Use environment variables instead of hardcoding secrets",
            "Use a secrets manager",
            "Remove the secret from the config file",
        ],
    ),
    "PORT_IN_USE_001": IssueInfo(
        id="PORT_IN_USE_001",
        title="Port is occupied",
        description="A commonly used development port is already in use.",
        why_it_matters="Port conflicts can prevent AI tools and local servers from starting.",
        suggested_actions=[
            "Check if you need this port for another service",
            "Close the process if unintended: taskkill /PID <pid> /F (Windows)",
            "Or change the port in your tool configuration",
        ],
    ),
    "DOCKER_DAEMON_001": IssueInfo(
        id="DOCKER_DAEMON_001",
        title="Docker daemon not responding",
        description="Docker CLI is installed but the daemon is not responding.",
        why_it_matters="Docker-based MCP servers and tools won't work.",
        suggested_actions=[
            "Start Docker Desktop or docker daemon",
            "Check Docker service status",
        ],
    ),
    "OLLAMA_SERVER_001": IssueInfo(
        id="OLLAMA_SERVER_001",
        title="Ollama server not responding",
        description="Ollama is installed but its local server is not responding.",
        why_it_matters="Ollama-based AI tools require the server to be running.",
        suggested_actions=[
            "Run: ollama serve",
            "Or start Ollama from your system tray",
        ],
    ),
    "GIT_NOT_INSTALLED_001": IssueInfo(
        id="GIT_NOT_INSTALLED_001",
        title="Git not installed",
        description="Git executable was not found on PATH.",
        why_it_matters="Git is required by many AI coding tools for version control and repository operations.",
        suggested_actions=[
            "Install Git from https://git-scm.com",
            "Or use your package manager: apt install git, brew install git, etc.",
        ],
    ),
    "GPU_NOT_DETECTED_001": IssueInfo(
        id="GPU_NOT_DETECTED_001",
        title="GPU not detected",
        description="No GPU was detected on the system.",
        why_it_matters="GPU acceleration is important for running local AI models efficiently.",
        suggested_actions=[
            "Check GPU drivers are installed",
            "On Windows, check Device Manager for GPU status",
        ],
    ),
}


def get_issue_info(issue_id: str) -> IssueInfo | None:
    """Look up issue information by ID."""
    return ISSUE_KNOWLEDGE.get(issue_id)
