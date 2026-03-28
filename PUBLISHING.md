# 🚀 Publishing Checklist

**Ready to publish your customized Evergreen Toolkit repository.**

> **Note:** This guide is for **publishing** your customized toolkit as a public repository (i.e., sharing your fork with the community). This is NOT the deployment step — for deploying the toolkit to your OpenClaw workspace, see [QUICKSTART.md](QUICKSTART.md) Step 5 and `scripts/deploy.sh`. Skip this file during initial setup.

---

## Pre-Publishing Checklist

### ✅ Code & Content

- [ ] All personal information sanitized
- [ ] Phone numbers replaced with placeholders
- [ ] Email addresses generalized
- [ ] Hostnames replaced with generic names
- [ ] API keys removed (replaced with placeholders)
- [ ] No wallet addresses or credentials
- [ ] All paths are relative or use `~/.openclaw/`

### ✅ Documentation

- [ ] README.md - Overview and quick start
- [ ] docs/SETUP-GUIDE.md - Complete setup guide
- [ ] docs/SCHEDULING.md - Timezone-aware scheduling
- [ ] docs/TROUBLESHOOTING.md - Common issues
- [ ] config/README.md - Configuration examples
- [ ] memory/README.md - Memory architecture docs
- [ ] evergreens/EVERGREENS.md - Framework documentation

### ✅ Code Quality

- [ ] Python scripts executable (`chmod +x`)
- [ ] Shell scripts executable (`chmod +x`)
- [ ] requirements.txt complete
- [ ] .gitignore configured
- [ ] LICENSE file (MIT)
- [ ] Run `python3 scripts/validate-customization.py` to verify placeholder replacement

### ✅ Repository Structure

```
evergreen-toolkit/
├── README.md
├── QUICKSTART.md
├── ARCHITECTURE.md
├── AGENT-ONBOARDING.md
├── CONTRIBUTING.md
├── PUBLISHING.md
├── CHANGELOG.md
├── GLOSSARY.md
├── MEMORY-SYSTEM.md
├── SECURITY.md
├── LICENSE
├── requirements.txt
├── config/
│   ├── README.md
│   ├── AGENTS-TEMPLATE.md
│   ├── MEMORY-TEMPLATE.md
│   ├── HEARTBEAT-TEMPLATE.md
│   ├── agenda-template.md
│   ├── categories.example.yaml
│   ├── crontab.sample
│   ├── memory_env.example
│   └── openclaw-plugins.example.json
├── docs/
│   ├── README.md
│   ├── AUTONOMY-GUIDELINES.md
│   ├── HEARTBEAT-MEMORY-INTEGRATION.md
│   ├── MEMORY-FIRST-STRATEGY.md
│   ├── MEMORY-INTEGRATION.md
│   ├── NAME-CUSTOMIZATION.md
│   ├── OPERATIONAL-GUIDE.md
│   ├── PLUGIN-RECOMMENDATIONS.md
│   ├── SCHEDULING.md
│   ├── SETUP-GUIDE.md
│   ├── TROUBLESHOOTING.md
│   └── UPSTREAM-MONITORING-GUIDE.md
├── evergreens/
│   ├── EVERGREENS.md
│   ├── DASHBOARD.html
│   ├── upstream-architecture/
│   ├── system-health/
│   ├── prompt-injection/
│   └── household-memory/
├── internal-docs/
│   └── (implementation plans, merge notes, project reviews — maintainer reference documents)
├── memory/
│   ├── README.md
│   ├── SKILL.md
│   ├── MULTI-USER-GUIDE.md
│   ├── OPENCLAW-FORK-CHANGES.md
│   ├── UPSTREAM-CREDITS.md
│   ├── IDENTITY-VERIFICATION.md
│   ├── APPROVED-CONTACTS.json
│   ├── USERS-README.md
│   ├── settings.md
│   ├── curator_prompts/
│   ├── docs/
│   ├── para/
│   │   ├── README.md
│   │   └── templates/
│   └── scripts/ (~36 Python files)
├── scripts/
│   ├── evergreen-ai-runner.sh
│   ├── evergreen-weekly-cycle.sh
│   ├── final-check-wrapper.sh
│   ├── health_check.sh
│   ├── setup.sh
│   ├── setup-markdown-viewer.sh
│   ├── run-single-evergreen.py
│   ├── evergreen_ai_executor.py
│   ├── evergreen-scripted-executor.py
│   ├── evergreen-final-check.py
│   ├── seed-evergreens.py
│   ├── update_evergreen_dashboard.py
│   ├── preflight-check.py
│   ├── preflight-state-maintenance.py
│   ├── validate-customization.py
│   ├── verify-deploy.py
│   ├── weekly-synthesis.py
│   ├── evergreen_utils.py
│   ├── deploy.sh
│   ├── evergreen_utils.py
│   └── fix-markdown-links.js
├── templates/
│   ├── EXAMPLE-COMPLETED-CYCLE.md
│   └── STATE-TEMPLATE.md
└── tools/
    ├── markdown-viewer.js
    ├── MARKDOWN-VIEWER.md
    └── README.md
```

