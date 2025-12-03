#!/usr/bin/env python3
# /// script
# dependencies = [
#     "click>=8.1.7",
#     "rich>=13.0.0",
# ]
# ///

# ========== SECTION 1: MODULE DOCSTRING ==========
"""
Generate Slash Command Markdown Files - Create .md files with frontmatter

Generates complete slash command markdown files for Claude Code projects,
including YAML frontmatter, argument parsing section, workflow template,
and report format template. Follows builder-workflow.md blueprint patterns.

Usage:
    uv run generate_command.py --name analyze-code --description "Analyze code files"
    uv run generate_command.py --name test-runner --description "Run tests" --tools Read,Bash
    uv run generate_command.py --name deploy --args "environment" --json

Examples:
    # Basic command
    uv run generate_command.py --name analyze-code --description "Analyze code"

    # With specific tools
    uv run generate_command.py --name validate --description "Validate files" --tools "Read,Grep"

    # With custom output path
    uv run generate_command.py --name sync --description "Sync files" --output ".claude/commands/sync.md"

    # JSON output for integration
    uv run generate_command.py --name build --description "Build project" --json

Exit Codes:
    0 - Success
    1 - Warning (partial success)
    2 - Error (operation failed)
    3 - Critical (invalid input or permissions)

Requirements:
    - Python 3.11+
    - UV package manager
    - Write permissions to output directory
"""

# ========== SECTION 2: IMPORTS ==========
import click
import json
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

# ========== SECTION 3: CONSTANTS & CONFIGURATION ==========
DEFAULT_OUTPUT_DIR = ".claude/commands"
DEFAULT_TOOLS = "Read,Write,Edit,Bash"
ALLOWED_TOOLS = {
    "Read", "Write", "Edit", "Bash", "Glob", "Grep", "AskUserQuestion",
    "WebFetch", "WebSearch", "Skill", "SlashCommand", "Task", "NotebookEdit",
    "mcp__context7__resolve-library-id", "mcp__context7__get-library-docs",
    "mcp__playwright__browser_navigate", "mcp__playwright__browser_snapshot",
    "mcp__notion__API-post-search", "mcp__notion__API-retrieve-a-page"
}

# ========== SECTION 4: PROJECT ROOT AUTO-DETECTION ==========
def find_project_root(start_path: Path) -> Path:
    """Auto-detect project root using .git, pyproject.toml, or .moai markers."""
    current = start_path
    while current != current.parent:
        if any((current / marker).exists() for marker in [".git", "pyproject.toml", ".moai"]):
            return current
        current = current.parent
    raise RuntimeError("Project root not found")

PROJECT_ROOT = find_project_root(Path.cwd())

# ========== SECTION 5: DATA MODELS ==========
@dataclass
class CommandMetadata:
    """Command metadata for markdown generation."""
    name: str
    description: str
    tools: list[str]
    args: list[str] | None = None
    timestamp: str | None = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class GeneratedCommand:
    """Result of command generation."""
    status: str
    command_name: str
    output_path: str | None = None
    content: str | None = None
    message: str | None = None

