#!/usr/bin/env python3
"""
Risk Calculator - Multi-factor risk scoring for process termination decisions
Calculates risk score (0-100) based on process characteristics
"""

import subprocess
import sys
from datetime import datetime, time
from typing import Dict, Tuple
import json


class RiskCalculator:
    """Calculate risk score for killing a process"""

    # Process type risk scores (30 points max)
    PROCESS_TYPE_SCORES = {
        # Infrastructure - CRITICAL (30 pts)
        'postgres': 30,
        'mysql': 30,
        'mongodb': 30,
        'redis': 30,
        'docker': 30,
        'containerd': 30,
        'k8s': 30,
        'nginx': 30,
        'apache': 30,

        # Development servers - MEDIUM (15 pts)
        'node': 15,
        'npm': 15,
        'bun': 15,
        'deno': 15,
        'python': 15,
        'uvicorn': 15,
        'gunicorn': 15,
        'flask': 15,
        'django': 15,

        # Build tools - LOW (5 pts)
        'webpack': 5,
        'vite': 5,
        'rollup': 5,
        'tsc': 5,
        'babel': 5,

        # Unknown - MEDIUM (10 pts)
        'default': 10
    }

    def __init__(self, pid: int, process_name: str, uptime_seconds: int):
        self.pid = pid
        self.process_name = process_name.lower()
        self.uptime_seconds = uptime_seconds
        self.risk_score = 0
        self.risk_factors = []

    def calculate_type_risk(self) -> int:
        """Calculate risk based on process type (30 points max)"""
        for key, score in self.PROCESS_TYPE_SCORES.items():
            if key in self.process_name:
                self.risk_factors.append(f"Process type '{key}': +{score} pts")
                return score

        score = self.PROCESS_TYPE_SCORES['default']
        self.risk_factors.append(f"Unknown process type: +{score} pts")
        return score

    def calculate_uptime_risk(self) -> int:
        """Calculate risk based on uptime (20 points max)"""
        days = self.uptime_seconds / 86400

        if days > 30:
            score = 20
            self.risk_factors.append(f"Long uptime ({days:.1f} days): +{score} pts (likely production)")
        elif days > 7:
            score = 15
            self.risk_factors.append(f"Moderate uptime ({days:.1f} days): +{score} pts")
        elif days > 1:
            score = 10
            self.risk_factors.append(f"Recent process ({days:.1f} days): +{score} pts")
        else:
            hours = self.uptime_seconds / 3600
            score = 5
            self.risk_factors.append(f"Very recent ({hours:.1f} hours): +{score} pts (likely temporary)")

        return score

    def calculate_connection_risk(self) -> int:
        """Calculate risk based on active connections (20 points max)"""
        try:
            # Check for open network connections
            result = subprocess.run(
                ['lsof', '-Pan', '-p', str(self.pid), '-iTCP', '-iTCP:LISTEN'],
                capture_output=True,
                text=True,
                timeout=5
            )

            connections = len(result.stdout.strip().split('\n')) - 1 if result.stdout.strip() else 0

            if connections > 10:
                score = 20
                self.risk_factors.append(f"Many connections ({connections}): +{score} pts")
            elif connections > 5:
                score = 15
                self.risk_factors.append(f"Several connections ({connections}): +{score} pts")
            elif connections > 0:
                score = 10
                self.risk_factors.append(f"Active connections ({connections}): +{score} pts")
            else:
                score = 0
                self.risk_factors.append(f"No connections: +{score} pts")

            return score

        except Exception as e:
            self.risk_factors.append(f"Connection check failed: +5 pts (assume some risk)")
            return 5

    def calculate_resource_risk(self) -> int:
        """Calculate risk based on CPU/Memory patterns (15 points max)"""
        try:
            # Get CPU and memory usage
            result = subprocess.run(
                ['ps', '-p', str(self.pid), '-o', '%cpu,%mem'],
                capture_output=True,
                text=True,
                timeout=5
            )

            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return 5

            cpu_mem = lines[1].split()
            cpu = float(cpu_mem[0])
            mem = float(cpu_mem[1])

            # High resource usage = active work
            if cpu > 50 or mem > 10:
                score = 15
                self.risk_factors.append(f"High resource usage (CPU: {cpu}%, Mem: {mem}%): +{score} pts")
            elif cpu > 10 or mem > 5:
                score = 10
                self.risk_factors.append(f"Moderate resource usage (CPU: {cpu}%, Mem: {mem}%): +{score} pts")
            elif cpu > 1 or mem > 1:
                score = 5
                self.risk_factors.append(f"Low resource usage (CPU: {cpu}%, Mem: {mem}%): +{score} pts")
            else:
                score = 0
                self.risk_factors.append(f"Idle process (CPU: {cpu}%, Mem: {mem}%): +{score} pts")

            return score

        except Exception as e:
            self.risk_factors.append(f"Resource check failed: +5 pts")
            return 5

    def calculate_time_risk(self) -> int:
        """Calculate risk based on time of day (15 points max)"""
        now = datetime.now()
        current_time = now.time()

        # Work hours: 9 AM - 6 PM = higher risk (someone might be using it)
        work_start = time(9, 0)
        work_end = time(18, 0)

        if work_start <= current_time <= work_end:
            score = 15
            self.risk_factors.append(f"During work hours ({now.strftime('%H:%M')}): +{score} pts")
        elif time(6, 0) <= current_time < work_start or work_end < current_time <= time(22, 0):
            score = 10
            self.risk_factors.append(f"During evening hours ({now.strftime('%H:%M')}): +{score} pts")
        else:
            score = 5
            self.risk_factors.append(f"During night hours ({now.strftime('%H:%M')}): +{score} pts")

        return score

    def calculate_total_risk(self) -> Dict:
        """Calculate total risk score and categorize"""
        self.risk_score = 0
        self.risk_factors = []

        # Sum all risk factors
        self.risk_score += self.calculate_type_risk()
        self.risk_score += self.calculate_uptime_risk()
        self.risk_score += self.calculate_connection_risk()
        self.risk_score += self.calculate_resource_risk()
        self.risk_score += self.calculate_time_risk()

        # Determine risk level
        if self.risk_score >= 71:
            level = "CRITICAL"
            action = "PROTECT - Do NOT kill"
            color = "🔴"
        elif self.risk_score >= 41:
            level = "HIGH"
            action = "CONFIRM - Require explicit confirmation"
            color = "🟠"
        elif self.risk_score >= 21:
            level = "MEDIUM"
            action = "WARN - Show warning before kill"
            color = "🟡"
        else:
            level = "LOW"
            action = "SAFE - Can kill with minimal risk"
            color = "🟢"

        return {
            'pid': self.pid,
            'process_name': self.process_name,
            'risk_score': self.risk_score,
            'risk_level': level,
            'recommended_action': action,
            'color': color,
            'risk_factors': self.risk_factors
        }


