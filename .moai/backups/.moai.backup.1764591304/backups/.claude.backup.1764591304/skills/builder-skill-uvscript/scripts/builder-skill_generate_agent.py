#!/usr/bin/env python3
# /// script
# dependencies = [
#     "click>=8.1.7",
#     "rich>=13.0.0",
#     "pyyaml>=6.0",
# ]
# ///

"""
Generate MoAI Agent YAML Files - Complete Frontmatter Generator

Creates properly formatted MoAI agent YAML files with complete frontmatter,
orchestration metadata, mission statements, and workflow templates.

Usage:
    uv run generate_agent.py --name <name> --description <desc>
    uv run generate_agent.py --name expert-api --description "API specialist"
    uv run generate_agent.py --help

Examples:
    # Generate basic agent
    uv run generate_agent.py --name expert-api --description "REST API development specialist"

    # Generate with custom tools
    uv run generate_agent.py --name manager-test --description "Test orchestrator" --tools "Read,Write,Bash"

    # Generate with JSON output
    uv run generate_agent.py --name expert-db --description "Database expert" --json

    # Custom output path
    uv run generate_agent.py --name expert-ui --description "UI specialist" --output /path/to/agent.md

Exit Codes:
    0 - Success (agent file created)
    1 - Warning (file exists, user declined overwrite)
    2 - Error (invalid input or validation failure)
    3 - Critical (unable to write file or system error)

Requirements:
    - Python 3.11+
    - UV package manager
    - Access to project root (.claude/agents/ directory)

Notes:
    - Designed for UV execution only (no manual pip install)
    - Works from any directory (auto-detects project root)
    - MCP-wrappable for future server integration
    - Validates agent naming conventions ({role}-{domain})
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
DEFAULT_TOOLS = ["Read", "Write", "Edit", "Bash"]
DEFAULT_MODEL = "inherit"
DEFAULT_PERMISSION_MODE = "bypassPermissions"
DEFAULT_COLOR = "blue"

# Agent name validation patterns
VALID_ROLES = ["expert", "manager", "builder", "mcp", "ai"]

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
class AgentConfig:
    """
    Agent configuration data model with all frontmatter fields.

    Attributes:
        name: Agent name in {role}-{domain} format
        description: One-line agent description
        tools: List of tool names (Read, Write, Edit, etc.)
        model: Model selection (inherit, sonnet, haiku)
        color: Console color (blue, green, yellow, etc.)
        permissionMode: Permission mode (bypassPermissions, askPermission)
        skills: Optional list of skill names
        can_resume: Whether agent supports resume pattern
        parallel_safe: Whether agent can run in parallel
    """
    name: str
    description: str
    tools: list[str] = field(default_factory=lambda: DEFAULT_TOOLS.copy())
    model: str = DEFAULT_MODEL
    color: str = DEFAULT_COLOR
    permissionMode: str = DEFAULT_PERMISSION_MODE
    skills: list[str] = field(default_factory=list)
    can_resume: bool = True
    parallel_safe: bool = True

    def to_frontmatter(self) -> dict:
        """Convert to YAML frontmatter dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "tools": ", ".join(self.tools),
            "model": self.model,
            "color": self.color,
            "permissionMode": self.permissionMode,
            "skills": ", ".join(self.skills) if self.skills else None,
        }

    def to_orchestration_metadata(self) -> dict:
        """Convert to orchestration metadata dictionary."""
        return {
            "orchestration": {
                "can_resume": self.can_resume,
                "typical_chain_position": "variable",
                "depends_on": [],
                "resume_pattern": "single-session" if self.can_resume else "none",
                "parallel_safe": self.parallel_safe,
            },
            "coordination": {
                "spawns_subagents": False,
                "delegates_to": [],
                "requires_approval": False,
            },
            "performance": {
                "avg_execution_time_seconds": 300,
                "context_heavy": False,
                "mcp_integration": [],
                "skill_count": len(self.skills),
            }
        }

# ========== SECTION 6: VALIDATION ==========
def validate_agent_name(name: str) -> tuple[bool, Optional[str]]:
    """
    Validate agent name follows {role}-{domain} convention.

    Args:
        name: Agent name to validate

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_agent_name("expert-api")
        (True, None)
        >>> validate_agent_name("invalid_name")
        (False, "Agent name must follow {role}-{domain} format")
    """
    if not name:
        return False, "Agent name cannot be empty"

    parts = name.split("-")
    if len(parts) < 2:
        return False, f"Agent name must follow {{role}}-{{domain}} format (e.g., expert-api). Got: {name}"

    role = parts[0]
    if role not in VALID_ROLES:
        return False, f"Invalid role '{role}'. Must be one of: {', '.join(VALID_ROLES)}"

    domain = "-".join(parts[1:])
    if not domain or not domain.replace("-", "").isalnum():
        return False, f"Invalid domain '{domain}'. Must be alphanumeric with hyphens"

    return True, None

