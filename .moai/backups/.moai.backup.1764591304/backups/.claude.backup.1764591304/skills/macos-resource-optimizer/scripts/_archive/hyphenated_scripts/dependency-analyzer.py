#!/usr/bin/env python3
"""
Dependency Analyzer - Process tree analysis and safe kill validation
Analyzes parent-child relationships and prevents killing processes with dependencies
"""

import subprocess
import sys
from typing import Dict, List, Set, Tuple
import json


class ProcessTree:
    """Build and analyze process dependency tree"""

    def __init__(self):
        self.processes: Dict[int, Dict] = {}
        self.children: Dict[int, Set[int]] = {}
        self.orphans: Set[int] = set()

    def load_processes(self):
        """Load all processes and build tree structure"""
        try:
            # Get all processes with PID, PPID, and command
            result = subprocess.run(
                ['ps', '-axo', 'pid,ppid,comm'],
                capture_output=True,
                text=True,
                timeout=10
            )

            lines = result.stdout.strip().split('\n')[1:]  # Skip header

            for line in lines:
                parts = line.split(None, 2)
                if len(parts) < 3:
                    continue

                pid = int(parts[0])
                ppid = int(parts[1])
                command = parts[2]

                self.processes[pid] = {
                    'pid': pid,
                    'ppid': ppid,
                    'command': command
                }

                # Track parent-child relationships
                if ppid not in self.children:
                    self.children[ppid] = set()
                self.children[ppid].add(pid)

            # Find orphaned processes
            self._find_orphans()

        except Exception as e:
            print(f"❌ Error loading processes: {e}", file=sys.stderr)
            sys.exit(1)

    def _find_orphans(self):
        """Identify orphaned processes (parent doesn't exist)"""
        for pid, info in self.processes.items():
            ppid = info['ppid']
            # Orphan if parent is not in process list (except init process with ppid=1)
            if ppid != 0 and ppid != 1 and ppid not in self.processes:
                self.orphans.add(pid)

    def get_children(self, pid: int, recursive: bool = False) -> Set[int]:
        """
        Get child processes of a given PID

        Args:
            pid: Parent process ID
            recursive: If True, get all descendants

        Returns:
            Set of child PIDs
        """
        if pid not in self.children:
            return set()

        children = self.children[pid].copy()

        if recursive:
            # Recursively get all descendants
            for child in list(children):
                children.update(self.get_children(child, recursive=True))

        return children

    def get_ancestors(self, pid: int) -> List[int]:
        """
        Get all parent processes up to root

        Args:
            pid: Process ID

        Returns:
            List of ancestor PIDs (immediate parent first)
        """
        ancestors = []
        current = pid

        while current in self.processes:
            ppid = self.processes[current]['ppid']
            if ppid == 0 or ppid == current:  # Reached root
                break
            ancestors.append(ppid)
            current = ppid

        return ancestors

    def is_safe_to_kill(self, pid: int) -> Tuple[bool, str]:
        """
        Check if it's safe to kill a process

        Args:
            pid: Process ID to check

        Returns:
            Tuple of (is_safe, reason)
        """
        if pid not in self.processes:
            return False, f"Process {pid} not found"

        # Check for children
        children = self.get_children(pid, recursive=False)
        if children:
            child_commands = [self.processes[c]['command'] for c in list(children)[:3]]
            return False, f"Has {len(children)} child process(es): {', '.join(child_commands)}..."

        # Check if it's a system process
        command = self.processes[pid]['command']
        system_processes = ['launchd', 'kernel_task', 'init', 'systemd']
        if any(sp in command.lower() for sp in system_processes):
            return False, f"System process: {command}"

        # Safe to kill
        return True, "No dependencies found"

    def get_kill_order(self, pids: List[int]) -> List[int]:
        """
        Calculate safe kill order (children before parents)

        Args:
            pids: List of PIDs to kill

        Returns:
            Ordered list of PIDs (kill in this order)
        """
        # Build dependency graph
        all_pids = set(pids)
        for pid in pids:
            all_pids.update(self.get_children(pid, recursive=True))

        # Topological sort (children first)
        ordered = []
        visited = set()

        def visit(pid):
            if pid in visited or pid not in all_pids:
                return
            visited.add(pid)

            # Visit children first
            for child in self.get_children(pid, recursive=False):
                visit(child)

            ordered.append(pid)

        for pid in all_pids:
            visit(pid)

        return ordered

    def analyze_process(self, pid: int) -> Dict:
        """
        Comprehensive analysis of a single process

        Args:
            pid: Process ID

        Returns:
            Dictionary with analysis results
        """
        if pid not in self.processes:
            return {'error': f'Process {pid} not found'}

        info = self.processes[pid]
        children = self.get_children(pid, recursive=False)
        descendants = self.get_children(pid, recursive=True)
        ancestors = self.get_ancestors(pid)
        is_safe, reason = self.is_safe_to_kill(pid)

        return {
            'pid': pid,
            'ppid': info['ppid'],
            'command': info['command'],
            'is_orphan': pid in self.orphans,
            'num_children': len(children),
            'num_descendants': len(descendants),
            'children': [
                {'pid': c, 'command': self.processes[c]['command']}
                for c in list(children)[:5]  # Limit to first 5
            ],
            'ancestors': [
                {'pid': a, 'command': self.processes[a]['command']}
                for a in ancestors[:5]  # Limit to first 5
            ],
            'safe_to_kill': is_safe,
            'safety_reason': reason
        }


