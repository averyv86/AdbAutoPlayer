#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13.7.0", "pyyaml>=6.0", "httpx>=0.27.0"]
# ///
"""
MoAI Upstream Sync Tool

Safely merges upstream MoAI-ADK updates while preserving local customizations.
Reads MANIFEST.md to determine which files to protect.

Usage:
    uv run sync-upstream.py --preview     # Dry run, show what would change
    uv run sync-upstream.py --apply       # Apply changes
    uv run sync-upstream.py --check       # Check for new upstream version
    uv run sync-upstream.py --status      # Show sync status

Author: MoAI-ADK Team
Version: 1.0.0
"""

import argparse
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Paths relative to project root
UPSTREAM_TEMPLATES = Path("moai-adk/src/moai_adk/templates")
LOCAL_ROOT = Path(".")
MANIFEST_PATH = Path(".moai/customizations/MANIFEST.md")
CHANGELOG_PATH = Path(".moai/customizations/upstream-changelog.md")
CONFIG_PATH = Path(".moai/config/config.json")

# Files that should NEVER be overwritten (always protected)
PROTECTED_FILES = [
    ".claude/agents/moai/builder-reverse-engineer.md",
    ".claude/agents/moai/builder-workflow.md",
    ".claude/agents/moai/builder-agent.md",
    ".claude/agents/moai/builder-command.md",
    ".claude/agents/moai/builder-skill.md",
    ".claude/commands/moai/99-release.md",
    "CLAUDE.md",
    "CLAUDE.local.md",
    ".moai/config/config.json",
]

# Directories with custom content (protect entire directory)
PROTECTED_DIRS = [
    ".claude/skills/builder-skill-uvscript/",
    ".claude/skills/macos-resource-optimizer/",
    ".moai/customizations/",
    ".moai/scripts/",
]

