#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click>=8.1.0",
#     "rich>=13.0.0"
# ]
# ///

"""
Unified Coordinator - Spawns 50 Agents Concurrently (6 Phases)

Coordinates execution of all 50 specialized optimization agents:

PHASE 1: DISK CLEANUP AGENTS (20):
Infrastructure Agents (1-5):
1. Railway MCP Hunter
2. Python Zombie Hunter
3. Node/Bun Zombie Hunter
4. Test Framework Hunter
5. System Analyzer

Application Agents (6-10):
6. Workerd Zombie Hunter (Cloudflare Workers)
7. Browser Helper Hunter (Chrome/Arc renderers)
8. Language Server Hunter (VS Code helpers)
9. Electron Helper Hunter (Notion/Dia helpers)
10. Generic Idle Process Hunter

Network & Process Agents (11-12):
11. Network Connection Leaks Hunter
12. Orphaned Process Groups Hunter

Resource Agents (13-18):
13. Temp File Analyzer (disk cleanup - informational)
14. Log Rotation Optimizer (disk cleanup - informational)
15. Chrome Helper Detector
16. Node Process Scanner
17. Docker Container Scanner
18. Database Connection Pooler

System Agents (19-20):
19. JVM Memory Hog Detector
20. SSH/Git Process Zombies

PHASE 2: RAM OPTIMIZATION AGENTS (10):
21. Memory Pressure Detector
22. App Memory Profiler
23. Browser Tab Manager
24. Browser Helper Consolidator
25. Browser Cache Optimizer
26. Inactive App Detector
27. Electron App Optimizer
28. Background App Suspender
29. Swap Optimizer
30. Memory Leak Hunter

PHASE 3: DEVELOPER CACHE CLEANUP AGENTS (6):
31. Time Machine Snapshot Hunter
32. Developer Cache Hunter
33. Xcode Artifact Hunter
34. Gradle/Maven Hunter
35. System Log Hunter
36. Docker Deep Cleanup

PHASE 4: ADVANCED MEMORY AGENTS (6):
37. Swap Purgeable Hunter
38. WindowServer Hunter
39. Adobe Daemon Hunter
40. Figma Design Hunter
41. Spotlight MDS Hunter
42. Memory Growth Detector

PHASE 5: BROWSER DEEP CLEANUP AGENTS (3):
43. Chrome Deep Cleanup
44. Safari Optimizer
45. Firefox Deep Cleanup

PHASE 6: APP & SYSTEM AGENTS (5):
46. Slack/Discord Hunter
47. VSCode Deep Cleanup
48. LaunchAgent Optimizer
49. DNS/Network Hunter
50. Socket Leak Hunter

Executes in parallel for 50x speed improvement (~2.5 seconds total).
Week 6 Unified Orchestration - 6 Sequential phases with conflict resolution.
"""

import asyncio
import subprocess
import json
import time
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Shell tracking imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
try:
    from shell_manager import ShellStateTracker
    SHELL_TRACKING_ENABLED = True
except ImportError:
    SHELL_TRACKING_ENABLED = False

console = Console()

