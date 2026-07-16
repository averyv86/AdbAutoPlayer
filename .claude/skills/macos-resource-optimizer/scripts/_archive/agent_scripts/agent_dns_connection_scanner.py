#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "psutil>=6.1.0",
#     "click>=8.1.0",
#     "rich>=13.0.0"
# ]
# ///

"""
DNS/Network Cache Hunter - Agent 14

Analyzes DNS and network cache status for optimization.

Detection Targets:
- DNS cache status via dscacheutil
- ARP cache entries via arp -a
- Active network connections count
- Network interface statistics

Reports:
- Stale DNS cache entries
- ARP cache size
- Connection statistics
- Optimization suggestions
"""

import json
import subprocess
import time
from typing import Any, Dict, List

import click
import psutil
from rich.console import Console
from rich.table import Table

console = Console()


def run_command(cmd: List[str], timeout: int = 10) -> tuple[str, int]:
    """Run a command and return output and return code."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "Command timed out", 1
    except Exception as e:
        return str(e), 1


def get_dns_cache_stats() -> Dict[str, Any]:
    """Get DNS cache statistics."""
    stats = {
        "flush_recommended": False,
        "cache_info": {},
        "error": None,
    }

    # Get DNS cache statistics (requires sudo for detailed info)
    output, code = run_command(["dscacheutil", "-statistics"])

    if code == 0:
        lines = output.strip().split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                stats["cache_info"][key.strip()] = value.strip()
    else:
        stats["error"] = "Could not retrieve DNS statistics"

    return stats


def get_arp_cache() -> Dict[str, Any]:
    """Get ARP cache entries."""
    result = {
        "entries": [],
        "total_count": 0,
        "stale_count": 0,
    }

    output, code = run_command(["arp", "-a"])

    if code == 0:
        for line in output.strip().split('\n'):
            if line and '(' in line:
                result["entries"].append(line.strip())
                result["total_count"] += 1

                # Check for incomplete entries (potential stale)
                if "incomplete" in line.lower():
                    result["stale_count"] += 1

    return result


def get_network_connections() -> Dict[str, Any]:
    """Get network connection statistics using netstat (more reliable on macOS)."""
    stats = {
        "total": 0,
        "established": 0,
        "listening": 0,
        "time_wait": 0,
        "close_wait": 0,
        "other": 0,
        "by_status": {},
        "error": None,
    }

    # Use netstat instead of psutil (avoids permission issues on macOS)
    output, code = run_command(["netstat", "-an"])

    if code != 0:
        stats["error"] = "Could not retrieve connection statistics"
        return stats

    for line in output.strip().split('\n'):
        # Parse TCP/UDP lines
        if 'tcp' in line.lower() or 'udp' in line.lower():
            stats["total"] += 1
            parts = line.split()

            # Find status (usually last column for TCP)
            status = "UNKNOWN"
            if len(parts) >= 6 and 'tcp' in line.lower():
                status = parts[-1] if parts[-1].isupper() else "UNKNOWN"
            elif 'udp' in line.lower():
                status = "UDP"

            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            if status == 'ESTABLISHED':
                stats["established"] += 1
            elif status in ['LISTEN', 'LISTENING']:
                stats["listening"] += 1
            elif status == 'TIME_WAIT':
                stats["time_wait"] += 1
            elif status == 'CLOSE_WAIT':
                stats["close_wait"] += 1
            else:
                stats["other"] += 1

    return stats


def get_network_io_stats() -> Dict[str, Any]:
    """Get network I/O statistics."""
    io_counters = psutil.net_io_counters()

    return {
        "bytes_sent": io_counters.bytes_sent,
        "bytes_recv": io_counters.bytes_recv,
        "packets_sent": io_counters.packets_sent,
        "packets_recv": io_counters.packets_recv,
        "errors_in": io_counters.errin,
        "errors_out": io_counters.errout,
        "drops_in": io_counters.dropin,
        "drops_out": io_counters.dropout,
    }


def get_interface_stats() -> List[Dict[str, Any]]:
    """Get per-interface statistics."""
    interfaces = []
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    for iface_name, iface_stats in stats.items():
        iface_info = {
            "name": iface_name,
            "is_up": iface_stats.isup,
            "speed": iface_stats.speed,
            "mtu": iface_stats.mtu,
            "addresses": [],
        }

        if iface_name in addrs:
            for addr in addrs[iface_name]:
                if addr.family.name == 'AF_INET':
                    iface_info["addresses"].append({
                        "type": "IPv4",
                        "address": addr.address,
                    })
                elif addr.family.name == 'AF_INET6':
                    iface_info["addresses"].append({
                        "type": "IPv6",
                        "address": addr.address[:30] + "..." if len(addr.address) > 30 else addr.address,
                    })

        interfaces.append(iface_info)

    return interfaces


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"


def detect_network_zombies(verbose: bool = False) -> Dict[str, Any]:
    """Main detection function for DNS/network analysis."""
    start_time = time.time()

    if verbose:
        console.print("[cyan]Analyzing DNS and network caches...[/cyan]\n")

    dns_stats = get_dns_cache_stats()
    arp_cache = get_arp_cache()
    conn_stats = get_network_connections()
    io_stats = get_network_io_stats()
    interfaces = get_interface_stats()

    # Determine recommendations
    recommendations = []
    zombies_found = 0
    actions = 0

    # Check for stale ARP entries
    if arp_cache["stale_count"] > 0:
        recommendations.append(f"Found {arp_cache['stale_count']} incomplete ARP entries")
        zombies_found += arp_cache["stale_count"]
        actions += 1

    # Check for excessive TIME_WAIT connections
    if conn_stats["time_wait"] > 100:
        recommendations.append(f"High TIME_WAIT connections ({conn_stats['time_wait']})")
        zombies_found += 1
        actions += 1

    # Check for CLOSE_WAIT connections (potential leaks)
    if conn_stats["close_wait"] > 10:
        recommendations.append(f"CLOSE_WAIT connections detected ({conn_stats['close_wait']}) - potential socket leaks")
        zombies_found += conn_stats["close_wait"]
        actions += 1

    # Check for network errors
    if io_stats["errors_in"] + io_stats["errors_out"] > 100:
        recommendations.append("High network error count - consider checking interfaces")
        actions += 1

    # DNS flush recommendation
    dns_flush_cmd = "sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder"

    execution_time = (time.time() - start_time) * 1000

    return {
        "zombies_found": zombies_found,
        "memory_freed_mb": 0,  # Network cleanup doesn't free memory directly
        "actions_taken": actions,
        "status": "success",
        "time_ms": round(execution_time, 2),
        "details": {
            "dns": dns_stats,
            "arp_cache": {
                "total_entries": arp_cache["total_count"],
                "stale_entries": arp_cache["stale_count"],
            },
            "connections": conn_stats,
            "io_stats": {
                "bytes_sent": format_bytes(io_stats["bytes_sent"]),
                "bytes_recv": format_bytes(io_stats["bytes_recv"]),
                "packets_sent": io_stats["packets_sent"],
                "packets_recv": io_stats["packets_recv"],
                "errors": io_stats["errors_in"] + io_stats["errors_out"],
                "drops": io_stats["drops_in"] + io_stats["drops_out"],
            },
            "interfaces": len([i for i in interfaces if i["is_up"]]),
            "recommendations": recommendations,
            "dns_flush_command": dns_flush_cmd,
        }
    }


def print_table(result: Dict[str, Any]) -> None:
    """Print results in table format."""
    # Connection stats table
    table = Table(title="Network Connection Statistics")
    table.add_column("Status", style="cyan")
    table.add_column("Count", justify="right")

    for status, count in result["details"]["connections"]["by_status"].items():
        style = "red" if status in ['CLOSE_WAIT', 'TIME_WAIT'] and count > 10 else "white"
        table.add_row(status, str(count), style=style)

    console.print(table)

    # I/O stats
    io = result["details"]["io_stats"]
    console.print(f"\n[bold]Network I/O:[/bold]")
    console.print(f"  Sent: {io['bytes_sent']} ({io['packets_sent']} packets)")
    console.print(f"  Received: {io['bytes_recv']} ({io['packets_recv']} packets)")
    console.print(f"  Errors: {io['errors']}, Drops: {io['drops']}")


def print_summary(result: Dict[str, Any]) -> None:
    """Print summary format."""
    console.print(f"\n[bold]DNS/Network Cache Analysis[/bold]")
    console.print(f"Status: {result['status']}")
    console.print(f"Issues found: {result['zombies_found']}")
    console.print(f"Execution time: {result['time_ms']:.2f}ms")

    console.print(f"\n[bold]Statistics:[/bold]")
    console.print(f"  Active connections: {result['details']['connections']['total']}")
    console.print(f"  Established: {result['details']['connections']['established']}")
    console.print(f"  Listening: {result['details']['connections']['listening']}")
    console.print(f"  TIME_WAIT: {result['details']['connections']['time_wait']}")
    console.print(f"  CLOSE_WAIT: {result['details']['connections']['close_wait']}")

    arp = result["details"]["arp_cache"]
    console.print(f"\n[bold]ARP Cache:[/bold]")
    console.print(f"  Total entries: {arp['total_entries']}")
    console.print(f"  Stale entries: {arp['stale_entries']}")

    if result["details"]["recommendations"]:
        console.print(f"\n[bold]Recommendations:[/bold]")
        for rec in result["details"]["recommendations"]:
            console.print(f"  [yellow]- {rec}[/yellow]")

    console.print(f"\n[dim]DNS flush command: {result['details']['dns_flush_command']}[/dim]")


@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'summary']),
              default='summary', help='Output format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def main(format: str, verbose: bool) -> None:
    """Analyze DNS and network caches for optimization."""
    result = detect_network_zombies(verbose=verbose)

    if format == 'json':
        click.echo(json.dumps(result, indent=2))
    elif format == 'table':
        print_table(result)
    elif format == 'summary':
        print_summary(result)


if __name__ == '__main__':
    main()
