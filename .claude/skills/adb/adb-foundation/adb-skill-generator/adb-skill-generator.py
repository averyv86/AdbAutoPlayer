#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "pyyaml>=6.0",
# ]
# ///

"""
ADB Skill Generator - Rapid adb-* skill creation from templates

Automates creation of new adb-* skills by generating:
  - Skill directory structure (.claude/skills/adb-{name}/)
  - SKILL.md metadata file with proper formatting
  - Script templates matching established patterns
  - Workflow YAML examples (optional)

Usage:
    uv run adb-skill-generator.py --skill-name myapp --description "My app automation"
    uv run adb-skill-generator.py --skill-name myapp --script-count 3
    uv run adb-skill-generator.py --list-templates

Examples:
    # Generate minimal skill (1 launcher script)
    uv run adb-skill-generator.py \\
        --skill-name banking \\
        --description "Banking app automation via Play Integrity bypass"

    # Generate full skill (3 scripts + workflow)
    uv run adb-skill-generator.py \\
        --skill-name fitness \\
        --description "Fitness app testing" \\
        --script-count 3 \\
        --with-workflow

    # List available templates
    uv run adb-skill-generator.py --list-templates

Exit Codes:
    0 - Success (skill created)
    1 - Warning (partial creation)
    2 - Error (skill creation failed)
    3 - Critical (invalid parameters)
"""

# ========== SECTION 2: IMPORTS ==========
import subprocess
import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any
import click
import yaml

# ========== SECTION 3: CONSTANTS ==========
ADB_SKILL_GENERATOR_VERSION = "1.0.0"
SKILL_TEMPLATES_DIR = Path(__file__).parent / "templates"
SKILLS_BASE_DIR = ".claude/skills"

SCRIPT_TEMPLATES = {
    "launcher": "adb_script_launcher_template.py",
    "checker": "adb_script_checker_template.py",
    "automator": "adb_script_automator_template.py",
    "tester": "adb_script_tester_template.py",
}

SKILL_CATEGORIES = [
    "adb-app-automation",
    "adb-device-management",
    "adb-system-control",
    "adb-testing",
    "adb-validation",
]

# ========== SECTION 4: PROJECT ROOT AUTO-DETECTION ==========
def find_project_root(start_path: Path = None) -> Path:
    """Auto-detect project root by searching for markers."""
    current = (start_path or Path.cwd()).resolve()
    while current != current.parent:
        if any((current / marker).exists() for marker in
               [".git", "pyproject.toml", ".moai", ".claude"]):
            return current
        current = current.parent
    return Path.cwd()

# ========== SECTION 5: DATA MODELS ==========
@dataclass
class SkillGenerationResult:
    """Result of skill generation operation."""
    skill_name: str
    success: bool = False
    skill_path: Optional[Path] = None
    scripts_created: int = 0
    skill_md_created: bool = False
    workflow_created: bool = False
    timestamp: float = 0.0
    duration: float = 0.0
    error: Optional[str] = None
    exit_code: int = 0
    messages: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return asdict(self)

# ========== SECTION 6: HELPER FUNCTIONS ==========
def validate_skill_name(skill_name: str) -> bool:
    """Validate skill name format (adb-{name})."""
    if not skill_name:
        return False
    if not skill_name.startswith("adb-"):
        skill_name = f"adb-{skill_name}"
    # Only alphanumeric and hyphens
    return all(c.isalnum() or c == '-' for c in skill_name)

def slugify(text: str) -> str:
    """Convert text to slug format."""
    return text.lower().replace(" ", "-").replace("_", "-")

def read_template(template_name: str) -> Optional[str]:
    """Read script template content."""
    template_path = SKILL_TEMPLATES_DIR / template_name
    if template_path.exists():
        return template_path.read_text()
    return None

