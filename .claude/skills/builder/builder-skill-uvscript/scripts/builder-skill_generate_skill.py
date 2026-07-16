#!/usr/bin/env python3
# /// script
# dependencies = [
#     "click>=8.1.7",
#     "rich>=13.0.0",
#     "pyyaml>=6.0",
# ]
# ///

"""
Generate MoAI Skill Structure - Complete Skill Generator

Creates properly formatted MoAI skill directories with SKILL.md frontmatter,
script metadata, and progressive disclosure documentation following IndieDevDan
UV script patterns.

Usage:
    uv run generate_skill.py --name <name> --description <desc>
    uv run generate_skill.py --name moai-connector-api --description "REST API toolkit"
    uv run generate_skill.py --help

Examples:
    # Generate basic skill
    uv run generate_skill.py --name moai-connector-rest --description "REST API client generation"

    # Generate with multiple scripts
    uv run generate_skill.py --name moai-toolkit-data --description "Data processing utilities" \
        --scripts "process.py,transform.py,validate.py"

    # Generate with keywords
    uv run generate_skill.py --name moai-library-testing --description "Testing toolkit" \
        --keywords "test,pytest,vitest,automation"

    # JSON output mode
    uv run generate_skill.py --name moai-platform-cache --description "Caching solutions" --json

Exit Codes:
    0 - Success (skill directory and files created)
    1 - Warning (directory exists, user declined overwrite)
    2 - Error (invalid input or validation failure)
    3 - Critical (unable to write files or system error)

Requirements:
    - Python 3.11+
    - UV package manager
    - Access to project root (.claude/skills/ directory)

Notes:
    - Designed for UV execution only (no manual pip install)
    - Works from any directory (auto-detects project root)
    - MCP-wrappable for future server integration
    - Validates skill naming conventions (moai-*)
    - Creates flat scripts/ directory (no nested subdirectories)
"""

# ========== SECTION 2: IMPORTS ==========
import click
import json
import sys
import yaml
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

# ========== SECTION 3: CONSTANTS & CONFIGURATION ==========
DEFAULT_SCRIPTS = ["script1.py"]
DEFAULT_OUTPUT_DIR = ".claude/skills"
VALID_SKILL_PREFIXES = ["moai-", "skill-"]
MAX_SCRIPTS = 20
DEFAULT_VERSION = "1.0.0"

# ========== SECTION 4: PROJECT ROOT AUTO-DETECTION ==========
def find_project_root(start_path: Path) -> Path:
    """
    Auto-detect project root by searching for markers.

    Searches upward from start_path looking for .git, pyproject.toml, or .moai
    directory to identify the project root.

    Args:
        start_path: Starting directory for search

    Returns:
        Path to project root

    Raises:
        RuntimeError: If project root cannot be found

    Examples:
        >>> find_project_root(Path.cwd())
        Path('/path/to/project')
    """
    current = start_path.resolve()
    while current != current.parent:
        if any((current / marker).exists() for marker in
               [".git", "pyproject.toml", ".moai", ".claude"]):
            return current
        current = current.parent
    raise RuntimeError(
        "Project root not found. Expected .git, pyproject.toml, .moai, or .claude directory."
    )

PROJECT_ROOT = find_project_root(Path.cwd())

# ========== SECTION 5: DATA MODELS ==========
@dataclass
class ScriptMetadata:
    """Script metadata for SKILL.md frontmatter."""
    name: str
    purpose: str
    type: str = "python"
    zero_context: bool = True
    version: str = DEFAULT_VERSION

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        return {
            "name": self.name,
            "purpose": self.purpose,
            "type": self.type,
            "zero_context": self.zero_context,
            "version": self.version,
            "last_updated": _get_current_date()
        }

