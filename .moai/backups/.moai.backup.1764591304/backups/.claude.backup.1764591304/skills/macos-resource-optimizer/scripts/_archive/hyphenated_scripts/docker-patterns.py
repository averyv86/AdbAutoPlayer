#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "rich>=13.0.0",
# ]
# ///

"""
Docker Container Pattern Detection
Classifies containers and detects potential issues
"""

import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class DockerPatternDetector:
    def __init__(self):
        self.containers = []
        self.patterns = {
            "production": [],
            "development": [],
            "one_off": [],
            "zombie": [],
            "high_risk": []
        }
        self.port_conflicts = []
        self.duplicate_services = []

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

    def get_container_details(self, container_id: str) -> Dict[str, Any]:
        """Get detailed container information"""
        try:
            result = subprocess.run(
                ["docker", "inspect", container_id],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)[0]
        except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError):
            return {}

    def calculate_uptime_days(self, started_at: str) -> int:
        """Calculate container uptime in days"""
        try:
            started = datetime.fromisoformat(started_at.replace("Z", "+00:00")).replace(tzinfo=None)
            return (datetime.now() - started).days
        except (ValueError, AttributeError):
            return 0

    def classify_container_type(self, container: Dict[str, Any]) -> str:
        """Classify container as production/development/one-off based on patterns"""
        name = container.get("name", "").lower()
        image = container.get("image", "").lower()
        env_vars = container.get("env", {})
        ports = container.get("ports", [])
        uptime_days = container.get("uptime_days", 0)
        restart_count = container.get("restart_count", 0)
        state = container.get("state", "")

        # Production indicators
        production_score = 0

        # Long uptime suggests production
        if uptime_days > 30:
            production_score += 3
        elif uptime_days > 7:
            production_score += 1

        # High restart count suggests critical service
        if restart_count > 10:
            production_score += 2
        elif restart_count > 5:
            production_score += 1

        # Production environment variables
        prod_env_indicators = ["production", "prod", "live"]
        for var_name, var_value in env_vars.items():
            if any(indicator in str(var_value).lower() for indicator in prod_env_indicators):
                production_score += 2
            if "node_env" in var_name.lower() and "production" in str(var_value).lower():
                production_score += 3
            if "flask_env" in var_name.lower() and "production" in str(var_value).lower():
                production_score += 3

        # Standard production ports
        production_ports = [80, 443, 8080, 8443]
        if any(port in production_ports for port in ports):
            production_score += 2

        # Development indicators
        dev_score = 0

        # Development environment variables
        dev_env_indicators = ["development", "dev", "test", "debug", "local"]
        for var_name, var_value in env_vars.items():
            if any(indicator in str(var_value).lower() for indicator in dev_env_indicators):
                dev_score += 2
            if "debug" in var_name.lower() and str(var_value).lower() in ["true", "1"]:
                dev_score += 2

        # Development ports (common dev server ports)
        dev_ports = range(3000, 9001)
        if any(port in dev_ports for port in ports):
            dev_score += 1

        # Development naming patterns
        dev_patterns = ["dev", "test", "local", "debug", "tmp"]
        if any(pattern in name for pattern in dev_patterns):
            dev_score += 2
        if any(pattern in image for pattern in dev_patterns):
            dev_score += 1

        # One-off indicators
        oneoff_score = 0

        # Short-lived containers
        if state == "exited" and uptime_days < 1:
            oneoff_score += 3

        # One-off naming patterns
        oneoff_patterns = ["temp", "tmp", "test", "once", "run"]
        if any(pattern in name for pattern in oneoff_patterns):
            oneoff_score += 2

        # No restart policy
        if restart_count == 0 and uptime_days < 7:
            oneoff_score += 1

        # Classify based on scores
        if production_score >= 5:
            return "production"
        elif dev_score >= 3:
            return "development"
        elif oneoff_score >= 3:
            return "one_off"
        elif production_score > dev_score:
            return "production"
        elif dev_score > 0:
            return "development"
        else:
            return "unknown"

    def calculate_risk_score(self, container: Dict[str, Any]) -> int:
        """Calculate risk score for container deletion (0-100, higher = riskier)"""
        risk_score = 0

        # Running containers are high risk to delete
        if container["state"] == "running":
            risk_score += 50

        # Long uptime suggests important service
        uptime_days = container.get("uptime_days", 0)
        if uptime_days > 90:
            risk_score += 30
        elif uptime_days > 30:
            risk_score += 20
        elif uptime_days > 7:
            risk_score += 10

        # High restart count suggests critical service
        restart_count = container.get("restart_count", 0)
        if restart_count > 20:
            risk_score += 20
        elif restart_count > 10:
            risk_score += 10

        # Production classification increases risk
        if container.get("classification") == "production":
            risk_score += 30
        elif container.get("classification") == "development":
            risk_score += 5

        # Named containers are often important
        name = container.get("name", "")
        if not any(pattern in name for pattern in ["temp", "tmp", "test"]):
            risk_score += 10

        # Volumes increase risk (data could be lost)
        if container.get("has_volumes", False):
            risk_score += 15

        return min(risk_score, 100)

    def detect_port_conflicts(self) -> None:
        """Detect containers using the same ports"""
        port_map = {}

        for container in self.containers:
            for port in container.get("ports", []):
                if port not in port_map:
                    port_map[port] = []
                port_map[port].append({
                    "id": container["id"],
                    "name": container["name"],
                    "state": container["state"]
                })

        # Find conflicts (same port, multiple containers, at least one running)
        for port, containers in port_map.items():
            if len(containers) > 1:
                running_count = sum(1 for c in containers if c["state"] == "running")
                if running_count > 1:
                    self.port_conflicts.append({
                        "port": port,
                        "containers": containers,
                        "severity": "critical" if running_count > 1 else "warning"
                    })

    def detect_duplicate_services(self) -> None:
        """Detect duplicate services (same image, different containers)"""
        image_map = {}

        for container in self.containers:
            image = container.get("image", "")
            if image:
                if image not in image_map:
                    image_map[image] = []
                image_map[image].append({
                    "id": container["id"],
                    "name": container["name"],
                    "state": container["state"],
                    "uptime_days": container.get("uptime_days", 0)
                })

        # Find duplicates
        for image, containers in image_map.items():
            if len(containers) > 1:
                running_count = sum(1 for c in containers if c["state"] == "running")
                self.duplicate_services.append({
                    "image": image,
                    "count": len(containers),
                    "running": running_count,
                    "containers": containers
                })

    def analyze_containers(self) -> None:
        """Analyze all containers and classify them"""
        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                check=True
            )

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                try:
                    basic_info = json.loads(line)
                    detailed_info = self.get_container_details(basic_info["ID"])

                    if not detailed_info:
                        continue

                    # Extract environment variables
                    env_vars = {}
                    for env_str in detailed_info.get("Config", {}).get("Env", []):
                        if "=" in env_str:
                            key, value = env_str.split("=", 1)
                            env_vars[key] = value

                    # Extract ports
                    ports = []
                    port_bindings = detailed_info.get("NetworkSettings", {}).get("Ports", {})
                    if port_bindings:
                        for container_port, host_bindings in port_bindings.items():
                            if host_bindings:
                                for binding in host_bindings:
                                    try:
                                        ports.append(int(binding.get("HostPort", 0)))
                                    except (ValueError, TypeError):
                                        pass

                    # Calculate uptime
                    started_at = detailed_info.get("State", {}).get("StartedAt", "")
                    uptime_days = self.calculate_uptime_days(started_at)

                    container = {
                        "id": basic_info["ID"][:12],
                        "name": basic_info["Names"],
                        "image": basic_info["Image"],
                        "state": basic_info["State"],
                        "status": basic_info["Status"],
                        "created": detailed_info.get("Created", ""),
                        "started_at": started_at,
                        "uptime_days": uptime_days,
                        "restart_count": detailed_info.get("RestartCount", 0),
                        "env": env_vars,
                        "ports": ports,
                        "has_volumes": len(detailed_info.get("Mounts", [])) > 0,
                        "labels": detailed_info.get("Config", {}).get("Labels", {})
                    }

                    # Classify container
                    container["classification"] = self.classify_container_type(container)

                    # Calculate risk score
                    container["risk_score"] = self.calculate_risk_score(container)

                    # Add to containers list
                    self.containers.append(container)

                    # Add to pattern category
                    classification = container["classification"]
                    if classification in self.patterns:
                        self.patterns[classification].append(container)

                    # Identify zombies (stopped for >30 days)
                    if container["state"] == "exited" and uptime_days > 30:
                        self.patterns["zombie"].append(container)

                    # Identify high risk (risk score > 70)
                    if container["risk_score"] > 70:
                        self.patterns["high_risk"].append(container)

                except (json.JSONDecodeError, KeyError) as e:
                    console.print(f"[yellow]Warning: Error parsing container: {e}[/yellow]")
                    continue

            # Detect conflicts and duplicates
            self.detect_port_conflicts()
            self.detect_duplicate_services()

        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error analyzing containers: {e}[/red]")

    def display_classification_summary(self) -> None:
        """Display container classification summary"""
        console.print("\n[bold cyan]Container Classification Summary[/bold cyan]\n")

        # Pattern distribution
        table = Table(title="Container Distribution")
        table.add_column("Type", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Running", justify="right", style="green")
        table.add_column("Stopped", justify="right", style="yellow")

        for pattern_type in ["production", "development", "one_off", "zombie"]:
            containers = self.patterns[pattern_type]
            running = sum(1 for c in containers if c["state"] == "running")
            stopped = len(containers) - running

            table.add_row(
                pattern_type.replace("_", " ").title(),
                str(len(containers)),
                str(running),
                str(stopped)
            )

        console.print(table)

    def display_high_risk_containers(self) -> None:
        """Display high-risk containers"""
        if not self.patterns["high_risk"]:
            return

        console.print("\n[bold yellow]⚠️  High-Risk Containers (Risk Score > 70)[/bold yellow]\n")

        table = Table()
        table.add_column("Name", style="cyan")
        table.add_column("Type")
        table.add_column("State")
        table.add_column("Uptime", justify="right")
        table.add_column("Risk Score", justify="right", style="red")

        for container in sorted(self.patterns["high_risk"], key=lambda x: x["risk_score"], reverse=True):
            table.add_row(
                container["name"],
                container["classification"],
                container["state"],
                f"{container['uptime_days']}d",
                f"{container['risk_score']}/100"
            )

        console.print(table)

    def display_port_conflicts(self) -> None:
        """Display port conflicts"""
        if not self.port_conflicts:
            return

        console.print("\n[bold red]🚨 Port Conflicts Detected[/bold red]\n")

        for conflict in self.port_conflicts:
            severity_color = "red" if conflict["severity"] == "critical" else "yellow"
            console.print(f"[{severity_color}]Port {conflict['port']}:[/{severity_color}]")

            for container in conflict["containers"]:
                state_color = "green" if container["state"] == "running" else "dim"
                console.print(f"  • [{state_color}]{container['name']} ({container['id']}) - {container['state']}[/{state_color}]")

            console.print()

    def display_duplicate_services(self) -> None:
        """Display duplicate services"""
        if not self.duplicate_services:
            return

        console.print("\n[bold yellow]Duplicate Services Detected[/bold yellow]\n")

        for duplicate in sorted(self.duplicate_services, key=lambda x: x["count"], reverse=True):
            console.print(f"[cyan]Image:[/cyan] {duplicate['image']}")
            console.print(f"[yellow]Instances:[/yellow] {duplicate['count']} total, {duplicate['running']} running")

            for container in duplicate["containers"]:
                state_color = "green" if container["state"] == "running" else "dim"
                console.print(f"  • [{state_color}]{container['name']} ({container['id']}) - {container['state']}, {container['uptime_days']}d uptime[/{state_color}]")

            console.print()

    def display_cleanup_recommendations(self) -> None:
        """Display cleanup recommendations"""
        console.print("\n[bold green]Cleanup Recommendations[/bold green]\n")

        recommendations = []

        # Zombie containers
        if self.patterns["zombie"]:
            recommendations.append(
                f"• Remove {len(self.patterns['zombie'])} zombie containers (stopped >30 days)"
            )

        # One-off containers
        oneoff_stopped = [c for c in self.patterns["one_off"] if c["state"] == "exited"]
        if oneoff_stopped:
            recommendations.append(
                f"• Clean up {len(oneoff_stopped)} one-off containers"
            )

        # Duplicate services
        if self.duplicate_services:
            recommendations.append(
                f"• Review {len(self.duplicate_services)} duplicate services for consolidation"
            )

        # Port conflicts
        if self.port_conflicts:
            recommendations.append(
                f"• Resolve {len(self.port_conflicts)} port conflicts"
            )

        if recommendations:
            for rec in recommendations:
                console.print(rec)
        else:
            console.print("[green]No immediate cleanup recommendations[/green]")

    def export_analysis(self, output_file: str = "docker-patterns.json") -> None:
        """Export pattern analysis to JSON"""
        try:
            analysis_data = {
                "timestamp": datetime.now().isoformat(),
                "total_containers": len(self.containers),
                "patterns": {
                    pattern_type: [
                        {
                            "id": c["id"],
                            "name": c["name"],
                            "state": c["state"],
                            "risk_score": c["risk_score"],
                            "uptime_days": c["uptime_days"]
                        }
                        for c in containers
                    ]
                    for pattern_type, containers in self.patterns.items()
                },
                "port_conflicts": self.port_conflicts,
                "duplicate_services": self.duplicate_services,
                "containers": self.containers
            }

            with open(output_file, 'w') as f:
                json.dump(analysis_data, f, indent=2)

            console.print(f"\n[green]Analysis saved to: {output_file}[/green]")

        except Exception as e:
            console.print(f"[red]Error saving analysis: {e}[/red]")

    def run_analysis(self) -> None:
        """Run complete pattern detection analysis"""
        if not self.check_docker_available():
            sys.exit(1)

        console.print("[cyan]Analyzing Docker container patterns...[/cyan]\n")

        with console.status("[bold green]Analyzing containers..."):
            self.analyze_containers()

        self.display_classification_summary()
        self.display_high_risk_containers()
        self.display_port_conflicts()
        self.display_duplicate_services()
        self.display_cleanup_recommendations()

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Detect Docker container patterns and issues")
    parser.add_argument(
        "--output",
        type=str,
        default="docker-patterns.json",
        help="Output file for pattern analysis (default: docker-patterns.json)"
    )

    args = parser.parse_args()

    detector = DockerPatternDetector()
    detector.run_analysis()
    detector.export_analysis(args.output)

if __name__ == "__main__":
    main()
