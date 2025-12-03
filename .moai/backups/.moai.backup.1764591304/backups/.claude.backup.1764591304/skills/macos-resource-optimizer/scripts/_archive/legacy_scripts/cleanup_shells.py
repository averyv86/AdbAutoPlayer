#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click>=8.1.0",
#     "rich>=13.0.0",
#     "psutil>=6.1.0"
# ]
# ///

"""
Shell Cleanup Utility - Batch shell management and cleanup

Commands:
  cleanup  - Remove all stale/completed shells from registry
  purge    - Force remove all shells (with confirmation)
  status   - Show summary of shell states
  validate - Check all registered shells and update their status

Features:
  - Rich console output with tables showing shell status
  - Dry-run mode (--dry-run flag)
  - Age-based filtering (--max-age-seconds)
  - Category filtering (--category coordinator|agent|hive_mind|background)
  - JSON output option (--json)
  - Verbose mode (--verbose)
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import click
import psutil
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()


# ============================================================================
# Shell State Tracker (Self-contained implementation)
# ============================================================================

class ShellState(Enum):
    """Shell lifecycle states"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STALE = "stale"
    ORPHANED = "orphaned"


@dataclass
class ShellInfo:
    """Information about a tracked shell"""
    shell_id: str
    pid: int
    category: str
    command: str
    created_at: float
    updated_at: float
    state: str
    exit_code: Optional[int] = None
    error_message: Optional[str] = None


class ShellStateTracker:
    """Tracks shell states and manages registry persistence"""

    def __init__(self, config_path: Optional[Path] = None, registry_path: Optional[Path] = None):
        self.base_dir = Path(__file__).parent.parent
        self.config_path = config_path or self.base_dir / "config" / "shell-config.json"
        self.config = self._load_config()
        self.registry_path = registry_path or self.base_dir / self.config["shell_tracking"]["persistence_file"]
        self.registry: Dict[str, ShellInfo] = {}
        self._load_registry()

    def _load_config(self) -> Dict:
        """Load shell configuration"""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return self._default_config()

    def _default_config(self) -> Dict:
        """Default configuration if file not found"""
        return {
            "shell_tracking": {
                "enabled": True,
                "persistence_file": "data/shell-registry.json",
                "max_shell_age_seconds": 300,
                "cleanup_interval_seconds": 60
            },
            "shell_categories": {
                "coordinator": {"timeout_seconds": 120},
                "agent": {"timeout_seconds": 60},
                "hive_mind": {"timeout_seconds": 300},
                "background": {"timeout_seconds": 600}
            },
            "cleanup_policy": {
                "completed_retention_seconds": 60,
                "failed_retention_seconds": 300
            }
        }

    def _load_registry(self) -> None:
        """Load shell registry from disk"""
        try:
            if self.registry_path.exists():
                with open(self.registry_path) as f:
                    data = json.load(f)
                    for shell_id, info in data.items():
                        self.registry[shell_id] = ShellInfo(**info)
        except (json.JSONDecodeError, TypeError):
            self.registry = {}

    def _save_registry(self) -> None:
        """Persist registry to disk"""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w') as f:
            data = {k: asdict(v) for k, v in self.registry.items()}
            json.dump(data, f, indent=2)

    def get_all_shells(self) -> List[ShellInfo]:
        """Get all tracked shells"""
        return list(self.registry.values())

    def get_shells_by_category(self, category: str) -> List[ShellInfo]:
        """Filter shells by category"""
        return [s for s in self.registry.values() if s.category == category]

    def get_shells_by_state(self, state: ShellState) -> List[ShellInfo]:
        """Filter shells by state"""
        return [s for s in self.registry.values() if s.state == state.value]

    def validate_shell(self, shell: ShellInfo) -> ShellState:
        """Validate shell state against actual process status"""
        try:
            proc = psutil.Process(shell.pid)
            if proc.status() == psutil.STATUS_ZOMBIE:
                return ShellState.STALE
            return ShellState.RUNNING
        except psutil.NoSuchProcess:
            age = time.time() - shell.updated_at
            if shell.state == ShellState.COMPLETED.value:
                return ShellState.COMPLETED
            if shell.state == ShellState.FAILED.value:
                return ShellState.FAILED
            return ShellState.ORPHANED

    def update_shell_state(self, shell_id: str, state: ShellState) -> None:
        """Update shell state"""
        if shell_id in self.registry:
            self.registry[shell_id].state = state.value
            self.registry[shell_id].updated_at = time.time()

    def remove_shell(self, shell_id: str) -> bool:
        """Remove shell from registry"""
        if shell_id in self.registry:
            del self.registry[shell_id]
            return True
        return False

    def is_stale(self, shell: ShellInfo, max_age: Optional[int] = None) -> bool:
        """Check if shell is stale based on age"""
        max_age = max_age or self.config["shell_tracking"]["max_shell_age_seconds"]
        age = time.time() - shell.created_at
        return age > max_age

    def save(self) -> None:
        """Save registry to disk"""
        self._save_registry()


# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging for shell operations"""
    base_dir = Path(__file__).parent.parent
    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "shell-operations.log"

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler() if verbose else logging.NullHandler()
        ]
    )
    return logging.getLogger(__name__)


# ============================================================================
# CLI Commands
# ============================================================================

@click.group()
@click.option('--verbose', is_flag=True, help='Show detailed output')
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
@click.pass_context
def cli(ctx, verbose: bool, json_output: bool):
    """Shell Cleanup Utility - Manage and cleanup shell processes"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['json_output'] = json_output
    ctx.obj['logger'] = setup_logging(verbose)
    ctx.obj['tracker'] = ShellStateTracker()


@cli.command()
@click.option('--dry-run', is_flag=True, help='Show what would be cleaned without doing it')
@click.option('--max-age-seconds', type=int, default=None, help='Max shell age before cleanup')
@click.option('--category', type=click.Choice(['coordinator', 'agent', 'hive_mind', 'background']),
              help='Filter by category')
@click.pass_context
def cleanup(ctx, dry_run: bool, max_age_seconds: Optional[int], category: Optional[str]):
    """Remove stale/completed shells from registry"""
    tracker: ShellStateTracker = ctx.obj['tracker']
    logger = ctx.obj['logger']
    json_output = ctx.obj['json_output']

    shells = tracker.get_all_shells()
    if category:
        shells = [s for s in shells if s.category == category]

    to_remove = []
    for shell in shells:
        actual_state = tracker.validate_shell(shell)
        is_stale = tracker.is_stale(shell, max_age_seconds)

        if actual_state in [ShellState.COMPLETED, ShellState.ORPHANED, ShellState.STALE] or is_stale:
            to_remove.append(shell)
            tracker.update_shell_state(shell.shell_id, actual_state)

    if json_output:
        result = {
            "action": "cleanup",
            "dry_run": dry_run,
            "shells_to_remove": len(to_remove),
            "shells": [asdict(s) for s in to_remove]
        }
        print(json.dumps(result, indent=2))
        return

    # Display summary before cleanup
    _display_cleanup_summary(to_remove, "Shells to Clean Up", dry_run)

    if not to_remove:
        console.print("[green]No shells require cleanup[/green]")
        return

    if dry_run:
        console.print(f"\n[yellow]DRY RUN: Would remove {len(to_remove)} shells[/yellow]")
        logger.info(f"DRY RUN: Would remove {len(to_remove)} shells")
        return

    # Perform cleanup
    removed = 0
    for shell in to_remove:
        if tracker.remove_shell(shell.shell_id):
            removed += 1
            logger.info(f"Removed shell {shell.shell_id} (PID: {shell.pid})")

    tracker.save()
    console.print(f"\n[green]Removed {removed} shells from registry[/green]")
    logger.info(f"Cleanup complete: removed {removed} shells")


@cli.command()
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def purge(ctx, force: bool):
    """Force remove ALL shells from registry (requires confirmation)"""
    tracker: ShellStateTracker = ctx.obj['tracker']
    logger = ctx.obj['logger']
    json_output = ctx.obj['json_output']

    shells = tracker.get_all_shells()

    if json_output:
        result = {
            "action": "purge",
            "force": force,
            "shells_count": len(shells),
            "shells": [asdict(s) for s in shells]
        }
        print(json.dumps(result, indent=2))
        return

    if not shells:
        console.print("[green]Registry is empty - nothing to purge[/green]")
        return

    _display_cleanup_summary(shells, "All Shells (PURGE)", dry_run=False)

    if not force:
        console.print("\n[bold red]WARNING: This will remove ALL shells from the registry![/bold red]")
        if not Confirm.ask("Are you sure you want to purge all shells?"):
            console.print("[yellow]Purge cancelled[/yellow]")
            return

    # Clear registry
    count = len(shells)
    tracker.registry.clear()
    tracker.save()

    console.print(f"\n[green]Purged {count} shells from registry[/green]")
    logger.warning(f"PURGE: Removed all {count} shells from registry")


@cli.command()
@click.option('--category', type=click.Choice(['coordinator', 'agent', 'hive_mind', 'background']),
              help='Filter by category')
@click.pass_context
def status(ctx, category: Optional[str]):
    """Show summary of shell states"""
    tracker: ShellStateTracker = ctx.obj['tracker']
    json_output = ctx.obj['json_output']

    shells = tracker.get_all_shells()
    if category:
        shells = [s for s in shells if s.category == category]

    # Calculate statistics
    stats = {
        "total": len(shells),
        "by_state": {},
        "by_category": {},
        "stale_count": 0
    }

    for shell in shells:
        actual_state = tracker.validate_shell(shell)
        state_name = actual_state.value
        stats["by_state"][state_name] = stats["by_state"].get(state_name, 0) + 1
        stats["by_category"][shell.category] = stats["by_category"].get(shell.category, 0) + 1
        if tracker.is_stale(shell):
            stats["stale_count"] += 1

    if json_output:
        result = {
            "action": "status",
            "statistics": stats,
            "shells": [asdict(s) for s in shells]
        }
        print(json.dumps(result, indent=2))
        return

    # Display status panel
    console.print(Panel.fit(
        "[bold cyan]Shell Registry Status[/bold cyan]",
        border_style="cyan"
    ))

    # Summary table
    summary_table = Table(title="Summary", show_header=True, header_style="bold cyan")
    summary_table.add_column("Metric", style="yellow")
    summary_table.add_column("Value", justify="right")
    summary_table.add_row("Total Shells", str(stats["total"]))
    summary_table.add_row("Stale Shells", f"[red]{stats['stale_count']}[/red]" if stats["stale_count"] else "0")

    console.print(summary_table)

    # State breakdown
    if stats["by_state"]:
        state_table = Table(title="\nBy State", show_header=True, header_style="bold magenta")
        state_table.add_column("State", style="yellow")
        state_table.add_column("Count", justify="right")
        for state, count in sorted(stats["by_state"].items()):
            color = "green" if state == "completed" else "red" if state in ["failed", "stale", "orphaned"] else "cyan"
            state_table.add_row(state.title(), f"[{color}]{count}[/{color}]")
        console.print(state_table)

    # Category breakdown
    if stats["by_category"]:
        cat_table = Table(title="\nBy Category", show_header=True, header_style="bold blue")
        cat_table.add_column("Category", style="yellow")
        cat_table.add_column("Count", justify="right")
        for cat, count in sorted(stats["by_category"].items()):
            cat_table.add_row(cat.replace("_", " ").title(), str(count))
        console.print(cat_table)

    # Detailed shell list
    if shells and ctx.obj['verbose']:
        _display_shell_table(shells, "All Registered Shells")


@cli.command()
@click.option('--category', type=click.Choice(['coordinator', 'agent', 'hive_mind', 'background']),
              help='Filter by category')
@click.pass_context
def validate(ctx, category: Optional[str]):
    """Check all registered shells and update their status"""
    tracker: ShellStateTracker = ctx.obj['tracker']
    logger = ctx.obj['logger']
    json_output = ctx.obj['json_output']

    shells = tracker.get_all_shells()
    if category:
        shells = [s for s in shells if s.category == category]

    validation_results = []
    updated = 0

    for shell in shells:
        old_state = shell.state
        new_state = tracker.validate_shell(shell)

        if old_state != new_state.value:
            tracker.update_shell_state(shell.shell_id, new_state)
            updated += 1
            logger.info(f"Shell {shell.shell_id}: {old_state} -> {new_state.value}")

        validation_results.append({
            "shell_id": shell.shell_id,
            "pid": shell.pid,
            "category": shell.category,
            "old_state": old_state,
            "new_state": new_state.value,
            "changed": old_state != new_state.value
        })

    if updated > 0:
        tracker.save()

    if json_output:
        result = {
            "action": "validate",
            "total_checked": len(shells),
            "updated": updated,
            "results": validation_results
        }
        print(json.dumps(result, indent=2))
        return

    # Display validation results
    console.print(Panel.fit(
        "[bold cyan]Shell Validation Results[/bold cyan]",
        border_style="cyan"
    ))

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Shell ID", style="dim")
    table.add_column("PID", justify="right")
    table.add_column("Category")
    table.add_column("Old State")
    table.add_column("New State")
    table.add_column("Changed")

    for result in validation_results:
        changed_str = "[green]Yes[/green]" if result["changed"] else "[dim]No[/dim]"
        new_color = "green" if result["new_state"] == "completed" else \
                    "red" if result["new_state"] in ["failed", "stale", "orphaned"] else "cyan"
        table.add_row(
            result["shell_id"][:12] + "...",
            str(result["pid"]),
            result["category"],
            result["old_state"],
            f"[{new_color}]{result['new_state']}[/{new_color}]",
            changed_str
        )

    console.print(table)
    console.print(f"\n[bold]Validated {len(shells)} shells, updated {updated}[/bold]")


# ============================================================================
# Helper Functions
# ============================================================================

def _display_shell_table(shells: List[ShellInfo], title: str) -> None:
    """Display shells in a rich table"""
    table = Table(title=f"\n{title}", show_header=True, header_style="bold cyan")
    table.add_column("Shell ID", style="dim", max_width=15)
    table.add_column("PID", justify="right")
    table.add_column("Category")
    table.add_column("State")
    table.add_column("Age (s)", justify="right")
    table.add_column("Command", max_width=40)

    for shell in shells:
        age = int(time.time() - shell.created_at)
        state_color = "green" if shell.state == "completed" else \
                      "red" if shell.state in ["failed", "stale", "orphaned"] else "cyan"
        table.add_row(
            shell.shell_id[:12] + "...",
            str(shell.pid),
            shell.category,
            f"[{state_color}]{shell.state}[/{state_color}]",
            str(age),
            shell.command[:40] + ("..." if len(shell.command) > 40 else "")
        )

    console.print(table)


def _display_cleanup_summary(shells: List[ShellInfo], title: str, dry_run: bool) -> None:
    """Display cleanup summary"""
    mode = "[yellow]DRY RUN[/yellow]" if dry_run else "[red]EXECUTE[/red]"

    console.print(Panel.fit(
        f"[bold cyan]{title}[/bold cyan]\n{mode}",
        border_style="yellow" if dry_run else "red"
    ))

    if not shells:
        return

    _display_shell_table(shells, f"Shells ({len(shells)} total)")

    # Memory summary
    total_pids = len(shells)
    categories = {}
    for shell in shells:
        categories[shell.category] = categories.get(shell.category, 0) + 1

    console.print(f"\n[bold]Summary:[/bold] {total_pids} shells across {len(categories)} categories")
    for cat, count in categories.items():
        console.print(f"  {cat}: {count}")


if __name__ == "__main__":
    cli()