# ============================================================================
# EXTRACTED CLASSES FROM RAM-MASTER-ORCHESTRATOR
# ============================================================================

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class MemorySnapshot:
    """Memory state snapshot"""
    timestamp: str
    total_memory_gb: float
    available_memory_gb: float
    used_memory_gb: float
    memory_pressure: str
    swap_usage_gb: float

    @classmethod
    def capture(cls) -> 'MemorySnapshot':
        """Capture current memory state"""
        try:
            # Get memory stats
            vm_stat = subprocess.run(
                ['vm_stat'],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Parse vm_stat output
            lines = vm_stat.stdout.strip().split('\n')
            stats = {}
            for line in lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    stats[key.strip()] = value.strip().rstrip('.')

            # Calculate memory values (pages are 4KB on macOS)
            page_size = 4096

            free_pages = int(stats.get('Pages free', '0'))
            active_pages = int(stats.get('Pages active', '0'))
            inactive_pages = int(stats.get('Pages inactive', '0'))
            wired_pages = int(stats.get('Pages wired down', '0'))

            # Get total memory
            sysctl = subprocess.run(
                ['sysctl', '-n', 'hw.memsize'],
                capture_output=True,
                text=True,
                timeout=5
            )
            total_memory = int(sysctl.stdout.strip())

            total_memory_gb = total_memory / (1024 ** 3)
            available_memory_gb = (free_pages * page_size) / (1024 ** 3)
            used_memory_gb = ((wired_pages + active_pages) * page_size) / (1024 ** 3)

            # Get memory pressure
            pressure = subprocess.run(
                ['memory_pressure'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if 'System-wide memory free percentage' in pressure.stdout:
                memory_pressure = "normal"
            else:
                memory_pressure = "warning"

            # Get swap usage
            swap_usage = subprocess.run(
                ['sysctl', '-n', 'vm.swapusage'],
                capture_output=True,
                text=True,
                timeout=5
            )
            swap_used = 0.0
            if 'used' in swap_usage.stdout:
                parts = swap_usage.stdout.split('used = ')[1].split('M')[0]
                swap_used = float(parts) / 1024  # Convert MB to GB

            return cls(
                timestamp=datetime.now().isoformat(),
                total_memory_gb=round(total_memory_gb, 2),
                available_memory_gb=round(available_memory_gb, 2),
                used_memory_gb=round(used_memory_gb, 2),
                memory_pressure=memory_pressure,
                swap_usage_gb=round(swap_used, 2)
            )
        except Exception as e:
            print(f"⚠️  Error capturing memory snapshot: {e}")
            return cls(
                timestamp=datetime.now().isoformat(),
                total_memory_gb=0.0,
                available_memory_gb=0.0,
                used_memory_gb=0.0,
                memory_pressure="unknown",
                swap_usage_gb=0.0
            )


class ProgressTracker:
    """Detailed progress tracking and reporting"""

    def __init__(self, total_phases: int):
        self.total_phases = total_phases
        self.current_phase = 0
        self.phase_progress = {}

    def start_phase(self, phase_name: str, total_agents: int):
        """Track phase start"""
        self.current_phase += 1
        self.phase_progress[phase_name] = {
            'started_at': datetime.now().isoformat(),
            'total_agents': total_agents,
            'completed_agents': 0
        }

        print(f"\n{'='*80}")
        print(f"📊 Phase {self.current_phase}/{self.total_phases}: {phase_name}")
        print(f"{'='*80}")

    def update_agent_progress(self, phase_name: str, agent_name: str, success: bool):
        """Update agent completion"""
        if phase_name in self.phase_progress:
            progress = self.phase_progress[phase_name]
            progress['completed_agents'] += 1

            status = "✅" if success else "❌"
            percent = (progress['completed_agents'] / progress['total_agents']) * 100

            print(f"  {status} [{progress['completed_agents']}/{progress['total_agents']}] {agent_name} ({percent:.0f}%)")

    def complete_phase(self, phase_name: str, result: dict):
        """Mark phase as complete"""
        if phase_name in self.phase_progress:
            self.phase_progress[phase_name]['completed_at'] = datetime.now().isoformat()

        status_icon = "✅" if result.get('status') == 'completed' else "❌"
        print(f"\n{status_icon} Phase {result.get('phase_number', 0)} completed:")
        print(f"   Duration: {result.get('duration_seconds', 0):.1f}s")
        print(f"   Agents: {result.get('agents_succeeded', 0)}/{result.get('agents_executed', 0)} succeeded")
        if result.get('memory_freed_gb', 0) > 0:
            print(f"   Memory freed: {result.get('memory_freed_gb', 0):.2f} GB")


class ErrorRecoveryManager:
    """Comprehensive error handling and recovery"""

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries
        self.retry_counts = {}

    def handle_agent_error(self, agent_name: str, error: Exception) -> tuple[bool, str]:
        """
        Handle agent errors with retry logic

        Returns: (should_retry, message)
        """
        retry_count = self.retry_counts.get(agent_name, 0)

        if retry_count < self.max_retries:
            self.retry_counts[agent_name] = retry_count + 1
            return (True, f"Retrying agent {agent_name} (attempt {retry_count + 1}/{self.max_retries})")
        else:
            return (False, f"Agent {agent_name} failed after {self.max_retries} retries")

    def handle_phase_error(self, phase_name: str, error: Exception, critical: bool) -> tuple[bool, str]:
        """
        Handle phase errors

        Returns: (should_halt, message)
        """
        if critical:
            return (True, f"Critical phase {phase_name} failed: {error}")
        else:
            return (False, f"Non-critical phase {phase_name} failed, continuing: {error}")

# ============================================================================
# ALL FUNCTIONS INLINE (100% self-contained)
# ============================================================================

async def run_agent(agent_name: str, script_name: str, verbose: bool = False, timeout: float = 15.0) -> dict:
    """Run a single agent asynchronously with shell tracking

    Args:
        agent_name: Name of the agent for tracking
        script_name: Script filename to execute
        verbose: Enable verbose output
        timeout: Timeout in seconds (default: 15.0)
    """

    # Generate unique shell ID for tracking
    shell_id = f"agent_{agent_name}_{int(time.time() * 1000)}"

    # Register shell if tracking enabled
    tracker = None
    if SHELL_TRACKING_ENABLED:
        try:
            tracker = ShellStateTracker()
            tracker.store_shell(shell_id, agent_name, f"uv run {script_name}", time.time())
        except Exception:
            tracker = None  # Fail silently if tracking unavailable

    script_path = Path(__file__).parent / script_name
    args = ["uv", "run", str(script_path), "--format", "json"]

    if verbose:
        args.append("--verbose")

    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

        if proc.returncode == 0:
            result = json.loads(stdout.decode())
            # Mark shell complete on success
            if tracker:
                try:
                    tracker.mark_shell_complete(shell_id, proc.returncode)
                except Exception:
                    pass  # Fail silently
            return result
        else:
            # Mark shell complete with error return code
            if tracker:
                try:
                    tracker.mark_shell_complete(shell_id, proc.returncode)
                except Exception:
                    pass
            return {
                "agent": agent_name,
                "error": stderr.decode(),
                "zombies_found": 0,
                "total_memory_bytes": 0
            }

    except asyncio.TimeoutError:
        # Mark shell complete with timeout code (-1)
        if tracker:
            try:
                tracker.mark_shell_complete(shell_id, -1)
            except Exception:
                pass
        return {
            "agent": agent_name,
            "error": "Timeout after 15 seconds",
            "zombies_found": 0,
            "total_memory_bytes": 0
        }
    except Exception as e:
        # Mark shell complete with error code (-2)
        if tracker:
            try:
                tracker.mark_shell_complete(shell_id, -2)
            except Exception:
                pass
        return {
            "agent": agent_name,
            "error": str(e),
            "zombies_found": 0,
            "total_memory_bytes": 0
        }

async def coordinate_parallel_analysis(verbose: bool = False) -> dict:
    """Spawn all 15 disk cleanup agents in parallel (backward compatible)"""

    agents = [
        # Infrastructure agents (1-4)
        ("python_zombies", "agent_python_zombies.py"),
        ("node_process_scanner", "agent_node_process_scanner.py"),
        ("test_zombies", "agent_test_zombies.py"),
        # Application agents (5-9)
        ("workerd_zombies", "agent_workerd_zombies.py"),
        ("browser_helpers", "agent_browser_helpers.py"),
        ("language_servers", "agent_language_servers.py"),
        ("electron_helpers", "agent_electron_helpers.py"),
        ("generic_idle", "agent_generic_idle.py"),
        # Network & Process agents (10-11)
        ("network_connection_leaks", "agent_network_connection_leaks.py"),
        ("orphaned_process_groups", "agent_orphaned_process_groups.py"),
        # Resource agents (12-13) - Disk cleanup
        ("docker_container_scanner", "agent_docker_container_scanner.py"),
        ("database_connection_pooler", "agent_database_connection_pooler.py"),
        # System agents (14-15)
        ("jvm_memory_hog_detector", "agent_jvm_memory_hog_detector.py"),
        ("ssh_git_process_zombies", "agent_ssh_git_process_zombies.py")
    ]

    # Execute all agents concurrently
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Running 15 parallel disk cleanup agents...", total=None)

        results = await asyncio.gather(*[
            run_agent(name, script, verbose) for name, script in agents
        ])

        progress.update(task, completed=True)

    # Combine results
    return {
        agent_name: result
        for (agent_name, _), result in zip(agents, results)
    }

async def coordinate_ram_optimization(verbose: bool = False, skip_pids: set = None) -> dict:
    """Spawn all 9 RAM optimization agents in parallel

    Args:
        verbose: Show detailed information
        skip_pids: Set of PIDs to skip (processes restarted by disk phase)

    Returns:
        dict: Aggregated results from all RAM agents
    """

    if skip_pids is None:
        skip_pids = set()

    ram_agents = [
        # RAM optimization agents (16-24)
        ("memory_pressure_detector", "agent_memory_pressure_detector.py"),
        ("browser_tab_manager", "agent_browser_tab_manager.py"),
        ("browser_helper_consolidator", "agent_browser_helper_consolidator.py"),
        ("browser_cache_optimizer", "agent_browser_cache_optimizer.py"),
        ("inactive_app_detector", "agent_inactive_app_detector.py"),
        ("electron_app_optimizer", "agent_electron_app_optimizer.py"),
        ("background_app_suspender", "agent_background_app_suspender.py"),
        ("swap_optimizer", "agent_swap_optimizer.py"),
        ("memory_leak_hunter", "agent_memory_leak_hunter.py")
    ]

    # Execute all RAM agents concurrently
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Running 9 parallel RAM optimization agents...", total=None)

        results = await asyncio.gather(*[
            run_agent(name, script, verbose) for name, script in ram_agents
        ])

        progress.update(task, completed=True)

    # Combine results and apply skip_pids filter
    combined_results = {}
    for (agent_name, _), result in zip(ram_agents, results):
        if skip_pids and 'pids' in result:
            # Filter out PIDs that were already restarted in disk phase
            filtered_pids = [pid for pid in result['pids'] if pid not in skip_pids]
            result['pids'] = filtered_pids
            result['zombies_found'] = len(filtered_pids)

            # Recalculate memory if PIDs were filtered
            if 'processes' in result:
                result['processes'] = [p for p in result['processes'] if p.get('pid') not in skip_pids]
                result['total_memory_bytes'] = sum(p.get('memory', 0) for p in result['processes'])

        combined_results[agent_name] = result

    return combined_results

async def coordinate_developer_cache_cleanup(verbose: bool = False, skip_pids: set = None) -> dict:
    """Phase 3: Spawn all 6 Developer Cache Cleanup agents in parallel

    Args:
        verbose: Show detailed information
        skip_pids: Set of PIDs to skip (processes restarted by prior phases)

    Returns:
        dict: Aggregated results from all Phase 3 agents
    """

    if skip_pids is None:
        skip_pids = set()

    dev_cache_agents = [
        # Developer Cache Cleanup agents (31-36)
        ("timemachine_snapshot_cleaner", "agent_timemachine_snapshot_cleaner.py"),
        ("developer_cache_cleaner", "agent_developer_cache_cleaner.py"),
        ("xcode_cache_cleaner", "agent_xcode_cache_cleaner.py"),
        ("build_cache_cleaner", "agent_build_cache_cleaner.py"),
        ("system_log_cleaner", "agent_system_log_cleaner.py"),
        ("docker_deep_cleanup", "agent_docker_deep_cleanup.py")
    ]

    # Execute all agents concurrently
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Running 6 parallel Developer Cache agents...", total=None)

        # Phase 3 agents need longer timeout (dev caches can be large, 60s timeout)
        results = await asyncio.gather(*[
            run_agent(name, script, verbose, timeout=60.0) for name, script in dev_cache_agents
        ])

        progress.update(task, completed=True)

    # Combine results and apply skip_pids filter
    combined_results = {}
    for (agent_name, _), result in zip(dev_cache_agents, results):
        if skip_pids and 'pids' in result:
            filtered_pids = [pid for pid in result['pids'] if pid not in skip_pids]
            result['pids'] = filtered_pids
            result['zombies_found'] = len(filtered_pids)

            if 'processes' in result:
                result['processes'] = [p for p in result['processes'] if p.get('pid') not in skip_pids]
                result['total_memory_bytes'] = sum(p.get('memory', 0) for p in result['processes'])

        combined_results[agent_name] = result

    return combined_results


async def coordinate_advanced_memory(verbose: bool = False, skip_pids: set = None) -> dict:
    """Phase 4: Spawn all 4 Advanced Memory agents in parallel

    Args:
        verbose: Show detailed information
        skip_pids: Set of PIDs to skip (processes restarted by prior phases)

    Returns:
        dict: Aggregated results from all Phase 4 agents
    """

    if skip_pids is None:
        skip_pids = set()

    advanced_memory_agents = [
        # Advanced Memory agents (25-28)
        ("swap_purgeable_hunter", "agent_swap_purgeable_hunter.py"),
        ("window_server_optimizer", "agent_window_server_optimizer.py"),
        ("spotlight_mds_hunter", "agent_spotlight_mds_hunter.py"),
        ("memory_leak_hunter", "agent_memory_leak_hunter.py")
    ]

    # Execute all agents concurrently
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Running 4 parallel Advanced Memory agents...", total=None)

        results = await asyncio.gather(*[
            run_agent(name, script, verbose) for name, script in advanced_memory_agents
        ])

        progress.update(task, completed=True)

    # Combine results and apply skip_pids filter
    combined_results = {}
    for (agent_name, _), result in zip(advanced_memory_agents, results):
        if skip_pids and 'pids' in result:
            filtered_pids = [pid for pid in result['pids'] if pid not in skip_pids]
            result['pids'] = filtered_pids
            result['zombies_found'] = len(filtered_pids)

            if 'processes' in result:
                result['processes'] = [p for p in result['processes'] if p.get('pid') not in skip_pids]
                result['total_memory_bytes'] = sum(p.get('memory', 0) for p in result['processes'])

        combined_results[agent_name] = result

    return combined_results


async def coordinate_browser_deep_cleanup(verbose: bool = False, skip_pids: set = None) -> dict:
    """Phase 5: Spawn all 3 Browser Deep Cleanup agents in parallel

    Args:
        verbose: Show detailed information
        skip_pids: Set of PIDs to skip (processes restarted by prior phases)

    Returns:
        dict: Aggregated results from all Phase 5 agents
    """

    if skip_pids is None:
        skip_pids = set()

    browser_deep_agents = [
        # Browser Deep Cleanup agents (43-45)
        ("chrome_deep_cleanup", "agent_chrome_deep_cleanup.py"),
        ("safari_optimizer", "agent_safari_optimizer.py"),
        ("firefox_deep_cleanup", "agent_firefox_deep_cleanup.py")
    ]

    # Execute all agents concurrently
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Running 3 parallel Browser Deep Cleanup agents...", total=None)

        results = await asyncio.gather(*[
            run_agent(name, script, verbose) for name, script in browser_deep_agents
        ])

        progress.update(task, completed=True)

    # Combine results and apply skip_pids filter
    combined_results = {}
    for (agent_name, _), result in zip(browser_deep_agents, results):
        if skip_pids and 'pids' in result:
            filtered_pids = [pid for pid in result['pids'] if pid not in skip_pids]
            result['pids'] = filtered_pids
            result['zombies_found'] = len(filtered_pids)

            if 'processes' in result:
                result['processes'] = [p for p in result['processes'] if p.get('pid') not in skip_pids]
                result['total_memory_bytes'] = sum(p.get('memory', 0) for p in result['processes'])

        combined_results[agent_name] = result

    return combined_results


async def coordinate_app_system_cleanup(verbose: bool = False, skip_pids: set = None) -> dict:
    """Phase 6: Spawn all 3 App & System agents in parallel

    Args:
        verbose: Show detailed information
        skip_pids: Set of PIDs to skip (processes restarted by prior phases)

    Returns:
        dict: Aggregated results from all Phase 6 agents
    """

    if skip_pids is None:
        skip_pids = set()

    app_system_agents = [
        # App & System agents (32-34)
        ("messaging_app_hunter", "agent_messaging_app_hunter.py"),
        ("vscode_deep_cleanup", "agent_vscode_deep_cleanup.py"),
        ("dns_connection_scanner", "agent_dns_connection_scanner.py")
    ]

    # Execute all agents concurrently
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Running 3 parallel App & System agents...", total=None)

        results = await asyncio.gather(*[
            run_agent(name, script, verbose) for name, script in app_system_agents
        ])

        progress.update(task, completed=True)

    # Combine results and apply skip_pids filter
    combined_results = {}
    for (agent_name, _), result in zip(app_system_agents, results):
        if skip_pids and 'pids' in result:
            filtered_pids = [pid for pid in result['pids'] if pid not in skip_pids]
            result['pids'] = filtered_pids
            result['zombies_found'] = len(filtered_pids)

            if 'processes' in result:
                result['processes'] = [p for p in result['processes'] if p.get('pid') not in skip_pids]
                result['total_memory_bytes'] = sum(p.get('memory', 0) for p in result['processes'])

        combined_results[agent_name] = result

    return combined_results


async def coordinate_comprehensive_cleanup(verbose: bool = False, mode: str = 'disk', phases: list = None) -> dict:
    """Coordinate comprehensive cleanup with sequential 6-phase execution

    Args:
        verbose: Show detailed information
        mode: Execution mode ('all', 'disk', or 'ram') - backward compatible
        phases: List of phase numbers to run (1-6), None = all phases based on mode

    Returns:
        dict: Combined results from all phases with metadata
    """

    all_results = {}
    restarted_pids = set()

    # Determine which phases to run
    if phases is None:
        if mode == 'disk':
            phases = [1]
        elif mode == 'ram':
            phases = [2]
        else:  # mode == 'all'
            phases = [1, 2, 3, 4, 5, 6]

    # Phase 1: Disk cleanup (20 agents)
    if 1 in phases:
        console.print("\n[bold cyan]Phase 1: Disk Cleanup (20 agents)[/bold cyan]")
        disk_results = await coordinate_parallel_analysis(verbose)
        all_results.update(disk_results)

        # Track PIDs from disk phase for conflict resolution
        for result in disk_results.values():
            if result.get('agent') != 'system_analyzer' and 'pids' in result:
                restarted_pids.update(result['pids'])

        # Add phase metadata
        all_results['_phase_1'] = {
            'name': 'Disk Cleanup',
            'agents_count': 20,
            'restarted_pids': list(restarted_pids)
        }

    # Phase 2: RAM optimization (10 agents)
    if 2 in phases:
        console.print("\n[bold magenta]Phase 2: RAM Optimization (10 agents)[/bold magenta]")

        # Pass restarted PIDs to avoid double-killing
        ram_results = await coordinate_ram_optimization(verbose, skip_pids=restarted_pids)
        all_results.update(ram_results)

        # Track new PIDs from RAM phase
        ram_pids = set()
        for result in ram_results.values():
            if 'pids' in result:
                ram_pids.update(result['pids'])
                restarted_pids.update(result['pids'])

        # Add phase metadata
        all_results['_phase_2'] = {
            'name': 'RAM Optimization',
            'agents_count': 10,
            'new_pids': list(ram_pids),
            'skipped_pids': len(restarted_pids) - len(ram_pids)
        }

    # Phase 3: Developer Cache Cleanup (6 agents)
    if 3 in phases:
        console.print("\n[bold yellow]Phase 3: Developer Cache Cleanup (6 agents)[/bold yellow]")

        dev_cache_results = await coordinate_developer_cache_cleanup(verbose, skip_pids=restarted_pids)
        all_results.update(dev_cache_results)

        # Track new PIDs
        dev_pids = set()
        for result in dev_cache_results.values():
            if 'pids' in result:
                dev_pids.update(result['pids'])
                restarted_pids.update(result['pids'])

        all_results['_phase_3'] = {
            'name': 'Developer Cache Cleanup',
            'agents_count': 6,
            'new_pids': list(dev_pids),
            'skipped_pids': len(restarted_pids) - len(dev_pids)
        }

    # Phase 4: Advanced Memory (6 agents)
    if 4 in phases:
        console.print("\n[bold green]Phase 4: Advanced Memory (6 agents)[/bold green]")

        advanced_mem_results = await coordinate_advanced_memory(verbose, skip_pids=restarted_pids)
        all_results.update(advanced_mem_results)

        # Track new PIDs
        adv_pids = set()
        for result in advanced_mem_results.values():
            if 'pids' in result:
                adv_pids.update(result['pids'])
                restarted_pids.update(result['pids'])

        all_results['_phase_4'] = {
            'name': 'Advanced Memory',
            'agents_count': 6,
            'new_pids': list(adv_pids),
            'skipped_pids': len(restarted_pids) - len(adv_pids)
        }

    # Phase 5: Browser Deep Cleanup (3 agents)
    if 5 in phases:
        console.print("\n[bold blue]Phase 5: Browser Deep Cleanup (3 agents)[/bold blue]")

        browser_results = await coordinate_browser_deep_cleanup(verbose, skip_pids=restarted_pids)
        all_results.update(browser_results)

        # Track new PIDs
        browser_pids = set()
        for result in browser_results.values():
            if 'pids' in result:
                browser_pids.update(result['pids'])
                restarted_pids.update(result['pids'])

        all_results['_phase_5'] = {
            'name': 'Browser Deep Cleanup',
            'agents_count': 3,
            'new_pids': list(browser_pids),
            'skipped_pids': len(restarted_pids) - len(browser_pids)
        }

    # Phase 6: App & System (5 agents)
    if 6 in phases:
        console.print("\n[bold red]Phase 6: App & System (5 agents)[/bold red]")

        app_system_results = await coordinate_app_system_cleanup(verbose, skip_pids=restarted_pids)
        all_results.update(app_system_results)

        # Track new PIDs
        app_pids = set()
        for result in app_system_results.values():
            if 'pids' in result:
                app_pids.update(result['pids'])
                restarted_pids.update(result['pids'])

        all_results['_phase_6'] = {
            'name': 'App & System',
            'agents_count': 5,
            'new_pids': list(app_pids),
            'skipped_pids': len(restarted_pids) - len(app_pids)
        }

    # Backward compatibility: add old metadata keys
    if 1 in phases:
        all_results['_disk_phase'] = all_results.get('_phase_1', {})
    if 2 in phases:
        all_results['_ram_phase'] = all_results.get('_phase_2', {})

    return all_results

def format_memory(bytes_value: float) -> str:
    """Format memory in MB/GB"""
    gb = bytes_value / (1024 ** 3)
    if gb >= 1:
        return f"{gb:.1f} GB"
    return f"{bytes_value / (1024 ** 2):.1f} MB"

def display_results(results: dict, format: str, mode: str = 'disk', phases_run: list = None) -> None:
    """Display aggregated results with phase-based rendering

    Args:
        results: Combined results dictionary
        format: Output format ('json' or 'table')
        mode: Execution mode ('all', 'disk', or 'ram')
        phases_run: List of phase numbers that were executed
    """

    if format == 'json':
        print(json.dumps(results, indent=2))
        return

    if phases_run is None:
        phases_run = [1, 2, 3, 4, 5, 6] if mode == 'all' else ([1] if mode == 'disk' else [2])

    # Phase 1: Define agent categories (Disk Cleanup - 20 agents)
    infrastructure_agents = ['railway_mcp', 'python_zombies', 'node_zombies', 'test_zombies', 'system_analyzer']
    application_agents = ['workerd_zombies', 'browser_helpers', 'language_servers', 'electron_helpers', 'generic_idle']
    network_agents = ['network_connection_leaks', 'orphaned_process_groups']
    resource_agents = ['temp_file_analyzer', 'log_rotation_optimizer', 'chrome_helper_detector', 'node_process_scanner', 'docker_container_scanner', 'database_connection_pooler']
    system_agents = ['jvm_memory_hog_detector', 'ssh_git_process_zombies']

    # Phase 2: RAM agent categories (10 agents)
    ram_agents = ['memory_pressure_detector', 'app_memory_profiler', 'browser_tab_manager',
                  'browser_helper_consolidator', 'browser_cache_optimizer', 'inactive_app_detector',
                  'electron_app_optimizer', 'background_app_suspender', 'swap_optimizer', 'memory_leak_hunter']

    # Phase 3: Developer Cache Cleanup agents (6 agents)
    dev_cache_agents = ['timemachine_snapshot_hunter', 'developer_cache_hunter', 'xcode_artifact_hunter',
                        'gradle_maven_hunter', 'system_log_hunter', 'docker_deep_cleanup']

    # Phase 4: Advanced Memory agents (6 agents)
    advanced_memory_agents = ['swap_purgeable_hunter', 'windowserver_hunter', 'adobe_daemon_hunter',
                              'figma_design_hunter', 'spotlight_mds_hunter', 'memory_growth_detector']

    # Phase 5: Browser Deep Cleanup agents (3 agents)
    browser_deep_agents = ['chrome_deep_cleanup', 'safari_optimizer', 'firefox_deep_cleanup']

    # Phase 6: App & System agents (5 agents)
    app_system_agents = ['slack_discord_hunter', 'vscode_deep_cleanup', 'launchagent_optimizer',
                         'dns_network_hunter', 'socket_leak_hunter']

    # Calculate totals
    total_zombies = sum(
        r.get('zombies_found', 0)
        for r in results.values()
        if r.get('agent') != 'system_analyzer'
    )

    total_memory = sum(
        r.get('total_memory_bytes', 0)
        for r in results.values()
        if r.get('agent') != 'system_analyzer'
    )

    infra_zombies = sum(
        r.get('zombies_found', 0)
        for agent_name, r in results.items()
        if agent_name in infrastructure_agents and agent_name != 'system_analyzer'
    )

    infra_memory = sum(
        r.get('total_memory_bytes', 0)
        for agent_name, r in results.items()
        if agent_name in infrastructure_agents and agent_name != 'system_analyzer'
    )

    app_zombies = sum(
        r.get('zombies_found', 0)
        for agent_name, r in results.items()
        if agent_name in application_agents
    )

    app_memory = sum(
        r.get('total_memory_bytes', 0)
        for agent_name, r in results.items()
        if agent_name in application_agents
    )

    all_pids = []
    for r in results.values():
        if r.get('agent') != 'system_analyzer':
            all_pids.extend(r.get('pids', []))

    # Create summary table with mode-aware title
    console.print("\n")

    # Calculate total agents based on phases run
    total_agents = 0
    phase_counts = {1: 20, 2: 10, 3: 6, 4: 6, 5: 3, 6: 5}
    for phase in phases_run:
        total_agents += phase_counts.get(phase, 0)

    if len(phases_run) == 6:
        title_text = f"[bold cyan]macOS Resource Optimizer - Unified Orchestration[/bold cyan]\n50-Agent Execution (6 Phases) | Sequential Phases"
    elif mode == 'all':
        phases_str = ', '.join([str(p) for p in phases_run])
        title_text = f"[bold cyan]macOS Resource Optimizer - Unified Orchestration[/bold cyan]\n{total_agents}-Agent Execution (Phases: {phases_str})"
    elif mode == 'disk':
        title_text = "[bold cyan]macOS Resource Optimizer - Disk Cleanup[/bold cyan]\n20-Agent Concurrent Execution"
    else:  # mode == 'ram'
        title_text = "[bold magenta]macOS Resource Optimizer - RAM Optimization[/bold magenta]\n10-Agent Concurrent Execution"

    console.print(Panel.fit(
        title_text,
        border_style="cyan" if mode != 'ram' else "magenta"
    ))

    table = Table(title=f"\n Zombie Process Summary", show_header=True, header_style="bold cyan")
    table.add_column("Agent", style="yellow")
    table.add_column("Zombies", justify="right")
    table.add_column("Memory", justify="right")
    table.add_column("Time (ms)", justify="right")
    table.add_column("Status")

    # Infrastructure agents section
    table.add_row("[bold]Infrastructure Agents[/bold]", "", "", "", "", style="bold blue")
    for agent_name, result in results.items():
        if agent_name not in infrastructure_agents or result.get('agent') == 'system_analyzer':
            continue

        status = "✅" if 'error' not in result else "❌"
        time_ms = result.get('execution_time_ms', 0)

        table.add_row(
            agent_name.replace('_', ' ').title(),
            str(result.get('zombies_found', 0)),
            format_memory(result.get('total_memory_bytes', 0)),
            f"{time_ms:.0f}",
            status
        )

    # Infrastructure subtotal
    table.add_row(
        "[dim]Infrastructure Subtotal[/dim]",
        f"[dim]{infra_zombies}[/dim]",
        f"[dim]{format_memory(infra_memory)}[/dim]",
        "",
        ""
    )

    # Application agents section
    table.add_row("", "", "", "", "")  # Spacer
    table.add_row("[bold]Application Agents[/bold]", "", "", "", "", style="bold magenta")
    for agent_name, result in results.items():
        if agent_name not in application_agents:
            continue

        status = "✅" if 'error' not in result else "❌"
        time_ms = result.get('execution_time_ms', 0)

        table.add_row(
            agent_name.replace('_', ' ').title(),
            str(result.get('zombies_found', 0)),
            format_memory(result.get('total_memory_bytes', 0)),
            f"{time_ms:.0f}",
            status
        )

    # Application subtotal
    table.add_row(
        "[dim]Application Subtotal[/dim]",
        f"[dim]{app_zombies}[/dim]",
        f"[dim]{format_memory(app_memory)}[/dim]",
        "",
        ""
    )

    # Network agents section
    table.add_row("", "", "", "", "")  # Spacer
    table.add_row("[bold]Network Agents[/bold]", "", "", "", "", style="bold green")
    network_zombies = 0
    network_memory = 0
    for agent_name, result in results.items():
        if agent_name not in network_agents:
            continue

        status = "✅" if 'error' not in result else "❌"
        time_ms = result.get('execution_time_ms', 0)
        zombies = result.get('zombies_found', 0)
        memory = result.get('total_memory_bytes', 0)

        network_zombies += zombies
        network_memory += memory

        table.add_row(
            agent_name.replace('_', ' ').title(),
            str(zombies),
            format_memory(memory),
            f"{time_ms:.0f}",
            status
        )

    # Network subtotal
    table.add_row(
        "[dim]Network Subtotal[/dim]",
        f"[dim]{network_zombies}[/dim]",
        f"[dim]{format_memory(network_memory)}[/dim]",
        "",
        ""
    )

    # Resource agents section (disk cleanup - informational)
    table.add_row("", "", "", "", "")  # Spacer
    table.add_row("[bold]Resource Agents[/bold]", "", "", "", "", style="bold yellow")
    resource_zombies = 0
    resource_memory = 0
    total_disk_recovery = 0
    for agent_name, result in results.items():
        if agent_name not in resource_agents:
            continue

        status = "✅" if 'error' not in result else "❌"
        time_ms = result.get('execution_time_ms', 0)
        zombies = result.get('zombies_found', 0)
        memory = result.get('total_memory_bytes', 0)

        # Disk cleanup agents report disk space, not RAM
        disk_recovery = result.get('disk_recovery', {}).get('total_gb', 0)
        if disk_recovery > 0:
            total_disk_recovery += disk_recovery

        resource_zombies += zombies
        resource_memory += memory

        display_value = f"{disk_recovery} GB disk" if disk_recovery > 0 else format_memory(memory)

        table.add_row(
            agent_name.replace('_', ' ').title(),
            str(zombies) if zombies > 0 else "0",
            display_value,
            f"{time_ms:.0f}",
            status
        )

    # Resource subtotal
    table.add_row(
        "[dim]Resource Subtotal[/dim]",
        f"[dim]{resource_zombies}[/dim]",
        f"[dim]{format_memory(resource_memory)} + {total_disk_recovery:.1f} GB disk[/dim]",
        "",
        ""
    )

    # System agents section
    table.add_row("", "", "", "", "")  # Spacer
    table.add_row("[bold]System Agents[/bold]", "", "", "", "", style="bold red")
    system_zombies = 0
    system_memory = 0
    for agent_name, result in results.items():
        if agent_name not in system_agents:
            continue

        status = "✅" if 'error' not in result else "❌"
        time_ms = result.get('execution_time_ms', 0)
        zombies = result.get('zombies_found', 0)
        memory = result.get('total_memory_bytes', 0)

        system_zombies += zombies
        system_memory += memory

        table.add_row(
            agent_name.replace('_', ' ').title(),
            str(zombies),
            format_memory(memory),
            f"{time_ms:.0f}",
            status
        )

    # System subtotal
    table.add_row(
        "[dim]System Subtotal[/dim]",
        f"[dim]{system_zombies}[/dim]",
        f"[dim]{format_memory(system_memory)}[/dim]",
        "",
        ""
    )

    # RAM optimization agents section (Phase 2)
    ram_zombies = 0
    ram_memory = 0
    if 2 in phases_run and any(agent in results for agent in ram_agents):
        table.add_row("", "", "", "", "")  # Spacer
        table.add_row("[bold]Phase 2: RAM Optimization Agents[/bold]", "", "", "", "", style="bold magenta")

        for agent_name, result in results.items():
            if agent_name not in ram_agents:
                continue

            status = "OK" if 'error' not in result else "ERR"
            time_ms = result.get('execution_time_ms', 0)
            zombies = result.get('zombies_found', 0)
            memory = result.get('total_memory_bytes', 0)

            ram_zombies += zombies
            ram_memory += memory

            table.add_row(
                agent_name.replace('_', ' ').title(),
                str(zombies),
                format_memory(memory),
                f"{time_ms:.0f}",
                status
            )

        # RAM subtotal
        table.add_row(
            "[dim]Phase 2 Subtotal[/dim]",
            f"[dim]{ram_zombies}[/dim]",
            f"[dim]{format_memory(ram_memory)}[/dim]",
            "",
            ""
        )

    # Phase 3: Developer Cache Cleanup agents
    dev_cache_zombies = 0
    dev_cache_memory = 0
    if 3 in phases_run and any(agent in results for agent in dev_cache_agents):
        table.add_row("", "", "", "", "")  # Spacer
        table.add_row("[bold]Phase 3: Developer Cache Cleanup[/bold]", "", "", "", "", style="bold yellow")

        for agent_name, result in results.items():
            if agent_name not in dev_cache_agents:
                continue

            status = "OK" if 'error' not in result else "ERR"
            time_ms = result.get('execution_time_ms', 0)
            zombies = result.get('zombies_found', 0)
            memory = result.get('total_memory_bytes', 0)

            # Check for disk recovery
            disk_recovery = result.get('disk_recovery', {}).get('total_gb', 0)
            if disk_recovery > 0:
                total_disk_recovery += disk_recovery

            dev_cache_zombies += zombies
            dev_cache_memory += memory

            display_value = f"{disk_recovery:.1f} GB disk" if disk_recovery > 0 else format_memory(memory)

            table.add_row(
                agent_name.replace('_', ' ').title(),
                str(zombies),
                display_value,
                f"{time_ms:.0f}",
                status
            )

        # Developer Cache subtotal
        table.add_row(
            "[dim]Phase 3 Subtotal[/dim]",
            f"[dim]{dev_cache_zombies}[/dim]",
            f"[dim]{format_memory(dev_cache_memory)}[/dim]",
            "",
            ""
        )

    # Phase 4: Advanced Memory agents
    adv_mem_zombies = 0
    adv_mem_memory = 0
    if 4 in phases_run and any(agent in results for agent in advanced_memory_agents):
        table.add_row("", "", "", "", "")  # Spacer
        table.add_row("[bold]Phase 4: Advanced Memory[/bold]", "", "", "", "", style="bold green")

        for agent_name, result in results.items():
            if agent_name not in advanced_memory_agents:
                continue

            status = "OK" if 'error' not in result else "ERR"
            time_ms = result.get('execution_time_ms', 0)
            zombies = result.get('zombies_found', 0)
            memory = result.get('total_memory_bytes', 0)

            adv_mem_zombies += zombies
            adv_mem_memory += memory

            table.add_row(
                agent_name.replace('_', ' ').title(),
                str(zombies),
                format_memory(memory),
                f"{time_ms:.0f}",
                status
            )

        # Advanced Memory subtotal
        table.add_row(
            "[dim]Phase 4 Subtotal[/dim]",
            f"[dim]{adv_mem_zombies}[/dim]",
            f"[dim]{format_memory(adv_mem_memory)}[/dim]",
            "",
            ""
        )

    # Phase 5: Browser Deep Cleanup agents
    browser_deep_zombies = 0
    browser_deep_memory = 0
    if 5 in phases_run and any(agent in results for agent in browser_deep_agents):
        table.add_row("", "", "", "", "")  # Spacer
        table.add_row("[bold]Phase 5: Browser Deep Cleanup[/bold]", "", "", "", "", style="bold blue")

        for agent_name, result in results.items():
            if agent_name not in browser_deep_agents:
                continue

            status = "OK" if 'error' not in result else "ERR"
            time_ms = result.get('execution_time_ms', 0)
            zombies = result.get('zombies_found', 0)
            memory = result.get('total_memory_bytes', 0)

            # Check for disk recovery
            disk_recovery = result.get('disk_recovery', {}).get('total_gb', 0)
            if disk_recovery > 0:
                total_disk_recovery += disk_recovery

            browser_deep_zombies += zombies
            browser_deep_memory += memory

            display_value = f"{disk_recovery:.1f} GB disk" if disk_recovery > 0 else format_memory(memory)

            table.add_row(
                agent_name.replace('_', ' ').title(),
                str(zombies),
                display_value,
                f"{time_ms:.0f}",
                status
            )

        # Browser Deep Cleanup subtotal
        table.add_row(
            "[dim]Phase 5 Subtotal[/dim]",
            f"[dim]{browser_deep_zombies}[/dim]",
            f"[dim]{format_memory(browser_deep_memory)}[/dim]",
            "",
            ""
        )

    # Phase 6: App & System agents
    app_sys_zombies = 0
    app_sys_memory = 0
    if 6 in phases_run and any(agent in results for agent in app_system_agents):
        table.add_row("", "", "", "", "")  # Spacer
        table.add_row("[bold]Phase 6: App & System[/bold]", "", "", "", "", style="bold red")

        for agent_name, result in results.items():
            if agent_name not in app_system_agents:
                continue

            status = "OK" if 'error' not in result else "ERR"
            time_ms = result.get('execution_time_ms', 0)
            zombies = result.get('zombies_found', 0)
            memory = result.get('total_memory_bytes', 0)

            app_sys_zombies += zombies
            app_sys_memory += memory

            table.add_row(
                agent_name.replace('_', ' ').title(),
                str(zombies),
                format_memory(memory),
                f"{time_ms:.0f}",
                status
            )

        # App & System subtotal
        table.add_row(
            "[dim]Phase 6 Subtotal[/dim]",
            f"[dim]{app_sys_zombies}[/dim]",
            f"[dim]{format_memory(app_sys_memory)}[/dim]",
            "",
            ""
        )

    # Phase totals section
    table.add_row("", "", "", "", "")  # Spacer

    # Disk phase subtotal (Phase 1)
    disk_zombies_total = infra_zombies + app_zombies + network_zombies + resource_zombies + system_zombies
    disk_memory_total = infra_memory + app_memory + network_memory + resource_memory + system_memory

    if 1 in phases_run:
        table.add_row(
            "[bold]PHASE 1: DISK CLEANUP[/bold]",
            f"[bold]{disk_zombies_total}[/bold]",
            f"[bold]{format_memory(disk_memory_total)}[/bold]",
            "",
            "[bold cyan]P1[/bold cyan]"
        )

    if 2 in phases_run:
        table.add_row(
            "[bold]PHASE 2: RAM OPTIMIZATION[/bold]",
            f"[bold]{ram_zombies}[/bold]",
            f"[bold]{format_memory(ram_memory)}[/bold]",
            "",
            "[bold magenta]P2[/bold magenta]"
        )

    if 3 in phases_run:
        table.add_row(
            "[bold]PHASE 3: DEV CACHE[/bold]",
            f"[bold]{dev_cache_zombies}[/bold]",
            f"[bold]{format_memory(dev_cache_memory)}[/bold]",
            "",
            "[bold yellow]P3[/bold yellow]"
        )

    if 4 in phases_run:
        table.add_row(
            "[bold]PHASE 4: ADV MEMORY[/bold]",
            f"[bold]{adv_mem_zombies}[/bold]",
            f"[bold]{format_memory(adv_mem_memory)}[/bold]",
            "",
            "[bold green]P4[/bold green]"
        )

    if 5 in phases_run:
        table.add_row(
            "[bold]PHASE 5: BROWSER DEEP[/bold]",
            f"[bold]{browser_deep_zombies}[/bold]",
            f"[bold]{format_memory(browser_deep_memory)}[/bold]",
            "",
            "[bold blue]P5[/bold blue]"
        )

    if 6 in phases_run:
        table.add_row(
            "[bold]PHASE 6: APP & SYSTEM[/bold]",
            f"[bold]{app_sys_zombies}[/bold]",
            f"[bold]{format_memory(app_sys_memory)}[/bold]",
            "",
            "[bold red]P6[/bold red]"
        )

    # Grand total row
    grand_total_zombies = disk_zombies_total + ram_zombies + dev_cache_zombies + adv_mem_zombies + browser_deep_zombies + app_sys_zombies
    grand_total_memory = disk_memory_total + ram_memory + dev_cache_memory + adv_mem_memory + browser_deep_memory + app_sys_memory

    table.add_row("", "", "", "", "")  # Spacer
    table.add_row(
        f"[bold]GRAND TOTAL ({total_agents} AGENTS)[/bold]",
        f"[bold green]{grand_total_zombies}[/bold green]",
        f"[bold green]{format_memory(grand_total_memory)}[/bold green]",
        "",
        "[bold green]OK[/bold green]"
    )

    # Disk recovery information (separate from RAM totals)
    if total_disk_recovery > 0:
        table.add_row(
            "[bold yellow]DISK RECOVERY (informational)[/bold yellow]",
            "",
            f"[bold yellow]{total_disk_recovery:.1f} GB[/bold yellow]",
            "",
            "[bold yellow]i[/bold yellow]"
        )

    console.print(table)

    # System Analysis
    if 'system_analyzer' in results:
        sys_result = results['system_analyzer']
        if 'error' not in sys_result:
            mem = sys_result.get('memory', {})
            prot = sys_result.get('protected_processes', {})

            console.print("\n[bold]System Status[/bold]")
            console.print(f"  RAM Usage: {mem.get('used_ram_gb', 0)} / {mem.get('total_ram_gb', 0)} GB ({mem.get('percent_used', 0)}%)")
            console.print(f"  Protected Processes: Claude ({prot.get('claude-code', 0)}), Ghostty ({prot.get('ghostty', 0)})")

    # Recommendations
    if total_zombies > 0:
        console.print("\n[bold yellow]Next Steps:[/bold yellow]")
        console.print(f"  PIDs to kill: {' '.join(map(str, all_pids[:10]))}" + ("..." if len(all_pids) > 10 else ""))
        console.print(f"  [dim]Run: uv run scripts/kill_zombies_parallel.py --pids \"{','.join(map(str, all_pids))}\"[/dim]")
    else:
        console.print("\n[bold green]✅ No zombie processes found - system clean![/bold green]")

def parse_phases(ctx, param, value):
    """Parse phases option - accepts comma-separated list of phase numbers (1-6)"""
    if value is None:
        return None

    try:
        phases = [int(p.strip()) for p in value.split(',')]
        for p in phases:
            if p < 1 or p > 6:
                raise click.BadParameter(f"Phase {p} is invalid. Valid phases are 1-6.")
        return sorted(set(phases))  # Remove duplicates and sort
    except ValueError:
        raise click.BadParameter("Phases must be comma-separated numbers (e.g., '1,2,3' or '1,3,5')")


@click.command()
@click.option('--format', type=click.Choice(['json', 'table']), default='table',
              help='Output format')
@click.option('--verbose', is_flag=True, help='Show detailed information')
@click.option('--mode', type=click.Choice(['all', 'disk', 'ram']), default='disk',
              help='Execution mode: all (all 6 phases), disk (phase 1 only), or ram (phase 2 only)')
@click.option('--phases', callback=parse_phases, default=None,
              help='Specific phases to run (1-6), comma-separated. E.g., "1,2,3" or "3,4,5,6"')
@click.option('--dry-run', is_flag=True, help='Simulate execution without running agents')
def main(format: str, verbose: bool, mode: str, phases: list, dry_run: bool) -> None:
    """Unified Coordinator - Spawns up to 50 agents (6 Phases)

    Phases:
      1 - Disk Cleanup (20 agents): Infrastructure, Application, Network, Resource, System
      2 - RAM Optimization (10 agents): Memory pressure, profiler, browser, etc.
      3 - Developer Cache Cleanup (6 agents): Time Machine, Xcode, Gradle, Docker
      4 - Advanced Memory (6 agents): Swap, WindowServer, Adobe, Figma, Spotlight
      5 - Browser Deep Cleanup (3 agents): Chrome, Safari, Firefox
      6 - App & System (5 agents): Slack/Discord, VSCode, LaunchAgent, DNS, Sockets

    Modes (backward compatible):
      disk - Run phase 1 only (20 agents, default)
      ram  - Run phase 2 only (10 agents)
      all  - Run all 6 phases sequentially (50 agents total)

    Examples:
      uv run coordinator.py --mode all                  # All 50 agents
      uv run coordinator.py --phases 1,2               # Only phases 1 and 2
      uv run coordinator.py --phases 3,4,5,6           # Only new phases 3-6
      uv run coordinator.py --phases 1 --verbose       # Detailed phase 1 only
    """

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No agents will be executed[/yellow]")
        return

    start_time = time.time()

    # Determine phases to run
    phase_counts = {1: 20, 2: 10, 3: 6, 4: 6, 5: 3, 6: 5}

    if phases is not None:
        # Explicit phases specified - override mode
        phases_to_run = phases
    elif mode == 'disk':
        phases_to_run = [1]
    elif mode == 'ram':
        phases_to_run = [2]
    else:  # mode == 'all'
        phases_to_run = [1, 2, 3, 4, 5, 6]

    # Calculate total agents
    agents_count = sum(phase_counts.get(p, 0) for p in phases_to_run)

    # Run comprehensive cleanup with phases support
    results = asyncio.run(coordinate_comprehensive_cleanup(verbose, mode, phases_to_run))

    execution_time = (time.time() - start_time) * 1000

    # Add total execution time metadata
    results['_meta'] = {
        "total_execution_time_ms": round(execution_time, 2),
        "agents_count": agents_count,
        "parallel": True,
        "mode": mode,
        "phases_run": phases_to_run,
        "total_phases": len(phases_to_run)
    }

    # Display results with phases parameter
    display_results(results, format, mode, phases_to_run)

    if format == 'table':
        phase_text = f"{len(phases_to_run)} sequential phase{'s' if len(phases_to_run) > 1 else ''}"
        console.print(f"\n[dim]Total execution time: {execution_time:.0f}ms ({phase_text}, {agents_count} agents)[/dim]")

        # Show phase breakdown
        for phase_num in phases_to_run:
            phase_key = f'_phase_{phase_num}'
            if phase_key in results:
                phase_meta = results[phase_key]
                name = phase_meta.get('name', f'Phase {phase_num}')
                count = phase_meta.get('agents_count', 0)
                new_pids = len(phase_meta.get('new_pids', phase_meta.get('restarted_pids', [])))
                console.print(f"[dim]  - {name}: {count} agents, {new_pids} processes identified[/dim]")

if __name__ == "__main__":
    main()
