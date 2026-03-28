#!/usr/bin/env python3
"""
Post-deploy verification for Evergreen Toolkit.

Validates that the deployed workspace is correctly structured and
independent of the cloned repo.

Usage:
    python3 scripts/verify-deploy.py [--workspace <path>] [--repo <path>]

Can be run:
  1. Automatically at the end of deploy.sh
  2. Manually anytime to verify workspace integrity
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

passed = 0
warned = 0
failed = 0


def check(name, ok, msg_ok="OK", msg_fail="Missing", severity="error"):
    global passed, warned, failed
    if ok:
        passed += 1
        print(f"  {GREEN}✓{RESET} {name}: {msg_ok}")
    elif severity == "warning":
        warned += 1
        print(f"  {YELLOW}⚠{RESET} {name}: {msg_fail}")
    else:
        failed += 1
        print(f"  {RED}✗{RESET} {name}: {msg_fail}")


def check_structure(workspace: Path):
    """Verify required directories and files exist."""
    print("Workspace structure:")

    for d in ["scripts", "evergreens", "memory/scripts", "tools", "logs"]:
        p = workspace / d
        check(f"  {d}/", p.is_dir())

    for eg in ["upstream-architecture", "system-health", "prompt-injection", "household-memory"]:
        state = workspace / "evergreens" / eg / "STATE.md"
        check(f"  evergreens/{eg}/STATE.md", state.exists())

    required_scripts = [
        "evergreen-ai-runner.sh",
        "evergreen-weekly-cycle.sh",
        "final-check-wrapper.sh",
        "health_check.sh",
        "fix-markdown-links.js",
        "setup-markdown-viewer.sh",
        "run-single-evergreen.py",
        "evergreen_ai_executor.py",
        "evergreen-scripted-executor.py",
        "evergreen-final-check.py",
        "update_evergreen_dashboard.py",
        "evergreen_utils.py",
        "preflight-state-maintenance.py",
        "weekly-synthesis.py",
        "seed-evergreens.py",
        "validate-customization.py",
        "verify-deploy.py",
        "preflight-check.py",
    ]
    for s in required_scripts:
        check(f"  scripts/{s}", (workspace / "scripts" / s).exists())

    check("  evergreens/EVERGREENS.md", (workspace / "evergreens" / "EVERGREENS.md").exists())


def check_runtime(workspace: Path):
    """Verify runtime dependencies."""
    print("\nRuntime:")

    venv = workspace / ".venv"
    check(".venv exists", venv.is_dir())

    python_bin = venv / "bin" / "python3"
    if python_bin.exists():
        try:
            result = subprocess.run(
                [str(python_bin), "-c", "print('ok')"],
                capture_output=True, text=True, timeout=10
            )
            check(".venv/bin/python3 works", result.returncode == 0,
                  "Executable", "Not working")
        except Exception:
            check(".venv/bin/python3 works", False, msg_fail="Error running python3")
    else:
        check(".venv/bin/python3 exists", False)

    env_file = workspace / ".memory_env"
    check(".memory_env exists", env_file.exists())

    if env_file.exists():
        content = env_file.read_text()
        is_template = "<agent>" in content or "your-agent" in content
        check(".memory_env configured", not is_template,
              "Configured", "Still contains template placeholders", severity="warning")


def check_config(workspace: Path):
    """Verify workspace config files exist."""
    print("\nConfiguration:")

    for f in ["AGENTS.md", "MEMORY.md", "HEARTBEAT.md"]:
        check(f, (workspace / f).exists())

    check("ARCHITECTURE.md", (workspace / "ARCHITECTURE.md").exists(),
          severity="warning" if not (workspace / "ARCHITECTURE.md").exists() else "error")


def check_symlinks(workspace: Path, repo_path: Path = None):
    """Walk workspace looking for symlinks that point into the repo."""
    print("\nSymlink check:")

    issues = []
    for path in workspace.rglob("*"):
        if path.is_symlink():
            target = path.resolve()
            issue = f"{path.relative_to(workspace)} → {target}"

            if repo_path and str(target).startswith(str(repo_path.resolve())):
                issue += " [POINTS INTO REPO]"

            issues.append(issue)

    if not issues:
        check("No symlinks found", True, "Clean — no symlinks in workspace")
    else:
        for issue in issues:
            points_to_repo = "[POINTS INTO REPO]" in issue
            check(f"Symlink: {issue}", False,
                  msg_fail="Symlink found" + (" — will break if repo is deleted" if points_to_repo else ""),
                  severity="warning")


def check_repo_path_leakage(workspace: Path, repo_path: Path = None):
    """Check config files for hardcoded repo paths."""
    print("\nRepo path leakage:")

    # Patterns that suggest repo dependency
    repo_patterns = [
        "~/evergreen-toolkit/",
        "/evergreen-toolkit/",
        "$TOOLKIT",
    ]
    if repo_path:
        repo_patterns.append(str(repo_path))

    files_to_check = [
        workspace / "AGENTS.md",
        workspace / "MEMORY.md",
        workspace / "HEARTBEAT.md",
    ]

    clean = True
    for fpath in files_to_check:
        if not fpath.exists():
            continue
        content = fpath.read_text()
        for pattern in repo_patterns:
            if pattern in content:
                check(f"{fpath.name}: no repo paths", False,
                      msg_fail=f"Contains '{pattern}'", severity="warning")
                clean = False
                break
        else:
            check(f"{fpath.name}: no repo paths", True, "Clean")

    # Check installed crontab
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            crontab_content = result.stdout
            for pattern in repo_patterns:
                if pattern in crontab_content:
                    check("Installed crontab: no repo paths", False,
                          msg_fail=f"Contains '{pattern}'", severity="warning")
                    clean = False
                    break
            else:
                check("Installed crontab: no repo paths", True, "Clean")
        else:
            check("Installed crontab", True, "No crontab installed (OK)", severity="warning")
    except Exception:
        pass  # crontab command not available

    if clean:
        check("Overall path independence", True, "No repo path leakage detected")


def check_timing_json(workspace: Path):
    """Verify timing.json files are valid JSON."""
    print("\nData integrity:")

    for eg in ["upstream-architecture", "system-health", "prompt-injection", "household-memory"]:
        timing = workspace / "evergreens" / eg / "timing.json"
        if timing.exists():
            try:
                with open(timing) as f:
                    json.load(f)
                check(f"{eg}/timing.json", True, "Valid JSON")
            except json.JSONDecodeError as e:
                check(f"{eg}/timing.json", False, msg_fail=f"Invalid JSON: {e}", severity="warning")
        else:
            check(f"{eg}/timing.json", False, msg_fail="Not found", severity="warning")


def main():
    parser = argparse.ArgumentParser(description="Verify Evergreen Toolkit deployment")
    parser.add_argument("--workspace", type=str, help="Workspace path to verify")
    parser.add_argument("--repo", type=str, help="Repo path (for symlink/path checks)")
    args = parser.parse_args()

    if args.workspace:
        workspace = Path(args.workspace)
    else:
        # Default: derive from script location
        workspace = Path(__file__).parent.parent

    if args.repo:
        repo_path = Path(args.repo)
    else:
        # Check common clone locations
        common = Path.home() / "evergreen-toolkit"
        repo_path = common if common.exists() else None

    print(f"\n{'=' * 55}")
    print("  Evergreen Toolkit — Post-Deploy Verification")
    print(f"{'=' * 55}")
    print(f"  Workspace: {workspace}\n")

    check_structure(workspace)
    check_runtime(workspace)
    check_config(workspace)
    check_symlinks(workspace, repo_path)
    check_repo_path_leakage(workspace, repo_path)
    check_timing_json(workspace)

    # Summary
    total = passed + warned + failed
    print(f"\n{'=' * 55}")
    print(f"  Results: {GREEN}{passed} passed{RESET}, {YELLOW}{warned} warnings{RESET}, {RED}{failed} failed{RESET} ({total} checks)")
    if failed == 0 and warned == 0:
        print(f"  {GREEN}Deployment verified! Workspace is self-contained.{RESET}")
    elif failed == 0:
        print(f"  {YELLOW}Deployment OK with warnings. Review above.{RESET}")
    else:
        print(f"  {RED}Issues found. Fix the errors above.{RESET}")
    print(f"{'=' * 55}\n")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
