#!/usr/bin/env node
/**
 * Markdown Viewer Server
 * 
 * A simple web server that renders Markdown files with proper formatting.
 * Usage: node markdown-viewer.js [--port 3000] [--workspace /path/to/workspace]
 * 
 * Endpoints:
 * - GET /view?file=/path/to/file.md  - Render markdown file
 * - GET /health                       - Health check
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

// Config
function getArg(name) {
  const idx = process.argv.findIndex(arg => arg === `--${name}` || arg.startsWith(`--${name}=`));
  if (idx === -1) return undefined;
  const arg = process.argv[idx];
  if (arg.includes('=')) return arg.split('=')[1];
  return process.argv[idx + 1];
}
const PORT = getArg('port') || 3000;
const WORKSPACE = getArg('workspace')
  || process.env.OPENCLAW_WORKSPACE 
  || path.join(require('os').homedir(), '.openclaw', 'workspace');

// HTML escape helper for user-controlled values in error responses
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// Simple Markdown parser (no external dependencies)
function parseMarkdown(md) {
  // Escape HTML
  let html = md
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  
  // Headers
  html = html.replace(/^###### (.*)$/gm, '<h6>$1</h6>');
  html = html.replace(/^##### (.*)$/gm, '<h5>$1</h5>');
  html = html.replace(/^#### (.*)$/gm, '<h4>$1</h4>');
  html = html.replace(/^### (.*)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.*)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.*)$/gm, '<h1>$1</h1>');
  
  // Bold and italic
  html = html.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/___(.*?)___/g, '<strong><em>$1</em></strong>');
  html = html.replace(/__(.*?)__/g, '<strong>$1</strong>');
  html = html.replace(/_(.*?)_/g, '<em>$1</em>');
  
  // Strikethrough
  html = html.replace(/~~(.*?)~~/g, '<del>$1</del>');
  
  // Code blocks (fenced)
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre class="code-block"${lang ? ` data-lang="${lang}"` : ''}><code>${code.trim()}</code></pre>`;
  });
  
  // Inline code
  html = html.replace(/`(.*?)`/g, '<code class="inline-code">$1</code>');
  
  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  
  // Images
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="markdown-image">');
  
  // Blockquotes
  html = html.replace(/^&gt; (.*$)/gm, '<blockquote>$1</blockquote>');
  html = html.replace(/<blockquote>(.*?)<\/blockquote>\n<blockquote>(.*?)<\/blockquote>/g, '<blockquote>$1<br/>$2</blockquote>');
  
  // Horizontal rule
  html = html.replace(/^---$/gm, '<hr/>');
  html = html.replace(/^\*\*\*$/gm, '<hr/>');
  
  // Checkboxes (GitHub style) — must come before generic list rules
  html = html.replace(/^- \[x\] (.*$)/gm, '<li class="task done">☑ $1</li>');
  html = html.replace(/^- \[ \] (.*$)/gm, '<li class="task">☐ $1</li>');
  
  // Unordered lists
  html = html.replace(/^[\*\-] (.*$)/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
  
  // Ordered lists
  html = html.replace(/^\d+\. (.*$)/gm, '<li class="ordered">$1</li>');
  
  // Tables (basic support)
  html = html.replace(/^\|(.+)\|$/gm, (match, content) => {
    const cells = content.split('|').map(cell => cell.trim());
    return '<tr>' + cells.map(cell => `<td>${cell}</td>`).join('') + '</tr>';
  });
  html = html.replace(/<tr>.+<\/tr>\n<tr>(<td>-+<\/td>)+<\/tr>\n/g, ''); // Remove separator row
  
  // Line breaks
  html = html.replace(/\n\n/g, '</p><p>');
  html = html.replace(/\n/g, '<br/>');
  
  // Wrap in paragraph tags
  if (!html.startsWith('<')) {
    html = '<p>' + html + '</p>';
  }
  
  return html;
}

function getStyles() {
  return `
    <style>
      :root {
        --bg-primary: #0d1117;
        --bg-secondary: #161b22;
        --bg-tertiary: #21262d;
        --text-primary: #e6edf3;
        --text-secondary: #8b949e;
        --text-tertiary: #6e7681;
        --accent: #58a6ff;
        --accent-hover: #79c0ff;
        --border: #30363d;
        --success: #3fb950;
        --warning: #d29922;
        --error: #f85149;
        --code-bg: #161b22;
      }
      
      * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
      }
      
      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
        background: var(--bg-primary);
        color: var(--text-primary);
        line-height: 1.6;
        padding: 2rem;
        max-width: 900px;
        margin: 0 auto;
      }
      
      .markdown-body {
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 2rem 2.5rem;
      }
      
      h1, h2, h3, h4, h5, h6 {
        margin-top: 1.5em;
        margin-bottom: 0.75em;
        font-weight: 600;
        line-height: 1.25;
        color: var(--text-primary);
      }
      
      h1 { 
        font-size: 2em; 
        padding-bottom: 0.3em;
        border-bottom: 1px solid var(--border);
        margin-top: 0;
      }
      
      h2 { 
        font-size: 1.5em; 
        padding-bottom: 0.3em;
        border-bottom: 1px solid var(--border);
      }
      
      h3 { font-size: 1.25em; }
      h4 { font-size: 1em; }
      h5 { font-size: 0.875em; }
      h6 { font-size: 0.85em; color: var(--text-secondary); }
      
      p {
        margin-bottom: 1em;
      }
      
      a {
        color: var(--accent);
        text-decoration: none;
      }
      
      a:hover {
        text-decoration: underline;
        color: var(--accent-hover);
      }
      
      code {
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 0.9em;
      }
      
      .inline-code {
        background: var(--code-bg);
        padding: 0.2em 0.4em;
        border-radius: 3px;
        color: var(--text-primary);
      }
      
      .code-block {
        background: var(--code-bg);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 1rem;
        overflow-x: auto;
        margin: 1rem 0;
      }
      
      .code-block code {
        color: var(--text-primary);
      }
      
      blockquote {
        border-left: 4px solid var(--accent);
        padding-left: 1rem;
        color: var(--text-secondary);
        margin: 1rem 0;
      }
      
      ul, ol {
        margin: 1rem 0;
        padding-left: 2rem;
      }
      
      li {
        margin-bottom: 0.5em;
      }
      
      li.task {
        list-style: none;
        margin-left: -1.5rem;
      }
      
      li.task.done {
        color: var(--success);
      }
      
      hr {
        border: none;
        border-top: 1px solid var(--border);
        margin: 2rem 0;
      }
      
      table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
      }
      
      td, th {
        border: 1px solid var(--border);
        padding: 0.5rem 1rem;
        text-align: left;
      }
      
      tr:nth-child(even) {
        background: var(--bg-tertiary);
      }
      
      .header-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border);
      }
      
      .file-path {
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 0.85em;
        color: var(--text-secondary);
        background: var(--bg-tertiary);
        padding: 0.4em 0.8em;
        border-radius: 4px;
      }
      
      .back-link {
        color: var(--accent);
        font-size: 0.9em;
      }
      
      .error-box {
        background: rgba(248, 81, 73, 0.1);
        border: 1px solid var(--error);
        border-radius: 6px;
        padding: 1.5rem;
        margin: 2rem 0;
      }
      
      .error-box h1 {
        color: var(--error);
        border: none;
        margin-top: 0;
      }
      
      .emoji {
        font-style: normal;
      }
      
      /* Status badges */
      .status-badge {
        display: inline-block;
        padding: 0.25em 0.5em;
        border-radius: 999px;
        font-size: 0.75em;
        font-weight: 600;
        margin-right: 0.5em;
      }
      
      .status-success { 
        background: rgba(63, 185, 80, 0.2); 
        color: var(--success); 
      }
      
      .status-warning { 
        background: rgba(210, 153, 34, 0.2); 
        color: var(--warning); 
      }
      
      .status-error { 
        background: rgba(248, 81, 73, 0.2); 
        color: var(--error); 
      }
    </style>
  `;
}

function renderPage(title, content, filePath = null, error = false) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  ${getStyles()}
</head>
<body>
  <div class="markdown-body">
    ${filePath && !error ? `
    <div class="header-bar">
      <a href="file://${WORKSPACE}/evergreens/DASHBOARD.html" class="back-link">← Back to Dashboard</a>
      <span class="file-path">${filePath}</span>
    </div>
    ` : ''}
    ${content}
  </div>
</body>
</html>`;
}

