#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "rich>=13.0.0",
# ]
# ///

"""
Docker Cleanup Orchestrator
Orchestrates safe Docker resource cleanup with interactive confirmation
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class DockerCleanup:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.cleanup_results = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "actions": [],
            "space_freed": 0,
            "errors": []
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

    def get_current_disk_usage(self) -> Dict[str, int]:
        """Get current Docker disk usage"""
        try:
            result = subprocess.run(
                ["docker", "system", "df", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                check=True
            )

            usage = {
                "images": 0,
                "containers": 0,
                "volumes": 0,
                "build_cache": 0
            }

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    resource_type = data.get("Type", "").lower()
                    size = self.parse_size(data.get("Size", "0B"))

                    if "images" in resource_type:
                        usage["images"] = size
                    elif "containers" in resource_type:
                        usage["containers"] = size
                    elif "volumes" in resource_type:
                        usage["volumes"] = size
                    elif "build" in resource_type:
                        usage["build_cache"] = size

                except (json.JSONDecodeError, KeyError):
                    continue

            return usage

        except subprocess.CalledProcessError:
            return {"images": 0, "containers": 0, "volumes": 0, "build_cache": 0}

    def cleanup_containers(self, days: int = 7) -> Tuple[int, int]:
        """Clean up stopped containers older than specified days"""
        hours = days * 24

        try:
            # First, list what will be removed
            list_result = subprocess.run(
                ["docker", "container", "ls", "-a", "--filter", f"until={hours}h", "--filter", "status=exited", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                check=True
            )

            containers_to_remove = []
            for line in list_result.stdout.strip().split('\n'):
                if line:
                    try:
                        container = json.loads(line)
                        containers_to_remove.append({
                            "id": container["ID"][:12],
                            "name": container["Names"],
                            "image": container["Image"],
                            "status": container["Status"]
                        })
                    except (json.JSONDecodeError, KeyError):
                        continue

            if not containers_to_remove:
                console.print("[yellow]No stopped containers to remove[/yellow]")
                return 0, 0

            # Display containers
            table = Table(title=f"Stopped Containers (>{days} days old)")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Image")
            table.add_column("Status", style="yellow")

            for container in containers_to_remove:
                table.add_row(
                    container["id"],
                    container["name"],
                    container["image"],
                    container["status"]
                )

            console.print(table)

            if not self.dry_run and not Confirm.ask(f"\nRemove {len(containers_to_remove)} stopped containers?"):
                console.print("[yellow]Skipped container cleanup[/yellow]")
                return 0, 0

            if self.dry_run:
                console.print(f"[cyan][DRY RUN] Would remove {len(containers_to_remove)} containers[/cyan]")
                return len(containers_to_remove), 0

            # Execute cleanup
            result = subprocess.run(
                ["docker", "container", "prune", "--filter", f"until={hours}h", "-f"],
                capture_output=True,
                text=True,
                check=True
            )

            # Parse space freed
            space_freed = 0
            for line in result.stdout.split('\n'):
                if "Total reclaimed space:" in line:
                    size_str = line.split(":")[-1].strip()
                    space_freed = self.parse_size(size_str)

            self.cleanup_results["actions"].append({
                "type": "containers",
                "count": len(containers_to_remove),
                "space_freed": space_freed
            })

            console.print(f"[green]✓ Removed {len(containers_to_remove)} containers ({self.format_bytes(space_freed)} freed)[/green]")
            return len(containers_to_remove), space_freed

        except subprocess.CalledProcessError as e:
            error_msg = f"Error cleaning up containers: {e}"
            console.print(f"[red]{error_msg}[/red]")
            self.cleanup_results["errors"].append(error_msg)
            return 0, 0

    def cleanup_images(self, days: int = 30, all_images: bool = False) -> Tuple[int, int]:
        """Clean up unused images older than specified days"""
        hours = days * 24

        try:
            # Build command
            cmd = ["docker", "image", "prune", "--filter", f"until={hours}h"]
            if all_images:
                cmd.append("-a")

            # First, list what will be removed (dry run)
            list_cmd = cmd + ["--format", "{{json .}}"]

            # Get current images count
            images_result = subprocess.run(
                ["docker", "images", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                check=True
            )

            total_images = len([l for l in images_result.stdout.strip().split('\n') if l])

            console.print(f"\n[cyan]Found {total_images} total images[/cyan]")
            console.print(f"[cyan]Scanning for {'all ' if all_images else 'dangling '}images older than {days} days...[/cyan]")

            if not self.dry_run and not Confirm.ask(f"\nPrune {'all ' if all_images else 'dangling '}images older than {days} days?"):
                console.print("[yellow]Skipped image cleanup[/yellow]")
                return 0, 0

            if self.dry_run:
                console.print(f"[cyan][DRY RUN] Would prune {'all ' if all_images else 'dangling '}images[/cyan]")
                return 0, 0

            # Execute cleanup
            cmd.append("-f")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Parse results
            deleted_count = 0
            space_freed = 0

            for line in result.stdout.split('\n'):
                if "Total reclaimed space:" in line:
                    size_str = line.split(":")[-1].strip()
                    space_freed = self.parse_size(size_str)
                elif line.startswith("Deleted Images:"):
                    # Count deleted images
                    deleted_count = len([l for l in result.stdout.split('\n') if l.startswith('deleted:')])

            self.cleanup_results["actions"].append({
                "type": "images",
                "count": deleted_count,
                "space_freed": space_freed
            })

            console.print(f"[green]✓ Removed {deleted_count} images ({self.format_bytes(space_freed)} freed)[/green]")
            return deleted_count, space_freed

        except subprocess.CalledProcessError as e:
            error_msg = f"Error cleaning up images: {e}"
            console.print(f"[red]{error_msg}[/red]")
            self.cleanup_results["errors"].append(error_msg)
            return 0, 0

    def cleanup_volumes(self) -> Tuple[int, int]:
        """Clean up unused volumes"""
        try:
            # First, list volumes
            list_result = subprocess.run(
                ["docker", "volume", "ls", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                check=True
            )

            total_volumes = len([l for l in list_result.stdout.strip().split('\n') if l])

            console.print(f"\n[cyan]Found {total_volumes} total volumes[/cyan]")

            if not self.dry_run and not Confirm.ask("\nRemove unused volumes? [red](WARNING: This cannot be undone)[/red]"):
                console.print("[yellow]Skipped volume cleanup[/yellow]")
                return 0, 0

            if self.dry_run:
                console.print("[cyan][DRY RUN] Would prune unused volumes[/cyan]")
                return 0, 0

            # Execute cleanup
            result = subprocess.run(
                ["docker", "volume", "prune", "-f"],
                capture_output=True,
                text=True,
                check=True
            )

            # Parse results
            space_freed = 0
            for line in result.stdout.split('\n'):
                if "Total reclaimed space:" in line:
                    size_str = line.split(":")[-1].strip()
                    space_freed = self.parse_size(size_str)

            deleted_count = len([l for l in result.stdout.split('\n') if l.startswith('deleted:')])

            self.cleanup_results["actions"].append({
                "type": "volumes",
                "count": deleted_count,
                "space_freed": space_freed
            })

            console.print(f"[green]✓ Removed {deleted_count} volumes ({self.format_bytes(space_freed)} freed)[/green]")
            return deleted_count, space_freed

        except subprocess.CalledProcessError as e:
            error_msg = f"Error cleaning up volumes: {e}"
            console.print(f"[red]{error_msg}[/red]")
            self.cleanup_results["errors"].append(error_msg)
            return 0, 0

    def cleanup_networks(self) -> Tuple[int, int]:
        """Clean up unused networks"""
        try:
            # First, list networks
            list_result = subprocess.run(
                ["docker", "network", "ls", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                check=True
            )

            total_networks = len([l for l in list_result.stdout.strip().split('\n') if l])

            console.print(f"\n[cyan]Found {total_networks} total networks[/cyan]")

            if not self.dry_run and not Confirm.ask("\nRemove unused networks?"):
                console.print("[yellow]Skipped network cleanup[/yellow]")
                return 0, 0

            if self.dry_run:
                console.print("[cyan][DRY RUN] Would prune unused networks[/cyan]")
                return 0, 0

            # Execute cleanup
            result = subprocess.run(
                ["docker", "network", "prune", "-f"],
                capture_output=True,
                text=True,
                check=True
            )

            deleted_count = len([l for l in result.stdout.split('\n') if l.startswith('deleted:')])

            self.cleanup_results["actions"].append({
                "type": "networks",
                "count": deleted_count,
                "space_freed": 0
            })

            console.print(f"[green]✓ Removed {deleted_count} networks[/green]")
            return deleted_count, 0

        except subprocess.CalledProcessError as e:
            error_msg = f"Error cleaning up networks: {e}"
            console.print(f"[red]{error_msg}[/red]")
            self.cleanup_results["errors"].append(error_msg)
            return 0, 0

    def cleanup_build_cache(self) -> int:
        """Clean up Docker build cache"""
        try:
            if not self.dry_run and not Confirm.ask("\nRemove build cache?"):
                console.print("[yellow]Skipped build cache cleanup[/yellow]")
                return 0

            if self.dry_run:
                console.print("[cyan][DRY RUN] Would prune build cache[/cyan]")
                return 0

            result = subprocess.run(
                ["docker", "builder", "prune", "-f"],
                capture_output=True,
                text=True,
                check=True
            )

            space_freed = 0
            for line in result.stdout.split('\n'):
                if "Total reclaimed space:" in line or "Total:" in line:
                    size_str = line.split(":")[-1].strip()
                    space_freed = self.parse_size(size_str)

            self.cleanup_results["actions"].append({
                "type": "build_cache",
                "count": 1,
                "space_freed": space_freed
            })

            console.print(f"[green]✓ Cleared build cache ({self.format_bytes(space_freed)} freed)[/green]")
            return space_freed

        except subprocess.CalledProcessError as e:
            error_msg = f"Error cleaning up build cache: {e}"
            console.print(f"[red]{error_msg}[/red]")
            self.cleanup_results["errors"].append(error_msg)
            return 0

    def display_final_report(self, space_before: Dict[str, int]) -> None:
        """Display final cleanup report"""
        console.print("\n[bold cyan]Cleanup Summary[/bold cyan]\n")

        # Get current usage
        space_after = self.get_current_disk_usage()

        # Calculate total freed
        total_freed = sum(action["space_freed"] for action in self.cleanup_results["actions"])
        self.cleanup_results["space_freed"] = total_freed

        # Display actions
        if self.cleanup_results["actions"]:
            table = Table(title="Actions Performed")
            table.add_column("Resource Type", style="cyan")
            table.add_column("Items Removed", justify="right")
            table.add_column("Space Freed", justify="right", style="green")

            for action in self.cleanup_results["actions"]:
                table.add_row(
                    action["type"].replace("_", " ").title(),
                    str(action["count"]),
                    self.format_bytes(action["space_freed"])
                )

            console.print(table)

        # Display space comparison
        console.print(f"\n[bold]Total Space Freed:[/bold] [green]{self.format_bytes(total_freed)}[/green]")

        # Display errors if any
        if self.cleanup_results["errors"]:
            console.print("\n[bold red]Errors:[/bold red]")
            for error in self.cleanup_results["errors"]:
                console.print(f"  • {error}")

    def export_report(self, output_file: str = "docker-cleanup-report.json") -> None:
        """Export cleanup report to JSON"""
        try:
            with open(output_file, 'w') as f:
                json.dump(self.cleanup_results, f, indent=2)
            console.print(f"\n[green]Cleanup report saved to: {output_file}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving report: {e}[/red]")

    def run_cleanup(
        self,
        container_days: int = 7,
        image_days: int = 30,
        all_images: bool = False,
        skip_volumes: bool = False,
        skip_networks: bool = False,
        skip_build_cache: bool = False
    ) -> None:
        """Run complete cleanup workflow"""
        if not self.check_docker_available():
            sys.exit(1)

        console.print("[bold cyan]Docker Resource Cleanup[/bold cyan]\n")

        if self.dry_run:
            console.print("[yellow]Running in DRY RUN mode - no changes will be made[/yellow]\n")

        # Get initial disk usage
        space_before = self.get_current_disk_usage()

        # Cleanup workflow
        console.print("[bold]Step 1: Containers[/bold]")
        self.cleanup_containers(container_days)

        console.print("\n[bold]Step 2: Images[/bold]")
        self.cleanup_images(image_days, all_images)

        if not skip_volumes:
            console.print("\n[bold]Step 3: Volumes[/bold]")
            self.cleanup_volumes()

        if not skip_networks:
            console.print("\n[bold]Step 4: Networks[/bold]")
            self.cleanup_networks()

        if not skip_build_cache:
            console.print("\n[bold]Step 5: Build Cache[/bold]")
            self.cleanup_build_cache()

        # Display final report
        self.display_final_report(space_before)

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Orchestrate Docker resource cleanup")
    parser.add_argument(
        "--container-days",
        type=int,
        default=7,
        help="Remove stopped containers older than N days (default: 7)"
    )
    parser.add_argument(
        "--image-days",
        type=int,
        default=30,
        help="Remove unused images older than N days (default: 30)"
    )
    parser.add_argument(
        "--all-images",
        action="store_true",
        help="Remove all unused images (not just dangling)"
    )
    parser.add_argument(
        "--skip-volumes",
        action="store_true",
        help="Skip volume cleanup"
    )
    parser.add_argument(
        "--skip-networks",
        action="store_true",
        help="Skip network cleanup"
    )
    parser.add_argument(
        "--skip-build-cache",
        action="store_true",
        help="Skip build cache cleanup"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleaned without making changes"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docker-cleanup-report.json",
        help="Output file for cleanup report (default: docker-cleanup-report.json)"
    )

    args = parser.parse_args()

    cleanup = DockerCleanup(dry_run=args.dry_run)
    cleanup.run_cleanup(
        container_days=args.container_days,
        image_days=args.image_days,
        all_images=args.all_images,
        skip_volumes=args.skip_volumes,
        skip_networks=args.skip_networks,
        skip_build_cache=args.skip_build_cache
    )
    cleanup.export_report(args.output)

if __name__ == "__main__":
    main()
