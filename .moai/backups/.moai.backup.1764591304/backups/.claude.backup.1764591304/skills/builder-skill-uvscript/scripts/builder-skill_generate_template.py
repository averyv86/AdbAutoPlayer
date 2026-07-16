#!/usr/bin/env python3
# /// script
# dependencies = [
#     "click>=8.0.0",
# ]
# ///

"""
MoAI Template Generator

Generate project templates from IndieDevDan skill patterns with variable substitution.

Usage:
    uv run template_generator.py --type skill --name my-skill
    uv run template_generator.py --type agent --name my-agent --json
    uv run template_generator.py --type command --name my-cmd --dry-run
    uv run template_generator.py --type script --name my_script.py

Exit Codes:
    0 - Success (template generated)
    1 - Invalid input (missing required parameters)
    2 - Template processing error (file reading/writing failed)
    3 - Validation error (generated template invalid)
"""

import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import click


# ============================================================================
# Configuration
# ============================================================================

TEMPLATES_BASE = Path("/Users/rdmtv/Documents/claydev-local/v1-projects/Agent OS/indiedevdan-beyond-mcp/beyond-mcp/docs/templates/skill-template")

TEMPLATE_PATHS = {
    "skill": TEMPLATES_BASE / ".claude/skills/example-skill/SKILL.md",
    "agent": TEMPLATES_BASE / ".claude/agents/agent-template.md",
    "command": TEMPLATES_BASE / ".claude/commands/command-template.md",
    "script": TEMPLATES_BASE / ".claude/skills/example-skill/scripts/script-template.py",
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class TemplateFile:
    """Represents a generated template file."""
    path: str
    size: int
    lines: int
    status: str


@dataclass
class ValidationResult:
    """Template validation results."""
    skill_md_valid: bool
    frontmatter_valid: bool
    size_check: str
    replacements: Dict[str, int]


@dataclass
class GenerationResult:
    """Complete template generation result."""
    template_type: str
    name: str
    files_created: List[Dict[str, Any]]
    validation: Dict[str, Any]
    next_steps: List[str]


# ============================================================================
# Template Processing
# ============================================================================

class TemplateGenerator:
    """Generate templates with variable substitution."""

    def __init__(self, template_type: str, name: str, description: Optional[str] = None):
        self.template_type = template_type
        self.name = name
        self.description = description or f"Auto-generated {template_type}"
        self.replacements_made = 0
        self.replacements_total = 0

    def generate_keywords(self, name: str) -> str:
        """Generate trigger keywords from name."""
        # Convert kebab-case or snake_case to keywords
        parts = name.replace('-', ' ').replace('_', ' ').split()
        return ', '.join([f'"{part}"' for part in parts])

    def generate_script_docs(self, name: str) -> str:
        """Generate script documentation placeholder."""
        return f"Scripts for {name} automation and data processing"

    def get_replacements(self) -> Dict[str, str]:
        """Get replacement mappings for template variables."""
        base_replacements = {
            '[REPLACE: Skill Name]': self.name.replace('-', ' ').title(),
            '[REPLACE: description...]': self.description,
            '[REPLACE: trigger keywords]': self.generate_keywords(self.name),
            '[REPLACE: script descriptions]': self.generate_script_docs(self.name),
            '[REPLACE: agent-name-kebab-case]': self.name,
            '[REPLACE: Brief description of what this agent does. Used by Claude to understand when to invoke this agent.]': self.description,
            '[REPLACE: Brief description of what this command does. Claude uses this to understand when to use this command.]': self.description,
            '[REPLACE: Script Title]': self.name.replace('-', ' ').replace('_', ' ').title(),
            '[REPLACE: Brief description of what this script does]': self.description,
        }

        # Template-specific replacements
        if self.template_type == 'skill':
            base_replacements.update({
                '[REPLACE: Describe when this skill should activate - include trigger keywords like "weather data", "market analysis", "code formatting", etc. Claude uses this to decide when to load the skill.]':
                    f"{self.description}. Activates on: {self.generate_keywords(self.name)}",
            })
        elif self.template_type == 'agent':
            base_replacements.update({
                '[REPLACE: Tool1, Tool2, Tool3, etc. - Comma-separated list of allowed tools]':
                    'Read, Write, Bash, Grep, Glob',
                '[REPLACE: haiku or sonnet]': 'sonnet',
                '[REPLACE: blue, green, purple, red, yellow, etc.]': 'blue',
            })
        elif self.template_type == 'command':
            base_replacements.update({
                '[REPLACE: Tool1, Tool2, Tool3, etc. - Comma-separated list of tools this command can use]':
                    'Read, Bash, Task',
            })

        return base_replacements

    def replace_variables(self, content: str) -> str:
        """Replace template variables in content."""
        replacements = self.get_replacements()
        modified_content = content
        self.replacements_total = len([line for line in content.split('\n') if '[REPLACE' in line])

        for placeholder, value in replacements.items():
            if placeholder in modified_content:
                modified_content = modified_content.replace(placeholder, value)
                self.replacements_made += 1

        return modified_content

    def get_output_path(self, base_dir: Path) -> Path:
        """Get output path based on template type."""
        if self.template_type == 'skill':
            return base_dir / f".claude/skills/{self.name}/SKILL.md"
        elif self.template_type == 'agent':
            return base_dir / f".claude/agents/{self.name}.md"
        elif self.template_type == 'command':
            return base_dir / f".claude/commands/{self.name}.md"
        elif self.template_type == 'script':
            script_name = self.name if self.name.endswith('.py') else f"{self.name}.py"
            return base_dir / f".claude/skills/scripts/{script_name}"
        else:
            raise ValueError(f"Unknown template type: {self.template_type}")

    def create_template_structure(self, output_path: Path) -> List[Path]:
        """Create necessary directory structure and return all paths created."""
        paths_created = []

        # Create parent directories
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.template_type == 'skill':
            # Create skill directory structure
            skill_dir = output_path.parent
            modules_dir = skill_dir / "modules"
            scripts_dir = skill_dir / "scripts"

            modules_dir.mkdir(exist_ok=True)
            scripts_dir.mkdir(exist_ok=True)

            # Create placeholder files
            (modules_dir / "quick-start.md").write_text("# Quick Start\n\nQuick reference documentation.\n")
            (scripts_dir / "README.md").write_text("# Scripts\n\nUtility scripts for this skill.\n")

            paths_created.extend([modules_dir / "quick-start.md", scripts_dir / "README.md"])

        return paths_created

    def validate_template(self, output_path: Path, content: str) -> ValidationResult:
        """Validate generated template."""
        lines = content.split('\n')
        line_count = len(lines)

        # Check frontmatter for skill/agent/command
        frontmatter_valid = False
        if content.startswith('---'):
            frontmatter_end = content.find('---', 3)
            if frontmatter_end > 0:
                frontmatter_valid = True

        # Check if skill.md is within size limits
        size_check = "N/A"
        if self.template_type == 'skill':
            if line_count <= 500:
                size_check = f"{line_count} lines (within 500 target)"
            else:
                size_check = f"{line_count} lines (EXCEEDS 500 limit - split required)"

        return ValidationResult(
            skill_md_valid=self.template_type == 'skill' and frontmatter_valid,
            frontmatter_valid=frontmatter_valid,
            size_check=size_check,
            replacements={
                "total": self.replacements_total,
                "completed": self.replacements_made,
                "missing": self.replacements_total - self.replacements_made
            }
        )

    def generate(self, output_dir: Path, dry_run: bool = False) -> GenerationResult:
        """Generate template with all processing."""
        # Read template source
        template_source = TEMPLATE_PATHS.get(self.template_type)
        if not template_source or not template_source.exists():
            raise FileNotFoundError(f"Template not found: {template_source}")

        template_content = template_source.read_text()

        # Process template
        processed_content = self.replace_variables(template_content)
        output_path = self.get_output_path(output_dir)

        files_created = []

        if not dry_run:
            # Create directory structure
            additional_paths = self.create_template_structure(output_path)

            # Write main template
            output_path.write_text(processed_content)

            # Record created files
            files_created.append(TemplateFile(
                path=str(output_path),
                size=len(processed_content),
                lines=len(processed_content.split('\n')),
                status="created"
            ))

            for path in additional_paths:
                files_created.append(TemplateFile(
                    path=str(path),
                    size=path.stat().st_size,
                    lines=len(path.read_text().split('\n')),
                    status="created"
                ))
        else:
            # Dry run - just show what would be created
            files_created.append(TemplateFile(
                path=str(output_path),
                size=len(processed_content),
                lines=len(processed_content.split('\n')),
                status="dry-run"
            ))

        # Validate
        validation = self.validate_template(output_path, processed_content)

        # Generate next steps
        next_steps = self.get_next_steps(output_path)

        return GenerationResult(
            template_type=self.template_type,
            name=self.name,
            files_created=[asdict(f) for f in files_created],
            validation=asdict(validation),
            next_steps=next_steps
        )

    def get_next_steps(self, output_path: Path) -> List[str]:
        """Generate contextual next steps."""
        steps = []

        if self.template_type == 'skill':
            steps.extend([
                f"Review {output_path}",
                "Add scripts to scripts/ directory if needed",
                "Update modules/ with detailed documentation",
                "Test skill activation with trigger keywords"
            ])
        elif self.template_type == 'agent':
            steps.extend([
                f"Review {output_path}",
                "Define agent workflow steps",
                "Configure tool permissions",
                "Test agent delegation via Task()"
            ])
        elif self.template_type == 'command':
            steps.extend([
                f"Review {output_path}",
                "Define command workflow",
                "Configure allowed tools",
                "Test command execution"
            ])
        elif self.template_type == 'script':
            steps.extend([
                f"Review {output_path}",
                "Implement script logic",
                "Add CLI options and help text",
                "Test with --json flag"
            ])

        return steps


# ============================================================================
# CLI
# ============================================================================

@click.command()
@click.option('--type', 'template_type',
              type=click.Choice(['skill', 'agent', 'command', 'script']),
              required=True,
              help='Template type to generate')
@click.option('--name', required=True,
              help='Template name (e.g., my-skill, my-agent)')
@click.option('--description',
              help='Brief description')
@click.option('--output', type=click.Path(),
              help='Output directory (default: .claude/)')
@click.option('--dry-run', is_flag=True,
              help='Preview without creating files')
@click.option('--json', 'output_json', is_flag=True,
              help='JSON output mode')
def main(template_type: str, name: str, description: Optional[str],
         output: Optional[str], dry_run: bool, output_json: bool):
    """
    Generate project templates from IndieDevDan skill patterns.

    Examples:
        uv run template_generator.py --type skill --name my-skill
        uv run template_generator.py --type agent --name my-agent --json
        uv run template_generator.py --type command --name my-cmd --dry-run
    """
    try:
        # Determine output directory
        output_dir = Path(output) if output else Path.cwd()

        # Generate template
        generator = TemplateGenerator(template_type, name, description)
        result = generator.generate(output_dir, dry_run=dry_run)

        # Output results
        if output_json:
            click.echo(json.dumps(asdict(result), indent=2))
        else:
            click.echo("\n" + "=" * 70)
            click.echo(f"Template Generation: {template_type.upper()}")
            click.echo("=" * 70)
            click.echo(f"\nName: {result.name}")
            click.echo(f"Type: {result.template_type}")
            click.echo(f"Mode: {'DRY RUN' if dry_run else 'CREATED'}")

            click.echo(f"\nFiles:")
            for file_info in result.files_created:
                status_icon = "📝" if file_info['status'] == 'dry-run' else "✅"
                click.echo(f"  {status_icon} {file_info['path']}")
                click.echo(f"     Size: {file_info['size']} bytes | Lines: {file_info['lines']}")

            click.echo(f"\nValidation:")
            val = result.validation
            click.echo(f"  Frontmatter: {'✅' if val['frontmatter_valid'] else '❌'}")
            click.echo(f"  Size Check: {val['size_check']}")
            click.echo(f"  Replacements: {val['replacements']['completed']}/{val['replacements']['total']}")

            click.echo(f"\nNext Steps:")
            for i, step in enumerate(result.next_steps, 1):
                click.echo(f"  {i}. {step}")

            click.echo("=" * 70)

        sys.exit(0)

    except FileNotFoundError as e:
        error_msg = f"Template file not found: {str(e)}"
        if output_json:
            click.echo(json.dumps({"error": error_msg, "exit_code": 2}, indent=2))
        else:
            click.echo(f"\n❌ Error: {error_msg}", err=True)
        sys.exit(2)

    except Exception as e:
        error_msg = f"Template generation failed: {str(e)}"
        if output_json:
            click.echo(json.dumps({"error": error_msg, "exit_code": 3}, indent=2))
        else:
            click.echo(f"\n❌ Error: {error_msg}", err=True)
        sys.exit(3)


if __name__ == "__main__":
    main()