# ========== SECTION 7: SKILL METADATA GENERATION ==========
def generate_skill_metadata(skill_name: str, description: str, scripts: List[str],
                          dependencies: Optional[List[str]] = None,
                          category: str = "adb-app-automation",
                          version: str = "1.0.0") -> Dict[str, Any]:
    """Generate SKILL.md frontmatter metadata."""
    if not skill_name.startswith("adb-"):
        skill_name = f"adb-{skill_name}"

    return {
        "name": skill_name,
        "description": description,
        "version": version,
        "modularized": True,
        "scripts_enabled": True,
        "tier": 3,  # App-specific skills are Tier 3
        "category": category,
        "last_updated": time.strftime("%Y-%m-%d"),
        "compliance_score": 100,
        "dependencies": dependencies or [
            "adb-screen-detection",
            "adb-navigation-base",
            "adb-workflow-orchestrator",
        ],
        "auto_trigger_keywords": [
            slugify(skill_name.replace("adb-", "")),
            "automation",
            "testing",
            "bypass" if "karrot" in skill_name or "magisk" in skill_name else "check",
        ],
        "scripts": [
            {
                "name": script,
                "purpose": f"{script.replace('.py', '').replace('adb-', '').replace('-', ' ').title()} automation",
                "type": "python",
                "command": f"uv run .claude/skills/{skill_name}/scripts/{script}",
                "zero_context": True if "launch" in script else False,
                "version": version,
                "last_updated": time.strftime("%Y-%m-%d"),
            }
            for script in scripts
        ],
        "color": "cyan",
    }

# ========== SECTION 8: SKILL.MD GENERATION ==========
def generate_skill_md_content(metadata: Dict[str, Any]) -> str:
    """Generate complete SKILL.md file content."""
    lines = []

    # Frontmatter
    lines.append("---")
    for key, value in metadata.items():
        if key == "scripts":
            lines.append("scripts:")
            for script in value:
                lines.append(f"  - name: {script['name']}")
                lines.append(f"    purpose: {script['purpose']}")
                lines.append(f"    type: {script['type']}")
                lines.append(f"    command: {script['command']}")
                lines.append(f"    zero_context: {str(script['zero_context']).lower()}")
                lines.append(f"    version: {script['version']}")
                lines.append(f"    last_updated: {script['last_updated']}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")

    # Quick reference
    lines.append("---")
    lines.append("")
    lines.append("## Quick Reference (30 seconds)")
    lines.append("")
    lines.append(f"**{metadata['description']}**")
    lines.append("")
    lines.append("**What It Does**: Automates interactions and testing for the target app.")
    lines.append("")
    lines.append("**Core Capabilities**:")
    lines.append("- 🚀 **App Control**: Launch and interact with app")
    lines.append("- 🔍 **Detection**: Monitor app behavior")
    lines.append("- ✅ **Validation**: Verify functionality")
    lines.append("")
    lines.append("**When to Use**:")
    lines.append("- Testing app on various devices")
    lines.append("- Automating app interactions")
    lines.append("- Validating app functionality")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Scripts section
    lines.append("## Scripts")
    lines.append("")
    for script in metadata['scripts']:
        script_name = script['name']
        lines.append(f"### {script_name}")
        lines.append("")
        lines.append(f"{script['purpose']}.")
        lines.append("")
        lines.append("```bash")
        lines.append(f"# Basic usage")
        lines.append(f"uv run .claude/skills/{metadata['name']}/scripts/{script_name}")
        lines.append("")
        lines.append(f"# With device specification")
        lines.append(f"uv run .claude/skills/{metadata['name']}/scripts/{script_name} \\")
        lines.append(f"    --device 127.0.0.1:5555")
        lines.append("")
        lines.append(f"# JSON output")
        lines.append(f"uv run .claude/skills/{metadata['name']}/scripts/{script_name} --json")
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)

