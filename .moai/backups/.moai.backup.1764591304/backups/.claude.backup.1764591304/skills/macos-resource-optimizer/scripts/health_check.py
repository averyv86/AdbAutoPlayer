#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=5.9.0"]
# ///

"""
Health Check System - Continuous System Monitoring

Monitors:
- Extension connectivity
- System resource health
- Process accessibility
- Configuration validity
- Service availability

Provides:
- Real-time health status
- Automated diagnostics
- Recovery recommendations
- Health history tracking

Author: MoAI-ADK
Version: 3.0.0 (Phase 3 - Production)
Date: 2025-12-01
"""

import json
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    component: str
    status: HealthStatus
    message: str
    details: Dict
    checked_at: str
    response_time_ms: float

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "checked_at": self.checked_at,
            "response_time_ms": self.response_time_ms
        }


class HealthChecker:
    """
    Comprehensive health monitoring system.

    Checks all critical components and provides diagnostics.
    """

    def __init__(self):
        """Initialize health checker."""
        self.history_path = Path(__file__).parent.parent / ".moai/logs/health-history.json"
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

    def check_extension_health(self) -> HealthCheckResult:
        """Check Chrome extension health."""
        start_time = time.time()

        manifest_paths = [
            Path.home() / "Library/Application Support/Google/Chrome/NativeMessagingHosts/com.moai.tab_suspender.json",
            Path.home() / "Library/Application Support/Dia Browser/NativeMessagingHosts/com.moai.tab_suspender.json",
        ]

        details = {
            "manifests_found": [],
            "manifests_valid": [],
            "connection_test": False
        }

        # Check manifests exist
        for path in manifest_paths:
            if path.exists():
                details["manifests_found"].append(str(path))

                # Validate manifest
                try:
                    with open(path) as f:
                        manifest = json.load(f)

                    if all(key in manifest for key in ["name", "path", "allowed_origins"]):
                        details["manifests_valid"].append(str(path))
                except Exception as e:
                    details["validation_error"] = str(e)

        # Test connection
        try:
            script_path = Path(__file__).parent / "tab_suspender.py"
            if script_path.exists():
                result = subprocess.run(
                    ["uv", "run", str(script_path), "--test"],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                details["connection_test"] = result.returncode == 0
        except Exception as e:
            details["connection_error"] = str(e)

        response_time = (time.time() - start_time) * 1000

        # Determine status
        if details["manifests_valid"] and details["connection_test"]:
            status = HealthStatus.HEALTHY
            message = "Extension fully operational"
        elif details["manifests_found"]:
            status = HealthStatus.DEGRADED
            message = "Extension configured but connection issues"
        else:
            status = HealthStatus.UNHEALTHY
            message = "Extension not installed"

        return HealthCheckResult(
            component="chrome_extension",
            status=status,
            message=message,
            details=details,
            checked_at=datetime.now().isoformat(),
            response_time_ms=response_time
        )

    def check_memory_health(self) -> HealthCheckResult:
        """Check system memory health."""
        start_time = time.time()

        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            details = {
                "memory_percent": mem.percent,
                "memory_available_gb": round(mem.available / 1024 / 1024 / 1024, 2),
                "swap_percent": swap.percent,
                "swap_used_gb": round(swap.used / 1024 / 1024 / 1024, 2)
            }

            # Determine status
            if mem.percent < 70 and swap.percent < 50:
                status = HealthStatus.HEALTHY
                message = "Memory usage normal"
            elif mem.percent < 85 and swap.percent < 80:
                status = HealthStatus.DEGRADED
                message = "Memory usage elevated"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Memory critically high"

        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = f"Memory check failed: {e}"
            details = {"error": str(e)}

        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            component="system_memory",
            status=status,
            message=message,
            details=details,
            checked_at=datetime.now().isoformat(),
            response_time_ms=response_time
        )

    def check_process_health(self) -> HealthCheckResult:
        """Check process enumeration health."""
        start_time = time.time()

        try:
            total = 0
            accessible = 0
            browser_found = False

            for proc in psutil.process_iter(['name']):
                total += 1
                try:
                    name = proc.info['name']
                    accessible += 1

                    if any(b in name for b in ['Chrome', 'Firefox', 'Safari', 'Dia']):
                        browser_found = True

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            accessibility_rate = (accessible / total * 100) if total > 0 else 0

            details = {
                "total_processes": total,
                "accessible_processes": accessible,
                "accessibility_rate": round(accessibility_rate, 1),
                "browser_detected": browser_found
            }

            # Determine status
            if accessibility_rate > 70 and browser_found:
                status = HealthStatus.HEALTHY
                message = "Process access normal"
            elif accessibility_rate > 50:
                status = HealthStatus.DEGRADED
                message = "Limited process access"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Insufficient process access"

        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = f"Process check failed: {e}"
            details = {"error": str(e)}

        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            component="process_access",
            status=status,
            message=message,
            details=details,
            checked_at=datetime.now().isoformat(),
            response_time_ms=response_time
        )

    def check_disk_health(self) -> HealthCheckResult:
        """Check disk space health."""
        start_time = time.time()

        try:
            disk = psutil.disk_usage('/')

            details = {
                "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                "used_percent": disk.percent
            }

            # Determine status
            if disk.percent < 80:
                status = HealthStatus.HEALTHY
                message = "Disk space sufficient"
            elif disk.percent < 90:
                status = HealthStatus.DEGRADED
                message = "Disk space low"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Disk space critical"

        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = f"Disk check failed: {e}"
            details = {"error": str(e)}

        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            component="disk_space",
            status=status,
            message=message,
            details=details,
            checked_at=datetime.now().isoformat(),
            response_time_ms=response_time
        )

    def run_all_checks(self) -> List[HealthCheckResult]:
        """Run all health checks."""
        checks = [
            self.check_extension_health(),
            self.check_memory_health(),
            self.check_process_health(),
            self.check_disk_health()
        ]

        # Save to history
        self._save_history(checks)

        return checks

    def _save_history(self, checks: List[HealthCheckResult]):
        """Save health check history."""
        try:
            # Load existing history
            if self.history_path.exists():
                with open(self.history_path) as f:
                    history = json.load(f)
            else:
                history = []

            # Add new checks
            history.append({
                "timestamp": datetime.now().isoformat(),
                "checks": [c.to_dict() for c in checks]
            })

            # Keep only last 100 entries
            if len(history) > 100:
                history = history[-100:]

            # Save
            with open(self.history_path, 'w') as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            print(f"⚠️  History save failed: {e}", file=sys.stderr)

    def get_overall_status(self, checks: List[HealthCheckResult]) -> HealthStatus:
        """Determine overall system health."""
        if any(c.status == HealthStatus.UNHEALTHY for c in checks):
            return HealthStatus.UNHEALTHY
        elif any(c.status == HealthStatus.DEGRADED for c in checks):
            return HealthStatus.DEGRADED
        elif all(c.status == HealthStatus.HEALTHY for c in checks):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN

    def format_results(self, checks: List[HealthCheckResult], format: str = "text") -> str:
        """Format health check results."""
        if format == "json":
            return json.dumps([c.to_dict() for c in checks], indent=2)

        # Text format
        lines = []
        lines.append("🏥 System Health Check")
        lines.append("=" * 60)
        lines.append("")

        status_icons = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.UNHEALTHY: "❌",
            HealthStatus.UNKNOWN: "❓"
        }

        for check in checks:
            icon = status_icons.get(check.status, "❓")
            lines.append(f"{icon} {check.component}: {check.message}")
            lines.append(f"   Response: {check.response_time_ms:.1f}ms")

            for key, value in check.details.items():
                lines.append(f"   {key}: {value}")

            lines.append("")

        # Overall status
        overall = self.get_overall_status(checks)
        overall_icon = status_icons.get(overall, "❓")
        lines.append(f"{overall_icon} Overall Status: {overall.value.upper()}")
        lines.append("")

        return "\n".join(lines)


def main():
    """CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description='System Health Check')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                        help='Output format')
    parser.add_argument('--watch', action='store_true',
                        help='Continuous monitoring mode')
    parser.add_argument('--interval', type=int, default=30,
                        help='Watch interval in seconds (default: 30)')

    args = parser.parse_args()

    checker = HealthChecker()

    if args.watch:
        print("🔄 Continuous monitoring mode (Ctrl+C to stop)")
        print()

        try:
            while True:
                checks = checker.run_all_checks()
                output = checker.format_results(checks, args.format)
                print(output)
                print(f"Next check in {args.interval} seconds...")
                print()
                time.sleep(args.interval)

        except KeyboardInterrupt:
            print("\n✅ Monitoring stopped")
            return 0

    else:
        checks = checker.run_all_checks()
        output = checker.format_results(checks, args.format)
        print(output)

        # Exit code based on overall status
        overall = checker.get_overall_status(checks)
        if overall == HealthStatus.HEALTHY:
            return 0
        elif overall == HealthStatus.DEGRADED:
            return 1
        else:
            return 2


if __name__ == "__main__":
    sys.exit(main())
