# 📄 Markdown Viewer

Simple HTTP server that serves formatted Markdown files as web pages.

## Quick Start

```bash
# Start viewer on port 3000
node markdown-viewer.js

# Start on custom port
node markdown-viewer.js --port 8080

# Stop viewer (if installed as systemd service)
sudo systemctl stop markdown-viewer
```

## Usage

Open in browser: `http://localhost:3000/view?file=/path/to/file.md`

Example: `http://localhost:3000/view?file=evergreens/upstream-architecture/AGENDA.md`

## Features

- GitHub-flavored Markdown rendering
- Syntax highlighting for code blocks
- Clean, readable styling
- Health check endpoint: `http://localhost:3000/health`
- No dependencies beyond Node.js

For full documentation (systemd setup, auto-link-fixing, security details), see [MARKDOWN-VIEWER.md](MARKDOWN-VIEWER.md).
