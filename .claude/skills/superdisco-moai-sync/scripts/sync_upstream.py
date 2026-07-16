#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13.7.0", "httpx>=0.27.0"]
# ///
"""
Superdisco MoAI Upstream Sync Tool

Safely merges upstream MoAI-ADK updates while preserving local customizations.

Usage:
    uv run sync_upstream.py --check     # Check for new upstream version
    uv run sync_upstream.py --status    # Show sync status
    uv run sync_upstream.py --preview   # Dry run, show what would change
    uv run sync_upstream.py --apply     # Apply changes

Author: Superdisco Agents
Version: 1.0.0
"""

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

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
CONFIG_PATH = PROJECT_ROOT / ".moai/config/config.json"
CHANGELOG_PATH = PROJECT_ROOT / ".moai/customizations/upstream-changelog.md"

# Protected files - always keep ours during merge
PROTECTED_FILES = [
    "src/moai_adk/templates/.claude/agents/moai/builder-workflow-designer.md",
    "src/moai_adk/templates/.claude/agents/moai/builder-reverse-engineer.md",
    "src/moai_adk/templates/.claude/agents/moai/builder-workflow.md",
    "src/moai_adk/templates/.claude/agents/moai/builder-agent.md",
    "src/moai_adk/templates/.claude/agents/moai/builder-command.md",
    "src/moai_adk/templates/.claude/agents/moai/builder-skill.md",
    "src/moai_adk/templates/.claude/skills/moai-library-toon/SKILL.md",
    "CHANGELOG.md",
]

PROTECTED_PATTERNS = [
    "src/moai_adk/templates/.claude/agents/moai/builder-*.md",
    "src/moai_adk/templates/.claude/agents/moai/expert-*.md",
]


# ═══════════════════════════════════════════════════════════════════════════════
# GIT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def run_git(args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run git command in moai-adk directory."""
    return subprocess.run(
        ["git"] + args,
        cwd=MOAI_ADK_DIR,
        capture_output=True,
        text=True,
        check=check
    )


def check_remotes() -> dict:
    """Check git remotes configuration."""
    result = run_git(["remote", "-v"], check=False)
    remotes = {}

    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            name = parts[0]
            url = parts[1]
            remotes[name] = url

    return remotes


def has_upstream() -> bool:
    """Check if upstream remote is configured."""
    remotes = check_remotes()
    return "upstream" in remotes


def add_upstream():
    """Add upstream remote."""
    run_git(["remote", "add", "upstream", "https://github.com/modu-ai/moai-adk.git"])
    console.print("[green]Added upstream remote[/]")


def fetch_upstream():
    """Fetch from upstream."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching upstream...", total=None)
        run_git(["fetch", "upstream"])
        progress.update(task, completed=True)


def get_commits_behind() -> List[str]:
    """Get commits behind upstream."""
    result = run_git(["log", "HEAD..upstream/main", "--oneline"], check=False)
    return [line for line in result.stdout.strip().split("\n") if line]


def get_commits_ahead() -> List[str]:
    """Get commits ahead of upstream."""
    result = run_git(["log", "upstream/main..HEAD", "--oneline"], check=False)
    return [line for line in result.stdout.strip().split("\n") if line]


# ═══════════════════════════════════════════════════════════════════════════════
# VERSION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_local_version() -> Optional[str]:
    """Get current MoAI version from config.json."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                config = json.load(f)
                return config.get("moai", {}).get("version")
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def get_latest_github_release() -> Optional[str]:
    """Check latest MoAI-ADK release from GitHub."""
    try:
        import httpx
        response = httpx.get(
            "https://api.github.com/repos/modu-ai/moai-adk/releases/latest",
            timeout=10.0
        )
        if response.status_code == 200:
            return response.json().get("tag_name", "").lstrip("v")
    except Exception:
        pass
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# SYNC FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def show_status():
    """Show sync status."""
    console.print(Panel.fit("[bold]Sync Status[/]"))

    # Check remotes
    remotes = check_remotes()
    table = Table(title="Git Remotes")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="green")

    for name, url in remotes.items():
        table.add_row(name, url)

    console.print(table)

    if not has_upstream():
        console.print("\n[yellow]Warning: upstream remote not configured[/]")
        console.print("Run: [cyan]git remote add upstream https://github.com/modu-ai/moai-adk.git[/]")
        return

    # Fetch and check commits
    fetch_upstream()

    ahead = get_commits_ahead()
    behind = get_commits_behind()

    console.print(f"\n[cyan]Commits ahead of upstream:[/] {len(ahead)}")
    for commit in ahead[:5]:
        console.print(f"  + {commit}")

    console.print(f"\n[yellow]Commits behind upstream:[/] {len(behind)}")
    for commit in behind[:5]:
        console.print(f"  - {commit}")


