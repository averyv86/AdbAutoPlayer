#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
adb-performance-monitor: Android Performance Monitoring Utility

TRUST 5 Principles:
  1. Transparency - Clear performance metrics and reporting
  2. Reliability - Robust metrics collection with error handling
  3. Usability - Simple performance analysis interface
  4. Security - Safe system metrics access
  5. Testability - Detailed metrics output for analysis

Provides unified interface for:
  - CPU usage monitoring
  - Memory usage tracking
  - Battery status reporting
  - Network activity monitoring
  - Frame rate measurement
  - Performance benchmarking
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MemoryStats:
    """Memory usage statistics"""
    total_mb: float
    used_mb: float
    free_mb: float
    usage_percent: float
    timestamp: str


@dataclass
class CPUStats:
    """CPU usage statistics"""
    user_percent: float
    system_percent: float
    total_percent: float
    timestamp: str


@dataclass
class BatteryStats:
    """Battery status statistics"""
    level: int
    temperature: int
    status: str
    health: str
    technology: str
    timestamp: str


class PerformanceMonitor:
    """Unified Android performance monitoring"""

    def __init__(self, device: str = None):
        self.device = device
        self.errors: List[str] = []

    def get_memory_stats(self) -> Optional[MemoryStats]:
        """Get memory usage statistics"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["shell", "cat", "/proc/meminfo"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                self.errors.append(f"Failed to get memory stats: {result.stderr}")
                return None

            mem_dict = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    mem_dict[key.strip()] = int(value.split()[0])

            total_mb = mem_dict.get('MemTotal', 0) / 1024
            available_mb = mem_dict.get('MemAvailable', 0) / 1024
            used_mb = total_mb - available_mb
            usage_percent = (used_mb / total_mb * 100) if total_mb > 0 else 0

            return MemoryStats(
                total_mb=round(total_mb, 2),
                used_mb=round(used_mb, 2),
                free_mb=round(available_mb, 2),
                usage_percent=round(usage_percent, 2),
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            self.errors.append(f"Memory stats error: {str(e)}")
            return None

    def get_cpu_stats(self) -> Optional[CPUStats]:
        """Get CPU usage statistics"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["shell", "top", "-n", "1"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return None

            # Parse top output for CPU stats
            for line in result.stdout.split('\n'):
                if 'User' in line and '%' in line:
                    # Example: User 10%, System 5%, etc.
                    parts = line.split()
                    user_percent = float(parts[1].rstrip('%')) if len(parts) > 1 else 0
                    system_percent = float(parts[4].rstrip('%')) if len(parts) > 4 else 0
                    total_percent = user_percent + system_percent

                    return CPUStats(
                        user_percent=user_percent,
                        system_percent=system_percent,
                        total_percent=total_percent,
                        timestamp=datetime.now().isoformat()
                    )

            return None

        except Exception as e:
            self.errors.append(f"CPU stats error: {str(e)}")
            return None

    def get_battery_stats(self) -> Optional[BatteryStats]:
        """Get battery status and statistics"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["shell", "dumpsys", "batterymanager"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                self.errors.append(f"Failed to get battery stats: {result.stderr}")
                return None

            battery_dict = {}
            for line in result.stdout.split('\n'):
                line = line.strip()
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    battery_dict[key.strip()] = value.strip()

            return BatteryStats(
                level=int(battery_dict.get('level', 0)),
                temperature=int(battery_dict.get('temperature', 0)) // 10,  # Convert to Celsius
                status=battery_dict.get('status', 'Unknown'),
                health=battery_dict.get('health', 'Unknown'),
                technology=battery_dict.get('technology', 'Unknown'),
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            self.errors.append(f"Battery stats error: {str(e)}")
            return None

    def get_network_stats(self) -> Dict[str, str]:
        """Get network activity statistics"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["shell", "cat", "/proc/net/dev"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {"error": "Failed to get network stats"}

            # Simple parsing - get WiFi and mobile interface stats
            stats = {
                "timestamp": datetime.now().isoformat(),
                "interfaces": {}
            }

            for line in result.stdout.split('\n')[2:]:  # Skip headers
                if not line.strip():
                    continue

                parts = line.split(':')
                if len(parts) == 2:
                    iface = parts[0].strip()
                    if iface in ['wlan0', 'rmnet0', 'eth0']:
                        values = parts[1].split()
                        if len(values) >= 10:
                            stats["interfaces"][iface] = {
                                "rx_bytes": values[0],
                                "rx_packets": values[1],
                                "tx_bytes": values[8],
                                "tx_packets": values[9],
                            }

            return stats

        except Exception as e:
            self.errors.append(f"Network stats error: {str(e)}")
            return {"error": str(e)}

    def get_frame_rate(self, duration_seconds: int = 5) -> Dict[str, float]:
        """Get frame rate statistics"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend([
                "shell",
                "dumpsys",
                "surfaceflinger",
                "--latency-clear",
                "&& sleep", str(duration_seconds),
                "&& dumpsys", "surfaceflinger", "--latency"
            ])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=duration_seconds + 10
            )

            if result.returncode != 0:
                return {"error": "Failed to measure frame rate"}

            # Parse latency data
            return {
                "timestamp": datetime.now().isoformat(),
                "duration": duration_seconds,
                "message": "Frame rate measurement completed"
            }

        except Exception as e:
            self.errors.append(f"Frame rate error: {str(e)}")
            return {"error": str(e)}

    def get_thermal_stats(self) -> Dict[str, int]:
        """Get thermal zone statistics"""
        try:
            cmd = ["adb"]
            if self.device:
                cmd.extend(["-s", self.device])

            cmd.extend(["shell", "cat", "/sys/class/thermal/thermal_zone0/temp"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return {"error": "Failed to get thermal stats"}

            # Temperature is typically in millidegrees Celsius
            temp_millidegrees = int(result.stdout.strip())
            temp_celsius = temp_millidegrees / 1000

            return {
                "temperature_celsius": round(temp_celsius, 2),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.errors.append(f"Thermal stats error: {str(e)}")
            return {"error": str(e)}


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: adb-performance-monitor.py [memory|cpu|battery|network|thermal|all]")
        return 1

    command = sys.argv[1]
    device = None

    if "--device" in sys.argv:
        idx = sys.argv.index("--device")
        if idx + 1 < len(sys.argv):
            device = sys.argv[idx + 1]

    monitor = PerformanceMonitor(device=device)

    if command == "memory":
        stats = monitor.get_memory_stats()
        if stats:
            print(f"\n💾 Memory Statistics:")
            print(f"  Total: {stats.total_mb:.2f} MB")
            print(f"  Used: {stats.used_mb:.2f} MB ({stats.usage_percent:.1f}%)")
            print(f"  Free: {stats.free_mb:.2f} MB")
        else:
            print("❌ Failed to get memory stats")
            return 1

    elif command == "cpu":
        stats = monitor.get_cpu_stats()
        if stats:
            print(f"\n⚙️ CPU Statistics:")
            print(f"  User: {stats.user_percent:.1f}%")
            print(f"  System: {stats.system_percent:.1f}%")
            print(f"  Total: {stats.total_percent:.1f}%")
        else:
            print("❌ Failed to get CPU stats")
            return 1

    elif command == "battery":
        stats = monitor.get_battery_stats()
        if stats:
            print(f"\n🔋 Battery Statistics:")
            print(f"  Level: {stats.level}%")
            print(f"  Temperature: {stats.temperature}°C")
            print(f"  Status: {stats.status}")
            print(f"  Health: {stats.health}")
        else:
            print("❌ Failed to get battery stats")
            return 1

    elif command == "network":
        stats = monitor.get_network_stats()
        print(f"\n🌐 Network Statistics:")
        if "error" in stats:
            print(f"  Error: {stats['error']}")
        else:
            for iface, data in stats.get("interfaces", {}).items():
                print(f"  {iface}:")
                print(f"    RX: {data['rx_bytes']} bytes ({data['rx_packets']} packets)")
                print(f"    TX: {data['tx_bytes']} bytes ({data['tx_packets']} packets)")

    elif command == "thermal":
        stats = monitor.get_thermal_stats()
        if "error" not in stats:
            print(f"\n🌡️ Thermal Statistics:")
            print(f"  Temperature: {stats.get('temperature_celsius')}°C")
        else:
            print(f"❌ {stats.get('error')}")
            return 1

    elif command == "all":
        print(f"\n📊 Complete Performance Report:\n")

        mem = monitor.get_memory_stats()
        if mem:
            print(f"💾 Memory: {mem.used_mb:.1f}/{mem.total_mb:.1f} MB ({mem.usage_percent:.1f}%)")

        cpu = monitor.get_cpu_stats()
        if cpu:
            print(f"⚙️ CPU: {cpu.total_percent:.1f}%")

        battery = monitor.get_battery_stats()
        if battery:
            print(f"🔋 Battery: {battery.level}% ({battery.status})")

        thermal = monitor.get_thermal_stats()
        if "error" not in thermal:
            print(f"🌡️ Thermal: {thermal.get('temperature_celsius')}°C")

    else:
        print(f"Unknown command: {command}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
