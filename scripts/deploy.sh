#!/usr/bin/env bash
# Evergreen Toolkit — Deploy to Workspace
#
# Copies operational files from the cloned repo to the OpenClaw workspace.
# After deployment, the live system runs entirely from the workspace.
# The repo can be kept for updates or deleted.
#
# Usage:
#   bash scripts/deploy.sh [--workspace <path>] [--force]
#
# Options:
#   --workspace <path>   Target workspace directory (default: ~/.openclaw/workspace)
#   --force              Overwrite existing scripts/tools (preserves user data)
#
# Run from inside the cloned repo after setup.sh has been run.

set -euo pipefail

# ── Parse arguments ─────────────────────────────────────────────────────
WORKSPACE=""
FORCE=0

while [[ $# -gt 0 ]]; do
    case $1 in
        --workspace)
            WORKSPACE="$2"
            shift 2
            ;;
        --force)
            FORCE=1
            shift
            ;;
        -h|--help)
            echo "Usage: bash scripts/deploy.sh [--workspace <path>] [--force]"
            echo ""
            echo "Options:"
            echo "  --workspace <path>   Target workspace (default: ~/.openclaw/workspace)"
            echo "  --force              Overwrite existing scripts/tools (preserves user data)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: bash scripts/deploy.sh [--workspace <path>] [--force]"
            exit 1
            ;;
    esac
done

# ── Resolve paths ─────────────────────────────────────────────────────
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE="${WORKSPACE:-$HOME/.openclaw/workspace}"
WORKSPACE="$(realpath -m "$WORKSPACE")"

echo "=== Evergreen Toolkit — Deploy to Workspace ==="
echo "Repo:      $REPO_DIR"
echo "Workspace: $WORKSPACE"
echo ""

# ── Safety checks ───────────────────────────────────────────────────────
REPO_REAL="$(realpath "$REPO_DIR")"
if [[ "$WORKSPACE" == "$REPO_REAL" || "$WORKSPACE" == "$REPO_REAL/"* ]]; then
    echo "ERROR: Workspace cannot be inside the repo directory."
    echo "  Repo:      $REPO_REAL"
    echo "  Workspace: $WORKSPACE"
    echo "Choose a different workspace path (e.g., ~/.openclaw/workspace)."
    exit 1
fi

if [[ ! -d "$REPO_DIR/.venv" ]]; then
    echo "ERROR: Virtual environment not found at $REPO_DIR/.venv"
    echo "Run 'bash scripts/setup.sh' first."
    exit 1
fi

if [[ ! -f "$REPO_DIR/.memory_env" ]]; then
    echo "ERROR: .memory_env not found in repo."
    echo "Copy from config/memory_env.example and configure it first."
    exit 1
fi

# Check that .memory_env has been configured (not still the raw template)
if grep -q '<agent>' "$REPO_DIR/.memory_env" 2>/dev/null; then
    echo "WARNING: .memory_env still contains <agent> placeholder."
    echo "Edit .memory_env with your actual values before deploying."
    read -rp "Continue anyway? [y/N] " yn
    [[ "$yn" =~ ^[Yy]$ ]] || exit 1
fi

# Check for existing workspace files
if [[ -d "$WORKSPACE/scripts" || -d "$WORKSPACE/evergreens" ]] && [[ "$FORCE" -eq 0 ]]; then
    echo "WARNING: Workspace already has evergreen files."
    echo "Use --force to overwrite scripts and tools (user data is preserved)."
    read -rp "Continue with --force behavior? [y/N] " yn
    if [[ "$yn" =~ ^[Yy]$ ]]; then
        FORCE=1
    else
        exit 1
    fi
fi

# ── Create workspace directories ────────────────────────────────────────
echo "Creating workspace directories..."
mkdir -p "$WORKSPACE"/{scripts,evergreens,memory/scripts,memory/para,memory/curator_prompts,memory/docs,tools,templates,logs,config}

# ── Helper: copy file if not exists or force ─────────────────────────────
copy_file() {
    local src="$1"
    local dst="$2"
    local overwrite="${3:-0}"  # 0=skip if exists, 1=overwrite

    if [[ ! -f "$src" ]]; then
        return
    fi

    if [[ -f "$dst" ]] && [[ "$overwrite" -eq 0 ]]; then
        return
    fi

    local dst_dir
    dst_dir="$(dirname "$dst")"
    mkdir -p "$dst_dir"
    cp "$src" "$dst"
}

# ── Helper: copy directory recursively ───────────────────────────────────
copy_dir() {
    local src="$1"
    local dst="$2"
    local overwrite="${3:-0}"

    if [[ ! -d "$src" ]]; then
        return
    fi

    mkdir -p "$dst"

    if [[ "$overwrite" -eq 1 ]]; then
        cp -r "$src"/. "$dst"/
    else
        # Only copy files that don't exist in destination
        cd "$src"
        find . -type f | while IFS= read -r f; do
            if [[ ! -f "$dst/$f" ]]; then
                mkdir -p "$(dirname "$dst/$f")"
                cp "$f" "$dst/$f"
            fi
        done
        cd - > /dev/null
    fi
}

