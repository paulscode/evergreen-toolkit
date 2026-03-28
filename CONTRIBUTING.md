# Contributing to Evergreen Toolkit

Thank you for considering contributing to the Evergreen Toolkit! This guide will help you contribute effectively.

---

## 🌲 What We're Building

The Evergreen Toolkit helps OpenClaw agents improve continuously through automated daily cycles. We focus on:

- **Simplicity** — Easy to install, understand, and extend
- **Reliability** — Fault-tolerant, self-healing, well-tested
- **Community-driven** — Built by the OpenClaw community, for the community

---

## How to Contribute

### 1. Report Bugs

Found a bug? Open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, OpenClaw version)
- Logs or error messages

### 2. Suggest Features

Have an idea? Open an issue with:
- Problem you're trying to solve
- Proposed solution
- Use cases
- Any alternatives you considered

### 3. Submit Code

**Before starting:**
1. Check existing issues/PRs to avoid duplicates
2. Comment on the issue to claim it (prevents duplicate work)
3. Create a feature branch: `git checkout -b feature/your-feature-name`

**Development:**
```bash
# Fork and clone (replace <your-username> with your GitHub username)
git clone https://github.com/<your-username>/evergreen-toolkit.git ~/evergreen-toolkit
cd ~/evergreen-toolkit

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make your changes
# ...

# Test locally (AI runner — recommended)
./scripts/evergreen-ai-runner.sh system-health

# Or test with direct executor
python3 scripts/run-single-evergreen.py --evergreen system-health
```

**Before submitting:**
- [ ] Code follows existing style (PEP 8 for Python)
- [ ] Added/updated tests if applicable
- [ ] Updated documentation
- [ ] Removed any hardcoded paths/secrets
- [ ] Tested on a fresh install

**Submit:**
```bash
# Commit with clear message
git add -A
git commit -m "feat: add disk usage trending to system-health evergreen

- Tracks disk usage over time in STATE.md
- Adds warning threshold at 85% capacity
- Includes cleanup recommendations in AGENDA.md
- Closes #42"

# Push and create PR
git push origin feature/your-feature-name
# Then open PR on GitHub
```

---

## Code Style

### Python

- Follow [PEP 8](https://pep8.org/)
- Use type hints where helpful
- Docstrings for all public functions
- Keep functions focused (single responsibility)

```python
def start_cycle(evergreen: str) -> dict:
    """Mark an evergreen cycle as started.
    
    Args:
        evergreen: Name of the evergreen
        
    Returns:
        Timing dict with started_at timestamp
    """
    # Implementation
```

### Markdown

- Use headers hierarchically (H1 → H2 → H3)
- Keep lines under 100 characters when possible
- Use code blocks for commands/examples
- Include tables for structured data

### JavaScript

- Use modern ES6+ syntax
- Async/await for async operations
- JSDoc comments for functions

---

## Testing

### Manual Testing

Always test your changes:

```bash
# Test evergreen execution
python3 scripts/run-single-evergreen.py --evergreen <your-evergreen>

# Test memory scripts
python3 memory/scripts/save_mem.py --user-id test

# Check dashboard generation
python3 scripts/update_evergreen_dashboard.py
```

### Test Coverage

Tests use **pytest**. Add tests for:
- New scripts (create `.test.py` or use `pytest`)
- Configuration examples
- Edge cases (missing files, network failures)

---

## Documentation

### Updating Docs

When adding features, update:
- `README.md` — Overview and quick start
- `docs/SETUP-GUIDE.md` — Setup instructions
- `docs/TROUBLESHOOTING.md` — Common issues
- Relevant evergreen STATE.md templates

### Documentation Style

- **Clear and concise** — Get to the point
- **Examples first** — Show, don't just tell
- **Sanitized** — No personal info, use placeholders
- **Tested** — Verify all commands work

### HTML Comment Convention

The project uses HTML comments to signal the nature of content in template files. Use these markers consistently:

| Marker | Meaning | Example |
|--------|---------|---------|
| `<!-- EXAMPLE: ... -->` | File contains illustrative data from the author's deployment. Replace entirely with your own. | Used in STATE.md, REFERENCES.md |
| `<!-- CUSTOMIZE: ... -->` | Inline point that needs customization for your environment. | Used for paths, versions, hostnames |
| `<!-- STATUS: STUB ... -->` | File is a placeholder for future work — minimal or no functional content. | Used in planned-but-unimplemented files |

---

## Review Process

1. **Submit PR** — Link to related issues
2. **Automated checks** — CI will run (when configured)
3. **Maintainer review** — Usually within 48 hours
4. **Feedback** — Address comments, push updates
5. **Merge** — Squash and merge to `main`

### PR Guidelines

- **Title format:** `type: brief description` (e.g., `feat: add cost optimization evergreen`)
- **Description:** What, why, how (with examples)
- **Screenshots:** For UI changes
- **Testing:** How you tested it

---

## Areas for Contribution

### High Priority

- Additional evergreen types (performance, cost, compliance)
- Unit tests and CI/CD pipeline
- Better visualizations and dashboards
- Internationalization (i18n)
- Performance optimizations

### Nice to Have

- Example evergreen templates
- Video tutorials
- Integration with other tools
- Monitoring/alerting improvements
- Community showcases

---

## Questions?

- **Discord:** https://discord.com/invite/clawd (#skills channel)
- **GitHub Issues:** https://github.com/paulscode/evergreen-toolkit/issues
- **Docs:** https://github.com/paulscode/evergreen-toolkit/tree/main/docs

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License (same as the project).

---

**Thank you for making the Evergreen Toolkit better! 🌲**