@dataclass
class SkillConfig:
    """
    Skill configuration data model with all frontmatter fields.

    Attributes:
        name: Skill name (moai-* or skill-* format)
        description: One-line skill description
        scripts: List of script names to create
        keywords: Auto-trigger keywords list
        version: Skill version
        modularized: Whether skill is modularized
        scripts_enabled: Whether scripts are enabled
    """
    name: str
    description: str
    scripts: list[str] = field(default_factory=lambda: DEFAULT_SCRIPTS.copy())
    keywords: list[str] = field(default_factory=list)
    version: str = DEFAULT_VERSION
    modularized: bool = True
    scripts_enabled: bool = True

    def to_frontmatter(self) -> dict:
        """Convert to YAML frontmatter dictionary."""
        script_list = []
        for script in self.scripts:
            script_name = script if script.endswith(".py") else f"{script}.py"
            script_list.append({
                "name": script_name,
                "purpose": f"[Define purpose for {script_name}]",
                "type": "python",
                "command": f"uv run .claude/skills/{self.name}/scripts/{script_name}",
                "zero_context": True,
                "version": self.version,
                "last_updated": _get_current_date()
            })

        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "modularized": self.modularized,
            "scripts_enabled": self.scripts_enabled,
            "last_updated": _get_current_date(),
            "compliance_score": 85,
            "auto_trigger_keywords": self.keywords if self.keywords else ["skill"],
            "scripts": script_list
        }

# ========== SECTION 6: VALIDATION ==========
def validate_skill_name(name: str) -> tuple[bool, Optional[str]]:
    """
    Validate skill name follows moai-* or skill-* convention.

    Args:
        name: Skill name to validate

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_skill_name("moai-connector-api")
        (True, None)
        >>> validate_skill_name("invalid_name")
        (False, "Skill name must start with 'moai-' or 'skill-'")
    """
    if not name:
        return False, "Skill name cannot be empty"

    if not any(name.startswith(prefix) for prefix in VALID_SKILL_PREFIXES):
        return False, f"Skill name must start with one of: {', '.join(VALID_SKILL_PREFIXES)}"

    if "_" in name:
        return False, "Skill name must use hyphens, not underscores (e.g., moai-connector-api)"

    if not name.replace("-", "").isalnum():
        return False, "Skill name must be alphanumeric with hyphens"

    return True, None

def validate_scripts(scripts_str: str) -> list[str]:
    """
    Validate and parse script names.

    Args:
        scripts_str: Comma-separated script names

    Returns:
        List of validated script names

    Raises:
        ValueError: If scripts string is invalid
    """
    if not scripts_str:
        return DEFAULT_SCRIPTS.copy()

    script_list = [s.strip() for s in scripts_str.split(",")]

    if not script_list or any(not s for s in script_list):
        raise ValueError("Script list cannot contain empty entries")

    if len(script_list) > MAX_SCRIPTS:
        raise ValueError(f"Cannot create more than {MAX_SCRIPTS} scripts")

    # Normalize script names (ensure .py extension)
    normalized = []
    for script in script_list:
        if script.endswith(".py"):
            normalized.append(script)
        else:
            normalized.append(f"{script}.py")

    return normalized

def validate_keywords(keywords_str: str) -> list[str]:
    """
    Validate and parse keyword list.

    Args:
        keywords_str: Comma-separated keywords

    Returns:
        List of validated keywords

    Raises:
        ValueError: If keywords string is invalid
    """
    if not keywords_str:
        return []

    keyword_list = [k.strip().lower() for k in keywords_str.split(",")]

    if not keyword_list or any(not k for k in keyword_list):
        raise ValueError("Keyword list cannot contain empty entries")

    return keyword_list

