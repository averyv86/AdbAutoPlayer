#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13.7.0", "pyyaml>=6.0"]
# ///
"""
Superdisco Agent & Skill Color Validator

Validates color assignments and frontmatter structure for all agents and skills.
Ensures correct color coding based on naming conventions:
  - Red: expert-*, manager-*, mcp-*, ai-*, builder-agent/skill/command, moai-* skills
  - Yellow: superdisco-*, builder-workflow-designer, builder-workflow, builder-reverse-engineer
  - Blue: default/fallback

Usage:
    uv run check_agents.py                # Human-readable table output
    uv run check_agents.py --json         # JSON output for automation
    uv run check_agents.py --verbose      # Detailed validation output

Exit Codes:
    0 - All validations passed
    1 - Validation errors found
    2 - Critical errors (missing files, parse errors)

Author: Superdisco Agents
Version: 1.0.0
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

def get_project_root() -> Path:
    """Find project root by looking for CLAUDE.md or .moai directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / "CLAUDE.md").exists() or (current / ".moai").exists():
            return current
        current = current.parent
    return Path.cwd()


PROJECT_ROOT = get_project_root()
AGENTS_DIR = PROJECT_ROOT / ".claude/agents/moai"
SKILLS_DIR = PROJECT_ROOT / ".claude/skills"

# Color assignment rules
RED_PREFIXES = ["expert-", "manager-", "mcp-", "ai-"]
RED_EXACT_NAMES = ["builder-agent", "builder-command", "builder-skill"]
YELLOW_PREFIXES = ["superdisco-"]
YELLOW_EXACT_NAMES = ["builder-workflow-designer", "builder-workflow", "builder-reverse-engineer"]
SKILL_RED_PREFIX = "moai-"


# ═══════════════════════════════════════════════════════════════════════════════
# FRONTMATTER PARSING
# ═══════════════════════════════════════════════════════════════════════════════

def parse_frontmatter(file_path: Path) -> Optional[Dict]:
    """Parse YAML frontmatter from markdown file."""
    try:
        content = file_path.read_text()
        if not content.startswith("---"):
            return None

        # Extract frontmatter between --- markers
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        frontmatter_text = parts[1].strip()

        # Try to parse YAML - handle unquoted colons in description
        try:
            return yaml.safe_load(frontmatter_text)
        except yaml.YAMLError:
            # If YAML parsing fails due to unquoted colons, try manual parsing
            result = {}
            for line in frontmatter_text.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' in line:
                    key, value = line.split(':', 1)
                    result[key.strip()] = value.strip()
            return result if result else None
    except Exception as e:
        console.print(f"[red]Error parsing {file_path.name}: {e}[/]")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

def get_expected_color(name: str, is_skill: bool = False) -> str:
    """Determine expected color based on naming rules."""
    if is_skill:
        # Skills: moai-* = red, superdisco-* = yellow, default = blue
        if name.startswith(SKILL_RED_PREFIX):
            return "red"
        elif any(name.startswith(prefix) for prefix in YELLOW_PREFIXES):
            return "yellow"
        else:
            return "blue"
    else:
        # Agents
        if name in YELLOW_EXACT_NAMES:
            return "yellow"
        elif name in RED_EXACT_NAMES:
            return "red"
        elif any(name.startswith(prefix) for prefix in YELLOW_PREFIXES):
            return "yellow"
        elif any(name.startswith(prefix) for prefix in RED_PREFIXES):
            return "red"
        else:
            return "blue"