def validate_tools(tools: str) -> list[str]:
    """
    Validate and parse tool list.

    Args:
        tools: Comma-separated tool names

    Returns:
        List of validated tool names

    Raises:
        ValueError: If tools string is invalid
    """
    if not tools:
        return DEFAULT_TOOLS.copy()

    tool_list = [t.strip() for t in tools.split(",")]
    if not tool_list or any(not t for t in tool_list):
        raise ValueError("Tool list cannot contain empty entries")

    return tool_list

# ========== SECTION 7: CORE BUSINESS LOGIC ==========
def generate_agent_content(config: AgentConfig) -> str:
    """
    Generate complete agent YAML file content.

    Creates YAML frontmatter with all required fields plus mission statement,
    orchestration metadata, workflow section, and report format templates.

    Args:
        config: Agent configuration

    Returns:
        Complete agent file content as string

    Examples:
        >>> config = AgentConfig(name="expert-api", description="API specialist")
        >>> content = generate_agent_content(config)
        >>> assert "---" in content
        >>> assert "# Primary Mission" in content
    """
    frontmatter = config.to_frontmatter()
    # Remove None values
    frontmatter = {k: v for k, v in frontmatter.items() if v is not None}

    orchestration = config.to_orchestration_metadata()

    # Build YAML frontmatter
    yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

    # Build orchestration metadata
    orchestration_yaml = yaml.dump(orchestration, default_flow_style=False, sort_keys=False)

    # Extract role and domain from name
    parts = config.name.split("-", 1)
    role = parts[0].capitalize()
    domain = parts[1].replace("-", " ").title()

    # Build full content
    content_parts = [
        "---",
        yaml_content.strip(),
        "---",
        "",
        f"# {config.name.upper()} Orchestration Metadata",
        "",
        f"**Version**: 1.0.0",
        f"**Last Updated**: {_get_current_date()}",
        "",
        "```yaml",
        orchestration_yaml.strip(),
        "```",
        "",
        "---",
        "",
        "# Primary Mission",
        "",
        f"As a {role} specializing in {domain}, this agent is responsible for:",
        "",
        "1. **Domain Expertise**: [Define core domain responsibilities]",
        "2. **Task Execution**: [Describe primary task types]",
        "3. **Quality Assurance**: [Outline quality standards]",
        "4. **Coordination**: [Specify interaction with other agents]",
        "",
        "---",
        "",
        "# Workflow",
        "",
        "## Phase 1: Analysis",
        "",
        "- Receive task requirements from orchestrator",
        "- Validate inputs and constraints",
        "- Plan execution strategy",
        "",
        "## Phase 2: Execution",
        "",
        "- Execute core domain tasks",
        "- Apply best practices and standards",
        "- Handle errors and edge cases",
        "",
        "## Phase 3: Validation",
        "",
        "- Verify outputs meet quality standards",
        "- Run domain-specific validations",
        "- Prepare results for delivery",
        "",
        "## Phase 4: Reporting",
        "",
        "- Format results according to output mode",
        "- Provide actionable recommendations",
        "- Document decisions and rationale",
        "",
        "---",
        "",
        "# Report Format",
        "",
        "## Success Report",
        "",
        "```",
        f"✅ {role} {domain.upper()} - SUCCESS",
        "",
        "**Task**: [Task description]",
        "**Status**: Completed successfully",
        "",
        "**Results**:",
        "- [Key result 1]",
        "- [Key result 2]",
        "- [Key result 3]",
        "",
        "**Quality Metrics**:",
        "- [Metric 1]: [Value]",
        "- [Metric 2]: [Value]",
        "",
        "**Recommendations**:",
        "- [Recommendation 1]",
        "- [Recommendation 2]",
        "```",
        "",
        "## Error Report",
        "",
        "```",
        f"❌ {role} {domain.upper()} - ERROR",
        "",
        "**Task**: [Task description]",
        "**Error**: [Error description]",
        "",
        "**Root Cause**:",
        "[Detailed root cause analysis]",
        "",
        "**Resolution Steps**:",
        "1. [Step 1]",
        "2. [Step 2]",
        "3. [Step 3]",
        "",
        "**Prevention**:",
        "- [Prevention measure 1]",
        "- [Prevention measure 2]",
        "```",
        "",
        "---",
        "",
        f"**Agent**: {config.name}",
        f"**Version**: 1.0.0",
        f"**Status**: ✅ Active",
        ""
    ]

    return "\n".join(content_parts)

def _get_current_date() -> str:
    """Get current date in YYYY-MM-DD format."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")

# ========== SECTION 8: OUTPUT FORMATTERS ==========
def format_json_output(success: bool, file_path: Optional[Path], lines: int,
                       error: Optional[str] = None) -> str:
    """
    Format output as JSON for MCP compatibility.

    Args:
        success: Whether operation succeeded
        file_path: Path to generated file (if successful)
        lines: Number of lines in generated file
        error: Error message (if failed)

    Returns:
        JSON-formatted string
    """
    data = {
        "status": "success" if success else "error",
    }

    if success and file_path:
        data["file_path"] = str(file_path)
        data["lines"] = lines

    if error:
        data["error"] = error

    return json.dumps(data, indent=2)

def format_human_output(config: AgentConfig, file_path: Path, lines: int) -> str:
    """
    Format output as human-readable success message.

    Args:
        config: Agent configuration
        file_path: Path to generated file
        lines: Number of lines in file

    Returns:
        Formatted string with Rich styling
    """
    console = Console()

    summary = f"""[bold green]✅ Agent Generated Successfully[/bold green]