# ========== SECTION 7: CORE BUSINESS LOGIC ==========
def generate_skill_content(config: SkillConfig) -> str:
    """
    Generate complete SKILL.md file content with YAML frontmatter.

    Creates YAML frontmatter with all required fields plus progressive disclosure
    documentation, available scripts section, architecture overview, and quick start.

    Args:
        config: Skill configuration

    Returns:
        Complete SKILL.md content as string

    Examples:
        >>> config = SkillConfig(name="moai-connector-api", description="REST API toolkit")
        >>> content = generate_skill_content(config)
        >>> assert "---" in content
        >>> assert "Available Scripts" in content
    """
    frontmatter = config.to_frontmatter()

    # Build YAML frontmatter
    yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

    # Build full content
    skill_name_display = config.name.replace("-", " ").title()
    script_count = len(config.scripts)

    content_parts = [
        "---",
        yaml_content.strip(),
        "---",
        "",
        "---",
        "",
        "## Quick Reference (30 seconds)",
        "",
        f"**{skill_name_display}**",
        "",
        f"**What It Does**: {config.description}",
        "",
        "**Core Capabilities**:",
        *[f"- 🔧 **[Capability {i+1}]**: [Brief description]" for i in range(3)],
        "",
        "**Progressive Disclosure Workflow**:",
        "```",
        "User Request → SKILL.md (200 tokens) → Script --help (0 tokens) → Execute",
        "     ↓              ↓                      ↓                    ↓",
        "   Dormant     Quick Check         Full Documentation    Implementation",
        "```",
        "",
        "**When to Use**:",
        *[f"- {cap}" for cap in [
            f"Generating or scaffolding {config.name.split('-')[1]} artifacts",
            "Creating production-ready code with MoAI standards compliance",
            "Rapid prototyping and template-based automation",
            "Integrating with existing MoAI workflow"
        ]],
        "",
        "---",
        "",
        "## Available Scripts",
        "",
        f"This skill includes {script_count} UV CLI scripts following IndieDevDan pattern (PEP 723, dual output, 200-300 lines each).",
        "",
    ]

    # Add script documentation
    for idx, script in enumerate(config.scripts, 1):
        script_name = script if script.endswith(".py") else f"{script}.py"
        script_base = script_name.replace(".py", "")

        content_parts.extend([
            f"### {idx}. {script_name}",
            "",
            f"**Purpose**: [Define purpose for {script_name}]",
            "",
            "**Usage**:",
            "```bash",
            f"# Basic usage",
            f"uv run .claude/skills/{config.name}/scripts/{script_name} [OPTIONS]",
            "",
            f"# JSON output mode",
            f"uv run .claude/skills/{config.name}/scripts/{script_name} --json",
            "",
            f"# Help",
            f"uv run .claude/skills/{config.name}/scripts/{script_name} --help",
            "```",
            "",
            "**Features**:",
            "- [Feature 1]",
            "- [Feature 2]",
            "- [Feature 3]",
            "",
            "**Exit Codes**: 0 (success), 1 (warning), 2 (error), 3 (critical)",
            "",
            "---",
            "",
        ])

    content_parts.extend([
        "## Architecture",
        "",
        "**Design Principles**:",
        "- **Self-Contained Scripts**: Each script is 200-300 lines with embedded dependencies (PEP 723)",
        "- **Progressive Disclosure**: Scripts dormant at 0 tokens until invoked",
        "- **Dual Output**: Human-readable (default) + JSON mode (--json flag)",
        "- **MCP-Wrappable**: Stateless, JSON output, no interactive prompts",
        "- **Context7 Integration**: Latest patterns from official MoAI documentation",
        "- **TRUST 5 Compliance**: All generated code follows MoAI quality standards",
        "",
        "**Integration Points**:",
        "- **manager-tdd**: Test generation and validation",
        "- **manager-quality**: Code quality checks and TRUST 5 validation",
        "- **mcp-context7**: Latest API documentation and patterns",
        "- **expert-[domain]**: Domain-specific code generation",
        "",
        "---",
        "",
        "## IndieDevDan Pattern Compliance",
        "",
        f"All {script_count} scripts follow **13 IndieDevDan rules** documented in `builder-workflow.md`:",
        "",
        "✅ Size Constraints: 200-300 lines target (max 500)",
        "✅ ASTRAL UV: PEP 723 `# /// script` dependency blocks",
        "✅ Directory Organization: Flat `scripts/` directory",
        "✅ Self-Containment: Embedded utilities, no shared imports",
        "✅ CLI Interface: Click framework, --help, --json flags",
        "✅ Structure: 9-section template (Shebang, Docstring, Imports, etc.)",
        "✅ Dependency Management: 0-3 packages, minimum version pinning",
        "✅ Documentation: Google-style docstrings, comprehensive --help",
        "✅ Testing: Basic unit tests (5-10 per script)",
        "✅ Single-File: No multi-file dependencies",
        "✅ Error Handling: Dual-mode errors (human + JSON)",
        "✅ Configuration: Environment variables, no hardcoded secrets",
        "✅ Progressive Disclosure: 0-token dormant, SKILL.md listing",
        "",
        "---",
        "",
        "## Quick Start",
        "",
        "```bash",
        *[f"# {i+1}. [Usage example {i+1}]" for i in range(3)],
        "```",
        "",
        "---",
        "",
        f"**Version**: {config.version}",
        f"**Status**: ✅ Active (Phase 1, Tier 1)",
        f"**Scripts**: {script_count} total (all MCP-ready)",
        f"**Lines**: ~[Calculate] total (avg ~250 lines/script)",
        f"**Last Updated**: {_get_current_date()}",
        ""
    ])

    return "\n".join(content_parts)

