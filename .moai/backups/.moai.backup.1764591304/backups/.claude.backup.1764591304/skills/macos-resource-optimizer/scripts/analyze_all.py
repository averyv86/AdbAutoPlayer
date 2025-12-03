#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=5.9.0"]
# ///

"""
Analyze All - Parallel Resource Analysis Orchestrator

Runs all 6 resource analyzers in parallel and aggregates results.

Usage:
    uv run scripts/analyze_all.py [--format json|toon]

Exit Codes:
    0: All systems healthy
    1: Warning detected in one or more categories
    2: Critical issue detected in one or more categories

Author: MoAI-ADK
Version: 3.0.0 (TOON-enabled, Parallel execution)
Date: 2025-12-01
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List


async def run_analyzer(category: str, format: str = "toon") -> Dict:
    """
    Run a single category analyzer as subprocess.

    Args:
        category: Resource category (cpu, memory, disk, network, battery, thermal)
        format: Output format (json or toon)

    Returns:
        Dict with category, output, exit_code, duration
    """
    script_path = Path(__file__).parent / f"analyze_{category}.py"

    if not script_path.exists():
        return {
            'category': category,
            'status': 'error',
            'error': f'Script not found: {script_path}',
            'exit_code': 3
        }

    start_time = time.time()

    try:
        # Run analyzer subprocess
        process = await asyncio.create_subprocess_exec(
            'uv', 'run', str(script_path), f'--format={format}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=30
        )

        duration = time.time() - start_time

        return {
            'category': category,
            'status': 'completed',
            'exit_code': process.returncode,
            'output': stdout.decode().strip(),
            'error': stderr.decode().strip() if stderr else None,
            'duration': round(duration, 2)
        }

    except asyncio.TimeoutError:
        return {
            'category': category,
            'status': 'timeout',
            'error': 'Analysis timeout after 30s',
            'exit_code': 3
        }
    except Exception as e:
        return {
            'category': category,
            'status': 'error',
            'error': str(e),
            'exit_code': 3
        }


async def analyze_all_parallel(format: str = "toon") -> Dict:
    """
    Run all analyzers in parallel.

    Args:
        format: Output format (json or toon)

    Returns:
        Dict with aggregated results
    """
    categories = ['cpu', 'memory', 'disk', 'network', 'battery', 'thermal']

    # Run all analyzers in parallel
    start_time = time.time()
    tasks = [run_analyzer(cat, format) for cat in categories]
    results = await asyncio.gather(*tasks)
    total_duration = time.time() - start_time

    # Aggregate results
    successful = [r for r in results if r['status'] == 'completed']
    failed = [r for r in results if r['status'] != 'completed']

    # Determine overall status
    exit_codes = [r['exit_code'] for r in successful]
    overall_exit_code = max(exit_codes) if exit_codes else 3

    return {
        'total_duration': round(total_duration, 2),
        'categories_analyzed': len(successful),
        'categories_failed': len(failed),
        'results': results,
        'overall_exit_code': overall_exit_code,
        'timestamp': time.time()
    }


async def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Analyze all resource categories in parallel')
    parser.add_argument('--format', choices=['json', 'toon'], default='toon',
                        help='Output format (default: toon)')
    parser.add_argument('--json', action='store_true',
                        help='Shorthand for --format json')
    args = parser.parse_args()

    # Override format if --json flag is used
    output_format = 'json' if args.json else args.format

    # Run parallel analysis
    aggregated = await analyze_all_parallel(output_format)

    # Output in requested format
    if output_format == 'json':
        print(json.dumps(aggregated, indent=2))
        return aggregated['overall_exit_code']

    # TOON format output (compact multi-category)
    print(f"# Analysis Summary")
    print(f"duration:{aggregated['total_duration']}")
    print(f"analyzed:{aggregated['categories_analyzed']}")
    print(f"failed:{aggregated['categories_failed']}")
    print(f"timestamp:{aggregated['timestamp']}")
    print()

    # Output each category result
    for result in aggregated['results']:
        if result['status'] == 'completed':
            print(f"# {result['category'].upper()}")
            print(result['output'])
            print()
        else:
            print(f"# {result['category'].upper()} - FAILED")
            print(f"error:{result['error']}")
            print()

    return aggregated['overall_exit_code']


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