# Files to always sync (core updates)
ALWAYS_SYNC = [
    ".claude/settings.json",  # Core settings (merge carefully)
]


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_project_root() -> Path:
    """Find project root by looking for CLAUDE.md or .moai directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / "CLAUDE.md").exists() or (current / ".moai").exists():
            return current
        current = current.parent
    return Path.cwd()


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


def get_current_version() -> Optional[str]:
    """Get current MoAI version from config.json."""
    project_root = get_project_root()
    config_file = project_root / CONFIG_PATH

    if config_file.exists():
        try:
            with open(config_file) as f:
                config = json.load(f)
                return config.get("moai", {}).get("version")
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def get_upstream_version() -> Optional[str]:
    """Get upstream MoAI version from templates config."""
    project_root = get_project_root()
    upstream_config = project_root / UPSTREAM_TEMPLATES / ".moai/config/config.json"

    if upstream_config.exists():
        try:
            with open(upstream_config) as f:
                config = json.load(f)
                return config.get("moai", {}).get("version")
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def check_latest_github_release() -> Optional[str]:
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


def get_file_diff(upstream_file: Path, local_file: Path) -> str:
    """Get diff between upstream and local file."""
    if not local_file.exists():
        return "NEW FILE"

    if not upstream_file.exists():
        return "DELETED IN UPSTREAM"

    try:
        result = subprocess.run(
            ["diff", "-u", str(local_file), str(upstream_file)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return "NO CHANGES"
        return result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout
    except Exception:
        return "DIFF ERROR"


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def check_version():
    """Check current vs upstream vs latest versions."""
    console.print(Panel.fit("MoAI Version Check", style="bold blue"))

    current = get_current_version()
    upstream = get_upstream_version()
    latest = check_latest_github_release()

    table = Table(title="Version Status")
    table.add_column("Source", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Status", style="yellow")

    table.add_row("Local Config", current or "Unknown", "Current")
    table.add_row("Local Upstream", upstream or "Unknown", "Templates")
    table.add_row("GitHub Latest", latest or "Unknown", "Available")

    console.print(table)

    if current and latest and current != latest:
        console.print(f"\n[yellow]Update available: {current} -> {latest}[/]")
        console.print("Run: [cyan]cd moai-adk && git pull origin main[/]")


def show_status():
    """Show sync status and protected files."""
    console.print(Panel.fit("MoAI Sync Status", style="bold blue"))

    project_root = get_project_root()

    # Protected files
    table = Table(title="Protected Files (Will NOT be overwritten)")
    table.add_column("File", style="red")
    table.add_column("Exists", style="green")

    for pf in PROTECTED_FILES:
        exists = (project_root / pf).exists()
        table.add_row(pf, "Yes" if exists else "No")

    console.print(table)

    # Protected directories
    table2 = Table(title="Protected Directories")
    table2.add_column("Directory", style="red")
    table2.add_column("Exists", style="green")

    for pd in PROTECTED_DIRS:
        exists = (project_root / pd).exists()
        table2.add_row(pd, "Yes" if exists else "No")

    console.print(table2)


def preview_sync():
    """Preview what would be synced (dry run)."""
    console.print(Panel.fit("MoAI Sync Preview (Dry Run)", style="bold yellow"))

    project_root = get_project_root()
    upstream_root = project_root / UPSTREAM_TEMPLATES

    if not upstream_root.exists():
        console.print(f"[red]Error: Upstream templates not found at {upstream_root}[/]")
        return

    changes = {"new": [], "update": [], "skip": [], "protected": []}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning files...", total=None)

        for upstream_file in upstream_root.rglob("*"):
            if upstream_file.is_dir():
                continue

            relative_path = str(upstream_file.relative_to(upstream_root))
            local_file = project_root / relative_path

            if is_protected(relative_path):
                changes["protected"].append(relative_path)
            elif not local_file.exists():
                changes["new"].append(relative_path)
            elif upstream_file.read_bytes() != local_file.read_bytes():
                changes["update"].append(relative_path)
            else:
                changes["skip"].append(relative_path)

    # Display results
    if changes["new"]:
        console.print(f"\n[green]New files to add ({len(changes['new'])}):[/]")
        for f in changes["new"][:10]:
            console.print(f"  + {f}")
        if len(changes["new"]) > 10:
            console.print(f"  ... and {len(changes['new']) - 10} more")

    if changes["update"]:
        console.print(f"\n[yellow]Files to update ({len(changes['update'])}):[/]")
        for f in changes["update"][:10]:
            console.print(f"  ~ {f}")
        if len(changes["update"]) > 10:
            console.print(f"  ... and {len(changes['update']) - 10} more")

    if changes["protected"]:
        console.print(f"\n[red]Protected files (skipped) ({len(changes['protected'])}):[/]")
        for f in changes["protected"][:10]:
            console.print(f"  # {f}")
        if len(changes["protected"]) > 10:
            console.print(f"  ... and {len(changes['protected']) - 10} more")

    console.print(f"\n[dim]Unchanged: {len(changes['skip'])} files[/]")

    return changes


def apply_sync():
    """Apply sync from upstream (actual sync)."""
    console.print(Panel.fit("MoAI Sync Apply", style="bold green"))

    # First preview
    changes = preview_sync()
    if not changes:
        return

    total_changes = len(changes["new"]) + len(changes["update"])
    if total_changes == 0:
        console.print("\n[green]Already up to date![/]")
        return

    # Confirm
    console.print(f"\n[yellow]About to sync {total_changes} files.[/]")
    confirm = console.input("[bold]Proceed? (y/N): [/]")

    if confirm.lower() != "y":
        console.print("[red]Aborted.[/]")
        return

    project_root = get_project_root()
    upstream_root = project_root / UPSTREAM_TEMPLATES

    synced = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Syncing files...", total=total_changes)

        for relative_path in changes["new"] + changes["update"]:
            upstream_file = upstream_root / relative_path
            local_file = project_root / relative_path

            # Create parent directories if needed
            local_file.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(upstream_file, local_file)
            synced.append(relative_path)

            progress.advance(task)

    # Update changelog
    update_changelog(synced)

    console.print(f"\n[green]Synced {len(synced)} files successfully![/]")
    console.print("\n[yellow]Next steps:[/]")
    console.print("  1. Review changes: [cyan]git diff[/]")
    console.print("  2. Test the changes")
    console.print("  3. Commit: [cyan]git add -A && git commit -m 'chore: sync upstream MoAI'[/]")


def update_changelog(synced_files: list):
    """Update the upstream changelog."""
    project_root = get_project_root()
    changelog_file = project_root / CHANGELOG_PATH

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    upstream_version = get_upstream_version() or "unknown"

    entry = f"""
## Sync {now}

**Upstream Version**: {upstream_version}
**Files Synced**: {len(synced_files)}

### Changed Files
"""
    for f in synced_files[:20]:
        entry += f"- `{f}`\n"

    if len(synced_files) > 20:
        entry += f"- ... and {len(synced_files) - 20} more\n"

    entry += "\n---\n"

    # Prepend to changelog
    existing = ""
    if changelog_file.exists():
        existing = changelog_file.read_text()

    header = "# MoAI Upstream Changelog\n\n> Auto-generated by sync-upstream.py\n\n---\n"
    if not existing.startswith("# MoAI"):
        existing = header + existing

    # Insert after header
    parts = existing.split("---\n", 1)
    if len(parts) == 2:
        new_content = parts[0] + "---\n" + entry + parts[1]
    else:
        new_content = existing + entry

    changelog_file.parent.mkdir(parents=True, exist_ok=True)
    changelog_file.write_text(new_content)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="MoAI Upstream Sync Tool - Safely sync MoAI-ADK updates"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Check for new upstream version"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Show sync status and protected files"
    )
    parser.add_argument(
        "--preview", action="store_true",
        help="Preview what would be synced (dry run)"
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Apply sync from upstream"
    )

    args = parser.parse_args()

    console.print("[bold blue]MoAI Upstream Sync Tool v1.0.0[/]\n")

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
        console.print("  uv run sync-upstream.py --check    # Check versions")
        console.print("  uv run sync-upstream.py --preview  # Dry run")
        console.print("  uv run sync-upstream.py --apply    # Apply sync")


if __name__ == "__main__":
    main()
