#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=5.9.0"]
# ///

"""
Background Task Monitor - Real-time Progress Tracking

Monitors multiple background tasks in parallel and reports progress in TOON format
for 60-75% token reduction compared to JSON.

Usage:
    # Run with specific tasks
    uv run scripts/background_monitor.py --tasks cpu,memory,disk

    # Monitor all categories
    uv run scripts/background_monitor.py --all

    # Custom update interval
    uv run scripts/background_monitor.py --all --interval 0.5

Features:
    - Real-time progress tracking
    - TOON-formatted output (token efficient)
    - Parallel task execution
    - Error handling and timeout detection
    - Summary statistics

Author: MoAI-ADK
Version: 3.0.0 (TOON-enabled)
Date: 2025-12-01
"""

import asyncio
import json
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from toon_codec import encode_toon


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class TaskInfo:
    """Information about a background task."""
    task_id: str
    category: str
    status: TaskStatus
    start_time: float
    end_time: Optional[float] = None
    exit_code: Optional[int] = None
    error: Optional[str] = None
    output: Optional[str] = None

    @property
    def duration(self) -> float:
        """Calculate task duration."""
        if self.end_time:
            return round(self.end_time - self.start_time, 2)
        return round(time.time() - self.start_time, 2)

    @property
    def is_done(self) -> bool:
        """Check if task is completed."""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.TIMEOUT]


class BackgroundMonitor:
    """Monitor multiple background analysis tasks."""

    def __init__(self, categories: List[str], interval: float = 1.0, timeout: float = 30.0):
        """
        Initialize background monitor.

        Args:
            categories: List of categories to analyze (cpu, memory, disk, etc.)
            interval: Progress update interval in seconds
            timeout: Task timeout in seconds
        """
        self.categories = categories
        self.interval = interval
        self.timeout = timeout
        self.tasks: Dict[str, TaskInfo] = {}
        self.start_time = time.time()

    async def run_task(self, category: str) -> TaskInfo:
        """
        Run a single analysis task.

        Args:
            category: Resource category to analyze

        Returns:
            TaskInfo with execution results
        """
        task_id = f"{category}_{int(time.time() * 1000)}"
        script_path = Path(__file__).parent / f"analyze_{category}.py"

        # Initialize task info
        task_info = TaskInfo(
            task_id=task_id,
            category=category,
            status=TaskStatus.PENDING,
            start_time=time.time()
        )
        self.tasks[task_id] = task_info

        if not script_path.exists():
            task_info.status = TaskStatus.FAILED
            task_info.error = f"Script not found: {script_path}"
            task_info.end_time = time.time()
            return task_info

        # Update to running
        task_info.status = TaskStatus.RUNNING

        try:
            # Execute analyzer subprocess
            process = await asyncio.create_subprocess_exec(
                'uv', 'run', str(script_path), '--format=toon',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )

            task_info.end_time = time.time()
            task_info.exit_code = process.returncode
            task_info.output = stdout.decode().strip()

            if process.returncode in [0, 1, 2]:
                task_info.status = TaskStatus.COMPLETED
            else:
                task_info.status = TaskStatus.FAILED
                task_info.error = stderr.decode().strip() if stderr else "Unknown error"

        except asyncio.TimeoutError:
            task_info.status = TaskStatus.TIMEOUT
            task_info.end_time = time.time()
            task_info.error = f"Task timeout after {self.timeout}s"

        except Exception as e:
            task_info.status = TaskStatus.FAILED
            task_info.end_time = time.time()
            task_info.error = str(e)

        return task_info

    def get_progress_toon(self) -> str:
        """
        Get current progress in TOON format.

        Returns:
            TOON-encoded progress report
        """
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        running = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)

        progress_percent = round((completed / total * 100), 1) if total > 0 else 0
        elapsed = round(time.time() - self.start_time, 2)

        # TOON format progress
        progress_data = {
            "total": total,
            "completed": completed,
            "running": running,
            "failed": failed,
            "pending": pending,
            "progress_pct": progress_percent,
            "elapsed": elapsed
        }

        return encode_toon(progress_data)

    def get_summary_toon(self) -> str:
        """
        Get final summary in TOON format.

        Returns:
            TOON-encoded summary report
        """
        total_duration = round(time.time() - self.start_time, 2)

        # Aggregate results
        completed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        failed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]

        # Calculate average duration for completed tasks
        avg_duration = round(
            sum(t.duration for t in completed_tasks) / len(completed_tasks), 2
        ) if completed_tasks else 0

        # Determine overall exit code
        if failed_tasks:
            overall_exit_code = 2  # Critical if any failed
        elif completed_tasks:
            # Use max exit code from completed tasks
            overall_exit_code = max((t.exit_code or 0) for t in completed_tasks)
        else:
            overall_exit_code = 3  # Error if nothing completed

        summary_data = {
            "total_duration": total_duration,
            "total_tasks": len(self.tasks),
            "completed": len(completed_tasks),
            "failed": len(failed_tasks),
            "avg_duration": avg_duration,
            "overall_exit": overall_exit_code
        }

        return encode_toon(summary_data)

    async def monitor_with_progress(self) -> Dict:
        """
        Run all tasks with real-time progress reporting.

        Returns:
            Final results dict
        """
        # Start all tasks in parallel
        task_coroutines = [self.run_task(cat) for cat in self.categories]
        all_tasks = [asyncio.create_task(coro) for coro in task_coroutines]

        # Monitor progress
        while not all(t.is_done for t in self.tasks.values()):
            # Print progress update in TOON format
            progress_toon = self.get_progress_toon()
            print(f"\r{progress_toon}", end="", flush=True)

            await asyncio.sleep(self.interval)

        # Wait for all tasks to complete
        await asyncio.gather(*all_tasks, return_exceptions=True)

        # Clear progress line
        print("\r" + " " * 100 + "\r", end="", flush=True)

        # Return final results
        return {
            'tasks': {tid: {
                'category': t.category,
                'status': t.status.value,
                'duration': t.duration,
                'exit_code': t.exit_code,
                'output': t.output,
                'error': t.error
            } for tid, t in self.tasks.items()},
            'summary': self.get_summary_toon()
        }


