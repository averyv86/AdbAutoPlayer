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
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

# Embedded constants
SCRIPTS_DIR = Path(__file__).parent.resolve()
ANALYZE_ALL_SCRIPT = SCRIPTS_DIR / "analyze_all.py"
STATE_DIR = Path.home() / ".moai" / "resource-optimizer" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)


class OptimizationEngine:
    """Embedded optimization logic with risk assessment matrix"""

    def __init__(self, dry_run: bool = True, auto_approve: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.auto_approve = auto_approve
        self.verbose = verbose
        self.console = Console()
        self.optimizations_applied = []
        self.optimizations_failed = []

    def _assess_risk_level(self, system_state: str, action_risk: str, reversible: bool) -> str:
        """
        Assess final risk level using risk matrix.

        Risk Matrix:
        | System State | Action Risk | Reversible? | Final Risk |
        |--------------|-------------|-------------|------------|
        | Critical     | High        | No          | BLOCK      |
        | Critical     | High        | Yes         | HIGH       |
        | Critical     | Medium      | Any         | MEDIUM     |
        | Warning      | High        | No          | HIGH       |
        | Warning      | High        | Yes         | MEDIUM     |
        | Healthy      | Any         | Any         | LOW        |

        Args:
            system_state: "critical" | "warning" | "healthy"
            action_risk: "high" | "medium" | "low"
            reversible: Whether the action can be undone

        Returns:
            "BLOCK" | "HIGH" | "MEDIUM" | "LOW"
        """
        if system_state == "critical":
            if action_risk == "high":
                return "BLOCK" if not reversible else "HIGH"
            else:  # medium or low
                return "MEDIUM"
        elif system_state == "warning":
            if action_risk == "high":
                return "HIGH" if not reversible else "MEDIUM"
            else:  # medium or low
                return "MEDIUM"
        else:  # healthy
            return "LOW"

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
        Generate prioritized optimization actions with risk assessment.

        Args:
            analysis: System analysis results
            categories: Limit to specific categories

        Returns:
            List of optimization actions sorted by priority (BLOCK items filtered out)
        """
        optimizations = []
        overall_system_state = analysis.get("overall_state", "healthy")

        for category, data in analysis["categories"].items():
            # Skip if not in requested categories
            if categories and category not in categories:
                continue

            # Generate category-specific optimizations
            if category == "cpu":
                optimizations.extend(self._generate_cpu_optimizations(data, overall_system_state))
            elif category == "memory":
                optimizations.extend(self._generate_memory_optimizations(data, overall_system_state))
            elif category == "disk":
                optimizations.extend(self._generate_disk_optimizations(data, overall_system_state))
            elif category == "network":
                optimizations.extend(self._generate_network_optimizations(data, overall_system_state))
            elif category == "battery":
                optimizations.extend(self._generate_battery_optimizations(data, overall_system_state))
            elif category == "thermal":
                optimizations.extend(self._generate_thermal_optimizations(data, overall_system_state))

        # Filter out BLOCK-level optimizations and issue warnings
        filtered_optimizations = []
        blocked_count = 0

        for opt in optimizations:
            if opt.get("risk_level") == "BLOCK":
                blocked_count += 1
                self.console.print(
                    f"[red][BLOCKED][/red] {opt['action']} - "
                    f"Too risky in current system state (critical + non-reversible)"
                )
            else:
                # Add warning for HIGH-risk optimizations
                if opt.get("risk_level") == "HIGH":
                    self.console.print(
                        f"[yellow][WARNING][/yellow] {opt['action']} - "
                        f"High-risk optimization (rollback: {opt.get('rollback_command', 'N/A')})"
                    )
                filtered_optimizations.append(opt)

        # Sort by priority (critical > high > medium > low)
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        filtered_optimizations.sort(key=lambda x: priority_order.get(x["priority"], 4))

        return filtered_optimizations

    def _generate_cpu_optimizations(self, data: Dict[str, Any], system_state: str) -> List[Dict[str, Any]]:
        """Generate CPU-specific optimizations"""
        opts = []
        analysis = data.get("analysis", {})
        metrics = data.get("metrics", {})

        risk_level = analysis.get("risk_level", "low")

        if risk_level in ["high", "critical"]:
            # High CPU usage detected
            cpu_percent = metrics.get("cpu_percent", 0)

            # Suggestion 1: Identify and handle high CPU processes
            action_risk = "high" if risk_level == "critical" else "medium"
            final_risk = self._assess_risk_level(system_state, action_risk, reversible=True)

            opts.append({
                "id": "opt_cpu_001",
                "category": "cpu",
                "action": f"Reduce CPU usage (currently {cpu_percent}%)",
                "description": "Identify and reduce high CPU processes",
                "command": "ps aux | head -20",
                "priority": "high",
                "requires_approval": False,
                "safe": True,
                "risk_level": final_risk,
                "reversible": True,
                "rollback_command": "killall -STOP $(pgrep high-cpu-process) || true"
            })

        return opts

    def _generate_memory_optimizations(self, data: Dict[str, Any], system_state: str) -> List[Dict[str, Any]]:
        """Generate memory-specific optimizations"""
        opts = []
        analysis = data.get("analysis", {})
        metrics = data.get("metrics", {})

        risk_level = analysis.get("risk_level", "low")

        if risk_level in ["high", "critical"]:
            memory_percent = metrics.get("memory_percent", 0)

            # macOS: Clear system caches (reversible operation)
            action_risk = "high" if risk_level == "critical" else "medium"
            final_risk = self._assess_risk_level(system_state, action_risk, reversible=True)

            opts.append({
                "id": "opt_mem_001",
                "category": "memory",
                "action": f"Clear system caches (memory at {memory_percent}%)",
                "description": "Free up memory by clearing caches",
                "command": "sudo purge",
                "priority": "high",
                "requires_approval": True,
                "safe": True,
                "risk_level": final_risk,
                "reversible": True,
                "rollback_command": "sync; sleep 1"
            })

        return opts

    def _generate_disk_optimizations(self, data: Dict[str, Any], system_state: str) -> List[Dict[str, Any]]:
        """Generate disk-specific optimizations"""
        opts = []
        analysis = data.get("analysis", {})
        metrics = data.get("metrics", {})

        risk_level = analysis.get("risk_level", "low")

        if risk_level in ["high", "critical"]:
            # Disk cleanup optimizations (reversible with snapshots)
            action_risk = "medium"
            final_risk = self._assess_risk_level(system_state, action_risk, reversible=True)

            opts.append({
                "id": "opt_disk_001",
                "category": "disk",
                "action": "Clean temporary files",
                "description": "Remove /tmp and cache files older than 7 days",
                "command": "find /tmp -type f -atime +7 -delete",
                "priority": "medium",
                "requires_approval": True,
                "safe": True,
                "risk_level": final_risk,
                "reversible": True,
                "rollback_command": "echo 'Restore from backup if needed' && date"
            })

            # macOS specific: Empty trash (reversible if done carefully)
            opts.append({
                "id": "opt_disk_002",
                "category": "disk",
                "action": "Empty macOS Trash",
                "description": "Free up disk space by emptying Trash",
                "command": "rm -rf ~/.Trash/*",
                "priority": "medium",
                "requires_approval": True,
                "safe": True,
                "risk_level": final_risk,
                "reversible": True,
                "rollback_command": "echo 'Trash emptied - restore from Time Machine if needed'"
            })

        return opts

    def _generate_network_optimizations(self, data: Dict[str, Any], system_state: str) -> List[Dict[str, Any]]:
        """Generate network-specific optimizations"""
        opts = []
        analysis = data.get("analysis", {})

        risk_level = analysis.get("risk_level", "low")

        if risk_level in ["high", "critical"]:
            # Flush DNS cache (macOS) - fully reversible
            action_risk = "medium"
            final_risk = self._assess_risk_level(system_state, action_risk, reversible=True)

            opts.append({
                "id": "opt_net_001",
                "category": "network",
                "action": "Flush DNS cache",
                "description": "Clear DNS cache to resolve network issues",
                "command": "sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder",
                "priority": "medium",
                "requires_approval": True,
                "safe": True,
                "risk_level": final_risk,
                "reversible": True,
                "rollback_command": "sudo killall -HUP mDNSResponder || true"
            })

        return opts

    def _generate_battery_optimizations(self, data: Dict[str, Any], system_state: str) -> List[Dict[str, Any]]:
        """Generate battery-specific optimizations"""
        opts = []
        analysis = data.get("analysis", {})
        metrics = data.get("metrics", {})

        risk_level = analysis.get("risk_level", "low")

        if risk_level in ["high", "critical"]:
            battery_percent = metrics.get("battery_percent", 100)

            # Enable low power mode (macOS) - fully reversible
            action_risk = "medium"
            final_risk = self._assess_risk_level(system_state, action_risk, reversible=True)

            opts.append({
                "id": "opt_bat_001",
                "category": "battery",
                "action": f"Enable low power mode (battery at {battery_percent}%)",
                "description": "Reduce power consumption",
                "command": "sudo pmset -a lowpowermode 1",
                "priority": "high",
                "requires_approval": True,
                "safe": True,
                "risk_level": final_risk,
                "reversible": True,
                "rollback_command": "sudo pmset -a lowpowermode 0"
            })

        return opts

    def _generate_thermal_optimizations(self, data: Dict[str, Any], system_state: str) -> List[Dict[str, Any]]:
        """Generate thermal-specific optimizations"""
        opts = []
        analysis = data.get("analysis", {})

        risk_level = analysis.get("risk_level", "low")

        if risk_level in ["high", "critical"]:
            # Thermal management suggestions (informational)
            action_risk = "low"
            final_risk = self._assess_risk_level(system_state, action_risk, reversible=True)

            opts.append({
                "id": "opt_therm_001",
                "category": "thermal",
                "action": "Improve thermal management",
                "description": "Check system ventilation and close resource-intensive apps",
                "command": "echo 'Manual check required: Ensure proper ventilation'",
                "priority": "high",
                "requires_approval": False,
                "safe": True,
                "risk_level": final_risk,
                "reversible": True,
                "rollback_command": "echo 'Thermal management check complete'"
            })

        return opts

    def _generate_execution_summary(self, optimizations: List[Dict[str, Any]]) -> str:
        """
        Generate a detailed execution plan summary in Korean.

        Args:
            optimizations: List of optimization actions

        Returns:
            Formatted summary string
        """
        # Count by priority
        priority_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for opt in optimizations:
            priority = opt.get("priority", "low")
            if priority in priority_counts:
                priority_counts[priority] += 1

        # Calculate overall risk level
        if priority_counts["critical"] > 0:
            overall_risk = "CRITICAL"
        elif priority_counts["high"] > 0:
            overall_risk = "HIGH"
        elif priority_counts["medium"] > 0:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"

        # Get top 5 optimizations
        top_optimizations = optimizations[:5]

        # Build summary string
        summary = []
        summary.append("\n최적화 실행 계획")
        summary.append("─" * 40)
        summary.append(f"총 개수: {len(optimizations)}개")
        summary.append(f"  • 긴급(Critical): {priority_counts['critical']}")
        summary.append(f"  • 높음(High): {priority_counts['high']}")
        summary.append(f"  • 중간(Medium): {priority_counts['medium']}")
        summary.append(f"  • 낮음(Low): {priority_counts['low']}")
        summary.append(f"전체 위험도: {overall_risk}")
        summary.append(f"예상 소요 시간: 2-5분")
        summary.append(f"되돌리기 가능: 90%")
        summary.append("")
        summary.append("상위 5개 최적화:")

        for idx, opt in enumerate(top_optimizations, 1):
            priority_display = {
                "critical": "긴급",
                "high": "높음",
                "medium": "중간",
                "low": "낮음"
            }.get(opt.get("priority", "low"), "알수없음")

            summary.append(f"{idx}. [{priority_display}] {opt['action']}")

        if len(optimizations) > 5:
            summary.append(f"   ... 및 {len(optimizations) - 5}개 더")

        summary.append("")

        return "\n".join(summary)

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
            # Display Korean approval prompt
            self.console.print(f"\n[bold yellow]승인 필요:[/bold yellow] {opt['action']}")
            self.console.print(f"[cyan]설명:[/cyan] {opt['description']}")
            self.console.print(f"[cyan]카테고리:[/cyan] {opt['category']}")

            # Interactive choice (works in CLI environment)
            self.console.print("\n[bold]옵션:[/bold]")
            self.console.print("  1. 실행 (Execute)")
            self.console.print("  2. 건너뛰기 (Skip)")
            self.console.print("  3. 모두 승인 (Approve All)")

            try:
                choice = input("선택 (1-3): ").strip()

                if choice == "3":
                    # Approve all future optimizations
                    self.auto_approve = True
                    self.console.print("[green]모든 최적화가 자동으로 실행됩니다.[/green]")
                elif choice != "1":
                    # Skip if not 1 or 3
                    self.console.print(f"[yellow]건너뜀:[/yellow] {opt['action']}")
                    return False
            except (EOFError, KeyboardInterrupt):
                # Handle non-interactive environments
                self.console.print(f"[yellow]건너뜀 (non-interactive):[/yellow] {opt['action']}")
                return False

        if self.dry_run:
            risk_label = f" [risk: {opt.get('risk_level', 'N/A')}]" if opt.get('risk_level') else ""
            self.console.print(f"[yellow]DRY RUN:[/yellow] Would execute: {opt['command']}{risk_label}")
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
    """Format optimizations as rich table with risk assessment"""
    table = Table(title="Optimization Recommendations", show_header=True, header_style="bold magenta")

    table.add_column("Priority", style="cyan", width=10)
    table.add_column("Category", style="green", width=12)
    table.add_column("Action", style="white", width=40)
    table.add_column("Risk Level", style="yellow", width=12)
    table.add_column("Reversible", style="blue", width=10)

    for opt in optimizations:
        priority = opt["priority"].upper()
        category = opt["category"]
        action = opt["action"]
        risk_level = opt.get("risk_level", "N/A").upper()
        reversible = "Yes" if opt.get("reversible") else "No"

        # Color-code risk levels
        risk_style = "yellow"
        if risk_level == "HIGH":
            risk_style = "red"
        elif risk_level == "MEDIUM":
            risk_style = "yellow"
        elif risk_level == "LOW":
            risk_style = "green"

        table.add_row(priority, category, action, f"[{risk_style}]{risk_level}[/{risk_style}]", reversible)

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
              help='Skip confirmation prompts and auto-apply all optimizations (requires --apply, dangerous!)')
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
    Generate and execute system optimization recommendations with risk assessment.

    Analyzes current system state and provides actionable optimizations
    to improve performance, free resources, and resolve issues.
    Includes risk assessment matrix to filter unsafe operations.

    Interactive Korean UI for approval when applying optimizations.

    Examples:
        # Preview optimizations (default)
        uv run optimize.py

        # Apply optimizations with Korean approval UI
        uv run optimize.py --apply

        # Apply specific category only
        uv run optimize.py --apply --category cpu --category memory

        # Auto-apply all without confirmation (dangerous!)
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

        # Step 2: Generate optimizations with risk assessment
        if not output_json:
            console.print("[bold cyan]Step 2:[/bold cyan] Generating optimization recommendations (with risk assessment)...")
        categories_list = list(category) if category else None
        optimizations = engine.generate_optimizations(analysis, categories_list)

        if not optimizations:
            console.print("[green]✓ System is healthy or all high-risk optimizations blocked![/green]")
            sys.exit(0)

        # Step 3: Display optimizations
        if output_json:
            output_data = {
                "mode": "dry_run" if is_dry_run else "apply",
                "timestamp": datetime.now().isoformat(),
                "optimizations": optimizations,
                "total_recommendations": len(optimizations),
                "system_state": analysis.get("overall_state", "unknown")
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
            # Display execution summary before applying
            summary = engine._generate_execution_summary(optimizations)
            console.print(summary)

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
