#!/usr/bin/env python3
"""
Duplicate Finder - Duplicate Service Detection
Finds duplicate processes, port conflicts, and redundant services.
"""

import os
import json
import subprocess
from collections import defaultdict
from typing import Dict, List, Set
import sys
import re

class DuplicateFinder:
    """Find duplicate processes and services"""

    def __init__(self):
        self.duplicates = {
            "processes": [],
            "ports": [],
            "docker": [],
            "dev_servers": []
        }

    def find_duplicate_processes(self) -> List[Dict]:
        """Find processes with multiple instances"""
        duplicates = []

        try:
            # Get process list and count occurrences
            ps_output = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                check=True
            )

            process_counts = defaultdict(list)

            for line in ps_output.stdout.split('\n')[1:]:  # Skip header
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    pid = parts[1]
                    command = parts[10]
                    process_name = command.split()[0] if command else "unknown"

                    # Extract base name (without path)
                    base_name = os.path.basename(process_name)

                    process_counts[base_name].append({
                        "pid": pid,
                        "command": command,
                        "user": parts[0],
                        "cpu": parts[2],
                        "mem": parts[3]
                    })

            # Find duplicates (count > 1)
            for process_name, instances in process_counts.items():
                if len(instances) > 1:
                    # Filter out legitimate multi-instance processes
                    if not self._is_legitimate_multi_instance(process_name):
                        duplicates.append({
                            "name": process_name,
                            "count": len(instances),
                            "instances": instances,
                            "recommendation": self._get_duplicate_recommendation(process_name, instances)
                        })

        except Exception as e:
            print(f"Error finding duplicate processes: {e}", file=sys.stderr)

        self.duplicates["processes"] = sorted(duplicates, key=lambda x: x["count"], reverse=True)
        return self.duplicates["processes"]

    def _is_legitimate_multi_instance(self, process_name: str) -> bool:
        """Check if process legitimately runs multiple instances"""
        legitimate_multi = [
            'chrome', 'chromium', 'firefox', 'safari',  # Browsers
            'python', 'node', 'ruby', 'java',  # Language runtimes (often OK)
            'bash', 'zsh', 'sh',  # Shells
            'ssh', 'sshd',  # SSH
            'git',  # Git operations
        ]

        return any(leg in process_name.lower() for leg in legitimate_multi)

    def _get_duplicate_recommendation(self, process_name: str, instances: List[Dict]) -> str:
        """Get recommendation for duplicate processes"""
        if 'code' in process_name.lower() or 'cursor' in process_name.lower():
            return "Multiple editor instances - consider consolidating workspaces"
        elif 'docker' in process_name.lower():
            return "Multiple Docker processes - check for stuck containers"
        elif 'server' in process_name.lower() or 'daemon' in process_name.lower():
            return "Multiple server instances - potential port conflict"
        else:
            return f"Review {len(instances)} instances - may be unnecessary"

    def find_port_conflicts(self) -> List[Dict]:
        """Find processes listening on the same ports"""
        conflicts = []

        try:
            # Get listening ports
            lsof_output = subprocess.run(
                ['lsof', '-i', '-P', '-n'],
                capture_output=True,
                text=True,
                check=True
            )

            port_map = defaultdict(list)

            for line in lsof_output.stdout.split('\n')[1:]:  # Skip header
                if 'LISTEN' in line:
                    parts = line.split()
                    if len(parts) >= 9:
                        command = parts[0]
                        pid = parts[1]
                        port_info = parts[8]

                        # Extract port number
                        port_match = re.search(r':(\d+)', port_info)
                        if port_match:
                            port = port_match.group(1)
                            port_map[port].append({
                                "command": command,
                                "pid": pid,
                                "address": port_info
                            })

            # Find conflicts (multiple processes on same port)
            for port, listeners in port_map.items():
                if len(listeners) > 1:
                    conflicts.append({
                        "port": port,
                        "count": len(listeners),
                        "listeners": listeners,
                        "recommendation": f"Port {port} conflict - {len(listeners)} processes attempting to listen"
                    })

        except subprocess.CalledProcessError:
            print("Warning: lsof requires elevated privileges for full port scanning", file=sys.stderr)
        except Exception as e:
            print(f"Error finding port conflicts: {e}", file=sys.stderr)

        self.duplicates["ports"] = conflicts
        return conflicts

    def find_duplicate_docker_containers(self) -> List[Dict]:
        """Find duplicate Docker containers from same image"""
        duplicates = []

        try:
            # Check if Docker is running
            docker_check = subprocess.run(
                ['docker', 'info'],
                capture_output=True,
                text=True
            )

            if docker_check.returncode != 0:
                return []

            # Get running containers
            docker_ps = subprocess.run(
                ['docker', 'ps', '--format', '{{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}'],
                capture_output=True,
                text=True,
                check=True
            )

            image_map = defaultdict(list)

            for line in docker_ps.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 4:
                        container_id, image, name, status = parts
                        image_map[image].append({
                            "id": container_id,
                            "name": name,
                            "status": status
                        })

            # Find duplicates
            for image, containers in image_map.items():
                if len(containers) > 1:
                    duplicates.append({
                        "image": image,
                        "count": len(containers),
                        "containers": containers,
                        "recommendation": f"Multiple containers from {image} - consolidate or remove unused"
                    })

        except FileNotFoundError:
            pass  # Docker not installed
        except Exception as e:
            print(f"Warning: Failed to check Docker containers: {e}", file=sys.stderr)

        self.duplicates["docker"] = duplicates
        return duplicates

    def find_duplicate_dev_servers(self) -> List[Dict]:
        """Find duplicate development servers"""
        duplicates = []

        try:
            ps_output = subprocess.run(
                ['ps', 'auxww'],
                capture_output=True,
                text=True,
                check=True
            )

            dev_patterns = {
                'npm dev': [],
                'yarn dev': [],
                'next dev': [],
                'vite': [],
                'webpack-dev-server': [],
                'rails server': [],
                'flask': [],
                'uvicorn': []
            }

            for line in ps_output.stdout.split('\n'):
                for pattern in dev_patterns.keys():
                    if pattern in line.lower():
                        parts = line.split(None, 10)
                        if len(parts) >= 11:
                            dev_patterns[pattern].append({
                                "pid": parts[1],
                                "command": parts[10],
                                "user": parts[0]
                            })

            # Find duplicates
            for pattern, instances in dev_patterns.items():
                if len(instances) > 1:
                    duplicates.append({
                        "type": pattern,
                        "count": len(instances),
                        "instances": instances,
                        "recommendation": f"Multiple '{pattern}' servers running - likely port conflicts"
                    })

        except Exception as e:
            print(f"Error finding dev server duplicates: {e}", file=sys.stderr)

        self.duplicates["dev_servers"] = duplicates
        return duplicates

    def generate_report(self, output_format: str = "text") -> str:
        """Generate duplicate detection report"""
        # Run all detection
        self.find_duplicate_processes()
        self.find_port_conflicts()
        self.find_duplicate_docker_containers()
        self.find_duplicate_dev_servers()

        if output_format == "json":
            return json.dumps(self.duplicates, indent=2)

        # Text format
        report = []
        report.append("=" * 80)
        report.append("DUPLICATE SERVICE DETECTION REPORT")
        report.append("=" * 80)
        report.append("")

        # Duplicate processes
        report.append("DUPLICATE PROCESSES")
        report.append("-" * 80)
        if self.duplicates["processes"]:
            for dup in self.duplicates["processes"][:10]:  # Top 10
                report.append(f"  {dup['name']} ({dup['count']} instances)")
                report.append(f"    → {dup['recommendation']}")
                for inst in dup["instances"][:3]:  # Show first 3
                    report.append(f"      PID {inst['pid']}: CPU {inst['cpu']}% | MEM {inst['mem']}%")
                if len(dup["instances"]) > 3:
                    report.append(f"      ... and {len(dup['instances']) - 3} more")
                report.append("")
        else:
            report.append("  No problematic duplicates found")
            report.append("")

        # Port conflicts
        report.append("PORT CONFLICTS")
        report.append("-" * 80)
        if self.duplicates["ports"]:
            for conflict in self.duplicates["ports"]:
                report.append(f"  Port {conflict['port']} ({conflict['count']} listeners)")
                for listener in conflict["listeners"]:
                    report.append(f"    PID {listener['pid']}: {listener['command']} @ {listener['address']}")
                report.append(f"    → {conflict['recommendation']}")
                report.append("")
        else:
            report.append("  No port conflicts detected")
            report.append("")

        # Docker duplicates
        report.append("DUPLICATE DOCKER CONTAINERS")
        report.append("-" * 80)
        if self.duplicates["docker"]:
            for dup in self.duplicates["docker"]:
                report.append(f"  {dup['image']} ({dup['count']} containers)")
                for container in dup["containers"]:
                    report.append(f"    {container['id'][:12]}: {container['name']} ({container['status']})")
                report.append(f"    → {dup['recommendation']}")
                report.append("")
        else:
            report.append("  No duplicate Docker containers found")
            report.append("")

        # Dev server duplicates
        report.append("DUPLICATE DEV SERVERS")
        report.append("-" * 80)
        if self.duplicates["dev_servers"]:
            for dup in self.duplicates["dev_servers"]:
                report.append(f"  {dup['type']} ({dup['count']} instances)")
                for inst in dup["instances"]:
                    report.append(f"    PID {inst['pid']}: {inst['command'][:60]}")
                report.append(f"    → {dup['recommendation']}")
                report.append("")
        else:
            report.append("  No duplicate dev servers found")
            report.append("")

        # Summary
        total_issues = (
            len(self.duplicates["processes"]) +
            len(self.duplicates["ports"]) +
            len(self.duplicates["docker"]) +
            len(self.duplicates["dev_servers"])
        )

        report.append("SUMMARY")
        report.append("-" * 80)
        report.append(f"Total duplicate/conflict issues: {total_issues}")
        report.append(f"  Duplicate processes: {len(self.duplicates['processes'])}")
        report.append(f"  Port conflicts: {len(self.duplicates['ports'])}")
        report.append(f"  Duplicate Docker: {len(self.duplicates['docker'])}")
        report.append(f"  Duplicate dev servers: {len(self.duplicates['dev_servers'])}")

        return "\n".join(report)


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Find duplicate services and port conflicts")
    parser.add_argument("--processes", action="store_true", help="Find duplicate processes")
    parser.add_argument("--ports", action="store_true", help="Find port conflicts")
    parser.add_argument("--docker", action="store_true", help="Find duplicate Docker containers")
    parser.add_argument("--servers", action="store_true", help="Find duplicate dev servers")
    parser.add_argument("--report", action="store_true", help="Generate full report")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    args = parser.parse_args()

    finder = DuplicateFinder()

    if args.processes:
        duplicates = finder.find_duplicate_processes()
        if args.format == "json":
            print(json.dumps(duplicates, indent=2))
        else:
            print(f"Found {len(duplicates)} duplicate process types")

    if args.ports:
        conflicts = finder.find_port_conflicts()
        if args.format == "json":
            print(json.dumps(conflicts, indent=2))
        else:
            print(f"Found {len(conflicts)} port conflicts")

    if args.docker:
        docker_dups = finder.find_duplicate_docker_containers()
        if args.format == "json":
            print(json.dumps(docker_dups, indent=2))
        else:
            print(f"Found {len(docker_dups)} duplicate Docker container sets")

    if args.servers:
        server_dups = finder.find_duplicate_dev_servers()
        if args.format == "json":
            print(json.dumps(server_dups, indent=2))
        else:
            print(f"Found {len(server_dups)} duplicate dev server types")

    if args.report or not any([args.processes, args.ports, args.docker, args.servers]):
        report = finder.generate_report(args.format)
        print(report)


if __name__ == "__main__":
    main()
