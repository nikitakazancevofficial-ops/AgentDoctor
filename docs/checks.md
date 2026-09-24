# Available Checks

## System Checks

| ID | Category | Description |
|----|----------|-------------|
| SYS_PYTHON_OK | system | Python version check |
| SYS_PYTHON_001 | system | Python below minimum |
| SYS_PLATFORM | system | OS detection |
| SYS_ARCH | system | Architecture detection |
| SYS_CPU | system | CPU info |
| SYS_RAM | system | RAM check |
| SYS_DISK | system | Disk space check |
| SYS_FS | system | Filesystem type |
| SYS_GIT | system | Git detection |
| SYS_GPU | system | GPU detection |
| SYS_WSL | system | WSL detection |
| SYS_VENV | system | Virtual environment |

## PATH Checks

| ID | Category | Description |
|----|----------|-------------|
| PATH_EMPTY_ENTRY_001 | path | Empty PATH entry |
| PATH_NONEXISTENT_001 | path | Non-existent PATH dirs |
| PATH_DUPLICATE_001 | path | Duplicate executables |
| PATH_SHADOW_001 | path | Shadowed executables |

## Network Checks

| ID | Category | Description |
|----|----------|-------------|
| DNS_* | network | DNS resolution |
| HTTP_* | network | HTTP connectivity |
| NET_DNS_001 | network | DNS failure |
| NET_HTTP_001 | network | HTTP failure |

## Proxy Checks

| ID | Category | Description |
|----|----------|-------------|
| PROXY_* | proxy | Proxy variable detection |
| NET_PROXY_001 | proxy | Proxy detected |
| NET_PROXY_NOLOCALHOST_001 | proxy | NO_PROXY missing localhost |

## MCP Checks

| ID | Category | Description |
|----|----------|-------------|
| MCP_NOT_FOUND | mcp | No MCP configs found |
| MCP_FOUND | mcp | MCP configs discovered |
| MCP_CONFIG_001 | mcp | Invalid JSON config |
| MCP_COMMAND_001 | mcp | Command not found |
| MCP_ENDPOINT_001 | mcp | Endpoint unreachable |
| MCP_SECRET_001 | mcp | Secret in config |

## Port Checks

| ID | Category | Description |
|----|----------|-------------|
| PORT_IN_USE_001 | ports | Port occupied |
| PORTS_ACCESS_DENIED | ports | Cannot scan ports |
| PORTS_OK | ports | No conflicts |

## Security Checks

| ID | Category | Description |
|----|----------|-------------|
| SECRET_DETECTED | secrets | Secret found in config |
| SECRETS_OK | secrets | No secrets found |

## Docker Checks

| ID | Category | Description |
|----|----------|-------------|
| DOCKER_OK | docker | Docker installed |
| DOCKER_DAEMON_001 | docker | Daemon not responding |
| DOCKER_COMPOSE_OK | docker | Compose available |

## Ollama Checks

| ID | Category | Description |
|----|----------|-------------|
| OLLAMA_OK | ollama | Ollama installed |
| OLLAMA_SERVER_OK | ollama | Server running |
| OLLAMA_SERVER_001 | ollama | Server not responding |
| OLLAMA_MODELS | ollama | Models available |
| OLLAMA_MISSING | ollama | Not installed |

## GPU Checks

| ID | Category | Description |
|----|----------|-------------|
| GPU_DETECTED | gpu | GPU found |
| GPU_NOT_DETECTED_001 | gpu | No GPU detected |

## Git Checks

| ID | Category | Description |
|----|----------|-------------|
| GIT_OK | git | Git installed |
| GIT_NOT_INSTALLED_001 | git | Git not found |
| GIT_REPO | git | Repository detected |
| GIT_BRANCH | git | Current branch |
| GIT_DIRTY | git | Uncommitted changes |
| GIT_CLEAN | git | Clean working tree |
| GIT_NOT_REPO | git | Not in a repo |
