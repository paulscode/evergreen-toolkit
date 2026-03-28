#!/usr/bin/env bash
# Evergreen Toolkit — Initial Setup
# Run from the toolkit root directory:
#   bash scripts/setup.sh

set -euo pipefail

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$TOOLKIT_DIR"

echo "=== Evergreen Toolkit Setup ==="
echo "Working directory: $TOOLKIT_DIR"
echo

# 1. Create virtual environment
if [[ ! -d .venv ]]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# 2. Install dependencies
echo "Installing Python dependencies..."
.venv/bin/pip install -q -r requirements.txt

# 3. Copy environment template if not already present
if [[ ! -f .memory_env ]]; then
    cp config/memory_env.example .memory_env
    chmod 600 .memory_env
    echo "Created .memory_env from template — edit it with your actual values."
else
    echo ".memory_env already exists."
fi

# 4. Make shell scripts executable
chmod +x scripts/*.sh

# 5. Create logs directory
mkdir -p logs

echo
echo "=== Setup complete ==="
echo
echo "Next steps:"
echo "  1. Edit .memory_env with your Redis, Qdrant, and agent details"
echo "  2. Deploy to workspace: bash scripts/deploy.sh --workspace ~/.openclaw/workspace"
echo "  3. Follow QUICKSTART.md from Step 6 onward (in the workspace)"
echo ""
echo "Full guide: QUICKSTART.md  |  Detailed guide: docs/SETUP-GUIDE.md"