function handleRequest(req, res) {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  
  // CORS headers — restrict to localhost origins (covers OpenClaw gateway,
  // other local services on different ports, and file:// protocol access)
  const origin = req.headers.origin;
  if (origin === 'null' || // file:// protocol
      (origin && /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin))) {
    res.setHeader('Access-Control-Allow-Origin', origin);
  }
  res.setHeader('Access-Control-Allow-Methods', 'GET');
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  
  // Health check
  if (url.pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', workspace: WORKSPACE, port: PORT }));
    return;
  }
  
  // View markdown file
  if (url.pathname === '/view') {
    const filePath = url.searchParams.get('file');
    
    if (!filePath) {
      res.writeHead(400);
      res.end(renderPage('Error', '<div class="error-box"><h1>🚫 Missing Parameter</h1><p>Please provide a <code>file</code> parameter with the path to a Markdown file.</p><p>Example: <code>/view?file=/home/user/.openclaw/workspace/evergreens/household-memory/AGENDA.md</code></p></div>', null, true));
      return;
    }
    
    // Security: Ensure file is within workspace
    const resolvedPath = path.resolve(filePath);
    if (!resolvedPath.startsWith(WORKSPACE + path.sep) && resolvedPath !== WORKSPACE) {
      res.writeHead(403);
      res.end(renderPage('Access Denied', `<div class="error-box"><h1>🔒 Access Denied</h1><p>File must be within workspace directory.</p><p>Workspace: <code>${escapeHtml(WORKSPACE)}</code></p><p>Requested: <code>${escapeHtml(filePath)}</code></p></div>`, null, true));
      return;
    }
    
    // Check file exists
    if (!fs.existsSync(resolvedPath)) {
      res.writeHead(404);
      res.end(renderPage('File Not Found', `<div class="error-box"><h1>📄 File Not Found</h1><p>The requested file does not exist:</p><p><code>${escapeHtml(filePath)}</code></p></div>`, filePath, true));
      return;
    }
    
    // Check file extension
    const ext = path.extname(resolvedPath).toLowerCase();
    if (!['.md', '.markdown', '.mdown'].includes(ext)) {
      res.writeHead(400);
      res.end(renderPage('Invalid File Type', `<div class="error-box"><h1>📄 Invalid File Type</h1><p>Please provide a Markdown file (.md, .markdown, or .mdown)</p></div>`, filePath, true));
      return;
    }
    
    // Read and render
    try {
      const content = fs.readFileSync(resolvedPath, 'utf8');
      const title = path.basename(resolvedPath);
      const html = parseMarkdown(content);
      
      res.writeHead(200);
      res.end(renderPage(title, html, resolvedPath));
    } catch (err) {
      res.writeHead(500);
      res.end(renderPage('Error', `<div class="error-box"><h1>⚠️ Error Reading File</h1><p>${escapeHtml(err.message)}</p></div>`, filePath, true));
    }
    
    return;
  }
  
  // Default - show help
  res.writeHead(200);
  res.end(renderPage('Markdown Viewer', `
    <h1>📄 Markdown Viewer</h1>
    <p>A simple web server for rendering Markdown files with proper formatting.</p>
    
    <h2>Usage</h2>
    <p>Open a Markdown file in your browser:</p>
    <pre class="code-block"><code>http://localhost:${PORT}/view?file=/path/to/file.md</code></pre>
    
    <h2>Example</h2>
    <p><a href="/view?file=${WORKSPACE}/HEARTBEAT.md">View HEARTBEAT.md</a></p>
    <p><a href="/view?file=${WORKSPACE}/evergreens/household-memory/AGENDA.md">View Household Memory Agenda</a></p>
    
    <h2>Features</h2>
    <ul>
      <li>✅ Headers (h1-h6)</li>
      <li>✅ Bold, italic, strikethrough</li>
      <li>✅ Links and images</li>
      <li>✅ Code blocks (fenced and inline)</li>
      <li>✅ Blockquotes</li>
      <li>✅ Lists (ordered, unordered, checkboxes)</li>
      <li>✅ Tables (basic)</li>
      <li>✅ Horizontal rules</li>
      <li>✅ GitHub-style task lists</li>
    </ul>
    
    <h2>Security</h2>
    <p>Files outside the workspace directory are blocked for security.</p>
    <p>Workspace: <code>${WORKSPACE}</code></p>
  `));
}

// Start server
const server = http.createServer(handleRequest);

server.listen(PORT, '127.0.0.1', () => {
  console.log(`📄 Markdown Viewer running at http://127.0.0.1:${PORT}`);
  console.log(`Workspace: ${WORKSPACE}`);
  console.log(``);
  console.log(`Usage:`);
  console.log(`  http://localhost:${PORT}/view?file=/path/to/file.md`);
  console.log(``);
  console.log(`Example:`);
  console.log(`  http://localhost:${PORT}/view?file=${WORKSPACE}/HEARTBEAT.md`);
});