[bold]Agent Details:[/bold]
  Name:        {config.name}
  Description: {config.description}
  Tools:       {', '.join(config.tools)}
  Model:       {config.model}

[bold]Output:[/bold]
  File:        {file_path}
  Lines:       {lines}
  Size:        {file_path.stat().st_size} bytes

[bold]Next Steps:[/bold]
  1. Review the generated agent file
  2. Customize mission and workflow sections
  3. Add domain-specific logic
  4. Test agent via Task() delegation
"""

    return summary

# ========== SECTION 9: CLI INTERFACE ==========
@click.command()
@click.option('--name', required=True,
              help='Agent name in {role}-{domain} format (e.g., expert-api)')
@click.option('--description', required=True,
              help='One-line agent description')
@click.option('--tools', default=','.join(DEFAULT_TOOLS),
              help=f'Comma-separated tool names (default: {",".join(DEFAULT_TOOLS)})')
@click.option('--model', default=DEFAULT_MODEL,
              help=f'Model selection: inherit, sonnet, haiku (default: {DEFAULT_MODEL})')
@click.option('--skills', default='',
              help='Comma-separated skill names (optional)')
@click.option('--output', type=click.Path(),
              help='Output file path (default: .claude/agents/{name}.md)')
@click.option('--json', 'json_mode', is_flag=True,
              help='Output in JSON format (MCP-compatible)')
@click.option('--force', is_flag=True,
              help='Overwrite existing file without prompting')
def main(name: str, description: str, tools: str, model: str, skills: str,
         output: Optional[str], json_mode: bool, force: bool):
    """
    Generate MoAI agent YAML files with complete frontmatter.

    Creates properly formatted agent files following MoAI-ADK conventions with
    YAML frontmatter, orchestration metadata, mission statements, workflow
    templates, and report format examples.

    \b
    Examples:
        # Basic agent generation
        uv run generate_agent.py --name expert-api --description "REST API specialist"

        # Custom tools and model
        uv run generate_agent.py --name manager-test --description "Test orchestrator" \\
            --tools "Read,Write,Bash" --model sonnet

        # JSON output for MCP
        uv run generate_agent.py --name expert-db --description "Database expert" --json

    \b
    Naming Convention:
        Agent names must follow {role}-{domain} format where:
        - role: expert, manager, builder, mcp, ai
        - domain: descriptive name (alphanumeric with hyphens)

    \b
    Examples of valid names:
        ✅ expert-api, manager-test, builder-agent, mcp-notion, ai-nano-banana
        ❌ api-expert (wrong role order), ExpertAPI (no camelCase), expert_api (no underscores)
    """
    console = Console()

    try:
        # Validate agent name
        is_valid, error_msg = validate_agent_name(name)
        if not is_valid:
            if json_mode:
                print(format_json_output(False, None, 0, error_msg))
            else:
                console.print(f"[bold red]❌ Invalid agent name:[/bold red] {error_msg}")
            sys.exit(2)

        # Validate and parse tools
        try:
            tool_list = validate_tools(tools)
        except ValueError as e:
            if json_mode:
                print(format_json_output(False, None, 0, str(e)))
            else:
                console.print(f"[bold red]❌ Invalid tools:[/bold red] {e}")
            sys.exit(2)

        # Parse skills
        skill_list = [s.strip() for s in skills.split(",") if s.strip()] if skills else []

        # Build agent config
        config = AgentConfig(
            name=name,
            description=description,
            tools=tool_list,
            model=model,
            skills=skill_list
        )

        # Determine output path
        if output:
            output_path = Path(output)
        else:
            agents_dir = PROJECT_ROOT / ".claude" / "agents" / "moai"
            agents_dir.mkdir(parents=True, exist_ok=True)
            output_path = agents_dir / f"{name}.md"

        # Check if file exists
        if output_path.exists() and not force:
            if json_mode:
                print(format_json_output(False, None, 0, f"File already exists: {output_path}"))
                sys.exit(1)
            else:
                console.print(f"[yellow]⚠️  File already exists:[/yellow] {output_path}")
                if not click.confirm("Overwrite?", default=False):
                    console.print("[yellow]Operation cancelled by user[/yellow]")
                    sys.exit(1)

        # Generate content
        content = generate_agent_content(config)
        lines = len(content.splitlines())

        # Write file
        try:
            output_path.write_text(content, encoding="utf-8")
        except OSError as e:
            if json_mode:
                print(format_json_output(False, None, 0, f"Failed to write file: {e}"))
            else:
                console.print(f"[bold red]❌ Failed to write file:[/bold red] {e}")
            sys.exit(3)

        # Output results
        if json_mode:
            print(format_json_output(True, output_path, lines))
        else:
            console.print(format_human_output(config, output_path, lines))

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