# ── Deploy scripts ──────────────────────────────────────────────────────
echo "Deploying scripts..."
SCRIPT_FILES=(
    evergreen-ai-runner.sh
    evergreen-weekly-cycle.sh
    final-check-wrapper.sh
    health_check.sh
    fix-markdown-links.js
    setup-markdown-viewer.sh
    run-single-evergreen.py
    evergreen_ai_executor.py
    evergreen-scripted-executor.py
    evergreen-final-check.py
    update_evergreen_dashboard.py
    evergreen_utils.py
    preflight-state-maintenance.py
    weekly-synthesis.py
    seed-evergreens.py
    validate-customization.py
    verify-deploy.py
    preflight-check.py
)

for f in "${SCRIPT_FILES[@]}"; do
    copy_file "$REPO_DIR/scripts/$f" "$WORKSPACE/scripts/$f" "$FORCE"
done

# Make shell scripts executable
chmod +x "$WORKSPACE"/scripts/*.sh 2>/dev/null || true

# ── Deploy evergreens ───────────────────────────────────────────────────
echo "Deploying evergreens..."
# Top-level evergreen files (always overwrite on --force)
copy_file "$REPO_DIR/evergreens/EVERGREENS.md" "$WORKSPACE/evergreens/EVERGREENS.md" "$FORCE"
copy_file "$REPO_DIR/evergreens/DASHBOARD.html" "$WORKSPACE/evergreens/DASHBOARD.html" "$FORCE"

# Each evergreen directory
for eg in upstream-architecture system-health prompt-injection household-memory; do
    EG_SRC="$REPO_DIR/evergreens/$eg"
    EG_DST="$WORKSPACE/evergreens/$eg"
    [[ ! -d "$EG_SRC" ]] && continue
    mkdir -p "$EG_DST"

    # User data files: only copy if they don't exist (never overwrite)
    for uf in STATE.md AGENDA.md timing.json; do
        copy_file "$EG_SRC/$uf" "$EG_DST/$uf" 0
    done

    # Other files: copy if not exists, or overwrite on --force
    cd "$EG_SRC"
    find . -type f ! -name STATE.md ! -name AGENDA.md ! -name timing.json | while IFS= read -r f; do
        # Skip agenda-history (user data)
        [[ "$f" == ./agenda-history/* ]] && continue
        copy_file "$EG_SRC/$f" "$EG_DST/$f" "$FORCE"
    done
    cd - > /dev/null

    # Ensure agenda-history directory exists
    mkdir -p "$EG_DST/agenda-history"
done

# ── Deploy memory system ────────────────────────────────────────────────
echo "Deploying memory system..."

# Memory scripts (always overwrite on --force — they're code, not user data)
copy_dir "$REPO_DIR/memory/scripts" "$WORKSPACE/memory/scripts" "$FORCE"

# Memory docs
copy_dir "$REPO_DIR/memory/docs" "$WORKSPACE/memory/docs" "$FORCE"

# Curator prompts (user data — skip if exists)
copy_dir "$REPO_DIR/memory/curator_prompts" "$WORKSPACE/memory/curator_prompts" 0

# PARA templates (always useful to have)
copy_dir "$REPO_DIR/memory/para/templates" "$WORKSPACE/memory/para/templates" "$FORCE"

# PARA README
copy_file "$REPO_DIR/memory/para/README.md" "$WORKSPACE/memory/para/README.md" "$FORCE"

# Memory reference docs (skip user data like APPROVED-CONTACTS.json, settings.md)
for mf in SKILL.md README.md MULTI-USER-GUIDE.md IDENTITY-VERIFICATION.md UPSTREAM-CREDITS.md OPENCLAW-FORK-CHANGES.md USERS-README.md; do
    copy_file "$REPO_DIR/memory/$mf" "$WORKSPACE/memory/$mf" "$FORCE"
done

# User data files — only copy if they don't exist
copy_file "$REPO_DIR/memory/APPROVED-CONTACTS.json" "$WORKSPACE/memory/APPROVED-CONTACTS.json" 0
copy_file "$REPO_DIR/memory/settings.md" "$WORKSPACE/memory/settings.md" 0

# ── Deploy tools ────────────────────────────────────────────────────────
echo "Deploying tools..."
copy_dir "$REPO_DIR/tools" "$WORKSPACE/tools" "$FORCE"

# ── Deploy templates ────────────────────────────────────────────────────
echo "Deploying templates..."
copy_dir "$REPO_DIR/templates" "$WORKSPACE/templates" "$FORCE"

# ── Deploy config templates as live files ────────────────────────────────
echo "Deploying workspace configuration files..."

# AGENTS.md — only if not already present (user-customized)
if [[ ! -f "$WORKSPACE/AGENTS.md" ]]; then
    cp "$REPO_DIR/config/AGENTS-TEMPLATE.md" "$WORKSPACE/AGENTS.md"
    echo "  Created AGENTS.md from template"
else
    echo "  AGENTS.md already exists (skipped)"
fi

# MEMORY.md — only if not already present
if [[ ! -f "$WORKSPACE/MEMORY.md" ]]; then
    cp "$REPO_DIR/config/MEMORY-TEMPLATE.md" "$WORKSPACE/MEMORY.md"
    echo "  Created MEMORY.md from template"
else
    echo "  MEMORY.md already exists (skipped)"
fi

# HEARTBEAT.md — only if not already present
if [[ ! -f "$WORKSPACE/HEARTBEAT.md" ]]; then
    cp "$REPO_DIR/config/HEARTBEAT-TEMPLATE.md" "$WORKSPACE/HEARTBEAT.md"
    echo "  Created HEARTBEAT.md from template"
else
    echo "  HEARTBEAT.md already exists (skipped)"
fi

# ARCHITECTURE.md — reference copy (overwrite on --force)
copy_file "$REPO_DIR/ARCHITECTURE.md" "$WORKSPACE/ARCHITECTURE.md" "$FORCE"

# ── Generate .gitignore ──────────────────────────────────────────────────
if [[ ! -f "$WORKSPACE/.gitignore" ]]; then
    cat > "$WORKSPACE/.gitignore" << 'GITIGNORE'
.memory_env
.venv/
logs/*.log
*.pyc
__pycache__/
.evergreen-*.lock
evergreens/*/.backups/
GITIGNORE
    echo "  Created .gitignore"
