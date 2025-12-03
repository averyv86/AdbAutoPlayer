#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13.7.0", "pyyaml>=6.0"]
# ///
"""
Add Color Property to MoAI Agents and Skills

Automatically adds `color:` property to all agent and skill YAML frontmatter
based on naming conventions:
- Red: Official MoAI (expert-*, manager-*, mcp-*, ai-*, builder-agent/skill/command, moai-*)
- Yellow: Custom Superdisco (builder-workflow-designer, builder-workflow, builder-reverse-engineer, superdisco-*)
- Blue: Normal Claude Code (default)

Usage:
    uv run add_colors.py --dry-run    # Preview changes
    uv run add_colors.py --apply      # Apply changes
    uv run add_colors.py --agents     # Only process agents
    uv run add_colors.py --skills     # Only process skills
"""

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Color mapping rules
CUSTOM_SUPERDISCO_AGENTS = {
    "builder-workflow-designer",
    "builder-workflow",
    "builder-reverse-engineer",
}

OFFICIAL_MOAI_PREFIXES = [
    "expert-",
    "manager-",
    "mcp-",
    "ai-",
    "builder-",
]


def get_project_root() -> Path:
    """Find project root by looking for CLAUDE.md or .moai directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / "CLAUDE.md").exists() or (current / ".moai").exists():
            return current
        current = current.parent
    return Path.cwd()


def determine_color(name: str, file_type: str = "agent") -> str:
    """
    Determine the appropriate color for an agent or skill.

    Args:
        name: The name of the agent or skill
        file_type: Either "agent" or "skill"

    Returns:
        Color string: "red", "yellow", or "blue"
    """
    # Custom Superdisco - Yellow
    if name.startswith("superdisco-"):
        return "yellow"

    if file_type == "agent" and name in CUSTOM_SUPERDISCO_AGENTS:
        return "yellow"

    # Official MoAI - Red
    if file_type == "skill" and name.startswith("moai-"):
        return "red"

    for prefix in OFFICIAL_MOAI_PREFIXES:
        if name.startswith(prefix):
            return "red"

    # Default - Blue
    return "blue"


def parse_frontmatter(content: str) -> tuple[dict | None, str, str]:
    """
    Parse YAML frontmatter from markdown content.

    Returns:
        Tuple of (frontmatter_dict, frontmatter_raw, body)
    """
    if not content.startswith("---"):
        return None, "", content

    # Find the closing ---
    end_match = re.search(r'\n---\n', content[3:])
    if not end_match:
        return None, "", content

    end_pos = end_match.start() + 3
    frontmatter_raw = content[4:end_pos]
    body = content[end_pos + 5:]  # Skip the closing ---\n

    # Parse frontmatter manually (simple key: value pairs)
    frontmatter = {}
    for line in frontmatter_raw.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            frontmatter[key.strip()] = value.strip()

    return frontmatter, frontmatter_raw, body


def add_color_to_frontmatter(frontmatter_raw: str, color: str) -> str:
    """
    Add color property to frontmatter string.

    Inserts color after the last property in frontmatter.
    """
    lines = frontmatter_raw.strip().split('\n')

    # Check if color already exists
    for i, line in enumerate(lines):
        if line.startswith('color:'):
            # Update existing color
            lines[i] = f"color: {color}"
            return '\n'.join(lines)

    # Add color at the end
    lines.append(f"color: {color}")
    return '\n'.join(lines)


def process_file(file_path: Path, file_type: str, dry_run: bool = True) -> dict:
    """
    Process a single file, adding color property if needed.

    Returns:
        Dict with status information
    """
    result = {
        "file": file_path.name,
        "name": "",
        "current_color": None,
        "new_color": None,
        "action": "skip",
        "error": None,
    }

    try:
        content = file_path.read_text(encoding='utf-8')
        frontmatter, frontmatter_raw, body = parse_frontmatter(content)

        if frontmatter is None:
            result["error"] = "No frontmatter found"
            return result

        name = frontmatter.get("name", file_path.stem)
        result["name"] = name
        result["current_color"] = frontmatter.get("color")

        # Determine the correct color
        new_color = determine_color(name, file_type)
        result["new_color"] = new_color

        # Check if update is needed
        if result["current_color"] == new_color:
            result["action"] = "unchanged"
            return result

        if result["current_color"] is None:
            result["action"] = "add"
        else:
            result["action"] = "update"

        if not dry_run:
            # Create backup
            backup_path = file_path.with_suffix(f".md.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")
            shutil.copy2(file_path, backup_path)

            # Update frontmatter
            new_frontmatter = add_color_to_frontmatter(frontmatter_raw, new_color)
            new_content = f"---\n{new_frontmatter}\n---\n{body}"

            file_path.write_text(new_content, encoding='utf-8')

            # Remove backup if successful
            backup_path.unlink()

        return result

    except Exception as e:
        result["error"] = str(e)
        return result


def find_agent_files(project_root: Path) -> list[Path]:
    """Find all agent definition files."""
    agents_dir = project_root / ".claude" / "agents" / "moai"
    if not agents_dir.exists():
        return []
    return sorted(agents_dir.glob("*.md"))


def find_skill_files(project_root: Path) -> list[Path]:
    """Find all skill SKILL.md files."""
    skills_dir = project_root / ".claude" / "skills"
    if not skills_dir.exists():
        return []
    return sorted(skills_dir.glob("*/SKILL.md"))


def display_results(results: list[dict], file_type: str, dry_run: bool):
    """Display processing results in a table."""
    table = Table(title=f"{file_type.capitalize()} Color Updates {'(DRY RUN)' if dry_run else ''}")

    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Current", style="dim")
    table.add_column("New", style="green")
    table.add_column("Action", style="yellow")

    stats = {"add": 0, "update": 0, "unchanged": 0, "error": 0}

    for r in results:
        if r["error"]:
            action_display = f"[red]Error: {r['error']}[/]"
            stats["error"] += 1
        else:
            action_display = r["action"]
            stats[r["action"]] = stats.get(r["action"], 0) + 1

        current = r["current_color"] or "-"
        new = r["new_color"] or "-"

        # Color the new color based on value
        if new == "red":
            new = f"[red]{new}[/]"
        elif new == "yellow":
            new = f"[yellow]{new}[/]"
        elif new == "blue":
            new = f"[blue]{new}[/]"

        table.add_row(r["name"] or r["file"], current, new, action_display)

    console.print(table)
    console.print()
    console.print(f"Summary: [green]{stats['add']} added[/], [yellow]{stats['update']} updated[/], "
                  f"[dim]{stats['unchanged']} unchanged[/], [red]{stats['error']} errors[/]")


def main():
    """Main entry point."""
    # Parse arguments
    args = sys.argv[1:]

    dry_run = "--dry-run" in args or "-n" in args
    apply = "--apply" in args or "-a" in args
    only_agents = "--agents" in args
    only_skills = "--skills" in args

    if not dry_run and not apply:
        dry_run = True  # Default to dry-run

    if apply:
        dry_run = False

    # Header
    console.print(Panel.fit(
        "[bold blue]MoAI Agent & Skill Color Updater[/]",
        subtitle="v1.0.0"
    ))
    console.print()

    project_root = get_project_root()
    console.print(f"[dim]Project root: {project_root}[/]")
    console.print()

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No files will be modified[/]")
        console.print()

    # Process agents
    if not only_skills:
        agent_files = find_agent_files(project_root)
        if agent_files:
            console.print(f"[bold]Processing {len(agent_files)} agents...[/]")
            agent_results = [process_file(f, "agent", dry_run) for f in agent_files]
            display_results(agent_results, "agent", dry_run)
            console.print()

    # Process skills
    if not only_agents:
        skill_files = find_skill_files(project_root)
        if skill_files:
            console.print(f"[bold]Processing {len(skill_files)} skills...[/]")
            skill_results = [process_file(f, "skill", dry_run) for f in skill_files]
            display_results(skill_results, "skill", dry_run)
            console.print()

    # Color legend
    console.print(Panel.fit(
        "[red]Red[/] = Official MoAI\n"
        "[yellow]Yellow[/] = Custom Superdisco\n"
        "[blue]Blue[/] = Claude Code Default",
        title="Color Legend"
    ))

    if dry_run:
        console.print()
        console.print("[dim]Run with --apply to apply changes[/]")


if __name__ == "__main__":
    main()
