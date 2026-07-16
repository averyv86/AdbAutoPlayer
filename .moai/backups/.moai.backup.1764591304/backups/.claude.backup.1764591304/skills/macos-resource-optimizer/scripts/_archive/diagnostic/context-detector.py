#!/usr/bin/env python3
"""
Context Detector - Work Context Awareness
Detects current work context to identify protected vs safe-to-kill processes.
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set
import sys

class ContextDetector:
    """Detect current work context and classify processes"""

    def __init__(self):
        self.context = {
            "editors": [],
            "projects": [],
            "git_repos": [],
            "dev_servers": [],
            "protected_processes": set(),
            "safe_processes": set()
        }

    def detect_open_editors(self) -> List[Dict]:
        """Detect open code editors and their projects"""
        editors = []

        # VS Code
        vscode_workspaces = self._find_vscode_workspaces()
        for ws in vscode_workspaces:
            editors.append({
                "type": "vscode",
                "workspace": ws,
                "protected_processes": ["code", "node", "typescript", "eslint"]
            })

        # Cursor (VS Code fork)
        cursor_workspaces = self._find_cursor_workspaces()
        for ws in cursor_workspaces:
            editors.append({
                "type": "cursor",
                "workspace": ws,
                "protected_processes": ["cursor", "node", "typescript", "eslint"]
            })

        # Zed
        zed_projects = self._find_zed_projects()
        for proj in zed_projects:
            editors.append({
                "type": "zed",
                "project": proj,
                "protected_processes": ["zed", "rust-analyzer"]
            })

        self.context["editors"] = editors
        return editors

    def _find_vscode_workspaces(self) -> List[Path]:
        """Find open VS Code workspaces"""
        workspaces = []

        # Check running VS Code processes
        try:
            ps_output = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                check=True
            )

            for line in ps_output.stdout.split('\n'):
                if 'code' in line.lower() and '--folder-uri' in line:
                    # Extract workspace path from command line
                    parts = line.split('--folder-uri')
                    if len(parts) > 1:
                        ws_path = parts[1].split()[0].replace('file://', '')
                        workspaces.append(Path(ws_path))
        except Exception as e:
            print(f"Warning: Failed to detect VS Code workspaces: {e}", file=sys.stderr)

        # Also check recent workspaces file
        vscode_storage = Path.home() / "Library/Application Support/Code/storage.json"
        if vscode_storage.exists():
            try:
                with open(vscode_storage, 'r') as f:
                    storage = json.load(f)
                    for ws in storage.get("openedPathsList", {}).get("workspaces3", []):
                        if "folderUri" in ws:
                            ws_path = ws["folderUri"].replace('file://', '')
                            workspaces.append(Path(ws_path))
            except Exception as e:
                print(f"Warning: Failed to read VS Code storage: {e}", file=sys.stderr)

        return list(set(workspaces))  # Deduplicate

    def _find_cursor_workspaces(self) -> List[Path]:
        """Find open Cursor workspaces"""
        workspaces = []

        try:
            ps_output = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                check=True
            )

            for line in ps_output.stdout.split('\n'):
                if 'cursor' in line.lower():
                    # Similar to VS Code detection
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.startswith('/') and not part.startswith('/Applications'):
                            if Path(part).exists() and Path(part).is_dir():
                                workspaces.append(Path(part))
        except Exception as e:
            print(f"Warning: Failed to detect Cursor workspaces: {e}", file=sys.stderr)

        return list(set(workspaces))

    def _find_zed_projects(self) -> List[Path]:
        """Find open Zed projects"""
        projects = []

        try:
            ps_output = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                check=True
            )

            for line in ps_output.stdout.split('\n'):
                if 'zed' in line.lower():
                    parts = line.split()
                    for part in parts:
                        if part.startswith('/') and Path(part).exists():
                            projects.append(Path(part))
        except Exception as e:
            print(f"Warning: Failed to detect Zed projects: {e}", file=sys.stderr)

        return list(set(projects))

    def detect_git_activity(self, hours: int = 4) -> List[Dict]:
        """Detect recent git activity"""
        cutoff = datetime.now() - timedelta(hours=hours)
        active_repos = []

        # Find git repositories
        home = Path.home()
        potential_repos = [
            home / "Documents",
            home / "Projects",
            home / "Code",
            home / "Development"
        ]

        for base_dir in potential_repos:
            if not base_dir.exists():
                continue

            try:
                # Find .git directories
                git_dirs = subprocess.run(
                    ['find', str(base_dir), '-name', '.git', '-type', 'd', '-maxdepth', 5],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                for git_dir in git_dirs.stdout.strip().split('\n'):
                    if not git_dir:
                        continue

                    repo_path = Path(git_dir).parent

                    # Check for recent activity
                    try:
                        git_log = subprocess.run(
                            ['git', '-C', str(repo_path), 'log', '-1', '--format=%ct'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )

                        if git_log.stdout.strip():
                            last_commit = datetime.fromtimestamp(int(git_log.stdout.strip()))
                            if last_commit >= cutoff:
                                active_repos.append({
                                    "path": repo_path,
                                    "last_commit": last_commit.isoformat(),
                                    "protected": True
                                })
                    except:
                        pass

            except Exception as e:
                print(f"Warning: Failed to scan {base_dir}: {e}", file=sys.stderr)

        self.context["git_repos"] = active_repos
        return active_repos

    def detect_dev_servers(self) -> List[Dict]:
        """Detect running development servers"""
        dev_servers = []

        try:
            # Get process list with working directories
            ps_output = subprocess.run(
                ['ps', 'auxww'],
                capture_output=True,
                text=True,
                check=True
            )

            # Common dev server patterns
            dev_patterns = [
                'npm run dev',
                'yarn dev',
                'next dev',
                'vite',
                'webpack-dev-server',
                'rails server',
                'python manage.py runserver',
                'flask run',
                'uvicorn',
                'fastapi'
            ]

            for line in ps_output.stdout.split('\n'):
                for pattern in dev_patterns:
                    if pattern in line.lower():
                        parts = line.split(None, 10)
                        if len(parts) >= 11:
                            dev_servers.append({
                                "pid": parts[1],
                                "command": parts[10],
                                "pattern": pattern,
                                "protected": True
                            })
                        break
        except Exception as e:
            print(f"Warning: Failed to detect dev servers: {e}", file=sys.stderr)

        self.context["dev_servers"] = dev_servers
        return dev_servers

    def classify_processes(self) -> Dict[str, List]:
        """Classify all processes as protected or safe-to-kill"""
        # Detect all contexts
        self.detect_open_editors()
        self.detect_git_activity()
        self.detect_dev_servers()

        # Build protected process set
        protected = set()

        # Add editor-related processes
        for editor in self.context["editors"]:
            protected.update(editor.get("protected_processes", []))

        # Add dev server processes
        for server in self.context["dev_servers"]:
            protected.add(server["pid"])

        # Get all running processes
        try:
            ps_output = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                check=True
            )

            all_processes = []
            safe_processes = []

            for line in ps_output.stdout.split('\n')[1:]:  # Skip header
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    pid = parts[1]
                    command = parts[10]
                    process_name = command.split()[0] if command else "unknown"

                    all_processes.append({
                        "pid": pid,
                        "name": process_name,
                        "command": command
                    })

                    # Check if protected
                    is_protected = False
                    for prot in protected:
                        if prot in process_name or prot in command:
                            is_protected = True
                            break

                    if not is_protected:
                        safe_processes.append({
                            "pid": pid,
                            "name": process_name,
                            "command": command
                        })

        except Exception as e:
            print(f"Error classifying processes: {e}", file=sys.stderr)
            return {"protected": [], "safe": []}

        return {
            "protected": [p for p in all_processes if p["pid"] not in [s["pid"] for s in safe_processes]],
            "safe": safe_processes
        }

    def generate_report(self, output_format: str = "text") -> str:
        """Generate context detection report"""
        classification = self.classify_processes()

        if output_format == "json":
            return json.dumps({
                "context": self.context,
                "classification": classification
            }, indent=2, default=str)

        # Text format
        report = []
        report.append("=" * 80)
        report.append("WORK CONTEXT DETECTION REPORT")
        report.append("=" * 80)
        report.append("")

        report.append("ACTIVE EDITORS")
        report.append("-" * 80)
        if self.context["editors"]:
            for editor in self.context["editors"]:
                report.append(f"  {editor['type'].upper()}")
                if 'workspace' in editor:
                    report.append(f"    Workspace: {editor['workspace']}")
                if 'project' in editor:
                    report.append(f"    Project: {editor['project']}")
                report.append(f"    Protected: {', '.join(editor['protected_processes'])}")
                report.append("")
        else:
            report.append("  No active editors detected")
            report.append("")

        report.append("RECENT GIT ACTIVITY (last 4 hours)")
        report.append("-" * 80)
        if self.context["git_repos"]:
            for repo in self.context["git_repos"]:
                report.append(f"  {repo['path']}")
                report.append(f"    Last commit: {repo['last_commit']}")
                report.append("")
        else:
            report.append("  No recent git activity")
            report.append("")

        report.append("RUNNING DEV SERVERS")
        report.append("-" * 80)
        if self.context["dev_servers"]:
            for server in self.context["dev_servers"]:
                report.append(f"  PID {server['pid']}: {server['pattern']}")
                report.append(f"    {server['command'][:80]}")
                report.append("")
        else:
            report.append("  No dev servers detected")
            report.append("")

        report.append("PROCESS CLASSIFICATION")
        report.append("-" * 80)
        report.append(f"Protected processes: {len(classification['protected'])}")
        report.append(f"Safe to kill: {len(classification['safe'])}")
        report.append("")

        report.append("SAFE TO KILL (top 20):")
        for proc in classification['safe'][:20]:
            report.append(f"  {proc['pid']:<8} {proc['name']:<30} {proc['command'][:40]}")

        if len(classification['safe']) > 20:
            report.append(f"  ... and {len(classification['safe']) - 20} more")

        return "\n".join(report)


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Detect work context and classify processes")
    parser.add_argument("--editors", action="store_true", help="Detect open editors")
    parser.add_argument("--git", action="store_true", help="Detect git activity")
    parser.add_argument("--servers", action="store_true", help="Detect dev servers")
    parser.add_argument("--classify", action="store_true", help="Classify all processes")
    parser.add_argument("--report", action="store_true", help="Generate full report")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    args = parser.parse_args()

    detector = ContextDetector()

    if args.editors:
        editors = detector.detect_open_editors()
        if args.format == "json":
            print(json.dumps(editors, indent=2, default=str))
        else:
            print("Active Editors:")
            for editor in editors:
                print(f"  {editor['type']}: {editor.get('workspace') or editor.get('project')}")

    if args.git:
        repos = detector.detect_git_activity()
        if args.format == "json":
            print(json.dumps(repos, indent=2, default=str))
        else:
            print("Recent Git Activity:")
            for repo in repos:
                print(f"  {repo['path']}: {repo['last_commit']}")

    if args.servers:
        servers = detector.detect_dev_servers()
        if args.format == "json":
            print(json.dumps(servers, indent=2))
        else:
            print("Running Dev Servers:")
            for server in servers:
                print(f"  PID {server['pid']}: {server['pattern']}")

    if args.classify:
        classification = detector.classify_processes()
        if args.format == "json":
            print(json.dumps(classification, indent=2))
        else:
            print(f"Protected: {len(classification['protected'])} processes")
            print(f"Safe to kill: {len(classification['safe'])} processes")

    if args.report or not any([args.editors, args.git, args.servers, args.classify]):
        report = detector.generate_report(args.format)
        print(report)


if __name__ == "__main__":
    main()