def preview_sync():
    """Preview what would be synced."""
    console.print(Panel.fit("[bold yellow]Sync Preview (Dry Run)[/]"))

    if not has_upstream():
        console.print("[red]Error: upstream remote not configured[/]")
        return

    fetch_upstream()

    # Get diff stat
    result = run_git(["diff", "--stat", "HEAD..upstream/main"], check=False)

    if not result.stdout.strip():
        console.print("[green]Already up to date![/]")
        return

    console.print("\n[bold]Files that would change:[/]")
    console.print(result.stdout)

    # Show protected files
    console.print("\n[bold red]Protected files (will be preserved):[/]")
    for f in PROTECTED_FILES[:10]:
        console.print(f"  # {f}")


def apply_sync():
    """Apply sync from upstream."""
    console.print(Panel.fit("[bold green]Applying Sync[/]"))

    if not has_upstream():
        add_upstream()

    fetch_upstream()

    behind = get_commits_behind()
    if not behind:
        console.print("[green]Already up to date![/]")
        return

    console.print(f"[yellow]About to sync {len(behind)} commits from upstream[/]")
    confirm = console.input("[bold]Proceed? (y/N): [/]")

    if confirm.lower() != "y":
        console.print("[red]Aborted.[/]")
        return

    # Create sync branch
    version = get_latest_github_release() or "latest"
    branch_name = f"sync/v{version}"

    run_git(["checkout", "-b", branch_name], check=False)

    # Merge upstream
    result = run_git(["merge", "upstream/main", "--no-commit"], check=False)

    if result.returncode != 0:
        console.print("\n[yellow]Merge conflicts detected. Resolving protected files...[/]")

        # Resolve protected files
        for f in PROTECTED_FILES:
            run_git(["checkout", "--ours", f], check=False)

        # Also resolve by pattern
        for pattern in PROTECTED_PATTERNS:
            run_git(["checkout", "--ours", pattern], check=False)

    # Stage all
    run_git(["add", "-A"])

    # Commit
    run_git(["commit", "-m", f"chore: sync upstream MoAI v{version} (preserve superdisco customizations)"])

    # Merge to main
    run_git(["checkout", "main"])
    run_git(["merge", branch_name])

    console.print(f"\n[green]Synced to v{version} successfully![/]")
    console.print("\nNext steps:")
    console.print("  1. Review changes: [cyan]git diff HEAD~1[/]")
    console.print("  2. Test the changes")
    console.print("  3. Push to fork: [cyan]git push origin main[/]")


def check_version():
    """Check current vs latest version."""
    console.print(Panel.fit("[bold]Version Check[/]"))

    local = get_local_version()
    latest = get_latest_github_release()

    table = Table(title="Version Status")
    table.add_column("Source", style="cyan")
    table.add_column("Version", style="green")

    table.add_row("Local Config", local or "Unknown")
    table.add_row("GitHub Latest", latest or "Unknown")

    console.print(table)

    if local and latest and local != latest:
        console.print(f"\n[yellow]Update available: {local} -> {latest}[/]")
        console.print("Run: [cyan]uv run sync_upstream.py --apply[/]")
    elif local == latest:
        console.print("\n[green]Already up to date![/]")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Superdisco MoAI Upstream Sync Tool"
    )
    parser.add_argument("--check", action="store_true", help="Check for new version")
    parser.add_argument("--status", action="store_true", help="Show sync status")
    parser.add_argument("--preview", action="store_true", help="Preview sync (dry run)")
    parser.add_argument("--apply", action="store_true", help="Apply sync")

    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold blue]Superdisco MoAI Upstream Sync[/]",
        subtitle="v1.0.0"
    ))

    if args.check:
        check_version()
    elif args.status:
        show_status()
    elif args.preview:
        preview_sync()
    elif args.apply:
        apply_sync()
    else:
        parser.print_help()
        console.print("\n[yellow]Example usage:[/]")
        console.print("  uv run sync_upstream.py --check    # Check versions")
        console.print("  uv run sync_upstream.py --status   # Show sync status")
        console.print("  uv run sync_upstream.py --preview  # Dry run")
        console.print("  uv run sync_upstream.py --apply    # Apply sync")


if __name__ == "__main__":
    main()