# ========== SECTION 6: CORE BUSINESS LOGIC ==========
class CommandGenerator:
    """Generate slash command markdown files with frontmatter and templates."""

    def __init__(self, metadata: CommandMetadata, output_dir: str | None = None):
        self.metadata = metadata
        output_path = output_dir or DEFAULT_OUTPUT_DIR
        # Resolve to absolute path from project root
        if not Path(output_path).is_absolute():
            self.output_dir = PROJECT_ROOT / output_path
        else:
            self.output_dir = Path(output_path)
        self.output_path = self.output_dir / f"{metadata.name}.md"

    def validate_inputs(self) -> tuple[bool, str]:
        """Validate command name, description, and tools."""
        if not self.metadata.name or not self.metadata.name.replace("-", "").replace("_", "").isalnum():
            return False, "Command name must be alphanumeric with hyphens/underscores only"

        if not self.metadata.description or len(self.metadata.description) < 5:
            return False, "Description must be at least 5 characters"

        invalid_tools = set(self.metadata.tools) - ALLOWED_TOOLS
        if invalid_tools:
            return False, f"Invalid tools: {', '.join(sorted(invalid_tools))}"

        return True, "Validation successful"

    def generate_frontmatter(self) -> str:
        """Generate YAML frontmatter for the command."""
        tools_str = ", ".join(self.metadata.tools)
        args_section = ""
        if self.metadata.args:
            args_section = f"\narguments: {self.metadata.args}"

        frontmatter = f"""---
name: {self.metadata.name}
description: {self.metadata.description}
tools: {tools_str}
model: inherit
permissionMode: bypassPermissions{args_section}
---"""
        return frontmatter

    def generate_workflow_section(self) -> str:
        """Generate workflow template section."""
        args_info = ""
        if self.metadata.args:
            args_list = ", ".join([f"`{arg}`" for arg in self.metadata.args])
            args_info = f"\n\n### Arguments\n- {args_list}: Required command arguments"

        tools_list = "\n- ".join(self.metadata.tools)

        workflow = f"""
# Workflow

## Purpose
Execute {self.metadata.name} command operations.

## Available Tools
- {tools_list}

## Execution Steps
1. Parse command arguments
2. Validate input parameters
3. Execute core operations
4. Format and return results{args_info}

## Error Handling
- Validate all inputs before execution
- Provide clear error messages
- Exit with appropriate exit codes (0=success, 1=warning, 2=error, 3=critical)
"""
        return workflow.strip()

    def generate_report_section(self) -> str:
        """Generate report format template section."""
        report = """
# Report Format

## Standard Output
When command completes successfully, return structured data:

```json
{
  "status": "success",
  "command": "command_name",
  "timestamp": "ISO-8601-timestamp",
  "results": {
    "detail": "operation-specific results"
  }
}
```

## Error Output
When command fails, return error information:

```json
{
  "status": "error",
  "command": "command_name",
  "timestamp": "ISO-8601-timestamp",
  "error": {
    "code": 2,
    "message": "Descriptive error message",
    "type": "ErrorType"
  }
}
```

## Exit Codes
- `0` - Success
- `1` - Warning (partial success)
- `2` - Error (operation failed)
- `3` - Critical (invalid input, permissions, or data loss)
"""
        return report.strip()

    def generate_content(self) -> str:
        """Generate complete markdown content."""
        frontmatter = self.generate_frontmatter()
        workflow = self.generate_workflow_section()
        report = self.generate_report_section()

        content = f"""{frontmatter}

# /{self.metadata.name}

**Description**: {self.metadata.description}

**Last Updated**: {self.metadata.timestamp}

{workflow}

{report}
"""
        return content

    def write_to_file(self, content: str) -> tuple[bool, str]:
        """Write generated content to output file."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.output_path.write_text(content, encoding="utf-8")
            # Get relative path safely
            try:
                rel_path = self.output_path.relative_to(PROJECT_ROOT)
            except ValueError:
                rel_path = self.output_path.absolute()
            return True, f"Command generated: {rel_path}"
        except PermissionError:
            return False, f"Permission denied writing to {self.output_path}"
        except Exception as e:
            return False, f"Failed to write file: {e}"

    def generate(self) -> GeneratedCommand:
        """Execute complete generation workflow."""
        is_valid, validation_msg = self.validate_inputs()
        if not is_valid:
            return GeneratedCommand(
                status="error",
                command_name=self.metadata.name,
                message=validation_msg
            )

        content = self.generate_content()
        success, write_msg = self.write_to_file(content)

        if success:
            return GeneratedCommand(
                status="success",
                command_name=self.metadata.name,
                output_path=str(self.output_path.relative_to(PROJECT_ROOT)),
                content=content,
                message=write_msg
            )
        else:
            return GeneratedCommand(
                status="error",
                command_name=self.metadata.name,
                message=write_msg
            )

# ========== SECTION 7: OUTPUT FORMATTERS ==========
def format_json(result: GeneratedCommand) -> str:
    """Format result as JSON."""
    return json.dumps(asdict(result), indent=2)

def format_human_readable(result: GeneratedCommand) -> str:
    """Format result as human-readable output."""
    if result.status == "success":
        output = f"✓ Command Generated Successfully\n"
        output += f"  Name: {result.command_name}\n"
        output += f"  Path: {result.output_path}\n"
        output += f"  Message: {result.message}"
        return output
    else:
        return f"✗ Command Generation Failed\n  Error: {result.message}"

# ========== SECTION 8: CLI INTERFACE ==========
@click.command()
@click.option('--name', required=True, help='Command name (e.g., "analyze-code")')
@click.option('--description', required=True, help='Command description')
@click.option('--tools', default=DEFAULT_TOOLS, help=f'Comma-separated tools (default: {DEFAULT_TOOLS})')
@click.option('--args', default=None, help='Comma-separated argument names (optional)')
@click.option('--output', default=None, help='Output directory path (default: .claude/commands)')
@click.option('--json', 'json_mode', is_flag=True, help='Output in JSON format')
def main(name: str, description: str, tools: str, args: str, output: str, json_mode: bool):
    """
    Generate slash command markdown files with frontmatter.

    Creates complete .md files for Claude Code slash commands, including
    YAML frontmatter, workflow templates, and report format examples.

    Examples:
        uv run generate_command.py --name analyze-code --description "Analyze code"
        uv run generate_command.py --name test --description "Run tests" --tools "Read,Bash"
        uv run generate_command.py --name deploy --args "environment,region" --json
    """
    try:
        # Parse tools and arguments
        tools_list = [t.strip() for t in tools.split(",") if t.strip()]
        args_list = [a.strip() for a in args.split(",")] if args else None

        # Create metadata and generator
        metadata = CommandMetadata(
            name=name,
            description=description,
            tools=tools_list,
            args=args_list
        )
        generator = CommandGenerator(metadata, output)

        # Generate command file
        result = generator.generate()

        # Output result
        if json_mode:
            print(format_json(result))
        else:
            print(format_human_readable(result))

        # Exit with appropriate code
        sys.exit(0 if result.status == "success" else 2)

    except Exception as e:
        error_result = GeneratedCommand(
            status="critical",
            command_name=name,
            message=f"Unexpected error: {str(e)}"
        )

        if json_mode:
            print(format_json(error_result))
        else:
            print(f"✗ Critical Error: {str(e)}", file=sys.stderr)

        sys.exit(3)

# ========== SECTION 9: ENTRY POINT ==========
if __name__ == "__main__":
    main()