def create_skill_structure(skill_path: Path, config: SkillConfig) -> tuple[bool, Optional[str]]:
    """
    Create skill directory structure with scripts/ subdirectory.

    Args:
        skill_path: Path to skill directory
        config: Skill configuration

    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Create main skill directory
        skill_path.mkdir(parents=True, exist_ok=True)

        # Create scripts subdirectory
        scripts_dir = skill_path / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        # Create stub script files
        for script in config.scripts:
            script_name = script if script.endswith(".py") else f"{script}.py"
            script_path = scripts_dir / script_name

            # Create stub content (placeholder for actual script)
            stub_content = f"""#!/usr/bin/env python3
# /// script
# dependencies = [
#     "click>=8.1.7",
# ]
# ///

\"\"\"
[Add script description here]

Usage:
    uv run {script_name} [OPTIONS]

Examples:
    uv run {script_name} --help
\"\"\"

import click
import json
import sys

@click.command()
@click.option('--json', 'json_mode', is_flag=True,
              help='Output in JSON format')
def main(json_mode: bool):
    \"\"\"[Add CLI description here]\"\"\"
    try:
        # Implementation here
        result = {{"status": "success", "message": "Script stub - implement core logic"}}

        if json_mode:
            print(json.dumps(result))
        else:
            print(f"✓ {{result['message']}}")

        sys.exit(0)

    except Exception as e:
        if json_mode:
            print(json.dumps({{"error": str(e)}}))
        else:
            print(f"❌ Error: {{e}}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
"""
            script_path.write_text(stub_content, encoding="utf-8")

        return True, None

    except OSError as e:
        return False, f"Failed to create directory structure: {e}"

def _get_current_date() -> str:
    """Get current date in YYYY-MM-DD format."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")

# ========== SECTION 8: OUTPUT FORMATTERS ==========
def format_json_output(success: bool, skill_path: Optional[Path], scripts: int,
                       error: Optional[str] = None) -> str:
    """
    Format output as JSON for MCP compatibility.

    Args:
        success: Whether operation succeeded
        skill_path: Path to generated skill directory
        scripts: Number of scripts created
        error: Error message (if failed)

    Returns:
        JSON-formatted string
    """
    data = {
        "status": "success" if success else "error",
    }

    if success and skill_path:
        data["skill_path"] = str(skill_path)
        data["scripts"] = scripts
        data["skill_md"] = str(skill_path / "SKILL.md")
        data["scripts_dir"] = str(skill_path / "scripts")

    if error:
        data["error"] = error

    return json.dumps(data, indent=2)

def format_human_output(config: SkillConfig, skill_path: Path, script_count: int) -> str:
    """
    Format output as human-readable success message.

    Args:
        config: Skill configuration
        skill_path: Path to generated skill directory
        script_count: Number of scripts created

    Returns:
        Formatted string with Rich styling
    """
    console = Console()

    summary = f"""[bold green]✅ Skill Generated Successfully[/bold green]

[bold]Skill Details:[/bold]
  Name:        {config.name}
  Description: {config.description}
  Version:     {config.version}
  Scripts:     {script_count}

[bold]Output:[/bold]
  Directory:   {skill_path}
  SKILL.md:    {skill_path / 'SKILL.md'}
  Scripts Dir: {skill_path / 'scripts'}

[bold]Scripts Created:[/bold]
  {chr(10).join(f'  - {s}' for s in config.scripts)}

[bold]Next Steps:[/bold]
  1. Edit SKILL.md to customize descriptions and keywords
  2. Implement script logic in scripts/ directory
  3. Add comprehensive --help documentation to each script
  4. Test scripts via 'uv run' command
  5. Validate with manager-quality for TRUST 5 compliance
"""

    return summary

# ========== SECTION 9: CLI INTERFACE ==========
@click.command()
@click.option('--name', required=True,
              help='Skill name (moai-* or skill-* format, e.g., moai-connector-api)')
@click.option('--description', required=True,
              help='One-line skill description')
@click.option('--scripts', default='script1.py',
              help='Comma-separated script names (default: script1.py)')
@click.option('--keywords', default='',
              help='Comma-separated auto-trigger keywords (optional)')
@click.option('--output', type=click.Path(),
              help='Output directory (default: .claude/skills/{name}/)')
@click.option('--json', 'json_mode', is_flag=True,
              help='Output in JSON format (MCP-compatible)')
@click.option('--force', is_flag=True,
              help='Overwrite existing skill without prompting')
