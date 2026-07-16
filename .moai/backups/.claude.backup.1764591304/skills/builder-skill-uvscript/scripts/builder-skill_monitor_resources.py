#!/usr/bin/env python3
# /// script
# dependencies = [
#     "psutil>=5.9.0",
#     "click>=8.1.0",
#     "rich>=13.0.0",
# ]
# ///

"""
macOS Resource Optimizer - Continuous System Monitor

Monitors system resources continuously with threshold-based alerts.
Saves monitoring history and provides graceful termination.

Features:
- Continuous monitoring loop with configurable interval
- Threshold-based alert system
- State persistence to JSON file
- Duration limit support
- Graceful SIGINT/SIGTERM handling
- JSON output for programmatic access

Usage:
    # Monitor for 30 seconds
    uv run monitor.py --duration 30

    # Monitor with 10-second interval
    uv run monitor.py --interval 10 --duration 60

    # Output JSON samples
    uv run monitor.py --duration 30 --json

Exit Codes:
    0: Success
    1: No alerts triggered
    2: Alerts triggered during monitoring
    3: Critical error occurred
"""

import asyncio
import json
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table


class ContinuousMonitor:
    """Embedded continuous monitoring engine with threshold alerts."""

    def __init__(
        self,
        interval: int = 5,
        duration: Optional[int] = None,
        state_file: Optional[Path] = None,
    ):
        """
        Initialize continuous monitor.

        Args:
            interval: Monitoring interval in seconds
            duration: Maximum monitoring duration in seconds (None = infinite)
            state_file: Path to state file for history persistence
        """
        self.interval = interval
        self.duration = duration
        self.state_file = state_file or (
            Path.home() / ".moai/resource-optimizer/monitor/state.json"
        )
        self.console = Console()
        self.running = True
        self.samples: List[Dict[str, Any]] = []
        self.alert_count = 0

        # Register signal handlers for graceful termination
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum: int, frame: Any) -> None:
        """
        Handle termination signals gracefully.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.console.print("\n[yellow]⚠️  Stopping monitoring...[/yellow]")
        self.running = False

    async def run_analysis(self) -> Dict[str, Any]:
        """
        Execute analyze_all.py to get current system status.

        Returns:
            Analysis results as dictionary

        Raises:
            Exception: If analysis execution fails
        """
        analyze_script = Path(__file__).parent / "analyze_all.py"

        proc = await asyncio.create_subprocess_exec(
            "uv",
            "run",
            str(analyze_script),
            "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        # Exit codes 0, 1, 2 are all valid (different status levels)
        if proc.returncode in [0, 1, 2]:
            return json.loads(stdout.decode())
        else:
            raise Exception(f"Analysis failed: {stderr.decode()}")

    def check_thresholds(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Check for threshold violations in analysis results.

        Args:
            analysis: Analysis results from analyze_all.py

        Returns:
            List of alert dictionaries with category, severity, and message
        """
        alerts = []

        for category, data in analysis.get("categories", {}).items():
            analysis_data = data.get("analysis", {})
            risk_level = analysis_data.get("risk_level", "low")

            # Trigger alerts for high and critical risk levels
            if risk_level in ["high", "critical"]:
                alerts.append(
                    {
                        "category": category,
                        "severity": risk_level,
                        "message": f"{category.upper()} {risk_level} risk detected",
                    }
                )

        return alerts

    def save_state(self) -> None:
        """Save monitoring history to state file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "last_updated": datetime.now().isoformat(),
            "samples": self.samples[-100:],  # Keep last 100 samples
            "total_samples": len(self.samples),
            "total_alerts": self.alert_count,
        }

        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def _create_status_table(
        self, sample: Dict[str, Any], sample_num: int
    ) -> Table:
        """
        Create Rich table for current status display.

        Args:
            sample: Current sample data
            sample_num: Sample number

        Returns:
            Rich Table object
        """
        table = Table(title=f"Monitoring Sample #{sample_num}")

        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("Timestamp", sample["timestamp"])
        table.add_row("Overall Status", sample["overall_status"])
        table.add_row("Risk Level", sample["overall_risk"])
        table.add_row("Alerts", str(len(sample["alerts"])))
        table.add_row("Total Samples", str(len(self.samples)))

        return table

    async def monitor_loop(self) -> int:
        """
        Main monitoring loop with continuous analysis and threshold checking.

        Returns:
            Exit code (0 = success, 1 = no alerts, 2 = alerts triggered)
        """
        start_time = datetime.now()

        self.console.print(
            Panel(
                f"[bold green]Continuous Monitoring Started[/bold green]\n"
                f"Interval: {self.interval}s\n"
                f"Duration: {self.duration or 'Infinite'}s\n"
                f"State File: {self.state_file}\n"
                f"Press Ctrl+C to stop",
                title="Monitor Configuration",
            )
        )

        while self.running:
            try:
                # Run analysis
                analysis = await self.run_analysis()

                # Check thresholds
                alerts = self.check_thresholds(analysis)

                # Record sample
                sample = {
                    "timestamp": datetime.now().isoformat(),
                    "overall_status": analysis.get("overall", {}).get(
                        "status", "unknown"
                    ),
                    "overall_risk": analysis.get("overall", {}).get(
                        "risk_level", "unknown"
                    ),
                    "alerts": alerts,
                }
                self.samples.append(sample)

                # Count alerts
                if alerts:
                    self.alert_count += len(alerts)

                # Display current status
                status_table = self._create_status_table(sample, len(self.samples))
                self.console.print(status_table)

                # Display alerts
                if alerts:
                    for alert in alerts:
                        severity_emoji = {"high": "⚠️ ", "critical": "🚨"}
                        self.console.print(
                            f"{severity_emoji.get(alert['severity'], '⚠️ ')}"
                            f"[bold red]{alert['message']}[/bold red]"
                        )

                # Save state periodically (every 10 samples)
                if len(self.samples) % 10 == 0:
                    self.save_state()

                # Check duration limit
                if self.duration:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed >= self.duration:
                        self.console.print(
                            f"\n[green]✅ Monitoring duration limit reached ({self.duration}s)[/green]"
                        )
                        break

                # Wait for next interval
                self.console.print(
                    f"\n[dim]Next check in {self.interval} seconds...[/dim]\n"
                )
                await asyncio.sleep(self.interval)

            except Exception as e:
                self.console.print(f"[red]❌ Error: {e}[/red]")
                await asyncio.sleep(self.interval)

        # Final save
        self.save_state()

        # Summary
        self.console.print(
            Panel(
                f"[bold green]Monitoring Stopped[/bold green]\n"
                f"Total Samples: {len(self.samples)}\n"
                f"Total Alerts: {self.alert_count}\n"
                f"State Saved: {self.state_file}",
                title="Monitoring Summary",
            )
        )

        # Determine exit code
        if self.alert_count > 0:
            return 2  # Alerts triggered
        elif len(self.samples) > 0:
            return 0  # Success, no alerts
        else:
            return 1  # No samples collected


@click.command()
@click.option(
    "--interval",
    type=int,
    default=5,
    help="Monitoring interval in seconds (default: 5)",
)
@click.option(
    "--duration",
    type=int,
    default=None,
    help="Maximum monitoring duration in seconds (optional, infinite by default)",
)
@click.option(
    "--state-file",
    type=click.Path(),
    help="Custom state file path (default: ~/.moai/resource-optimizer/monitor/state.json)",
)
@click.option(
    "--json", "output_json", is_flag=True, help="Output samples as JSON at the end"
)
def main(
    interval: int, duration: Optional[int], state_file: Optional[str], output_json: bool
) -> None:
    """
    Continuously monitor system resources with threshold alerts.

    Monitors macOS system resources at regular intervals and triggers alerts
    when risk thresholds are exceeded. Saves monitoring history for analysis.

    Examples:

        # Monitor for 30 seconds with default interval (5s)
        uv run monitor.py --duration 30

        # Monitor with custom interval and duration
        uv run monitor.py --interval 10 --duration 60

        # Output JSON samples at the end
        uv run monitor.py --duration 30 --json

        # Monitor indefinitely (Ctrl+C to stop)
        uv run monitor.py --interval 5
    """
    state_path = Path(state_file) if state_file else None
    monitor = ContinuousMonitor(interval, duration, state_path)

    try:
        exit_code = asyncio.run(monitor.monitor_loop())

        if output_json:
            click.echo(
                json.dumps(
                    {
                        "samples": monitor.samples,
                        "total_samples": len(monitor.samples),
                        "total_alerts": monitor.alert_count,
                    },
                    indent=2,
                )
            )

        sys.exit(exit_code)

    except Exception as e:
        click.echo(f"❌ Monitoring error: {e}", err=True)
        sys.exit(3)


if __name__ == "__main__":
    main()