def assess_process_risk(pid: int, process_name: str, uptime_seconds: int) -> Dict:
    """
    Assess the risk of killing a process

    Args:
        pid: Process ID
        process_name: Name of the process
        uptime_seconds: Process uptime in seconds

    Returns:
        Dictionary with risk assessment
    """
    calculator = RiskCalculator(pid, process_name, uptime_seconds)
    return calculator.calculate_total_risk()


def main():
    """CLI interface for risk calculation"""
    if len(sys.argv) < 4:
        print("Usage: risk-calculator.py <pid> <process_name> <uptime_seconds>")
        print("\nExample: risk-calculator.py 1234 'node server.js' 86400")
        sys.exit(1)

    pid = int(sys.argv[1])
    process_name = sys.argv[2]
    uptime_seconds = int(sys.argv[3])

    result = assess_process_risk(pid, process_name, uptime_seconds)

    # Print formatted output
    print(f"\n{result['color']} Risk Assessment for PID {pid}")
    print("=" * 60)
    print(f"Process: {result['process_name']}")
    print(f"Risk Score: {result['risk_score']}/100")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Recommended Action: {result['recommended_action']}")
    print("\nRisk Factors:")
    for factor in result['risk_factors']:
        print(f"  • {factor}")

    # Also output JSON for programmatic use
    print(f"\nJSON Output:")
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
