FROM node:22-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code globally
RUN npm install -g @anthropic-ai/claude-code

# Create non-root user for security
RUN useradd -m -s /bin/bash claude
USER claude

# Set up workspace
WORKDIR /workspace

# Default command
CMD ["claude", "--dangerously-skip-permissions"]
