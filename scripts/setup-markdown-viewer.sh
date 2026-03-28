#!/bin/bash
#
# Markdown Viewer Systemd Service Setup
# Creates and enables a systemd service for the markdown viewer
#
# Usage: ./setup-markdown-viewer.sh [--port 3000]
#
# NOTE: Requires sudo for systemd service installation.
# For manual/non-root setup, run directly instead:
#   node tools/markdown-viewer.js [--port 3000]
#

set -e

# Config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
PORT="${2:-3000}"
SERVICE_NAME="markdown-viewer"
USER="$(whoami)"

echo "🔧 Setting up Markdown Viewer as systemd service..."
echo "   Workspace: $WORKSPACE"
echo "   Port: $PORT"
echo "   User: $USER"
echo ""

# Create systemd service file
cat > /tmp/$SERVICE_NAME.service << EOF
[Unit]
Description=Markdown Viewer for $WORKSPACE
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORKSPACE
ExecStart=$(which node) $WORKSPACE/tools/markdown-viewer.js --port $PORT --workspace $WORKSPACE
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF

# Copy to systemd directory
echo "📄 Creating systemd service file..."
sudo cp /tmp/$SERVICE_NAME.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start service
echo "⚙️  Enabling and starting service..."
sudo systemctl enable $SERVICE_NAME.service
sudo systemctl start $SERVICE_NAME.service

# Verify
sleep 2
if sudo systemctl is-active --quiet $SERVICE_NAME.service; then
    echo ""
    echo "✅ Success! Markdown Viewer is now running."
    echo ""
    echo "   Service status: sudo systemctl status $SERVICE_NAME.service"
    echo "   View logs: journalctl -u $SERVICE_NAME.service -f"
    echo "   Test: curl http://localhost:$PORT/health"
    echo ""
    echo "   Viewer URL: http://localhost:$PORT/view?file=/path/to/file.md"
else
    echo "❌ Service failed to start. Check logs with: journalctl -u $SERVICE_NAME.service"
    exit 1
fi

# Cleanup
rm -f /tmp/$SERVICE_NAME.service
