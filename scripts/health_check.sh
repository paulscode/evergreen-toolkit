#!/bin/bash
# Health Check Script for OpenClaw
# Run periodically to check system health
# Designed for Linux. Partial macOS compatibility for file stat only.

set -e

# Colors (defined early — used in config warnings below)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Resolve workspace and source config
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$(dirname "$SCRIPT_DIR")"
if [ ! -f "$WORKSPACE/.memory_env" ]; then
    echo -e "${YELLOW}⚠️  WARNING: .memory_env not found — memory checks may be inaccurate${NC}"
    echo "  Run: cp config/memory_env.example .memory_env && nano .memory_env"
else
    source "$WORKSPACE/.memory_env"
fi
QDRANT_COLLECTION="${QDRANT_COLLECTION:-${AGENT_NAME:+${AGENT_NAME}-memories}}"  
if [ -z "$QDRANT_COLLECTION" ]; then
    echo -e "${YELLOW}⚠️  QDRANT_COLLECTION not set — set AGENT_NAME or QDRANT_COLLECTION in .memory_env${NC}"
    QDRANT_COLLECTION="agent-memories"
fi

# Check required tools
if ! command -v jq &>/dev/null; then
    echo -e "${YELLOW}⚠️  WARNING: jq not found — collection health checks will be skipped${NC}"
    echo "  Install: sudo apt install jq"
    JQ_AVAILABLE=false
else
    JQ_AVAILABLE=true
fi

# Configurable thresholds (override via environment variables)
DISK_WARN_THRESHOLD="${DISK_WARN_THRESHOLD:-70}"
DISK_CRIT_THRESHOLD="${DISK_CRIT_THRESHOLD:-85}"
MEM_WARN_THRESHOLD="${MEM_WARN_THRESHOLD:-70}"
MEM_CRIT_THRESHOLD="${MEM_CRIT_THRESHOLD:-85}"
BACKUP_STALE_HOURS="${BACKUP_STALE_HOURS:-26}"

ISSUES=0

echo "=== OpenClaw Health Check ==="
echo "Time: $(date)"
echo ""

# Check OpenClaw
echo -n "OpenClaw... "
if command -v openclaw &>/dev/null && openclaw health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
elif pgrep -f "openclaw" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Process found but 'openclaw health' failed${NC}"
else
    echo -e "${RED}✗ Not running${NC}"
    ISSUES=$((ISSUES + 1))
fi

# Check Redis
echo -n "Redis... "
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Responding${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
    ISSUES=$((ISSUES + 1))
fi

# Check Qdrant
echo -n "Qdrant... "
QDRANT_BASE="${QDRANT_URL:-http://localhost:6333}"
if curl -s "${QDRANT_BASE}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Responding${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
    ISSUES=$((ISSUES + 1))
fi

# Check collections
echo -n "Memory Collections... "
if [ "$JQ_AVAILABLE" = false ]; then
    echo -e "${YELLOW}⚠ Skipped (jq not installed)${NC}"
else
    TRUE_RECALL=$(curl -s "${QDRANT_BASE}/collections/${TRUE_RECALL_COLLECTION:-true_recall}" 2>/dev/null | jq -r '.result.status' 2>/dev/null || echo "missing")
    AGENT_MEMORIES=$(curl -s "${QDRANT_BASE}/collections/${QDRANT_COLLECTION}" 2>/dev/null | jq -r '.result.status' 2>/dev/null || echo "missing")

    if [ "$TRUE_RECALL" = "green" ] && [ "$AGENT_MEMORIES" = "green" ]; then
        echo -e "${GREEN}✓ All collections healthy${NC}"
    else
        echo -e "${YELLOW}⚠ true_recall: $TRUE_RECALL, ${QDRANT_COLLECTION}: $AGENT_MEMORIES${NC}"
        ISSUES=$((ISSUES + 1))
    fi
fi

# Check disk usage
echo -n "Disk Usage... "
DISK_USAGE=$(df -h "${WORKSPACE:-$HOME/.openclaw}" 2>/dev/null | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt "$DISK_WARN_THRESHOLD" ]; then
    echo -e "${GREEN}✓ ${DISK_USAGE}%${NC}"
elif [ "$DISK_USAGE" -lt "$DISK_CRIT_THRESHOLD" ]; then
    echo -e "${YELLOW}⚠ ${DISK_USAGE}%${NC}"
else
    echo -e "${RED}✗ ${DISK_USAGE}% (critical)${NC}"
    ISSUES=$((ISSUES + 1))
fi

# Check memory usage
echo -n "Memory Usage... "
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
if [ "$MEM_USAGE" -lt "$MEM_WARN_THRESHOLD" ]; then
    echo -e "${GREEN}✓ ${MEM_USAGE}%${NC}"
elif [ "$MEM_USAGE" -lt "$MEM_CRIT_THRESHOLD" ]; then
    echo -e "${YELLOW}⚠ ${MEM_USAGE}%${NC}"
else
    ISSUES=$((ISSUES + 1))
    echo -e "${RED}✗ ${MEM_USAGE}% (high)${NC}"
fi

# Check backup (optional — set BACKUP_DIR to your external backup location)
echo -n "Last Backup... "
BACKUP_DIR="${BACKUP_DIR:-}"
if [ -z "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}⚠ BACKUP_DIR not set (optional — set to check external backups)${NC}"
elif [ -d "$BACKUP_DIR" ]; then
    LATEST=$(ls -t $BACKUP_DIR/openclaw-*.tar.gz 2>/dev/null | head -1)
    if [ -n "$LATEST" ]; then
        # Platform-aware file modification time
        if [[ "$(uname)" == "Darwin" ]]; then
            BACKUP_AGE=$((($(date +%s) - $(stat -f %m "$LATEST")) / 3600))
        else
            BACKUP_AGE=$((($(date +%s) - $(stat -c %Y "$LATEST")) / 3600))
        fi
        # Stale threshold (configurable via BACKUP_STALE_HOURS, default: 26 hours)
        if [ "$BACKUP_AGE" -lt "$BACKUP_STALE_HOURS" ]; then
            echo -e "${GREEN}✓ ${BACKUP_AGE}h ago${NC}"
        else
            echo -e "${YELLOW}⚠ ${BACKUP_AGE}h ago (stale)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ No backups found${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Backup directory not configured${NC}"
fi

# Summary
echo ""
if [ "$ISSUES" -eq 0 ]; then
    echo -e "${GREEN}=== All Systems Healthy ===${NC}"
    exit 0
else
    echo -e "${RED}=== $ISSUES Issue(s) Found ===${NC}"
    exit 1
fi
