#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Script Usage Analyzer - Identify unused scripts for archival.

Scans agents and commands to determine which scripts are actually referenced.

Author: MoAI-ADK
Version: 1.0.0
Date: 2025-12-01
"""

import re
from pathlib import Path
from typing import Dict, List, Set

def scan_file_for_script_references(file_path: Path) -> Set[str]:
    """
    Scan a file for script references.

    Returns:
        Set of script names referenced in the file
    """
    references = set()

    try:
        content = file_path.read_text()

        # Pattern 1: uv run scripts/script_name.py
        pattern1 = r'uv run (?:scripts/)?([a-zA-Z0-9_-]+\.py)'

        # Pattern 2: Bash("uv run ...")
        pattern2 = r'Bash\(["\']uv run (?:scripts/)?([a-zA-Z0-9_-]+\.py)'

        # Pattern 3: execute("script_name.py")
        pattern3 = r'execute\(["\']([a-zA-Z0-9_-]+\.py)'

        # Pattern 4: import from script
        pattern4 = r'from ([a-zA-Z0-9_-]+) import'

        for pattern in [pattern1, pattern2, pattern3]:
            matches = re.findall(pattern, content)
            references.update(matches)

        # For imports, add .py extension
        import_matches = re.findall(pattern4, content)
        references.update(f"{m}.py" for m in import_matches if not m.startswith('.'))

    except Exception as e:
        pass

    return references


def analyze_script_usage() -> Dict:
    """
    Analyze which scripts are used by agents and commands.

    Returns:
        Dict with analysis results
    """
    base_path = Path(__file__).parent.parent
    scripts_dir = base_path / "scripts"
    agents_dir = base_path.parent.parent / "agents" / "macos-resource-optimizer"
    commands_dir = base_path.parent.parent / "commands" / "macos-resource-optimizer"

    # Get all Python scripts
    all_scripts = {f.name for f in scripts_dir.glob("*.py")}

    # Core scripts that must be kept
    core_scripts = {
        'analyze_all.py',
        'analyze_cpu.py',
        'analyze_memory.py',
        'analyze_disk.py',
        'analyze_network.py',
        'analyze_battery.py',
        'analyze_thermal.py',
        'status.py',
        'background_monitor.py',
        'convert_registry_to_toon.py',
        'coordinator.py',
        'analyze_script_usage.py'  # This script
    }

    # Scan all agent and command files for references
    referenced_scripts = set()

    # Scan agents
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            refs = scan_file_for_script_references(agent_file)
            referenced_scripts.update(refs)

    # Scan commands
    if commands_dir.exists():
        for cmd_file in commands_dir.glob("*.md"):
            refs = scan_file_for_script_references(cmd_file)
            referenced_scripts.update(refs)

    # Scan coordinator itself
    coordinator_path = scripts_dir / "coordinator.py"
    if coordinator_path.exists():
        refs = scan_file_for_script_references(coordinator_path)
        referenced_scripts.update(refs)

    # Scripts that are used
    used_scripts = core_scripts | referenced_scripts

    # Scripts that are unused (candidates for archival)
    unused_scripts = all_scripts - used_scripts

    # Categorize unused scripts
    hyphenated_scripts = {s for s in unused_scripts if '-' in s}
    legacy_scripts = {
        'cleanup_shells.py',
        'scheduler.py',
        'shell_manager.py',
        'kill_zombies_parallel.py'
    }

    utility_scripts = {
        'browser_utils.py',
        'hibernation_utils.py',
        'ram_utils.py',
        'analyze_processes.py',
        'report_memory.py',
        'verify_cleanup.py'
    }

    agent_scripts = {s for s in all_scripts if s.startswith('agent_')}
    unused_agent_scripts = agent_scripts - used_scripts

    return {
        'total_scripts': len(all_scripts),
        'core_scripts': sorted(core_scripts),
        'referenced_scripts': sorted(referenced_scripts),
        'used_scripts': sorted(used_scripts),
        'unused_scripts': sorted(unused_scripts),
        'hyphenated_scripts': sorted(hyphenated_scripts),
        'legacy_scripts': sorted(legacy_scripts & unused_scripts),
        'utility_scripts': sorted(utility_scripts),
        'agent_scripts_total': len(agent_scripts),
        'unused_agent_scripts': sorted(unused_agent_scripts),
        'archival_candidates': sorted(unused_scripts)
    }


def main():
    """Main execution."""
    import json

    print("🔍 Analyzing Script Usage...")
    print("=" * 60)

    results = analyze_script_usage()

    print(f"\n📊 Script Statistics:")
    print(f"   Total Scripts: {results['total_scripts']}")
    print(f"   Core Scripts (must keep): {len(results['core_scripts'])}")
    print(f"   Referenced by agents/commands: {len(results['referenced_scripts'])}")
    print(f"   Used Scripts: {len(results['used_scripts'])}")
    print(f"   Unused Scripts: {len(results['unused_scripts'])}")

    print(f"\n🗂️  Agent Scripts:")
    print(f"   Total: {results['agent_scripts_total']}")
    print(f"   Unused: {len(results['unused_agent_scripts'])}")

    print(f"\n📦 Archival Candidates ({len(results['archival_candidates'])}):")

    if results['hyphenated_scripts']:
        print(f"\n   Hyphenated (old style): {len(results['hyphenated_scripts'])}")
        for script in results['hyphenated_scripts']:
            print(f"      - {script}")

    if results['legacy_scripts']:
        print(f"\n   Legacy/Redundant: {len(results['legacy_scripts'])}")
        for script in results['legacy_scripts']:
            print(f"      - {script}")

    if results['unused_agent_scripts']:
        print(f"\n   Unused Agent Scripts: {len(results['unused_agent_scripts'])}")
        for script in sorted(results['unused_agent_scripts'])[:10]:
            print(f"      - {script}")
        if len(results['unused_agent_scripts']) > 10:
            print(f"      ... and {len(results['unused_agent_scripts']) - 10} more")

    print(f"\n✅ Analysis complete!")
    print(f"\n💡 Recommendation: Archive {len(results['archival_candidates'])} unused scripts")

    # Save results to JSON
    output_path = Path(__file__).parent.parent / "data" / "script-usage-analysis.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📁 Results saved to: {output_path}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