def main(name: str, description: str, scripts: str, keywords: str,
         output: Optional[str], json_mode: bool, force: bool):
    """
    Generate MoAI skill structure with SKILL.md and scripts/.

    Creates properly formatted skill directories following MoAI-ADK conventions
    with YAML frontmatter, script metadata, progressive disclosure documentation,
    and IndieDevDan UV script patterns.

    \b
    Examples:
        # Basic skill generation
        uv run generate_skill.py --name moai-connector-api --description "REST API toolkit"

        # With multiple scripts
        uv run generate_skill.py --name moai-toolkit-data --description "Data processing" \\
            --scripts "process.py,transform.py,validate.py"

        # With keywords and JSON output
        uv run generate_skill.py --name moai-library-testing --description "Testing utilities" \\
            --keywords "test,pytest,vitest" --json

    \b
    Naming Convention:
        Skill names must start with 'moai-' or 'skill-' and use hyphens:
        ✅ moai-connector-api, skill-kalshi-markets, moai-toolkit-codegen
        ❌ moai_connector_api (underscores), api-moai (wrong order)

    \b
    Script Management:
        - Scripts are created as stub files in scripts/ subdirectory
        - Each script is a standalone UV CLI script (PEP 723 format)
        - Scripts are self-contained with no shared imports
    """
    console = Console()

    try:
        # Validate skill name
        is_valid, error_msg = validate_skill_name(name)
        if not is_valid:
            if json_mode:
                print(format_json_output(False, None, 0, error_msg))
            else:
                console.print(f"[bold red]❌ Invalid skill name:[/bold red] {error_msg}")
            sys.exit(2)

        # Validate and parse scripts
        try:
            script_list = validate_scripts(scripts)
        except ValueError as e:
            if json_mode:
                print(format_json_output(False, None, 0, str(e)))
            else:
                console.print(f"[bold red]❌ Invalid scripts:[/bold red] {e}")
            sys.exit(2)

        # Validate and parse keywords
        try:
            keyword_list = validate_keywords(keywords)
        except ValueError as e:
            if json_mode:
                print(format_json_output(False, None, 0, str(e)))
            else:
                console.print(f"[bold red]❌ Invalid keywords:[/bold red] {e}")
            sys.exit(2)

        # Build skill config
        config = SkillConfig(
            name=name,
            description=description,
            scripts=script_list,
            keywords=keyword_list
        )

        # Determine output path
        if output:
            skill_path = Path(output).resolve()
        else:
            skills_dir = PROJECT_ROOT / DEFAULT_OUTPUT_DIR
            skill_path = skills_dir / name

        # Check if directory exists
        if skill_path.exists() and not force:
            if json_mode:
                print(format_json_output(False, None, 0, f"Skill directory already exists: {skill_path}"))
                sys.exit(1)
            else:
                console.print(f"[yellow]⚠️  Skill directory already exists:[/yellow] {skill_path}")
                if not click.confirm("Overwrite?", default=False):
                    console.print("[yellow]Operation cancelled by user[/yellow]")
                    sys.exit(1)

        # Create directory structure
        success, error = create_skill_structure(skill_path, config)
        if not success:
            if json_mode:
                print(format_json_output(False, None, 0, error))
            else:
                console.print(f"[bold red]❌ {error}[/bold red]")
            sys.exit(3)

        # Generate SKILL.md content
        skill_content = generate_skill_content(config)
        skill_md_path = skill_path / "SKILL.md"

        # Write SKILL.md
        try:
            skill_md_path.write_text(skill_content, encoding="utf-8")
        except OSError as e:
            if json_mode:
                print(format_json_output(False, None, len(config.scripts), f"Failed to write SKILL.md: {e}"))
            else:
                console.print(f"[bold red]❌ Failed to write SKILL.md:[/bold red] {e}")
            sys.exit(3)

        # Output results
        if json_mode:
            print(format_json_output(True, skill_path, len(config.scripts)))
        else:
            console.print(format_human_output(config, skill_path, len(config.scripts)))

        sys.exit(0)

    except Exception as e:
        if json_mode:
            print(format_json_output(False, None, 0, f"Unexpected error: {e}"))
        else:
            console.print(f"[bold red]❌ Unexpected error:[/bold red] {e}")
        sys.exit(3)

# ========== SECTION 10: ENTRY POINT ==========
if __name__ == "__main__":
    main()