> **Note:** The `scripts/` listing shows the main toolkit scripts. See the actual directory for the complete set (includes `__pycache__/`, etc.).

---

## Deploy to GitHub

### 1. Create Repository

```bash
# Go to github.com
# Create new repository: evergreen-toolkit
# Set to Public
# DO NOT initialize with README (we already have one)
```

### 2. Add Remote and Push

```bash
cd ~/evergreen-toolkit

# Add your GitHub remote
# CUSTOMIZE: replace paulscode with your GitHub username
git remote add origin https://github.com/<your-username>/evergreen-toolkit.git

# Verify remote
git remote -v

# Push to GitHub
git push -u origin main
```

### 3. Verify Repository

- Check all files uploaded at your repository URL
- Verify README renders correctly
- Test that links in README work

---

## Post-Deployment Tasks

### 1. Update README with Your Repo URL

The upstream README uses `paulscode` as the clone URL — this is correct for the canonical public repo. If you're publishing your own fork, update it to your GitHub username:

```bash
# In Installation section, update to your fork's URL:
git clone https://github.com/<your-username>/evergreen-toolkit.git
```

### 2. Add GitHub Topics

In repository settings, add topics:
- `openclaw`
- `ai-agents`
- `automation`
- `memory-system`
- `continuous-improvement`

### 3. Create Release (Optional)

```bash
# Tag the version
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0

# Go to GitHub → Releases → Create new release
# Select tag v1.0.0
# Add release notes
```

---

## Share with Community

### OpenClaw Discord

1. Join: https://discord.com/invite/clawd
2. Post in #skills or #showcase channel
3. Include:
   - Repository URL
   - Brief description
   - Key features
   - installation command

### ClawHub (Optional)

Submit to ClawHub for official skill listing:

```bash
clawhub publish evergreen-toolkit/
```

See ClawHub documentation for publishing guide.

---

## Maintenance Plan

### Ongoing Tasks

- **Monitor issues** - Respond to bug reports and feature requests
- **Update documentation** - Keep installation guide current
- **Community contributions** - Review and merge PRs
- **Version updates** - Tag new releases as features added

### Suggested Improvements

- [ ] Add unit tests for core scripts
- [ ] Create example configuration wizard
- [ ] Add Docker deployment option
- [ ] Create video walkthrough
- [ ] Add performance benchmarks
- [ ] Internationalize documentation

---

## Success Metrics

Track adoption and engagement:

- GitHub stars ⭐
- Forks 🍴
- Issues opened 🐛
- Community contributions 🤝
- Discord mentions 💬

---

## License Compliance

**MIT License** allows:

✅ Commercial use
✅ Modification
✅ Distribution
✅ Private use
✅ Patent use

**Requirements:**

⚠️ Include copyright notice
⚠️ Include license text
⚠️ State changes made (if modifying)

---

**🌲 Your Evergreen Toolkit is ready to help the OpenClaw community grow!**