# ========== SECTION 9: SCRIPT GENERATION ==========
def generate_script_file(skill_name: str, script_name: str, template_type: str = "launcher") -> str:
    """Generate script file from template with substitutions."""
    # Get base template content
    template_content = read_template(SCRIPT_TEMPLATES.get(template_type, "adb_script_launcher_template.py"))

    if not template_content:
        # Fallback: generate minimal script structure
        return f"""#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
# ]
# ///

\"\"\"
{script_name.replace('.py', '').replace('-', ' ').title()} - Automated app interaction

Usage:
    uv run {script_name}
    uv run {script_name} --device 127.0.0.1:5555

Exit Codes:
    0 - Success
    1 - Warning
    2 - Error
    3 - Critical
\"\"\"

import click
import json
import sys

@click.command()
@click.option('--device', type=str, help='Target device ID')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def cli(device: str, output_json: bool) -> None:
    \"\"\"
    {skill_name.replace('adb-', '').upper()} App Automation
    \"\"\"
    click.echo("Script generated from template", err=True)
    sys.exit(0)

if __name__ == "__main__":
    cli()
"""

    # Perform substitutions
    content = template_content.replace("{{SKILL_NAME}}", skill_name)
    content = content.replace("{{SCRIPT_NAME}}", script_name.replace('.py', ''))
    content = content.replace("{{SCRIPT_DESCRIPTION}}", f"{script_name} - Automated interaction")

    return content

# ========== SECTION 10: SKILL CREATION ==========
def create_skill(skill_name: str, description: str, script_count: int = 1,
                 with_workflow: bool = False, category: str = "adb-app-automation",
                 project_root: Path = None, verbose: bool = False) -> SkillGenerationResult:
    """Create complete adb-* skill directory structure."""
    start_time = time.time()

    if not project_root:
        project_root = find_project_root()

    # Normalize skill name
    if not skill_name.startswith("adb-"):
        skill_name = f"adb-{skill_name}"

    result = SkillGenerationResult(skill_name=skill_name, timestamp=start_time)

    # Validate
    if not validate_skill_name(skill_name):
        result.error = f"Invalid skill name: {skill_name}"
        result.exit_code = 3
        result.duration = time.time() - start_time
        return result

    # Create skill directory
    skill_path = project_root / SKILLS_BASE_DIR / skill_name
    try:
        skill_path.mkdir(parents=True, exist_ok=True)
        result.skill_path = skill_path
        result.messages.append(f"✅ Created skill directory: {skill_path}")
    except Exception as e:
        result.error = f"Failed to create skill directory: {str(e)}"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    # Create subdirectories
    subdirs = ["scripts", "workflows", "templates", "analysis"]
    for subdir in subdirs:
        try:
            (skill_path / subdir).mkdir(exist_ok=True)
            result.messages.append(f"✅ Created {subdir}/ subdirectory")
        except Exception as e:
            result.messages.append(f"⚠️  Could not create {subdir}/: {str(e)}")

    # Generate SKILL.md
    script_names = [
        f"{skill_name}-launch.py" if i == 0 else f"{skill_name}-{['check', 'test', 'validate'][i-1]}.py"
        for i in range(script_count)
    ]

    metadata = generate_skill_metadata(
        skill_name, description, script_names,
        category=category
    )

    skill_md_content = generate_skill_md_content(metadata)

    try:
        (skill_path / "SKILL.md").write_text(skill_md_content)
        result.skill_md_created = True
        result.messages.append(f"✅ Created SKILL.md (frontmatter + {len(script_names)} script references)")
    except Exception as e:
        result.messages.append(f"⚠️  Failed to create SKILL.md: {str(e)}")

    # Generate script files
    script_types = ["launcher"] + ["checker" if i == 1 else "tester" for i in range(1, script_count)]

    for i, script_name in enumerate(script_names):
        try:
            script_content = generate_script_file(skill_name, script_name, script_types[i])
            script_path = skill_path / "scripts" / script_name
            script_path.write_text(script_content)
            script_path.chmod(0o755)
            result.scripts_created += 1
            result.messages.append(f"✅ Created script: {script_name}")
        except Exception as e:
            result.messages.append(f"⚠️  Failed to create {script_name}: {str(e)}")

    # Generate workflow example (optional)
    if with_workflow:
        try:
            workflow_content = f"""# {skill_name} workflow example
name: {skill_name}-example
description: Example workflow for {skill_name}

parameters:
  device: "127.0.0.1:5555"
  timeout: 30

phases:
  - id: phase-1
    name: "Launch and check"
    steps:
      - id: step-1
        action: {skill_name.replace('adb-', '')}-launch
        params:
          device: "{{{{ device }}}}"
          timeout: "{{{{ timeout }}}}"

recovery:
  - on_error: step-1
    action: retry
    then: continue
"""
            workflow_path = skill_path / "workflows" / f"{skill_name}-example.toon"
            workflow_path.write_text(workflow_content)
            result.workflow_created = True
            result.messages.append(f"✅ Created example workflow: {skill_name}-example.toon")
        except Exception as e:
            result.messages.append(f"⚠️  Failed to create workflow: {str(e)}")

    result.success = result.skill_md_created and result.scripts_created > 0
    result.exit_code = 0 if result.success else 1
    result.duration = time.time() - start_time

    return result

