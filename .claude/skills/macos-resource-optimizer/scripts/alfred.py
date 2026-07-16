#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=5.9.0"]
# ///

"""
Alfred - Central Resource Optimizer Coordinator

The intelligent orchestrator that coordinates all resource optimization sub-agents
with TOON workflow, real-time progress tracking, and smart recommendations.

Usage:
    # Quick health check
    uv run scripts/alfred.py --quick

    # Full system analysis
    uv run scripts/alfred.py --analyze

    # Continuous monitoring
    uv run scripts/alfred.py --monitor

    # Specific categories
    uv run scripts/alfred.py --categories cpu,memory,disk

    # With optimization recommendations
    uv run scripts/alfred.py --analyze --recommend

Features:
    - Intelligent agent coordination
    - TOON format workflow (60-75% token savings)
    - Real-time progress tracking
    - Smart prioritization
    - Conversational interface
    - Resource-aware execution

Author: MoAI-ADK
Version: 1.0.0 (TOON-enabled)
Date: 2025-12-01
"""

import asyncio
import json
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil

sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from toon_codec import encode_toon, decode_toon


class Priority(Enum):
    """Task priority levels."""
    CRITICAL = 100
    HIGH = 80
    MEDIUM = 60
    LOW = 40


class AgentStatus(Enum):
    """Agent execution status."""
    IDLE = "idle"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentTask:
    """Represents a sub-agent task."""
    category: str
    script: str
    priority: Priority
    status: AgentStatus
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[Dict] = None
    error: Optional[str] = None

    @property
    def duration(self) -> float:
        """Calculate task duration."""
        if self.start_time and self.end_time:
            return round(self.end_time - self.start_time, 2)
        return 0.0


