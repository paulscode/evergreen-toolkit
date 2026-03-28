# Markdown Viewer

A lightweight web server for rendering Markdown files with proper formatting in the browser.

## Features

- ✅ Full Markdown rendering (headers, bold, italic, lists, tables, code blocks)
- ✅ GitHub-style checklists (☐ pending, ☑ complete)
- ✅ Syntax highlighting for code blocks
- ✅ Dark theme matching OpenClaw UI
- ✅ Security: Only serves files within workspace directory
- ✅ Zero dependencies (pure Node.js)
- ✅ "Back to Dashboard" navigation link
- ✅ Auto-fix for raw `file://` markdown links (via `fix-markdown-links.js`)

## Quick Start

```bash
# Start the viewer (default port 3000)
node tools/markdown-viewer.js

# Start on custom port
node tools/markdown-viewer.js --port 8080

# Start with explicit workspace path
node tools/markdown-viewer.js --port 3000 --workspace /path/to/workspace
```

## Usage

Open a Markdown file in your browser:

```
http://localhost:3000/view?file=/path/to/file.md
```

### Examples

```
http://localhost:3000/view?file=/home/user/.openclaw/workspace/evergreens/system-health/AGENDA.md
http://localhost:3000/view?file=/home/user/.openclaw/workspace/evergreens/DASHBOARD.html
http://localhost:3000/health
```

## Auto-Start on Boot (Recommended)

### Option 1: Use Setup Script

```bash
cd ~/.openclaw/workspace
./scripts/setup-markdown-viewer.sh --port 3000
```

This creates and enables a systemd service that:
- Starts automatically on boot
- Restarts if it crashes
- Logs to journal (`journalctl -u markdown-viewer -f`)

### Option 2: Manual Systemd Setup

1. Create service file: `/etc/systemd/system/markdown-viewer.service`

```ini
[Unit]
Description=Markdown Viewer for OpenClaw
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/.openclaw/workspace
ExecStart=/usr/bin/node /home/your_username/.openclaw/workspace/tools/markdown-viewer.js --port 3000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=markdown-viewer

[Install]
WantedBy=multi-user.target
```

2. Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable markdown-viewer.service
sudo systemctl start markdown-viewer.service
sudo systemctl status markdown-viewer.service
```

## Markdown Link Fixer

The `scripts/fix-markdown-links.js` script automatically scans for `file://` links to `.md` files and converts them to viewer URLs.

### When It Runs

- Automatically during every evergreen cycle (after dashboard update)
- Can be run manually at any time

### Manual Usage

```bash
# Preview changes (dry-run)
node scripts/fix-markdown-links.js --dry-run

# Apply fixes
node scripts/fix-markdown-links.js
```

### What It Does

Converts links like this:
```html
<a href="file:///home/user/.openclaw/workspace/evergreens/AGENDA.md">Agenda</a>
```

To this:
```html
<a href="http://localhost:3000/view?file=/home/user/.openclaw/workspace/evergreens/AGENDA.md">Agenda</a>
```

## Integration

### Evergreens Dashboard

The dashboard (`evergreens/DASHBOARD.html`) should link to agenda files through the markdown viewer:

```html
<a href="http://localhost:3000/view?file=/home/user/.openclaw/workspace/evergreens/system-health/AGENDA.md">
  📋 Current Agenda
</a>
```

The markdown viewer's "Back to Dashboard" link navigates to `evergreens/DASHBOARD.html` by default.

### Evergreen AI Runner

The `scripts/evergreen-ai-runner.sh` automatically runs the link fixer after each dashboard update:

```bash
# In the dashboard update section
LINK_FIXER="$WORKSPACE/scripts/fix-markdown-links.js"
if [[ -f "$LINK_FIXER" ]] && command -v node &>/dev/null; then
    node "$LINK_FIXER" 2>>"$LOG_FILE" || log "WARN: Markdown link fixer failed (non-fatal)"
fi
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /view?file=/path/to/file.md` | Render markdown file |
| `GET /health` | Health check (returns JSON) |

### Health Check Response

```json
{
  "status": "ok",
  "workspace": "/home/user/.openclaw/workspace",
  "port": 3000
}
```

## Security

The viewer only serves files within the workspace directory (`$OPENCLAW_WORKSPACE`). Attempts to access files outside this directory return a 403 error.

## Supported Markdown Features

### Text Formatting
- Headers (h1-h6)
- **Bold**, *italic*, ***bold italic***
- ~~Strikethrough~~
- `Inline code`

### Code Blocks

```javascript
const x = 123;
console.log(x);
```

### Lists

- Unordered items
- Ordered items
- [ ] Checkboxes (pending)
- [x] Checkboxes (complete)

### Other
- Blockquotes
- Horizontal rules
- Links and images
- Basic tables

## Troubleshooting

**Viewer not starting:**
```bash
# Check if port is in use
lsof -i :3000

# Check service status (if using systemd)
sudo systemctl status markdown-viewer.service

# Check logs
journalctl -u markdown-viewer.service -f

# Manual start for debugging
node tools/markdown-viewer.js --port 3000
```

**Page not rendering:**
- Ensure Node.js is installed: `node --version`
- Check file path is absolute and correct
- Verify file has `.md` extension

**Links showing raw markdown:**
- Run the link fixer: `node scripts/fix-markdown-links.js`
- Check that viewer is running: `curl http://localhost:3000/health`

## Files

- `tools/markdown-viewer.js` - Main server script
- `scripts/fix-markdown-links.js` - Link fixer for dashboard
- `scripts/setup-markdown-viewer.sh` - Systemd service installer

## Version

Unreleased (targeting 1.0.0)