def validate_agent(file_path: Path) -> Dict:
    """Validate a single agent file."""
    frontmatter = parse_frontmatter(file_path)

    if frontmatter is None:
        return {
            "file": file_path.name,
            "name": file_path.stem,
            "color": "missing",
            "expected_color": get_expected_color(file_path.stem, is_skill=False),
            "valid": False,
            "errors": ["Failed to parse frontmatter"],
            "warnings": []
        }

    errors = []
    warnings = []

    # Required fields
    required_fields = ["name", "description", "color"]
    for field in required_fields:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")

    # Validate name matches filename
    if "name" in frontmatter:
        expected_name = file_path.stem  # filename without .md
        actual_name = frontmatter["name"]
        if expected_name != actual_name:
            warnings.append(f"Name mismatch: file={expected_name}, frontmatter={actual_name}")

    # Validate color assignment
    if "name" in frontmatter and "color" in frontmatter:
        name = frontmatter["name"]
        actual_color = frontmatter["color"]
        expected_color = get_expected_color(name, is_skill=False)

        if actual_color != expected_color:
            errors.append(f"Color mismatch: expected={expected_color}, actual={actual_color}")

    return {
        "file": file_path.name,
        "name": frontmatter.get("name", "unknown"),
        "color": frontmatter.get("color", "missing"),
        "expected_color": get_expected_color(frontmatter.get("name", ""), is_skill=False),
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def validate_skill(skill_dir: Path) -> Dict:
    """Validate a single skill directory."""
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.exists():
        return {
            "directory": skill_dir.name,
            "name": skill_dir.name,
            "color": "missing",
            "expected_color": get_expected_color(skill_dir.name, is_skill=True),
            "valid": False,
            "errors": ["SKILL.md not found"],
            "warnings": []
        }

    frontmatter = parse_frontmatter(skill_file)

    if frontmatter is None:
        return {
            "directory": skill_dir.name,
            "name": skill_dir.name,
            "color": "missing",
            "expected_color": get_expected_color(skill_dir.name, is_skill=True),
            "valid": False,
            "errors": ["Failed to parse frontmatter"],
            "warnings": []
        }

    errors = []
    warnings = []

    # Required fields
    required_fields = ["name", "description", "version"]
    for field in required_fields:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")

    # Validate name matches directory
    if "name" in frontmatter:
        expected_name = skill_dir.name
        actual_name = frontmatter["name"]
        if expected_name != actual_name:
            warnings.append(f"Name mismatch: dir={expected_name}, frontmatter={actual_name}")

    # Validate color assignment (optional for skills, but if present should be correct)
    if "name" in frontmatter:
        name = frontmatter["name"]
        actual_color = frontmatter.get("color", "missing")
        expected_color = get_expected_color(name, is_skill=True)

        if actual_color != "missing" and actual_color != expected_color:
            errors.append(f"Color mismatch: expected={expected_color}, actual={actual_color}")
        elif actual_color == "missing":
            warnings.append("Color field not specified (optional but recommended)")

    return {
        "directory": skill_dir.name,
        "name": frontmatter.get("name", "unknown"),
        "color": frontmatter.get("color", "missing"),
        "expected_color": get_expected_color(frontmatter.get("name", ""), is_skill=True),
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def validate_all_agents() -> Tuple[List[Dict], int]:
    """Validate all agent files."""
    if not AGENTS_DIR.exists():
        console.print(f"[red]Agents directory not found: {AGENTS_DIR}[/]")
        return [], 2

    agent_files = sorted(AGENTS_DIR.glob("*.md"))
    results = []

    for agent_file in agent_files:
        result = validate_agent(agent_file)
        results.append(result)

    # Determine exit code
    has_errors = any(not r["valid"] for r in results)
    exit_code = 1 if has_errors else 0

    return results, exit_code


def validate_all_skills() -> Tuple[List[Dict], int]:
    """Validate all skill directories."""
    if not SKILLS_DIR.exists():
        console.print(f"[red]Skills directory not found: {SKILLS_DIR}[/]")
        return [], 2

    skill_dirs = sorted([d for d in SKILLS_DIR.iterdir() if d.is_dir()])
    results = []

    for skill_dir in skill_dirs:
        result = validate_skill(skill_dir)
        results.append(result)

    # Determine exit code
    has_errors = any(not r["valid"] for r in results)
    exit_code = 1 if has_errors else 0

    return results, exit_code


# ═══════════════════════════════════════════════════════════════════════════════
# OUTPUT FORMATTING
# ═══════════════════════════════════════════════════════════════════════════════

def display_results_table(agent_results: List[Dict], skill_results: List[Dict]):
    """Display validation results as Rich tables."""

    # Agents table
    if agent_results:
        table = Table(title="Agent Validation Results")
        table.add_column("Agent", style="cyan", no_wrap=True)
        table.add_column("Expected Color", style="dim")
        table.add_column("Actual Color", style="dim")
        table.add_column("Status", justify="center")
        table.add_column("Issues")

        for result in agent_results:
            status_icon = "✅" if result["valid"] else "❌"
            status_style = "green" if result["valid"] else "red"

            issues = []
            if result["errors"]:
                issues.extend([f"[red]ERROR: {e}[/]" for e in result["errors"]])
            if result["warnings"]:
                issues.extend([f"[yellow]WARN: {w}[/]" for w in result["warnings"]])

            issues_text = "\n".join(issues) if issues else "-"

            # Color the actual color if it doesn't match expected
            actual_color_style = "dim" if result["color"] == result["expected_color"] else "bold red"

            table.add_row(
                result["name"],
                result["expected_color"],
                f"[{actual_color_style}]{result['color']}[/]",
                f"[{status_style}]{status_icon}[/]",
                issues_text
            )

        console.print(table)

    # Skills table
    if skill_results:
        console.print()
        table = Table(title="Skill Validation Results")
        table.add_column("Skill", style="cyan", no_wrap=True)
        table.add_column("Expected Color", style="dim")
        table.add_column("Actual Color", style="dim")
        table.add_column("Status", justify="center")
        table.add_column("Issues")

        for result in skill_results:
            status_icon = "✅" if result["valid"] else "❌"
            status_style = "green" if result["valid"] else "red"

            issues = []
            if result["errors"]:
                issues.extend([f"[red]ERROR: {e}[/]" for e in result["errors"]])
            if result["warnings"]:
                issues.extend([f"[yellow]WARN: {w}[/]" for w in result["warnings"]])

            issues_text = "\n".join(issues) if issues else "-"

            # Color the actual color if it doesn't match expected
            actual_color_style = "dim" if result["color"] == result["expected_color"] else "bold red"

            table.add_row(
                result["name"],
                result["expected_color"],
                f"[{actual_color_style}]{result['color']}[/]",
                f"[{status_style}]{status_icon}[/]",
                issues_text
            )

        console.print(table)


def display_summary(agent_results: List[Dict], skill_results: List[Dict]):
    """Display summary statistics."""
    console.print()

    agent_valid = sum(1 for r in agent_results if r["valid"])
    agent_total = len(agent_results)
    skill_valid = sum(1 for r in skill_results if r["valid"])
    skill_total = len(skill_results)

    summary_table = Table(title="Validation Summary")
    summary_table.add_column("Category", style="cyan")
    summary_table.add_column("Valid", justify="right", style="green")
    summary_table.add_column("Invalid", justify="right", style="red")
    summary_table.add_column("Total", justify="right")

    summary_table.add_row(
        "Agents",
        str(agent_valid),
        str(agent_total - agent_valid),
        str(agent_total)
    )
    summary_table.add_row(
        "Skills",
        str(skill_valid),
        str(skill_total - skill_valid),
        str(skill_total)
    )

    console.print(summary_table)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate agent and skill color assignments"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results in JSON format"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Verbose output with detailed validation"
    )
    args = parser.parse_args()

    # Header
    if not args.json:
        console.print(Panel.fit(
            "[bold blue]Agent & Skill Color Validator[/]",
            subtitle="Superdisco MoAI Sync v1.0.0"
        ))

    # Validate agents
    agent_results, agent_exit_code = validate_all_agents()

    # Validate skills
    skill_results, skill_exit_code = validate_all_skills()

    # Determine overall exit code
    exit_code = max(agent_exit_code, skill_exit_code)

    # Output results
    if args.json:
        output = {
            "agents": agent_results,
            "skills": skill_results,
            "summary": {
                "agents_valid": sum(1 for r in agent_results if r["valid"]),
                "agents_total": len(agent_results),
                "skills_valid": sum(1 for r in skill_results if r["valid"]),
                "skills_total": len(skill_results),
                "all_valid": exit_code == 0
            }
        }
        print(json.dumps(output, indent=2))
    else:
        display_results_table(agent_results, skill_results)
        display_summary(agent_results, skill_results)

        if exit_code == 0:
            console.print("\n[green bold]✅ All validations passed![/]")
        else:
            console.print("\n[red bold]❌ Validation errors found![/]")

        if args.verbose:
            console.print(f"\n[dim]Project Root: {PROJECT_ROOT}[/]")
            console.print(f"[dim]Agents Dir:   {AGENTS_DIR}[/]")
            console.print(f"[dim]Skills Dir:   {SKILLS_DIR}[/]")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