class Alfred:
    """
    Central Resource Optimizer Coordinator.

    Alfred intelligently coordinates all resource optimization sub-agents,
    provides real-time progress in TOON format, and delivers actionable
    recommendations.
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize Alfred.

        Args:
            verbose: Enable detailed progress output
        """
        self.verbose = verbose
        self.tasks: Dict[str, AgentTask] = {}
        self.start_time = time.time()
        self.all_categories = ['cpu', 'memory', 'disk', 'network', 'battery', 'thermal']

    def greet(self):
        """Greet the user."""
        if self.verbose:
            print("🤖 Alfred - Resource Optimizer Coordinator")
            print("=" * 60)
            print("Coordinating resource optimization with TOON workflow")
            print()

    def assess_system_priority(self) -> Dict[str, Priority]:
        """
        Intelligently assess which categories need urgent attention.

        Returns:
            Dict mapping categories to priority levels
        """
        priorities = {}

        # Quick system check to determine priorities
        try:
            # CPU priority
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent > 90:
                priorities['cpu'] = Priority.CRITICAL
            elif cpu_percent > 75:
                priorities['cpu'] = Priority.HIGH
            else:
                priorities['cpu'] = Priority.MEDIUM

            # Memory priority
            mem = psutil.virtual_memory()
            if mem.percent > 90:
                priorities['memory'] = Priority.CRITICAL
            elif mem.percent > 75:
                priorities['memory'] = Priority.HIGH
            else:
                priorities['memory'] = Priority.MEDIUM

            # Disk priority
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                priorities['disk'] = Priority.CRITICAL
            elif disk.percent > 80:
                priorities['disk'] = Priority.HIGH
            else:
                priorities['disk'] = Priority.LOW

            # Network priority (based on connection count)
            try:
                connections = len(psutil.net_connections())
                priorities['network'] = Priority.HIGH if connections > 1000 else Priority.LOW
            except:
                priorities['network'] = Priority.LOW

            # Battery priority
            try:
                battery = psutil.sensors_battery()
                if battery and not battery.power_plugged:
                    if battery.percent < 20:
                        priorities['battery'] = Priority.CRITICAL
                    elif battery.percent < 40:
                        priorities['battery'] = Priority.HIGH
                    else:
                        priorities['battery'] = Priority.LOW
                else:
                    priorities['battery'] = Priority.LOW
            except:
                priorities['battery'] = Priority.LOW

            # Thermal priority
            priorities['thermal'] = Priority.MEDIUM

        except Exception as e:
            # Default priorities if assessment fails
            for cat in self.all_categories:
                priorities[cat] = Priority.MEDIUM

        return priorities

    def create_task_schedule(self, categories: List[str], priorities: Dict[str, Priority]) -> List[AgentTask]:
        """
        Create optimized task schedule.

        Args:
            categories: Categories to analyze
            priorities: Priority mapping

        Returns:
            List of scheduled tasks sorted by priority
        """
        tasks = []

        for category in categories:
            task = AgentTask(
                category=category,
                script=f"analyze_{category}.py",
                priority=priorities.get(category, Priority.MEDIUM),
                status=AgentStatus.SCHEDULED
            )
            tasks.append(task)
            self.tasks[category] = task

        # Sort by priority (highest first)
        return sorted(tasks, key=lambda t: t.priority.value, reverse=True)

    async def execute_agent(self, task: AgentTask) -> AgentTask:
        """
        Execute a single sub-agent.

        Args:
            task: Agent task to execute

        Returns:
            Updated task with results
        """
        script_path = Path(__file__).parent / task.script

        task.status = AgentStatus.RUNNING
        task.start_time = time.time()

        try:
            # Execute sub-agent
            process = await asyncio.create_subprocess_exec(
                'uv', 'run', str(script_path), '--format=toon',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=30
            )

            task.end_time = time.time()

            if process.returncode in [0, 1, 2]:
                task.status = AgentStatus.COMPLETED
                # Parse TOON output
                output = stdout.decode().strip()
                task.result = {'output': output, 'exit_code': process.returncode}
            else:
                task.status = AgentStatus.FAILED
                task.error = stderr.decode().strip()

        except asyncio.TimeoutError:
            task.status = AgentStatus.FAILED
            task.end_time = time.time()
            task.error = "Timeout after 30s"
        except Exception as e:
            task.status = AgentStatus.FAILED
            task.end_time = time.time()
            task.error = str(e)

        return task

    def print_progress_toon(self):
        """Print current progress in TOON format."""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == AgentStatus.COMPLETED)
        running = sum(1 for t in self.tasks.values() if t.status == AgentStatus.RUNNING)
        failed = sum(1 for t in self.tasks.values() if t.status == AgentStatus.FAILED)

        progress = {
            "total": total,
            "completed": completed,
            "running": running,
            "failed": failed,
            "progress": round(completed / total * 100, 1) if total > 0 else 0,
            "elapsed": round(time.time() - self.start_time, 1)
        }

        progress_toon = encode_toon(progress)
        print(f"\r📊 {progress_toon}", end="", flush=True)

    async def orchestrate_parallel(self, tasks: List[AgentTask]) -> Dict:
        """
        Orchestrate parallel execution of sub-agents with progress tracking.

        Args:
            tasks: List of tasks to execute

        Returns:
            Aggregated results
        """
        if self.verbose:
            print(f"🚀 Launching {len(tasks)} sub-agents in parallel...")
            print()

        # Execute all tasks in parallel
        task_coroutines = [self.execute_agent(task) for task in tasks]
        all_tasks = [asyncio.create_task(coro) for coro in task_coroutines]

        # Monitor progress
        while any(t.status == AgentStatus.RUNNING for t in self.tasks.values()):
            self.print_progress_toon()
            await asyncio.sleep(0.5)

        # Wait for completion
        await asyncio.gather(*all_tasks, return_exceptions=True)

        # Clear progress line
        print("\r" + " " * 100)

        # Aggregate results
        return self.aggregate_results()

    def aggregate_results(self) -> Dict:
        """
        Aggregate results from all sub-agents.

        Returns:
            Aggregated analysis results
        """
        results = {
            'total_duration': round(time.time() - self.start_time, 2),
            'categories': {},
            'issues': [],
            'recommendations': [],
            'overall_status': 'healthy',
            'overall_exit_code': 0
        }

        for category, task in self.tasks.items():
            if task.status == AgentStatus.COMPLETED:
                results['categories'][category] = {
                    'status': 'completed',
                    'duration': task.duration,
                    'exit_code': task.result.get('exit_code', 0),
                    'output': task.result.get('output', '')
                }

                # Track highest exit code
                exit_code = task.result.get('exit_code', 0)
                if exit_code > results['overall_exit_code']:
                    results['overall_exit_code'] = exit_code

                # Parse issues from TOON output
                if task.result and 'output' in task.result:
                    output = task.result['output']
                    if 'i:' in output:  # Issues present
                        results['issues'].append({
                            'category': category,
                            'severity': 'warning' if exit_code == 1 else 'critical'
                        })
                    if 'r:' in output:  # Recommendations present
                        results['recommendations'].append({
                            'category': category,
                            'has_recommendations': True
                        })

            elif task.status == AgentStatus.FAILED:
                results['categories'][category] = {
                    'status': 'failed',
                    'error': task.error
                }
                results['overall_exit_code'] = max(results['overall_exit_code'], 3)

        # Determine overall status
        if results['overall_exit_code'] >= 2:
            results['overall_status'] = 'critical'
        elif results['overall_exit_code'] == 1:
            results['overall_status'] = 'warning'

        return results

    def print_summary(self, results: Dict):
        """Print executive summary in TOON format."""
        print("✅ Analysis Complete")
        print("=" * 60)
        print()

        # Summary in TOON format
        summary = {
            "duration": results['total_duration'],
            "status": results['overall_status'],
            "categories": len(results['categories']),
            "issues": len(results['issues']),
            "recommendations": len(results['recommendations'])
        }

        print("📊 Executive Summary")
        print(encode_toon(summary))
        print()

        # Category results
        print("📋 Category Results")
        for category, data in results['categories'].items():
            if data['status'] == 'completed':
                status_emoji = "✅" if data['exit_code'] == 0 else ("⚠️" if data['exit_code'] == 1 else "🔴")
                print(f"\n{status_emoji} {category.upper()}")
                print(data['output'])
            else:
                print(f"\n❌ {category.upper()} - FAILED")
                print(f"error:{data.get('error', 'Unknown')}")

        print()

        # Overall recommendation
        if results['overall_status'] == 'critical':
            print("🔴 CRITICAL: Immediate attention required!")
        elif results['overall_status'] == 'warning':
            print("⚠️  WARNING: Some issues detected")
        else:
            print("✅ HEALTHY: System running optimally")

        print()

    async def quick_check(self) -> int:
        """
        Quick health check across all categories.

        Returns:
            Exit code (0=healthy, 1=warning, 2=critical)
        """
        self.greet()
        print("🏥 Quick Health Check")
        print()

        # Use status.py for instant check
        script_path = Path(__file__).parent / "status.py"

        try:
            process = await asyncio.create_subprocess_exec(
                'uv', 'run', str(script_path), '--format=toon',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)

            print(stdout.decode())
            return process.returncode

        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return 3

    async def full_analysis(self, categories: Optional[List[str]] = None) -> int:
        """
        Full system analysis with intelligent coordination.

        Args:
            categories: Specific categories to analyze (default: all)

        Returns:
            Exit code (0=healthy, 1=warning, 2=critical)
        """
        self.greet()

        # Determine categories
        if categories:
            target_categories = [c for c in categories if c in self.all_categories]
        else:
            target_categories = self.all_categories

        # Assess priorities
        if self.verbose:
            print("🧠 Assessing system priorities...")
        priorities = self.assess_system_priority()

        # Create schedule
        tasks = self.create_task_schedule(target_categories, priorities)

        if self.verbose:
            print(f"📋 Scheduled {len(tasks)} analysis tasks")
            for task in tasks:
                priority_emoji = "🔴" if task.priority == Priority.CRITICAL else "🟡" if task.priority == Priority.HIGH else "🟢"
                print(f"   {priority_emoji} {task.category} - {task.priority.name}")
            print()

        # Execute in parallel
        results = await self.orchestrate_parallel(tasks)

        # Print summary
        self.print_summary(results)

        return results['overall_exit_code']

    async def monitor_continuous(self, interval: int = 60):
        """
        Continuous monitoring mode.

        Args:
            interval: Check interval in seconds
        """
        self.greet()
        print(f"🔄 Continuous Monitoring (every {interval}s)")
        print("Press Ctrl+C to stop")
        print()

        try:
            iteration = 0
            while True:
                iteration += 1
                print(f"\n{'=' * 60}")
                print(f"Iteration #{iteration} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'=' * 60}\n")

                await self.full_analysis()

                print(f"\n⏰ Next check in {interval} seconds...")
                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped")
            return 0


