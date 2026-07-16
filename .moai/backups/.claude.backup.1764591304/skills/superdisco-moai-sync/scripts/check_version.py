#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13.7.0", "httpx>=0.27.0"]
# ///
"""
Superdisco MoAI Version Checker

Compare local, fork, and upstream versions.
Display customization summary and available updates.

Usage:
    uv run check_version.py          # Check all versions
    uv run check_version.py --clear  # Clear version cache

Author: Superdisco Agents
Version: 1.0.0
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

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
MOAI_ADK_DIR = PROJECT_ROOT / "moai-adk"
CONFIG_PATH = PROJECT_ROOT / ".moai/config/config.json"
CACHE_DIR = PROJECT_ROOT / ".moai/cache"
UPSTREAM_CONFIG = MOAI_ADK_DIR / "src/moai_adk/templates/.moai/config/config.json"


# ═══════════════════════════════════════════════════════════════════════════════
# VERSION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_local_version() -> Optional[str]:
    """Get current MoAI version from local config.json."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                config = json.load(f)
                return config.get("moai", {}).get("version")
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def get_moai_adk_version() -> Optional[str]:
    """Get version from moai-adk pyproject.toml."""
    pyproject = MOAI_ADK_DIR / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            for line in content.split("\n"):
                if line.strip().startswith("version"):
                    # Parse: version = "0.31.2"
                    parts = line.split("=")
                    if len(parts) >= 2:
                        version = parts[1].strip().strip('"').strip("'")
                        return version
        except Exception:
            pass
    return None


def get_upstream_template_version() -> Optional[str]:
    """Get version from upstream templates config."""
    if UPSTREAM_CONFIG.exists():
        try:
            with open(UPSTREAM_CONFIG) as f:
                config = json.load(f)
                return config.get("moai", {}).get("version")
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def get_latest_github_release() -> Optional[str]:
    """Check latest MoAI-ADK release from GitHub."""
    try:
        import httpx
        response = httpx.get(
            "https://api.github.com/repos/modu-ai/moai-adk/releases/latest",
            timeout=10.0
        )
        if response.status_code == 200:
            return response.json().get("tag_name", "").lstrip("v")
    except Exception:
        pass
    return None


def clear_cache():
    """Clear MoAI cache directory."""
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        console.print("[green]Cache cleared successfully![/]")
    else:
        console.print("[yellow]No cache directory found.[/]")


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOMIZATION SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

def get_customization_summary() -> dict:
    """Get summary of customizations."""
    custom_agents = []
    modified_agents = []
    custom_skills = []

    agents_dir = MOAI_ADK_DIR / "src/moai_adk/templates/.claude/agents/moai"
    if agents_dir.exists():
        # Custom agents (new files we created)
        custom_patterns = ["builder-workflow-designer.md", "builder-reverse-engineer.md"]
        for pattern in custom_patterns:
            if (agents_dir / pattern).exists():
                custom_agents.append(pattern)

        # Modified agents (TOON v4.0 integration)
        modified_patterns = ["builder-agent.md", "builder-command.md", "builder-skill.md", "builder-workflow.md"]
        for pattern in modified_patterns:
            if (agents_dir / pattern).exists():
                modified_agents.append(pattern)

    skills_dir = MOAI_ADK_DIR / "src/moai_adk/templates/.claude/skills"
    if skills_dir.exists():
        # Custom skill modifications
        toon_skill = skills_dir / "moai-library-toon/SKILL.md"
        if toon_skill.exists():
            custom_skills.append("moai-library-toon/SKILL.md")

    return {
        "custom_agents": custom_agents,
        "modified_agents": modified_agents,
        "custom_skills": custom_skills
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Superdisco MoAI Version Checker"
    )
    parser.add_argument(
        "--clear", action="store_true",
        help="Clear version cache"
    )
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold blue]Superdisco MoAI Version Checker[/]",
        subtitle="v1.0.0"
    ))

    if args.clear:
        clear_cache()
        return

    # Version table
    table = Table(title="Version Status")
    table.add_column("Source", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Status", style="yellow")

    local = get_local_version()
    moai_adk = get_moai_adk_version()
    template = get_upstream_template_version()
    latest = get_latest_github_release()

    table.add_row("Local Config", local or "Unknown", "Current")
    table.add_row("moai-adk pyproject", moai_adk or "Unknown", "Package")
    table.add_row("Template Config", template or "Unknown", "Templates")
    table.add_row("GitHub Latest", latest or "Unknown", "Available")

    console.print(table)

    # Check for updates
    if local and latest:
        if local != latest:
            console.print(f"\n[yellow]Update available: {local} -> {latest}[/]")
            console.print("Run: [cyan]cd moai-adk && git fetch upstream && git pull upstream main[/]")
        else:
            console.print("\n[green]Already up to date![/]")

    # Customization summary
    summary = get_customization_summary()

    if any(summary.values()):
        console.print("\n")
        table2 = Table(title="Customization Summary")
        table2.add_column("Type", style="cyan")
        table2.add_column("Files", style="green")
        table2.add_column("Count", style="yellow")

        if summary["custom_agents"]:
            table2.add_row("Custom Agents", ", ".join(summary["custom_agents"]), str(len(summary["custom_agents"])))
        if summary["modified_agents"]:
            table2.add_row("Modified Agents", ", ".join(summary["modified_agents"]), str(len(summary["modified_agents"])))
        if summary["custom_skills"]:
            table2.add_row("Custom Skills", ", ".join(summary["custom_skills"]), str(len(summary["custom_skills"])))

        console.print(table2)

    # Project paths
    console.print("\n")
    console.print(Panel.fit("[bold]Project Paths[/]"))
    console.print(f"  Project Root: [cyan]{PROJECT_ROOT}[/]")
    console.print(f"  MoAI-ADK:     [cyan]{MOAI_ADK_DIR}[/]")
    console.print(f"  Config:       [cyan]{CONFIG_PATH}[/]")
    console.print(f"  Cache:        [cyan]{CACHE_DIR}[/]")


if __name__ == "__main__":
    main()
