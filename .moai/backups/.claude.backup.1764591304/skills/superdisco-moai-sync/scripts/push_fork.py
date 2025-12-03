#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13.7.0"]
# ///
"""
Superdisco MoAI Fork Push Tool

Stage, commit, and push changes to fork (origin).

Usage:
    uv run push_fork.py --message "feat: description"
    uv run push_fork.py --status    # Just show git status
    uv run push_fork.py --dry-run   # Show what would be committed

Author: Superdisco Agents
Version: 1.0.0
"""

import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List

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


def get_status() -> dict:
    """Get git status."""
    result = run_git(["status", "--porcelain"], check=False)

    status = {
        "modified": [],
        "new": [],
        "deleted": [],
        "untracked": []
    }

    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        code = line[:2]
        file_path = line[3:]

        if "M" in code:
            status["modified"].append(file_path)
        elif "A" in code:
            status["new"].append(file_path)
        elif "D" in code:
            status["deleted"].append(file_path)
        elif "??" in code:
            status["untracked"].append(file_path)

    return status


def show_status():
    """Display git status."""
    status = get_status()

    table = Table(title="Git Status (moai-adk)")
    table.add_column("Status", style="cyan")
    table.add_column("Files", style="green")
    table.add_column("Count", style="yellow")

    if status["modified"]:
        files = "\n".join(status["modified"][:10])
        if len(status["modified"]) > 10:
            files += f"\n... and {len(status['modified']) - 10} more"
        table.add_row("Modified", files, str(len(status["modified"])))

    if status["new"]:
        files = "\n".join(status["new"][:10])
        table.add_row("New", files, str(len(status["new"])))

    if status["deleted"]:
        files = "\n".join(status["deleted"][:10])
        table.add_row("Deleted", files, str(len(status["deleted"])))

    if status["untracked"]:
        files = "\n".join(status["untracked"][:10])
        table.add_row("Untracked", files, str(len(status["untracked"])))

    if not any(status.values()):
        console.print("[green]Working tree clean - nothing to commit[/]")
        return False

    console.print(table)
    return True


def dry_run():
    """Show what would be committed."""
    console.print(Panel.fit("[bold yellow]Dry Run - What would be committed[/]"))

    status = get_status()
    if not any(status.values()):
        console.print("[green]Nothing to commit[/]")
        return

    console.print("\n[bold]Files to be staged:[/]")

    all_files = (
        status["modified"] +
        status["new"] +
        status["deleted"] +
        status["untracked"]
    )

    for f in all_files[:20]:
        console.print(f"  + {f}")

    if len(all_files) > 20:
        console.print(f"  ... and {len(all_files) - 20} more")


def commit_and_push(message: str):
    """Stage, commit, and push changes."""
    console.print(Panel.fit("[bold green]Committing and Pushing[/]"))

    # Check if there are changes
    status = get_status()
    if not any(status.values()):
        console.print("[green]Nothing to commit[/]")
        return

    # Stage all
    console.print("[cyan]Staging changes...[/]")
    run_git(["add", "-A"])

    # Commit
    console.print(f"[cyan]Committing with message: {message}[/]")

    # Use superdisco prefix if not already present
    if not message.startswith("superdisco:") and not message.startswith("feat:") and not message.startswith("fix:") and not message.startswith("chore:"):
        message = f"feat: superdisco - {message}"

    result = run_git(["commit", "-m", message], check=False)

    if result.returncode != 0:
        if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
            console.print("[green]Nothing to commit[/]")
            return
        console.print(f"[red]Commit failed: {result.stderr}[/]")
        return

    console.print(result.stdout)

    # Push
    console.print("[cyan]Pushing to origin...[/]")
    result = run_git(["push", "origin", "main"], check=False)

    if result.returncode != 0:
        console.print(f"[yellow]Push output: {result.stderr}[/]")

        # Try force push if diverged
        if "diverged" in result.stderr or "rejected" in result.stderr:
            console.print("[yellow]Branch diverged. Force push? (y/N)[/]")
            confirm = console.input()
            if confirm.lower() == "y":
                run_git(["push", "origin", "main", "--force"])
                console.print("[green]Force pushed successfully![/]")
            else:
                console.print("[red]Push cancelled[/]")
                return
    else:
        console.print("[green]Pushed successfully![/]")

    console.print("\n[bold]Summary:[/]")
    console.print(f"  - Committed: {sum(len(v) for v in status.values())} files")
    console.print(f"  - Message: {message}")
    console.print(f"  - Remote: origin (superdisco-agents/moai-adk)")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Superdisco MoAI Fork Push Tool"
    )
    parser.add_argument(
        "--message", "-m",
        help="Commit message"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Just show git status"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be committed"
    )

    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold blue]Superdisco MoAI Fork Push[/]",
        subtitle="v1.0.0"
    ))

    if args.status:
        show_status()
    elif args.dry_run:
        dry_run()
    elif args.message:
        commit_and_push(args.message)
    else:
        # Interactive mode
        has_changes = show_status()

        if has_changes:
            console.print("\n")
            message = console.input("[bold]Enter commit message (or 'q' to quit): [/]")

            if message.lower() != "q":
                commit_and_push(message)


if __name__ == "__main__":
    main()