async def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Alfred - Central Resource Optimizer Coordinator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  alfred.py --quick              # Quick health check
  alfred.py --analyze            # Full system analysis
  alfred.py --monitor            # Continuous monitoring
  alfred.py --categories cpu,memory  # Specific categories
        """
    )

    parser.add_argument('--quick', action='store_true',
                        help='Quick health check (fast)')
    parser.add_argument('--analyze', action='store_true',
                        help='Full system analysis (comprehensive)')
    parser.add_argument('--monitor', action='store_true',
                        help='Continuous monitoring mode')
    parser.add_argument('--categories', type=str,
                        help='Comma-separated categories (cpu,memory,disk,network,battery,thermal)')
    parser.add_argument('--interval', type=int, default=60,
                        help='Monitoring interval in seconds (default: 60)')
    parser.add_argument('--quiet', action='store_true',
                        help='Minimal output')
    parser.add_argument('--json', action='store_true',
                        help='Output in JSON format instead of TOON')

    args = parser.parse_args()

    # Create Alfred instance
    alfred = Alfred(verbose=not args.quiet)

    # Determine mode
    if args.quick:
        return await alfred.quick_check()
    elif args.monitor:
        return await alfred.monitor_continuous(args.interval)
    else:
        # Default to full analysis
        categories = None
        if args.categories:
            categories = [c.strip() for c in args.categories.split(',')]
        return await alfred.full_analysis(categories)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
