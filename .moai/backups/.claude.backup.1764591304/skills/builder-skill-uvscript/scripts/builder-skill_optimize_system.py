#!/usr/bin/env python3
# /// script
# dependencies = [
#     "psutil>=5.9.0",
#     "click>=8.1.0",
#     "rich>=13.0.0",
# ]
# ///

"""
System Resource Optimization Engine

Generates and executes optimization recommendations based on system analysis.
Supports dry-run preview and interactive application of optimizations.

Features:
- Collect system state via analyze_all.py
- Generate prioritized optimization actions
- Dry-run mode (default) - preview without changes
- Apply mode - execute optimizations with confirmation
- Category-specific optimizations (CPU, memory, disk, etc.)
- Rollback support via state snapshots

Exit codes:
- 0: Optimizations successful
- 1: Some optimizations failed (partial success)
- 2: All optimizations failed
- 3: Execution error
"""

import asyncio
import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import shutil

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

# Embedded constants
SCRIPTS_DIR = Path(__file__).parent.resolve()
ANALYZE_ALL_SCRIPT = SCRIPTS_DIR / "analyze_all.py"
STATE_DIR = Path.home() / ".moai" / "resource-optimizer" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)


class OptimizationEngine:
    """Embedded optimization logic"""

    def __init__(self, dry_run: bool = True, auto_approve: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.auto_approve = auto_approve
        self.verbose = verbose
        self.console = Console()
        self.optimizations_applied = []
        self.optimizations_failed = []

    async def collect_system_state(self) -> Dict[str, Any]:
        """
        Run analyze_all.py to get current system state.

        Returns:
            System analysis results
        """
        cmd = ["uv", "run", str(ANALYZE_ALL_SCRIPT), "--json"]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode in (0, 1, 2):  # Success, warning, or critical
            return json.loads(stdout.decode())
        else:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"Failed to collect system state: {error_msg}")

    def generate_optimizations(
        self,
        analysis: Dict[str, Any],
        categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate prioritized optimization actions.

        Args:
            analysis: System analysis results
            categories: Limit to specific categories

        Returns:
            List of optimization actions sorted by priority
        """
        optimizations = []

        for category, data in analysis["categories"].items():
            # Skip if not in requested categories
            if categories and category not in categories:
                continue

            # Generate category-specific optimizations
            if category == "cpu":
                optimizations.extend(self._generate_cpu_optimizations(data))
            elif category == "memory":
                optimizations.extend(self._generate_memory_optimizations(data))
            elif category == "disk":
                optimizations.extend(self._generate_disk_optimizations(data))
            elif category == "network":
                optimizations.extend(self._generate_network_optimizations(data))
            elif category == "battery":
                optimizations.extend(self._generate_battery_optimizations(data))
            elif category == "thermal":
                optimizations.extend(self._generate_thermal_optimizations(data))

        # Sort by priority (critical > high > medium > low)
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        optimizations.sort(key=lambda x: priority_order.get(x["priority"], 4))

        return optimizations

    def _generate_cpu_optimizations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate CPU-specific optimizations"""
        opts = []
        analysis = data.get("analysis", {})
        metrics = data.get("metrics", {})

        risk_level = analysis.get("risk_level", "low")

        if risk_level in ["high", "critical"]:
            # High CPU usage detected
            cpu_percent = metrics.get("cpu_percent", 0)

            # Suggestion 1: Identify and handle high CPU processes
            opts.append({
                "category": "cpu",
                "action": f"Reduce CPU usage (currently {cpu_percent}%)",
                "description": "Identify and reduce high CPU processes",
                "command": "ps aux | head -20",  # Safe inspection command
                "priority": "high",
                "requires_approval": False,
                "safe": True
            })

        return opts

    def _generate_memory_optimizations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate memory-specific optimizations"""
        opts = []
        analysis = data.get("analysis", {})
        metrics = data.get("metrics", {})

        risk_level = analysis.get("risk_level", "low")

        if risk_level in ["high", "critical"]:
            memory_percent = metrics.get("memory_percent", 0)

            # macOS: Clear system caches
            opts.append({
                "category": "memory",
                "action": f"Clear system caches (memory at {memory_percent}%)",
                "description": "Free up memory by clearing caches",
                "command": "sudo purge",
                "priority": "high",
                "requires_approval": True,
                "safe": True
            })

        return opts

    def _generate_disk_optimizations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate disk-specific optimizations"""
        opts = []
        analysis = data.get("analysis", {})
        metrics = data.get("metrics", {})

        risk_level = analysis.get("risk_level", "low")

        if risk_level in ["high", "critical"]:
            # Disk cleanup optimizations
            opts.append({
                "category": "disk",
                "action": "Clean temporary files",
                "description": "Remove /tmp and cache files",
                "command": "find /tmp -type f -atime +7 -delete",
                "priority": "medium",
                "requires_approval": True,
                "safe": True
            })

            # macOS specific: Empty trash
            opts.append({
                "category": "disk",
                "action": "Empty macOS Trash",
                "description": "Free up disk space by emptying Trash",
                "command": "rm -rf ~/.Trash/*",
                "priority": "medium",
                "requires_approval": True,
                "safe": True
            })

        return opts

    def _generate_network_optimizations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate network-specific optimizations"""
        opts = []
        analysis = data.get("analysis", {})

        risk_level = analysis.get("risk_level", "low")

        if risk_level in ["high", "critical"]:
            # Flush DNS cache (macOS)
            opts.append({
                "category": "network",
                "action": "Flush DNS cache",
                "description": "Clear DNS cache to resolve network issues",
                "command": "sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder",
                "priority": "medium",
                "requires_approval": True,
                "safe": True
            })

        return opts

    def _generate_battery_optimizations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate battery-specific optimizations"""
        opts = []
        analysis = data.get("analysis", {})
        metrics = data.get("metrics", {})

        risk_level = analysis.get("risk_level", "low")

        if risk_level in ["high", "critical"]:
            battery_percent = metrics.get("battery_percent", 100)

            # Enable low power mode (macOS)
            opts.append({
                "category": "battery",
                "action": f"Enable low power mode (battery at {battery_percent}%)",
                "description": "Reduce power consumption",
                "command": "sudo pmset -a lowpowermode 1",
                "priority": "high",
                "requires_approval": True,
                "safe": True
            })

        return opts

    def _generate_thermal_optimizations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate thermal-specific optimizations"""
        opts = []
        analysis = data.get("analysis", {})

        risk_level = analysis.get("risk_level", "low")

        if risk_level in ["high", "critical"]:
            # Thermal management suggestions
            opts.append({
                "category": "thermal",
                "action": "Improve thermal management",
                "description": "Check system ventilation and close resource-intensive apps",
                "command": "echo 'Manual check required: Ensure proper ventilation'",
                "priority": "high",
                "requires_approval": False,
                "safe": True
            })

        return opts

    async def apply_optimization(self, opt: Dict[str, Any]) -> bool:
        """
        Execute a single optimization.

        Args:
            opt: Optimization action dictionary

        Returns:
            True if successful, False otherwise
        """
        # Check approval requirement
        if opt.get("requires_approval") and not self.auto_approve:
            if not Confirm.ask(f"Apply: {opt['action']}?"):
                self.console.print(f"[yellow]Skipped:[/yellow] {opt['action']}")
                return False

        if self.dry_run:
            self.console.print(f"[yellow]DRY RUN:[/yellow] Would execute: {opt['command']}")
            return True

        # Execute command
        try:
            proc = await asyncio.create_subprocess_shell(
                opt["command"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                self.console.print(f"[green]✓[/green] Applied: {opt['action']}")
                self.optimizations_applied.append(opt)
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.console.print(f"[red]✗[/red] Failed: {opt['action']} - {error_msg}")
                self.optimizations_failed.append(opt)
                return False
        except Exception as e:
            self.console.print(f"[red]✗[/red] Error: {opt['action']} - {str(e)}")
            self.optimizations_failed.append(opt)
            return False

    async def apply_all_optimizations(self, optimizations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply all optimizations with progress tracking.

        Args:
            optimizations: List of optimization actions

        Returns:
            Summary of results
        """
        if not optimizations:
            self.console.print("[yellow]No optimizations needed![/yellow]")
            return {
                "total": 0,
                "applied": 0,
                "failed": 0,
                "skipped": 0
            }

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(
                f"Applying {len(optimizations)} optimizations...",
                total=len(optimizations)
            )

            for opt in optimizations:
                progress.update(task, description=f"Processing: {opt['action']}")
                await self.apply_optimization(opt)
                progress.advance(task)

        return {
            "total": len(optimizations),
            "applied": len(self.optimizations_applied),
            "failed": len(self.optimizations_failed),
            "skipped": len(optimizations) - len(self.optimizations_applied) - len(self.optimizations_failed)
        }

    def save_state_snapshot(self, analysis: Dict[str, Any]) -> Path:
        """
        Save system state before applying optimizations.

        Args:
            analysis: Current system analysis

        Returns:
            Path to saved state file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        state_file = STATE_DIR / f"state_before_{timestamp}.json"

        with open(state_file, "w") as f:
            json.dump(analysis, f, indent=2)

        return state_file


def format_optimizations_table(optimizations: List[Dict[str, Any]]) -> Table:
    """Format optimizations as rich table"""
    table = Table(title="Optimization Recommendations", show_header=True, header_style="bold magenta")

    table.add_column("Priority", style="cyan", width=10)
    table.add_column("Category", style="green", width=12)
    table.add_column("Action", style="white", width=50)
    table.add_column("Approval", style="yellow", width=10)

    for opt in optimizations:
        priority = opt["priority"].upper()
        category = opt["category"]
        action = opt["action"]
        requires_approval = "Yes" if opt.get("requires_approval") else "No"

        table.add_row(priority, category, action, requires_approval)

    return table


@click.command()
@click.option('--json', 'output_json', is_flag=True,
              help='Output as JSON instead of human-readable format')
@click.option('--dry-run', is_flag=True, default=True,
              help='Preview optimizations without applying (default)')
@click.option('--apply', is_flag=True,
              help='Apply optimizations (requires confirmation)')
@click.option('--category', multiple=True,
              help='Limit to specific categories (can specify multiple)')
@click.option('--auto-approve', is_flag=True,
              help='Skip confirmation prompts (dangerous!)')
@click.option('--verbose', is_flag=True,
              help='Show detailed output')
def main(
    output_json: bool,
    dry_run: bool,
    apply: bool,
    category: tuple,
    auto_approve: bool,
    verbose: bool
):
    """
    Generate and execute system optimization recommendations.

    Analyzes current system state and provides actionable optimizations
    to improve performance, free resources, and resolve issues.

    Examples:
        # Preview optimizations (default)
        uv run optimize.py

        # Apply optimizations with confirmation
        uv run optimize.py --apply

        # Apply specific category only
        uv run optimize.py --apply --category cpu --category memory

        # Auto-apply all (dangerous!)
        uv run optimize.py --apply --auto-approve

        # JSON output for automation
        uv run optimize.py --json
    """
    console = Console()

    # Determine run mode
    is_dry_run = not apply  # If --apply not specified, default to dry-run

    try:
        # Step 1: Collect system state
        if not output_json:
            console.print("[bold cyan]Step 1:[/bold cyan] Collecting system state...")
        engine = OptimizationEngine(dry_run=is_dry_run, auto_approve=auto_approve, verbose=verbose)
        analysis = asyncio.run(engine.collect_system_state())

        # Save state snapshot before any changes
        if not is_dry_run and not output_json:
            state_file = engine.save_state_snapshot(analysis)
            console.print(f"[green]State snapshot saved:[/green] {state_file}")

        # Step 2: Generate optimizations
        if not output_json:
            console.print("[bold cyan]Step 2:[/bold cyan] Generating optimization recommendations...")
        categories_list = list(category) if category else None
        optimizations = engine.generate_optimizations(analysis, categories_list)

        if not optimizations:
            console.print("[green]✓ System is healthy! No optimizations needed.[/green]")
            sys.exit(0)

        # Step 3: Display optimizations
        if output_json:
            output_data = {
                "mode": "dry_run" if is_dry_run else "apply",
                "timestamp": datetime.now().isoformat(),
                "optimizations": optimizations,
                "total_recommendations": len(optimizations)
            }
            click.echo(json.dumps(output_data, indent=2))
        else:
            console.print(f"\n[bold green]Found {len(optimizations)} optimization(s)[/bold green]\n")
            table = format_optimizations_table(optimizations)
            console.print(table)

            if is_dry_run:
                console.print("\n[yellow]DRY RUN MODE:[/yellow] Use --apply to execute optimizations")

        # Step 4: Apply optimizations (if requested)
        if not is_dry_run and not output_json:
            console.print("\n[bold cyan]Step 3:[/bold cyan] Applying optimizations...")
            results = asyncio.run(engine.apply_all_optimizations(optimizations))

            # Display summary
            console.print("\n[bold]Summary:[/bold]")
            console.print(f"  Total: {results['total']}")
            console.print(f"  [green]Applied: {results['applied']}[/green]")
            console.print(f"  [red]Failed: {results['failed']}[/red]")
            console.print(f"  [yellow]Skipped: {results['skipped']}[/yellow]")

            # Exit code based on results
            if results['failed'] == results['total']:
                sys.exit(2)  # All failed
            elif results['failed'] > 0:
                sys.exit(1)  # Partial success
            else:
                sys.exit(0)  # All successful

        sys.exit(0)

    except Exception as e:
        error_data = {
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "command": "optimize"
        }
        if output_json:
            click.echo(json.dumps(error_data, indent=2), err=True)
        else:
            console.print(f"[red]❌ Error running optimization: {e}[/red]")
        sys.exit(3)


if __name__ == "__main__":
    main()