# ========== SECTION 11: FORMATTERS ==========
def format_human_output(result: SkillGenerationResult) -> str:
    """Format result for human-readable output."""
    lines = []

    if result.success:
        lines.append(f"✅ SKILL CREATED: {result.skill_name}")
    else:
        lines.append(f"⚠️  SKILL CREATION INCOMPLETE: {result.skill_name}")

    if result.skill_path:
        lines.append(f"  Location: {result.skill_path}")

    lines.append(f"\n  Generated Files:")
    lines.append(f"    Scripts: {result.scripts_created}")
    lines.append(f"    SKILL.md: {'✅ Yes' if result.skill_md_created else '❌ No'}")
    lines.append(f"    Workflow: {'✅ Yes' if result.workflow_created else '❌ No'}")

    if result.messages:
        lines.append(f"\n  Details:")
        for msg in result.messages:
            lines.append(f"    {msg}")

    lines.append(f"\n  Duration: {result.duration:.1f}s")

    if result.error:
        lines.append(f"  Error: {result.error}")

    return "\n".join(lines)

def format_json_output(result: SkillGenerationResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2, default=str)

# ========== SECTION 12: CLI INTERFACE ==========
@click.command()
@click.option('--skill-name', type=str, help='Skill name (with or without adb- prefix)')
@click.option('--description', type=str, help='Skill description')
@click.option('--script-count', type=int, default=1, help='Number of scripts to generate (default: 1)')
@click.option('--with-workflow', is_flag=True, help='Generate example workflow')
@click.option('--category', type=click.Choice(SKILL_CATEGORIES),
              default='adb-app-automation', help='Skill category')
@click.option('--list-templates', is_flag=True, help='List available templates')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--verbose', is_flag=True, help='Verbose output')
def cli(skill_name: Optional[str], description: Optional[str], script_count: int,
        with_workflow: bool, category: str, list_templates: bool,
        output_json: bool, verbose: bool) -> None:
    """
    Generate new adb-* skill from templates.

    Examples:
        # Minimal skill (1 launcher script)
        uv run adb-skill-generator.py \\
            --skill-name banking \\
            --description "Banking app automation"

        # Full skill with 3 scripts and workflow
        uv run adb-skill-generator.py \\
            --skill-name fitness \\
            --description "Fitness app testing" \\
            --script-count 3 \\
            --with-workflow

        # List available templates
        uv run adb-skill-generator.py --list-templates
    """
    if list_templates:
        click.echo("Available script templates:")
        for template_type, template_file in SCRIPT_TEMPLATES.items():
            click.echo(f"  - {template_type}: {template_file}")
        return

    if not skill_name or not description:
        click.echo("Error: --skill-name and --description are required", err=True)
        sys.exit(3)

    # Create skill
    result = create_skill(skill_name, description, script_count=script_count,
                         with_workflow=with_workflow, category=category,
                         verbose=verbose)

    # Output result
    if output_json:
        click.echo(format_json_output(result))
    else:
        click.echo(format_human_output(result))

    sys.exit(result.exit_code)

# ========== SECTION 13: ENTRY POINT ==========
if __name__ == "__main__":
    cli()
