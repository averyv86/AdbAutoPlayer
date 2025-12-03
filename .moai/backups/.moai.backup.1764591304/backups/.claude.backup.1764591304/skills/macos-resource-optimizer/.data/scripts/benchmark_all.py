#!/usr/bin/env python3
"""
Performance Benchmark Suite for macOS Resource Optimizer Scripts
Measures execution time for all UV scripts with 3 runs per script.
"""

import subprocess
import time
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Script definitions with targets
SCRIPTS = {
    "status.py": {"target": 0.5, "args": ["--json"]},
    "analyze_cpu.py": {"target": 0.5, "args": ["--json"]},
    "analyze_memory.py": {"target": 0.5, "args": ["--json"]},
    "analyze_disk.py": {"target": 0.5, "args": ["--json"]},
    "analyze_network.py": {"target": 0.5, "args": ["--json"]},
    "analyze_battery.py": {"target": 0.5, "args": ["--json"]},
    "analyze_thermal.py": {"target": 0.5, "args": ["--json"]},
    "analyze_all.py": {"target": 2.5, "args": ["--json"], "critical": True},
    "optimize.py": {"target": 3.0, "args": ["--dry-run", "--json"]},
    "report.py": {"target": 2.0, "args": ["--json"]},
    "cache.py": {"target": 0.2, "args": ["--stats", "--json"]},
    "monitor.py": {"target": 10.0, "args": ["--duration=10", "--json"], "special": "10s execution"},
}

SCRIPTS_DIR = Path(__file__).parent
RUNS_PER_SCRIPT = 3


def run_benchmark(script_name: str, args: List[str]) -> Tuple[float, int]:
    """Run a single benchmark and return (duration, exit_code)"""
    script_path = SCRIPTS_DIR / script_name
    cmd = ["uv", "run", str(script_path)] + args

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=15,
            text=True
        )
        duration = time.time() - start
        return duration, result.returncode
    except subprocess.TimeoutExpired:
        duration = time.time() - start
        return duration, -1
    except Exception as e:
        duration = time.time() - start
        print(f"Error running {script_name}: {e}", file=sys.stderr)
        return duration, -2


def benchmark_script(script_name: str, config: Dict) -> Dict:
    """Benchmark a script with multiple runs"""
    print(f"\n{'='*60}")
    print(f"Benchmarking: {script_name}")
    print(f"Target: <{config['target']}s")
    print(f"{'='*60}")

    runs = []
    exit_codes = []

    for i in range(RUNS_PER_SCRIPT):
        print(f"Run {i+1}/{RUNS_PER_SCRIPT}...", end=" ", flush=True)
        duration, exit_code = run_benchmark(script_name, config.get("args", []))
        runs.append(duration)
        exit_codes.append(exit_code)

        status = "✅" if exit_code in [0, 1, 2] else "❌"
        print(f"{duration:.3f}s {status}")

        # Brief pause between runs
        time.sleep(0.5)

    avg_duration = sum(runs) / len(runs)
    min_duration = min(runs)
    max_duration = max(runs)
    passed = avg_duration < config["target"]

    result = {
        "script": script_name,
        "target": config["target"],
        "runs": runs,
        "exit_codes": exit_codes,
        "avg": avg_duration,
        "min": min_duration,
        "max": max_duration,
        "passed": passed,
        "critical": config.get("critical", False),
        "special": config.get("special")
    }

    print(f"\nAverage: {avg_duration:.3f}s (min: {min_duration:.3f}s, max: {max_duration:.3f}s)")
    print(f"Status: {'✅ PASS' if passed else '❌ FAIL'}")

    return result