else
    echo "  .gitignore already exists (skipped)"
fi

# ── Copy .memory_env ────────────────────────────────────────────────────
if [[ ! -f "$WORKSPACE/.memory_env" ]]; then
    cp "$REPO_DIR/.memory_env" "$WORKSPACE/.memory_env"
    chmod 600 "$WORKSPACE/.memory_env"
    echo "  Copied .memory_env to workspace"
else
    echo "  .memory_env already exists in workspace (skipped)"
fi

# ── Create Python virtual environment in workspace ──────────────────────
echo "Setting up Python virtual environment in workspace..."
if [[ ! -d "$WORKSPACE/.venv" ]]; then
    python3 -m venv "$WORKSPACE/.venv"
    "$WORKSPACE/.venv/bin/pip" install -q -r "$REPO_DIR/requirements.txt"
    echo "  Created .venv and installed dependencies"
else
    if [[ "$FORCE" -eq 1 ]]; then
        "$WORKSPACE/.venv/bin/pip" install -q -r "$REPO_DIR/requirements.txt"
        echo "  Updated .venv dependencies"
    else
        echo "  .venv already exists (skipped)"
    fi
fi

# Copy requirements.txt for future reference
copy_file "$REPO_DIR/requirements.txt" "$WORKSPACE/requirements.txt" "$FORCE"

# ── Generate pre-filled crontab ─────────────────────────────────────────
echo "Generating pre-filled crontab..."
CRONTAB_SRC="$REPO_DIR/config/crontab.sample"
CRONTAB_DST="$WORKSPACE/config/crontab.generated"

if [[ -f "$CRONTAB_SRC" ]]; then
    sed "s|\\\$WORKSPACE|$WORKSPACE|g; s|\$TOOLKIT|$WORKSPACE|g; s|/path/to/evergreen-toolkit|$WORKSPACE|g; s|/path/to/openclaw-workspace|$WORKSPACE|g" \
        "$CRONTAB_SRC" > "$CRONTAB_DST"
    echo "  Generated $CRONTAB_DST"
    echo "  Review and install with: crontab $CRONTAB_DST"
fi

# ── Run post-deploy verification ────────────────────────────────────────
VERIFY_SCRIPT="$WORKSPACE/scripts/verify-deploy.py"
if [[ -f "$VERIFY_SCRIPT" ]]; then
    echo ""
    echo "Running post-deploy verification..."
    "$WORKSPACE/.venv/bin/python3" "$VERIFY_SCRIPT" --workspace "$WORKSPACE" --repo "$REPO_DIR" || true
fi

# ── Done ────────────────────────────────────────────────────────────────
echo ""
echo "=== Deployment complete ==="
echo ""
echo "Next steps:"
echo "  1. cd $WORKSPACE"
echo "  2. Run preflight check:"
echo "       python3 scripts/preflight-check.py"
echo "  3. Edit AGENTS.md — replace <user> placeholders with actual names"
echo "  4. Edit MEMORY.md — verify paths are correct"
echo "  5. Edit HEARTBEAT.md — verify memory capture commands"
echo "  6. Initialize memory collections:"
echo "       source .venv/bin/activate && source .memory_env"
echo "       python3 memory/scripts/init_memory_collections.py"
echo "  7. Test one evergreen:"
echo "       ./scripts/evergreen-ai-runner.sh system-health"
echo "  8. Review and install crontab:"
echo "       cat config/crontab.generated"
echo "       crontab config/crontab.generated"
echo ""
echo "The cloned repo ($REPO_DIR) is no longer needed for runtime."
echo "Keep it for pulling updates, or delete it."
