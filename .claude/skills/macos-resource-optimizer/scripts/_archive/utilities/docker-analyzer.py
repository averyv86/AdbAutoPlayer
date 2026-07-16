#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "rich>=13.0.0",
# ]
# ///

"""
Docker Resource Analyzer
Analyzes Docker resources and identifies cleanup candidates
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table

console = Console()

class DockerAnalyzer:
    def __init__(self):
        self.analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "containers": [],
            "images": [],
            "volumes": [],
            "networks": [],
            "summary": {
                "total_reclaimable_space": 0,
                "stopped_containers": 0,
                "unused_images": 0,
                "unused_volumes": 0,
                "unused_networks": 0
            }
        }

    def check_docker_available(self) -> bool:
        """Check if Docker is installed and running"""
        try:
            subprocess.run(
                ["docker", "info"],
                capture_output=True,
                check=True,
                timeout=5
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            console.print("[red]Error: Docker is not installed or not running[/red]")
            return False

    def parse_size(self, size_str: str) -> int:
        """Convert Docker size string to bytes"""
        if not size_str or size_str == "0B":
            return 0

        units = {
            "B": 1,
            "KB": 1024,
            "MB": 1024**2,
            "GB": 1024**3,
            "TB": 1024**4
        }

        try:
            # Handle formats like "1.5GB" or "123MB"
            size_str = size_str.strip().upper()
            for unit, multiplier in units.items():
                if size_str.endswith(unit):
                    value = float(size_str[:-len(unit)])
                    return int(value * multiplier)
            return 0
        except (ValueError, AttributeError):
            return 0

    def format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human-readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f}{unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f}PB"

    def analyze_containers(self, days_threshold: int = 7) -> None:
        """Analyze Docker containers"""
        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                check=True
            )

            cutoff_date = datetime.now() - timedelta(days=days_threshold)

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                try:
                    container = json.loads(line)

                    # Get detailed info
                    inspect_result = subprocess.run(
                        ["docker", "inspect", container["ID"]],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    inspect_data = json.loads(inspect_result.stdout)[0]

                    created = datetime.fromisoformat(
                        inspect_data["Created"].replace("Z", "+00:00")
                    ).replace(tzinfo=None)

                    container_info = {
                        "id": container["ID"][:12],
                        "name": container["Names"],
                        "image": container["Image"],
                        "status": container["Status"],
                        "state": container["State"],
                        "created": created.isoformat(),
                        "size": inspect_data.get("SizeRw", 0),
                        "ports": container.get("Ports", ""),
                        "is_stopped": container["State"] != "running",
                        "age_days": (datetime.now() - created).days,
                        "reclaimable": False
                    }

                    # Mark as reclaimable if stopped and old enough
                    if container_info["is_stopped"] and container_info["age_days"] > days_threshold:
                        container_info["reclaimable"] = True
                        self.analysis_results["summary"]["stopped_containers"] += 1

                    self.analysis_results["containers"].append(container_info)

                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    console.print(f"[yellow]Warning: Error parsing container data: {e}[/yellow]")
                    continue

        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error analyzing containers: {e}[/red]")

    def analyze_images(self, days_threshold: int = 30) -> None:
        """Analyze Docker images and detect duplicates"""
        try:
            result = subprocess.run(
                ["docker", "images", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                check=True
            )

            image_ids = {}  # Track duplicate images by ID

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                try:
                    image = json.loads(line)

                    # Get detailed info
                    inspect_result = subprocess.run(
                        ["docker", "inspect", image["ID"]],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    inspect_data = json.loads(inspect_result.stdout)[0]

                    created = datetime.fromisoformat(
                        inspect_data["Created"].replace("Z", "+00:00")
                    ).replace(tzinfo=None)

                    image_info = {
                        "id": image["ID"].replace("sha256:", "")[:12],
                        "repository": image["Repository"],
                        "tag": image["Tag"],
                        "size": self.parse_size(image["Size"]),
                        "created": created.isoformat(),
                        "age_days": (datetime.now() - created).days,
                        "is_dangling": image["Repository"] == "<none>",
                        "reclaimable": False,
                        "duplicate_of": None
                    }

                    # Track duplicates
                    img_id = image_info["id"]
                    if img_id in image_ids:
                        image_info["duplicate_of"] = image_ids[img_id][0]["repository"] + ":" + image_ids[img_id][0]["tag"]
                        image_ids[img_id].append(image_info)
                    else:
                        image_ids[img_id] = [image_info]

                    # Mark as reclaimable if dangling or old unused image
                    if image_info["is_dangling"] or image_info["age_days"] > days_threshold:
                        image_info["reclaimable"] = True
                        self.analysis_results["summary"]["unused_images"] += 1
                        self.analysis_results["summary"]["total_reclaimable_space"] += image_info["size"]

                    self.analysis_results["images"].append(image_info)

                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    console.print(f"[yellow]Warning: Error parsing image data: {e}[/yellow]")
                    continue

        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error analyzing images: {e}[/red]")

    def analyze_volumes(self) -> None:
        """Analyze Docker volumes"""
        try:
            result = subprocess.run(
                ["docker", "volume", "ls", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                check=True
            )

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                try:
                    volume = json.loads(line)

                    # Check if volume is in use
                    inspect_result = subprocess.run(
                        ["docker", "volume", "inspect", volume["Name"]],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    inspect_data = json.loads(inspect_result.stdout)[0]

                    # Get size if possible
                    size = 0
                    if "Mountpoint" in inspect_data:
                        try:
                            du_result = subprocess.run(
                                ["du", "-sb", inspect_data["Mountpoint"]],
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            size = int(du_result.stdout.split()[0])
                        except (subprocess.CalledProcessError, ValueError, IndexError):
                            pass

                    volume_info = {
                        "name": volume["Name"],
                        "driver": volume.get("Driver", "local"),
                        "mountpoint": inspect_data.get("Mountpoint", ""),
                        "size": size,
                        "in_use": len(inspect_data.get("Options") or {}) > 0,
                        "reclaimable": False
                    }

                    # Mark as reclaimable if not in use
                    if not volume_info["in_use"]:
                        volume_info["reclaimable"] = True
                        self.analysis_results["summary"]["unused_volumes"] += 1
                        self.analysis_results["summary"]["total_reclaimable_space"] += size

                    self.analysis_results["volumes"].append(volume_info)

                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    console.print(f"[yellow]Warning: Error parsing volume data: {e}[/yellow]")
                    continue

        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error analyzing volumes: {e}[/red]")

    def analyze_networks(self) -> None:
        """Analyze Docker networks"""
        try:
            result = subprocess.run(
                ["docker", "network", "ls", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                check=True
            )

            system_networks = {"bridge", "host", "none"}

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                try:
                    network = json.loads(line)

                    # Get detailed info
                    inspect_result = subprocess.run(
                        ["docker", "network", "inspect", network["ID"]],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    inspect_data = json.loads(inspect_result.stdout)[0]

                    network_info = {
                        "id": network["ID"][:12],
                        "name": network["Name"],
                        "driver": network.get("Driver", "bridge"),
                        "scope": inspect_data.get("Scope", "local"),
                        "containers": len(inspect_data.get("Containers", {})),
                        "is_system": network["Name"] in system_networks,
                        "reclaimable": False
                    }

                    # Mark as reclaimable if custom network with no containers
                    if not network_info["is_system"] and network_info["containers"] == 0:
                        network_info["reclaimable"] = True
                        self.analysis_results["summary"]["unused_networks"] += 1

                    self.analysis_results["networks"].append(network_info)

                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    console.print(f"[yellow]Warning: Error parsing network data: {e}[/yellow]")
                    continue

        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error analyzing networks: {e}[/red]")

    def display_summary(self) -> None:
        """Display analysis summary"""
        console.print("\n[bold cyan]Docker Resource Analysis Summary[/bold cyan]\n")

        summary = self.analysis_results["summary"]

        # Overall stats
        table = Table(title="Resource Summary")
        table.add_column("Resource Type", style="cyan")
        table.add_column("Total", justify="right")
        table.add_column("Reclaimable", justify="right", style="yellow")

        table.add_row(
            "Containers",
            str(len(self.analysis_results["containers"])),
            str(summary["stopped_containers"])
        )
        table.add_row(
            "Images",
            str(len(self.analysis_results["images"])),
            str(summary["unused_images"])
        )
        table.add_row(
            "Volumes",
            str(len(self.analysis_results["volumes"])),
            str(summary["unused_volumes"])
        )
        table.add_row(
            "Networks",
            str(len(self.analysis_results["networks"])),
            str(summary["unused_networks"])
        )

        console.print(table)

        # Space summary
        console.print(f"\n[bold]Total Reclaimable Space:[/bold] [green]{self.format_bytes(summary['total_reclaimable_space'])}[/green]\n")

    def export_report(self, output_file: str = "docker-analysis.json") -> None:
        """Export analysis report to JSON"""
        try:
            with open(output_file, 'w') as f:
                json.dump(self.analysis_results, f, indent=2)
            console.print(f"[green]Analysis report saved to: {output_file}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving report: {e}[/red]")

    def run_analysis(self, container_days: int = 7, image_days: int = 30) -> None:
        """Run complete analysis"""
        if not self.check_docker_available():
            sys.exit(1)

        console.print("[cyan]Analyzing Docker resources...[/cyan]\n")

        with console.status("[bold green]Analyzing containers..."):
            self.analyze_containers(container_days)

        with console.status("[bold green]Analyzing images..."):
            self.analyze_images(image_days)

        with console.status("[bold green]Analyzing volumes..."):
            self.analyze_volumes()

        with console.status("[bold green]Analyzing networks..."):
            self.analyze_networks()

        self.display_summary()

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze Docker resources for cleanup")
    parser.add_argument(
        "--container-days",
        type=int,
        default=7,
        help="Days threshold for stopped containers (default: 7)"
    )
    parser.add_argument(
        "--image-days",
        type=int,
        default=30,
        help="Days threshold for unused images (default: 30)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docker-analysis.json",
        help="Output file for JSON report (default: docker-analysis.json)"
    )

    args = parser.parse_args()

    analyzer = DockerAnalyzer()
    analyzer.run_analysis(args.container_days, args.image_days)
    analyzer.export_report(args.output)

if __name__ == "__main__":
    main()