def generate_markdown_report(results: List[Dict], output_path: Path):
    """Generate markdown performance report"""
    total_scripts = len(results)
    passed_scripts = sum(1 for r in results if r["passed"])
    critical_script = next((r for r in results if r.get("critical")), None)

    report = f"""# Performance Benchmark Results

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Scripts Tested**: {total_scripts}
**Passed**: {passed_scripts}/{total_scripts} ({passed_scripts/total_scripts*100:.1f}%)

## Executive Summary

"""

    if critical_script:
        status = "✅ PASS" if critical_script["passed"] else "❌ FAIL"
        report += f"""### Critical Performance: {critical_script['script']}

- **Target**: <{critical_script['target']}s
- **Actual**: {critical_script['avg']:.3f}s
- **Status**: {status}
- **Min/Max**: {critical_script['min']:.3f}s / {critical_script['max']:.3f}s

"""

    report += """## Detailed Results

| Script | Target | Run 1 | Run 2 | Run 3 | Average | Min | Max | Status |
|--------|--------|-------|-------|-------|---------|-----|-----|--------|
"""

    for r in results:
        status = "✅" if r["passed"] else "❌"
        report += f"| {r['script']} | <{r['target']}s | "
        report += " | ".join(f"{run:.3f}s" for run in r['runs']) + " | "
        report += f"{r['avg']:.3f}s | {r['min']:.3f}s | {r['max']:.3f}s | {status} |\n"

    # Bottlenecks section
    failed = [r for r in results if not r["passed"]]
    report += "\n## Bottlenecks Identified\n\n"

    if failed:
        report += "### Failed Performance Targets\n\n"
        for r in failed:
            overhead = r['avg'] - r['target']
            report += f"- **{r['script']}**: {r['avg']:.3f}s (target: {r['target']}s, overhead: +{overhead:.3f}s)\n"
    else:
        report += "✅ All scripts met performance targets!\n"

    # Recommendations
    report += "\n## Recommendations\n\n"

    if failed:
        report += "### Optimization Priorities\n\n"
        sorted_failed = sorted(failed, key=lambda x: x['avg'] - x['target'], reverse=True)
        for i, r in enumerate(sorted_failed, 1):
            report += f"{i}. **{r['script']}**: Focus on reducing execution time by {(r['avg'] - r['target']):.3f}s\n"

    # Performance trends
    report += "\n### Performance Characteristics\n\n"

    fast_scripts = [r for r in results if r['avg'] < 0.3]
    if fast_scripts:
        report += f"- **Fast scripts** (<0.3s): {', '.join(r['script'] for r in fast_scripts)}\n"

    moderate_scripts = [r for r in results if 0.3 <= r['avg'] < 1.0]
    if moderate_scripts:
        report += f"- **Moderate scripts** (0.3-1.0s): {', '.join(r['script'] for r in moderate_scripts)}\n"

    slow_scripts = [r for r in results if r['avg'] >= 1.0]
    if slow_scripts:
        report += f"- **Slow scripts** (≥1.0s): {', '.join(r['script'] for r in slow_scripts)}\n"

    # Exit codes analysis
    report += "\n## Exit Code Analysis\n\n"
    for r in results:
        if all(code in [0, 1, 2] for code in r['exit_codes']):
            report += f"- **{r['script']}**: ✅ Consistent exit codes {set(r['exit_codes'])}\n"
        else:
            report += f"- **{r['script']}**: ⚠️ Unexpected exit codes {r['exit_codes']}\n"

    report += """

## Performance Regression Tests

See `tests/test_performance/test_script_performance.py` for automated regression tests.

## Benchmark Methodology

- **Runs per script**: 3
- **Measurement**: Wall clock time using `time.time()`
- **Environment**: macOS with UV runtime
- **Timeout**: 15s per script
- **Pause between runs**: 0.5s

---

*Generated by benchmark_all.py*
"""

    output_path.write_text(report)
    print(f"\n📄 Report saved to: {output_path}")


def generate_json_report(results: List[Dict], output_path: Path):
    """Generate JSON performance report for machine consumption"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_scripts": len(results),
        "passed_scripts": sum(1 for r in results if r["passed"]),
        "runs_per_script": RUNS_PER_SCRIPT,
        "results": results
    }

    output_path.write_text(json.dumps(report, indent=2))
    print(f"📄 JSON report saved to: {output_path}")


def main():
    """Main benchmarking execution"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║   macOS Resource Optimizer - Performance Benchmark Suite    ║
╚══════════════════════════════════════════════════════════════╝
""")

    results = []

    # Benchmark all scripts
    for script_name, config in SCRIPTS.items():
        result = benchmark_script(script_name, config)
        results.append(result)

    # Generate reports
    print("\n" + "="*60)
    print("Generating reports...")
    print("="*60)

    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    date_str = datetime.now().strftime('%Y%m%d-%H%M%S')
    md_path = reports_dir / f"performance-benchmark-{date_str}.md"
    json_path = reports_dir / f"performance-benchmark-{date_str}.json"

    generate_markdown_report(results, md_path)
    generate_json_report(results, json_path)

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["passed"])

    print("\n" + "="*60)
    print("BENCHMARK COMPLETE")
    print("="*60)
    print(f"Total scripts: {total}")
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"Failed: {total-passed}/{total}")

    # Critical check
    critical = next((r for r in results if r.get("critical")), None)
    if critical:
        status = "✅ PASS" if critical["passed"] else "❌ FAIL"
        print(f"\nCritical script ({critical['script']}): {status} ({critical['avg']:.3f}s)")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