async def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Monitor background analysis tasks with real-time progress')
    parser.add_argument('--tasks', type=str,
                        help='Comma-separated list of categories (cpu,memory,disk)')
    parser.add_argument('--all', action='store_true',
                        help='Monitor all categories')
    parser.add_argument('--interval', type=float, default=1.0,
                        help='Progress update interval in seconds (default: 1.0)')
    parser.add_argument('--timeout', type=float, default=30.0,
                        help='Task timeout in seconds (default: 30.0)')
    parser.add_argument('--format', choices=['json', 'toon'], default='toon',
                        help='Output format (default: toon)')

    args = parser.parse_args()

    # Determine categories to monitor
    if args.all:
        categories = ['cpu', 'memory', 'disk', 'network', 'battery', 'thermal']
    elif args.tasks:
        categories = [c.strip() for c in args.tasks.split(',')]
    else:
        print("Error: Specify --tasks or --all")
        return 1

    # Create monitor
    monitor = BackgroundMonitor(
        categories=categories,
        interval=args.interval,
        timeout=args.timeout
    )

    # Run with progress reporting
    print(f"# Starting background monitoring for {len(categories)} categories...")
    print()

    results = await monitor.monitor_with_progress()

    # Output final results
    if args.format == 'json':
        print(json.dumps(results, indent=2))
    else:
        # TOON format output
        print("# Monitoring Complete")
        print(results['summary'])
        print()

        print("# Task Results")
        for task_id, task_data in results['tasks'].items():
            print(f"\n## {task_data['category'].upper()}")
            print(f"status:{task_data['status']}")
            print(f"duration:{task_data['duration']}")

            if task_data['exit_code'] is not None:
                print(f"exit_code:{task_data['exit_code']}")

            if task_data['error']:
                print(f"error:{task_data['error']}")

            if task_data['output']:
                print(task_data['output'])

    # Return overall exit code
    summary_lines = results['summary'].split('\n')
    for line in summary_lines:
        if line.startswith('overall_exit:'):
            return int(line.split(':')[1])

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
