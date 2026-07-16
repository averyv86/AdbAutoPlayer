#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13.7.0"]
# ///
"""
Superdisco MoAI Change Tracker

Auto-detect modified files vs upstream.
Generate MANIFEST of customizations.
Update protected files list.

Usage:
    uv run track_changes.py           # Show all customizations
    uv run track_changes.py --update  # Update MANIFEST.md

Author: Superdisco Agents
Version: 1.0.0
"""

import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

def get_project_root() -> Path:
    """Find project root by looking for CLAUDE.md or .moai directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / "CLAUDE.md").exists() or (current / ".moai").exists():
            return current
        current = current.parent
    return Path.cwd()


PROJECT_ROOT = get_project_root()
MOAI_ADK_DIR = PROJECT_ROOT / "moai-adk"
MANIFEST_PATH = PROJECT_ROOT / ".moai/customizations/MANIFEST.md"

# Protected files - never overwrite during sync
PROTECTED_FILES = [
    "src/moai_adk/templates/.claude/agents/moai/builder-workflow-designer.md",
    "src/moai_adk/templates/.claude/agents/moai/builder-reverse-engineer.md",
    "src/moai_adk/templates/.claude/agents/moai/builder-workflow.md",
    "src/moai_adk/templates/.claude/agents/moai/builder-agent.md",
    "src/moai_adk/templates/.claude/agents/moai/builder-command.md",
    "src/moai_adk/templates/.claude/agents/moai/builder-skill.md",
    "src/moai_adk/templates/.claude/skills/moai-library-toon/SKILL.md",
]

# Protected directories
PROTECTED_DIRS = [
    ".claude/skills/superdisco-moai-sync/",
    ".moai/customizations/",
    ".moai/scripts/",
]


# ═══════════════════════════════════════════════════════════════════════════════
# DETECTION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_git_status() -> Dict[str, List[str]]:
    """Get git status showing changes."""
    result = {
        "modified": [],
        "new": [],
        "deleted": [],
        "untracked": []
    }

    try:
        # Get status from moai-adk directory
        output = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=MOAI_ADK_DIR,
            capture_output=True,
            text=True
        )

        for line in output.stdout.strip().split("\n"):
            if not line:
                continue
            status = line[:2].strip()
            file_path = line[3:]

            if status == "M":
                result["modified"].append(file_path)
            elif status == "A":
                result["new"].append(file_path)
            elif status == "D":
                result["deleted"].append(file_path)
            elif status == "??":
                result["untracked"].append(file_path)

    except Exception as e:
        console.print(f"[red]Error getting git status: {e}[/]")

    return result


def get_commits_ahead_of_upstream() -> List[str]:
    """Get commits that are ahead of upstream."""
    try:
        output = subprocess.run(
            ["git", "log", "upstream/main..HEAD", "--oneline"],
            cwd=MOAI_ADK_DIR,
            capture_output=True,
            text=True
        )
        return [line for line in output.stdout.strip().split("\n") if line]
    except Exception:
        return []


def is_protected(file_path: str) -> bool:
    """Check if a file is protected from overwriting."""
    # Check exact file matches
    if file_path in PROTECTED_FILES:
        return True

    # Check directory matches
    for protected_dir in PROTECTED_DIRS:
        if file_path.startswith(protected_dir):
            return True

    return False


def detect_custom_files() -> Dict[str, List[str]]:
    """Detect custom and modified files."""
    result = {
        "custom_agents": [],
        "modified_agents": [],
        "custom_skills": [],
        "local_only": []
    }

    # Custom agents (new files)
    agents_dir = MOAI_ADK_DIR / "src/moai_adk/templates/.claude/agents/moai"
    if agents_dir.exists():
        custom = ["builder-workflow-designer.md", "builder-reverse-engineer.md"]
        for agent in custom:
            if (agents_dir / agent).exists():
                result["custom_agents"].append(agent)

        modified = ["builder-agent.md", "builder-command.md", "builder-skill.md", "builder-workflow.md"]
        for agent in modified:
            if (agents_dir / agent).exists():
                result["modified_agents"].append(agent)

    # Custom skills
    skills_dir = MOAI_ADK_DIR / "src/moai_adk/templates/.claude/skills"
    if skills_dir.exists():
        toon = skills_dir / "moai-library-toon"
        if toon.exists():
            result["custom_skills"].append("moai-library-toon")

    # Local-only files
    local_files = [
        PROJECT_ROOT / "CLAUDE.local.md",
        PROJECT_ROOT / ".moai/config/config.json",
        PROJECT_ROOT / ".claude/commands/moai/99-release.md"
    ]
    for f in local_files:
        if f.exists():
            result["local_only"].append(str(f.relative_to(PROJECT_ROOT)))

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# MANIFEST UPDATE
# ═══════════════════════════════════════════════════════════════════════════════

def update_manifest(custom: Dict[str, List[str]]):
    """Update the MANIFEST.md file."""
    now = datetime.now().strftime("%Y-%m-%d")

    content = f"""# MoAI Customizations Manifest

