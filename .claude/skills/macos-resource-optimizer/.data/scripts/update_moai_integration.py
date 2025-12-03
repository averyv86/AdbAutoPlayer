#!/usr/bin/env python3
"""
Automated MoAI Integration Updater

Updates all agent and command files from old PythonEngineWrapper pattern
to new UV script execution pattern.

Usage:
    uv run update_moai_integration.py --dry-run  # Preview changes
    uv run update_moai_integration.py           # Apply changes
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any
from datetime import datetime
import click

# Script mapping for category-specific agents
CATEGORY_SCRIPTS = {
    "cpu": "analyze_cpu.py",
    "memory": "analyze_memory.py",
    "disk": "analyze_disk.py",
    "network": "analyze_network.py",
    "battery": "analyze_battery.py",
    "thermal": "analyze_thermal.py",
}


class MoAIIntegrationUpdater:
    """Update MoAI files to use UV script pattern"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.base_path = Path("/Users/rdmtv/Documents/claydev-local/projects-v2/moai-ir-deck/.claude")
        self.changes_made = []

    def update_all_files(self):
        """Update all agent, command, and SKILL files"""

        # Update 8 agent files
        agent_path = self.base_path / "agents/macos-resource-optimizer"
        if agent_path.exists():
            for agent_file in agent_path.glob("*.md"):
                self.update_agent_file(agent_file)
        else:
            click.echo(f"Warning: Agent path not found: {agent_path}")

        # Update 5 command files
        command_path = self.base_path / "commands/macos-resource-optimizer"
        if command_path.exists():
            for command_file in command_path.glob("*.md"):
                self.update_command_file(command_file)
        else:
            click.echo(f"Warning: Command path not found: {command_path}")

        # Update SKILL.md
        skill_file = self.base_path / "skills/macos-resource-optimizer/SKILL.md"
        if skill_file.exists():
            self.update_skill_file(skill_file)
        else:
            click.echo(f"Warning: SKILL.md not found: {skill_file}")

    def update_agent_file(self, filepath: Path):
        """Update agent file with UV script pattern"""
        content = filepath.read_text()
        original = content

        # Extract category from filename
        category = self._extract_category(filepath.stem)
        script_name = CATEGORY_SCRIPTS.get(category, "analyze_all.py")

        # Remove PythonEngineWrapper references
        content = self._remove_wrapper_references(content)

        # Update subprocess commands
        content = self._update_subprocess_commands(content, category)

        # Add UV script execution pattern
        content = self._add_uv_script_pattern(content, category, script_name)

        # Add JSON parsing examples
        content = self._add_json_parsing(content)

        # Add exit code handling
        content = self._add_exit_code_handling(content)

        if content != original:
            if not self.dry_run:
                filepath.write_text(content)

            self.changes_made.append({
                "file": str(filepath),
                "category": category,
                "script": script_name,
                "lines_changed": len(content.splitlines()) - len(original.splitlines())
            })

    def _extract_category(self, filename: str) -> str:
        """Extract resource category from filename"""
        for cat in CATEGORY_SCRIPTS.keys():
            if cat in filename.lower():
                return cat
        return None

    def _remove_wrapper_references(self, content: str) -> str:
        """Remove all PythonEngineWrapper references"""

        # Replace PythonEngineWrapper references with UV script pattern
        content = content.replace(
            "PythonEngineWrapper",
            "UV Script Execution"
        )

        # Replace coordinator.py references with specific scripts
        content = content.replace(
            "coordinator.py --category=",
            "analyze_"
        )

        content = content.replace(
            "coordinator.py",
            "UV scripts"
        )

        patterns_to_remove = [
            r'from moai_system\.wrapper import .*\n',
            r'wrapper = .*Wrapper\([^)]+\).*\n',
            r'result = wrapper\.execute_analysis\([^)]+\).*\n',
        ]

        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content, flags=re.MULTILINE)

        return content

    def _update_subprocess_commands(self, content: str, category: str) -> str:
        """Update subprocess commands to use UV scripts"""

        if category in CATEGORY_SCRIPTS:
            script_name = CATEGORY_SCRIPTS[category]

            # Replace coordinator.py references with actual script
            content = content.replace(
                f"coordinator.py --analyze --category={category}",
                f".claude/skills/macos-resource-optimizer/scripts/{script_name}"
            )

        # Replace analyze-all reference
        content = content.replace(
            "coordinator.py --analyze-all",
            ".claude/skills/macos-resource-optimizer/scripts/analyze_all.py"
        )

        # Replace optimize reference
        content = content.replace(
            "coordinator.py --optimize",
            ".claude/skills/macos-resource-optimizer/scripts/optimize.py"
        )

        return content

    def _add_uv_script_pattern(self, content: str, category: str, script_name: str) -> str:
        """Add UV script execution pattern section"""

        # Find "## Execution" or "## Core Functionality" section
        execution_pattern = r'(## (?:Execution|Core Functionality).*?\n)(.*?)(\n## |\Z)'

        uv_script_example = f'''

### UV Script Execution Pattern

Execute the {category if category else "analysis"} script using the UV runner:

```python
# Execute {script_name} with JSON output
result = Bash("uv run .claude/skills/macos-resource-optimizer/scripts/{script_name} --json")

# Parse JSON response
data = json.loads(result.stdout)

# Extract metrics
metrics = data["metrics"]
analysis = data["analysis"]
recommendations = analysis["recommendations"]

# Handle exit codes
if result.exit_code == 0:
    # System healthy
    pass
elif result.exit_code == 1:
    # Warning detected
    pass
elif result.exit_code == 2:
    # Critical issue
    pass
elif result.exit_code == 3:
    # Execution error
    pass
```
'''

        def add_uv_section(match):
            return match.group(1) + match.group(2) + uv_script_example + match.group(3)

        content = re.sub(execution_pattern, add_uv_section, content, flags=re.DOTALL)

        return content

    def _add_json_parsing(self, content: str) -> str:
        """Add JSON parsing examples"""

        # Check if JSON parsing section exists
        if "json.loads(result.stdout)" not in content:
            # Add after first code block with Bash()
            content = re.sub(
                r'(Bash\("uv run [^"]+"\))',
                r'\1\n\n# Parse JSON response\ndata = json.loads(result.stdout)',
                content,
                count=1
            )

        return content

    def _add_exit_code_handling(self, content: str) -> str:
        """Add exit code handling documentation"""

        exit_code_docs = '''

### Exit Code System

All analyzer scripts use consistent exit codes:

- **0**: System healthy (green)
- **1**: Warning detected (yellow)
- **2**: Critical issue (red)
- **3**: Execution error (script failure)

**Example**:
```python
if result.exit_code in [0, 1, 2]:
    # Valid analysis result
    data = json.loads(result.stdout)
else:
    # Execution error
    error_msg = result.stderr
```
'''

        # Add before first "## " section if not exists
        if "Exit Code System" not in content:
            content = re.sub(
                r'(## [A-Z].*?\n)',
                exit_code_docs + r'\n\1',
                content,
                count=1
            )

        return content

    def update_command_file(self, filepath: Path):
        """Update command file workflow"""
        content = filepath.read_text()
        original = content

        # Determine command type from filename
        command_name = filepath.stem.split('-')[0]  # e.g., "0" from "0-init.md"

        # Map command to script
        command_scripts = {
            "0": "status.py",
            "1": "analyze_all.py",
            "2": "optimize.py",
            "3": "monitor.py",
            "4": "report.py",
        }

        script_name = command_scripts.get(command_name, "analyze_all.py")

        # Remove old patterns
        content = self._remove_wrapper_references(content)

        # Update subprocess commands
        content = content.replace(
            "coordinator.py",
            f".claude/skills/macos-resource-optimizer/scripts/{script_name}"
        )

        # Add UV script usage examples
        if "uv run .claude/skills/macos-resource-optimizer/scripts/" not in content:
            content = self._add_command_uv_examples(content, command_name, script_name)

        if content != original:
            if not self.dry_run:
                filepath.write_text(content)

            self.changes_made.append({
                "file": str(filepath),
                "command": command_name,
                "script": script_name,
                "lines_changed": len(content.splitlines()) - len(original.splitlines())
            })

    def _add_command_uv_examples(self, content: str, command_name: str, script_name: str) -> str:
        """Add command-specific UV script examples"""

        examples = {
            "0": '''
### Quick Status Check

```python
# Execute status.py for quick health check
result = Bash("uv run .claude/skills/macos-resource-optimizer/scripts/status.py --json")
data = json.loads(result.stdout)

# Display results
overall_status = data["status"]
cpu_percent = data["cpu_percent"]
memory_percent = data["memory_percent"]
```
''',
            "1": '''
### Full System Analysis

```python
# Execute analyze_all.py for comprehensive analysis
result = Bash("uv run .claude/skills/macos-resource-optimizer/scripts/analyze_all.py --json")
data = json.loads(result.stdout)

# Access results
overall = data["overall"]
categories = data["categories"]

for category, cat_data in categories.items():
    metrics = cat_data["metrics"]
    analysis = cat_data["analysis"]
    # Process results
```
''',
            "2": '''
### Optimization Workflow

```python
# Step 1: Dry-run (preview)
result = Bash("uv run .claude/skills/macos-resource-optimizer/scripts/optimize.py --json --dry-run")
optimizations = json.loads(result.stdout)["optimizations"]

# Step 2: Apply (with confirmation)
result = Bash("uv run .claude/skills/macos-resource-optimizer/scripts/optimize.py --json --apply")
```
''',
            "3": '''
### Continuous Monitoring

```python
# Monitor for 60 seconds with 5-second intervals
result = Bash("uv run .claude/skills/macos-resource-optimizer/scripts/monitor.py --duration 60 --interval 5 --json")
data = json.loads(result.stdout)

# Access monitoring history
samples = data["samples"]
```
''',
            "4": '''
### Report Generation

```python
# Generate Markdown report
Bash("uv run .claude/skills/macos-resource-optimizer/scripts/report.py --format markdown --output report.md")

# Generate HTML report
Bash("uv run .claude/skills/macos-resource-optimizer/scripts/report.py --format html --output report.html")

# Get JSON data
result = Bash("uv run .claude/skills/macos-resource-optimizer/scripts/report.py --format json")
data = json.loads(result.stdout)
```
''',
        }

        example = examples.get(command_name, "")

        # Add after first heading
        content = re.sub(
            r'(^# .*?\n\n)',
            r'\1' + example + '\n\n',
            content,
            count=1,
            flags=re.MULTILINE
        )

        return content

    def update_skill_file(self, filepath: Path):
        """Update SKILL.md with UV script pattern"""
        content = filepath.read_text()
        original = content

        # Remove wrapper references
        content = self._remove_wrapper_references(content)

        # Update architecture section
        content = self._update_skill_architecture(content)

        # Update script catalog
        content = self._update_script_catalog(content)

        if content != original:
            if not self.dry_run:
                filepath.write_text(content)

            self.changes_made.append({
                "file": str(filepath),
                "type": "SKILL",
                "lines_changed": len(content.splitlines()) - len(original.splitlines())
            })

    def _update_skill_architecture(self, content: str) -> str:
        """Update architecture description in SKILL.md"""

        new_architecture = '''
## Architecture: UV-Based Single-File Scripts

The macOS Resource Optimizer uses **12 standalone UV scripts** instead of a wrapper layer:

- **Direct Execution**: Each script is executable via `uv run`
- **JSON Output**: Structured metrics + analysis + recommendations
- **Exit Codes**: 0 (healthy), 1 (warning), 2 (critical), 3 (error)
- **Self-Contained**: No imports between scripts (intentional duplication)

### Performance

- **Single category**: 0.3-0.5s
- **All 6 categories** (parallel): 1.5-2.0s
- **Continuous monitoring**: Real-time updates every 5s
'''

        # Replace old architecture section
        content = re.sub(
            r'## Architecture:.*?(?=\n## |$)',
            new_architecture,
            content,
            flags=re.DOTALL
        )

        return content

    def _update_script_catalog(self, content: str) -> str:
        """Update script catalog table in SKILL.md"""

        script_catalog = '''
### 12 UV Scripts Available

| Script | Purpose | Usage |
|--------|---------|-------|
| `status.py` | Quick health check | `uv run .../status.py --json` |
| `analyze_cpu.py` | CPU analysis | `uv run .../analyze_cpu.py --json --threshold 70.0` |
| `analyze_memory.py` | Memory analysis | `uv run .../analyze_memory.py --json` |
| `analyze_disk.py` | Disk I/O analysis | `uv run .../analyze_disk.py --json` |
| `analyze_network.py` | Network analysis | `uv run .../analyze_network.py --json` |
| `analyze_battery.py` | Battery analysis | `uv run .../analyze_battery.py --json` |
| `analyze_thermal.py` | Thermal analysis | `uv run .../analyze_thermal.py --json` |
| `analyze_all.py` | Parallel all-category | `uv run .../analyze_all.py --json` |
| `optimize.py` | Generate optimizations | `uv run .../optimize.py --dry-run` |
| `monitor.py` | Continuous monitoring | `uv run .../monitor.py --duration 60` |
| `report.py` | Multi-format reports | `uv run .../report.py --format html` |
| `cache.py` | Metrics caching | `uv run .../cache.py --operation stats` |
'''

        # Add after architecture section
        content = re.sub(
            r'(## Architecture:.*?)\n(## )',
            r'\1\n' + script_catalog + '\n\n\\2',
            content,
            flags=re.DOTALL
        )

        return content

    def print_summary(self):
        """Print summary of changes"""
        click.echo(f"\n{'='*60}")
        click.echo(f"MoAI Integration Update Summary")
        click.echo(f"{'='*60}\n")

        click.echo(f"Mode: {'DRY RUN (no files modified)' if self.dry_run else 'LIVE (files updated)'}\n")

        if self.changes_made:
            click.echo(f"Files modified: {len(self.changes_made)}\n")

            for change in self.changes_made:
                filename = Path(change["file"]).name
                lines_changed = change.get("lines_changed", 0)

                click.echo(f"  ✅ {filename}")
                click.echo(f"      Lines changed: {lines_changed}")

                if "category" in change:
                    click.echo(f"      Category: {change['category']}")
                    click.echo(f"      Script: {change['script']}")
                elif "command" in change:
                    click.echo(f"      Command: {change['command']}")
                    click.echo(f"      Script: {change['script']}")
                click.echo()
        else:
            click.echo("No changes needed - all files already up to date.\n")


@click.command()
@click.option('--dry-run', is_flag=True,
              help='Preview changes without modifying files')
def main(dry_run: bool):
    """Automated MoAI Integration Updater"""

    updater = MoAIIntegrationUpdater(dry_run=dry_run)

    try:
        updater.update_all_files()
        updater.print_summary()

        if dry_run:
            click.echo("Run without --dry-run to apply changes.\n")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