def analyze_dependencies(pid: int) -> Dict:
    """
    Analyze dependencies for a single process

    Args:
        pid: Process ID to analyze

    Returns:
        Dictionary with dependency analysis
    """
    tree = ProcessTree()
    tree.load_processes()
    return tree.analyze_process(pid)


def get_safe_kill_order(pids: List[int]) -> List[int]:
    """
    Get safe kill order for multiple processes

    Args:
        pids: List of process IDs

    Returns:
        Ordered list of PIDs
    """
    tree = ProcessTree()
    tree.load_processes()
    return tree.get_kill_order(pids)


def main():
    """CLI interface for dependency analysis"""
    if len(sys.argv) < 2:
        print("Usage: dependency-analyzer.py <command> [args]")
        print("\nCommands:")
        print("  analyze <pid>              - Analyze dependencies for a process")
        print("  kill-order <pid1> <pid2>   - Get safe kill order for processes")
        print("  tree                        - Show full process tree")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'analyze':
        if len(sys.argv) < 3:
            print("Usage: dependency-analyzer.py analyze <pid>")
            sys.exit(1)

        pid = int(sys.argv[2])
        result = analyze_dependencies(pid)

        if 'error' in result:
            print(f"❌ {result['error']}")
            sys.exit(1)

        # Print formatted output
        print(f"\n📊 Dependency Analysis for PID {pid}")
        print("=" * 60)
        print(f"Command: {result['command']}")
        print(f"Parent PID: {result['ppid']}")
        print(f"Is Orphan: {result['is_orphan']}")
        print(f"Children: {result['num_children']}")
        print(f"Total Descendants: {result['num_descendants']}")
        print(f"\n{'✅' if result['safe_to_kill'] else '❌'} Safe to Kill: {result['safe_to_kill']}")
        print(f"Reason: {result['safety_reason']}")

        if result['children']:
            print("\nChild Processes:")
            for child in result['children']:
                print(f"  • {child['pid']}: {child['command']}")

        if result['ancestors']:
            print("\nParent Chain:")
            for ancestor in result['ancestors']:
                print(f"  • {ancestor['pid']}: {ancestor['command']}")

        # JSON output
        print("\nJSON Output:")
        print(json.dumps(result, indent=2))

    elif command == 'kill-order':
        if len(sys.argv) < 3:
            print("Usage: dependency-analyzer.py kill-order <pid1> <pid2> ...")
            sys.exit(1)

        pids = [int(p) for p in sys.argv[2:]]
        order = get_safe_kill_order(pids)

        print(f"\n🔄 Safe Kill Order for {len(pids)} process(es)")
        print("=" * 60)
        print("Kill in this order (children before parents):")
        for i, pid in enumerate(order, 1):
            print(f"{i}. PID {pid}")

        print(f"\nJSON Output:")
        print(json.dumps({'kill_order': order}, indent=2))

    elif command == 'tree':
        tree = ProcessTree()
        tree.load_processes()

        print(f"\n🌳 Process Tree")
        print("=" * 60)
        print(f"Total Processes: {len(tree.processes)}")
        print(f"Orphaned Processes: {len(tree.orphans)}")
        print(f"Processes with Children: {len(tree.children)}")

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
