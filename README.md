# macSandbox

Run AI agents with full autonomy inside isolated Docker containers.

## What You Get

```bash
./sandbox.py --agent claude      # Claude in isolated container with --dangerously-skip-permissions
./sandbox.py --agent opencode    # any other agent in its own container
```

Each instance runs in its own Docker container. Your project directory is mounted at `/workspace`. The agent can do whatever it wants inside — when it exits, the container is destroyed.

## Requirements

- macOS, Linux, or Windows
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine on Linux)
- `uv` — [install](https://docs.astral.sh/uv/getting-started/installation/)

## Installation

### 1. Install Docker

Download and start [Docker Desktop](https://www.docker.com/products/docker-desktop/), or on Linux:

```bash
curl -fsSL https://get.docker.com | sh
```

### 2. Build the agent image

```bash
cd macSandbox
./sandbox.py --agent claude --build
```

### 3. Install the script

```bash
cp sandbox.py ~/.local/bin/
chmod +x ~/.local/bin/sandbox.py
```

## Usage

```bash
./sandbox.py --agent claude                             # interactive with full permissions
./sandbox.py --agent claude -c                          # continue last conversation
./sandbox.py --agent claude "refactor this codebase"   # start with a prompt
./sandbox.py --agent opencode                           # run a different agent
./sandbox.py --agent claude --memory 8G --cpus 4        # custom resources
```

### Mounting Host Directories

Use `--mount SRC:DST` to bind-mount paths from the host into the container. The flag is repeatable.

Both the `claude` and `opencode` containers run as non-root users (`claude` and `opencode` respectively), so config dirs live under `/home/<user>/` rather than `/root/`.

**Claude — mount auth so the container reuses your existing login:**

```bash
./sandbox.py --agent claude --mount ~/.claude:/home/claude/.claude
```

**Claude — mount auth read-only plus a GitHub CLI config:**

```bash
./sandbox.py --agent claude \
  --mount ~/.claude:/home/claude/.claude:ro \
  --mount ~/.config/gh:/home/claude/.config/gh:ro
```

**opencode — mount its config directory:**

```bash
./sandbox.py --agent opencode --mount ~/.config/opencode:/home/opencode/.config/opencode
```

**Any agent — mount additional context or shared data:**

```bash
./sandbox.py --agent claude \
  --mount ~/.claude:/home/claude/.claude \
  --mount ~/shared-data:/data:ro \
  "analyse the files in /data"
```

> **Root vs non-root:** If you build a custom `Dockerfile.myagent` that runs as `root`, use `/root/.claude` as the destination instead of `/home/<user>/.claude`.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SANDBOX_MEMORY` | `4G` | Memory limit per instance |
| `SANDBOX_CPUS` | `2` | CPU cores per instance |

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│  Host OS                                                │
│                                                         │
│  ┌─────────────┐                                        │
│  │   claude    │  ← Normal, your existing setup         │
│  └─────────────┘                                        │
│                                                         │
│  ┌─────────────────────────────────────────────────────┐│
│  │  sandbox.py →  Docker Container                     ││
│  │  ┌─────────────────────────────────────────────────┐││
│  │  │  Isolated container                             │││
│  │  │  • agent command runs here                      │││
│  │  │  • /workspace ← your project (mounted)          │││
│  │  │  • Isolated network, filesystem, processes      │││
│  │  └─────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

## Adding a New Agent

All you need is a Dockerfile named `Dockerfile.{agent}`.

```dockerfile
# Dockerfile.aider
FROM python:3.12-slim
RUN pip install aider-chat
WORKDIR /workspace
CMD ["aider", "--yes"]
```

```bash
./sandbox.py --agent aider --build
./sandbox.py --agent aider
```

## Repository Layout

```
macSandbox/
├── sandbox.py          # Entry point
├── Dockerfile.claude   # Claude container image
└── Dockerfile.opencode # opencode container image
```

## License

MIT

---

*Built by Claude, for Claude, with human supervision.*