> **Purpose**: Track all customizations to prevent upstream updates from overwriting them
> **Last Updated**: {now}
> **Prefix**: superdisco-

---

## Custom Agents (NEW - DO NOT OVERWRITE)

These agents were created specifically for this workspace:

"""
    for agent in custom.get("custom_agents", []):
        content += f"- `.claude/agents/moai/{agent}`\n"

    content += """
---

## Modified Agents (TOON v4.0 - DO NOT OVERWRITE)

These agents were modified with TOON v4.0 integration:

"""
    for agent in custom.get("modified_agents", []):
        content += f"- `.claude/agents/moai/{agent}`\n"

    content += """
---

## Custom Skills (DO NOT OVERWRITE)

"""
    for skill in custom.get("custom_skills", []):
        content += f"- `.claude/skills/{skill}/`\n"

    content += "- `.claude/skills/superdisco-moai-sync/` (this skill)\n"

    content += """
---

## Local-Only Files (NEVER SYNC)

"""
    for f in custom.get("local_only", []):
        content += f"- `{f}`\n"

    content += """
---

## Protected File Patterns

Files matching these patterns are NEVER overwritten during upstream sync:

```
src/moai_adk/templates/.claude/agents/moai/builder-*.md
src/moai_adk/templates/.claude/agents/moai/expert-*.md
src/moai_adk/templates/.claude/skills/moai-library-toon/
.claude/skills/superdisco-*/
.moai/customizations/
.moai/scripts/
CLAUDE.local.md
```

---

## Sync Workflow

```bash
# 1. Check status
uv run .claude/skills/superdisco-moai-sync/scripts/check_version.py

# 2. Track changes
uv run .claude/skills/superdisco-moai-sync/scripts/track_changes.py --update

# 3. Sync upstream
uv run .claude/skills/superdisco-moai-sync/scripts/sync_upstream.py --preview
uv run .claude/skills/superdisco-moai-sync/scripts/sync_upstream.py --apply

# 4. Push to fork
uv run .claude/skills/superdisco-moai-sync/scripts/push_fork.py --message "feat: description"
```
"""

    # Write manifest
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(content)
    console.print(f"[green]MANIFEST.md updated at {MANIFEST_PATH}[/]")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Superdisco MoAI Change Tracker"
    )
    parser.add_argument(
        "--update", action="store_true",
        help="Update MANIFEST.md"
    )
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold blue]Superdisco MoAI Change Tracker[/]",
        subtitle="v1.0.0"
    ))

    # Detect customizations
    custom = detect_custom_files()

    # Display table
    table = Table(title="Detected Customizations")
    table.add_column("Category", style="cyan")
    table.add_column("Files", style="green")
    table.add_column("Count", style="yellow")

    if custom["custom_agents"]:
        table.add_row("Custom Agents (NEW)", ", ".join(custom["custom_agents"]), str(len(custom["custom_agents"])))
    if custom["modified_agents"]:
        table.add_row("Modified Agents", ", ".join(custom["modified_agents"]), str(len(custom["modified_agents"])))
    if custom["custom_skills"]:
        table.add_row("Custom Skills", ", ".join(custom["custom_skills"]), str(len(custom["custom_skills"])))
    if custom["local_only"]:
        table.add_row("Local-Only", ", ".join(custom["local_only"]), str(len(custom["local_only"])))

    console.print(table)

    # Git status
    status = get_git_status()
    if any(status.values()):
        console.print("\n")
        table2 = Table(title="Git Status (moai-adk)")
        table2.add_column("Status", style="cyan")
        table2.add_column("Files", style="green")

        if status["modified"]:
            table2.add_row("Modified", "\n".join(status["modified"][:5]))
        if status["new"]:
            table2.add_row("New", "\n".join(status["new"][:5]))
        if status["deleted"]:
            table2.add_row("Deleted", "\n".join(status["deleted"][:5]))
        if status["untracked"]:
            table2.add_row("Untracked", "\n".join(status["untracked"][:5]))

        console.print(table2)

    # Commits ahead
    commits = get_commits_ahead_of_upstream()
    if commits:
        console.print(f"\n[yellow]Commits ahead of upstream: {len(commits)}[/]")
        for commit in commits[:5]:
            console.print(f"  - {commit}")

    # Update manifest
    if args.update:
        console.print("\n")
        update_manifest(custom)


if __name__ == "__main__":
    main()
