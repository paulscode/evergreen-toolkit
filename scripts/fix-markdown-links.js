#!/usr/bin/env node
/**
 * Markdown Link Fixer for Evergreen Dashboard
 * Scans workspace HTML/MD files for file:// links to .md files
 * and updates them to route through the markdown viewer service.
 * 
 * Usage: node scripts/fix-markdown-links.js [--dry-run]
 */

const fs = require('fs');
const path = require('path');

// Config
const WORKSPACE = process.env.OPENCLAW_WORKSPACE || path.join(require('os').homedir(), '.openclaw', 'workspace');
const MARKDOWN_VIEWER_PORT = process.env.MARKDOWN_VIEWER_PORT || '3000';
const MARKDOWN_VIEWER_URL = `http://localhost:${MARKDOWN_VIEWER_PORT}`;
const DRY_RUN = process.argv.includes('--dry-run');

// Patterns to match file:// links to .md files
const FILE_MD_PATTERN = /href=["']file:\/\/[^"']*\.md["']/g;

// Files to scan (add more as needed)
const FILES_TO_SCAN = [
  'evergreens/DASHBOARD.html',
  // Add other HTML/MD files that might contain agenda links
];

function fixLink(match) {
  const url = match.slice(6, -1); // Remove href=" and "
  const filePath = url.replace('file://', '');
  
  if (!filePath.endsWith('.md')) {
    return match; // Not a markdown file, skip
  }
  
  const viewerUrl = `${MARKDOWN_VIEWER_URL}/view?file=${filePath}`;
  return `href="${viewerUrl}"`;
}

function scanAndFix(filePath) {
  const fullPath = path.join(WORKSPACE, filePath);
  
  if (!fs.existsSync(fullPath)) {
    console.log(`⚠️  File not found: ${filePath}`);
    return { found: 0, fixed: 0 };
  }
  
  const content = fs.readFileSync(fullPath, 'utf8');
  const matches = content.match(FILE_MD_PATTERN) || [];
  
  if (matches.length === 0) {
    console.log(`✅ ${filePath}: No file:// .md links found`);
    return { found: 0, fixed: 0 };
  }
  
  console.log(`🔍 ${filePath}: Found ${matches.length} file:// .md link(s):`);
  matches.forEach(m => console.log(`   - ${m}`));
  
  const newContent = content.replace(FILE_MD_PATTERN, fixLink);
  
  if (DRY_RUN) {
    console.log(`   [DRY RUN] Would update ${matches.length} link(s)\n`);
    return { found: matches.length, fixed: 0 };
  }
  
  if (newContent === content) {
    console.log(`   No changes needed\n`);
    return { found: matches.length, fixed: 0 };
  }
  
  fs.writeFileSync(fullPath, newContent, 'utf8');
  console.log(`   ✅ Updated ${matches.length} link(s)\n`);
  
  return { found: matches.length, fixed: matches.length };
}

function scanAllMarkdownFiles() {
  console.log(`🔍 Scanning for file:// links to .md files in ${WORKSPACE}...\n`);
  
  const results = { filesScanned: 0, totalFound: 0, totalFixed: 0 };
  
  // Scan predefined files
  FILES_TO_SCAN.forEach(file => {
    const result = scanAndFix(file);
    results.filesScanned++;
    results.totalFound += result.found;
    results.totalFixed += result.fixed;
  });
  
  // Additional: scan all HTML files in evergreens/
  const evergreensDir = path.join(WORKSPACE, 'evergreens');
  if (fs.existsSync(evergreensDir)) {
    const files = fs.readdirSync(evergreensDir);
    files.forEach(file => {
      if (file.endsWith('.html')) {
        const result = scanAndFix(path.join('evergreens', file));
        results.filesScanned++;
        results.totalFound += result.found;
        results.totalFixed += result.fixed;
      }
    });
  }
  
  return results;
}

function main() {
  console.log(`🔗 Markdown Link Fixer for Evergreen Dashboard`);
  console.log(`Workspace: ${WORKSPACE}`);
  console.log(`Viewer URL: ${MARKDOWN_VIEWER_URL}`);
  console.log(`Dry Run: ${DRY_RUN ? 'YES' : 'NO'}\n`);
  
  const results = scanAllMarkdownFiles();
  
  console.log(`\n📊 Summary:`);
  console.log(`   Files scanned: ${results.filesScanned}`);
  console.log(`   Links found: ${results.totalFound}`);
  console.log(`   Links fixed: ${results.totalFixed}`);
  
  if (DRY_RUN) {
    console.log(`\nRun without --dry-run to apply fixes.`);
  } else if (results.totalFixed > 0) {
    console.log(`\n✅ All file:// .md links now route through markdown viewer!`);
  }
  
  process.exit(0);
}

main();
