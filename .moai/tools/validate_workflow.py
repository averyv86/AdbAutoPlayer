#!/usr/bin/env python3
# /// script
# dependencies = [
#     "click>=8.1.0",
# ]
# ///

"""
TOON Workflow Validation Tool - Comprehensive syntax and structure validator

Validates TOON workflow definitions for syntax correctness, structural integrity,
and agent/file references. Designed for integration with builder-workflow agent
and /moai:2-run command execution.

Usage:
    uv run validate_workflow.py workflow.toon
    uv run validate_workflow.py workflow.toon --json
    uv run validate_workflow.py workflow.toon --strict

Examples:
    # Full validation
    uv run validate_workflow.py .claude/workflows/SPEC-001/WORKFLOW.toon

    # Syntax only
    uv run validate_workflow.py workflow.toon --syntax-only

    # Structure validation only
    uv run validate_workflow.py workflow.toon --structure-only

    # JSON output
    uv run validate_workflow.py workflow.toon --output json

    # Strict mode (warnings = errors)
    uv run validate_workflow.py workflow.toon --strict

Exit Codes:
    0 - Valid (no errors)
    1 - Errors found (critical issues)
    2 - Warnings found (non-critical, non-strict mode only)

Requirements:
    - Python 3.11+
    - UV package manager
    - Access to project root

Notes:
    - Designed for UV execution only
    - Works from any directory (auto-detects project root)
    - MCP-wrappable for future server integration
"""

# ========== SECTION 2: IMPORTS ==========
import click
import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Literal

# ========== SECTION 3: CONSTANTS & CONFIGURATION ==========
EXIT_SUCCESS = 0
EXIT_ERRORS = 1
EXIT_WARNINGS = 2

# TOON syntax patterns
SECTION_PATTERN = re.compile(r'^(\w+)\[(\d+)\]\{([^}]+)\}:(.*)$')
REQUIRED_SECTIONS = ['wf', 'phases']

# ========== SECTION 4: PROJECT ROOT AUTO-DETECTION ==========
def find_project_root(start_path: Path) -> Path:
    """Auto-detect project root (.git, pyproject.toml, .moai)"""
    current = start_path.resolve()
    while current != current.parent:
        if any((current / marker).exists() for marker in
               [".git", "pyproject.toml", ".moai"]):
            return current
        current = current.parent
    raise RuntimeError("Project root not found (no .git, pyproject.toml, or .moai)")

PROJECT_ROOT = find_project_root(Path.cwd())

# ========== SECTION 5: DATA MODELS ==========
@dataclass
class ValidationResult:
    """Validation result with errors, warnings, and info"""
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        return asdict(self)

@dataclass
class TOONSection:
    """Parsed TOON section"""
    name: str
    count: int
    fields: list[str]
    rows: list[dict]

# ========== SECTION 6: CORE BUSINESS LOGIC ==========
class WorkflowValidator:
    """Main workflow validation logic"""

    def __init__(self, toon_content: str, agents_dir: Path):
        self.content = toon_content
        self.agents_dir = agents_dir
        self.sections: dict[str, TOONSection] = {}

    def validate_syntax(self) -> ValidationResult:
        """Validate TOON syntax (array counts, field counts, delimiters)"""
        result = ValidationResult(valid=True)

        lines = self.content.splitlines()
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            line_num = i + 1

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                i += 1
                continue

            # Check if this is a section header
            match = SECTION_PATTERN.match(line)
            if not match:
                # If not a header and not empty, it's an error
                result.errors.append(f"Line {line_num}: Invalid TOON syntax: {line}")
                i += 1
                continue

            section_name, count_str, fields_str, data = match.groups()
            expected_count = int(count_str)
            fields = [f.strip() for f in fields_str.split(',')]

            # Parse data rows
            rows = []

            # If data on same line as header
            if data.strip():
                values = self._parse_row(data, len(fields))
                if len(values) != len(fields):
                    result.errors.append(
                        f"Line {line_num}: Field count mismatch in '{section_name}'. "
                        f"Expected {len(fields)}, got {len(values)}"
                    )
                else:
                    rows.append(dict(zip(fields, values)))

            # Collect continuation lines (data rows on following lines)
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                next_line_num = i + 1

                # Stop if empty, comment, or new section
                if not next_line or next_line.startswith('#'):
                    i += 1
                    continue

                if SECTION_PATTERN.match(next_line):
                    break

                # Parse this data row
                values = self._parse_row(next_line, len(fields))
                if len(values) != len(fields):
                    result.errors.append(
                        f"Line {next_line_num}: Field count mismatch in '{section_name}'. "
                        f"Expected {len(fields)}, got {len(values)}"
                    )
                else:
                    rows.append(dict(zip(fields, values)))

                i += 1

            # Validate array count
            if len(rows) != expected_count:
                result.errors.append(
                    f"Section '{section_name}': Array count mismatch. "
                    f"Expected [{expected_count}], got {len(rows)} rows"
                )

            self.sections[section_name] = TOONSection(
                name=section_name,
                count=expected_count,
                fields=fields,
                rows=rows
            )

        # Check required sections
        for required in REQUIRED_SECTIONS:
            if required not in self.sections:
                result.errors.append(f"Missing required section: @{required}")

        result.valid = len(result.errors) == 0
        if result.valid:
            result.info.append("TOON syntax valid")

        return result

    def validate_structure(self) -> ValidationResult:
        """Validate workflow structure (phase deps, agent refs, file patterns)"""
        result = ValidationResult(valid=True)

        if 'phases' not in self.sections:
            result.errors.append("Cannot validate structure: missing @phases section")
            result.valid = False
            return result

        phases = self.sections['phases'].rows
        phase_ids = set()
        agent_names = set()

        # Validate phases
        for phase in phases:
            phase_id = phase.get('id', '')

            # Check phase ID is unique
            if phase_id in phase_ids:
                result.errors.append(f"Duplicate phase ID: {phase_id}")
            phase_ids.add(phase_id)

            # Extract agent names (handle pipe-separated agents)
            agents_field = phase.get('agent') or phase.get('agents', '')
            agents = [a.strip().strip('"') for a in agents_field.split('|')]
            agent_names.update(agents)

            # Validate dependencies reference valid phase IDs
            deps = phase.get('deps', '[]')
            if deps and deps != '[]':
                dep_ids = self._parse_array(deps)
                for dep_id in dep_ids:
                    if dep_id not in phase_ids and dep_id < phase_id:
                        result.warnings.append(
                            f"Phase {phase_id} depends on {dep_id}, but it appears later"
                        )

        # Check for circular dependencies
        cycles = self._check_dag_cycles(phases)
        if cycles:
            result.errors.append(f"Circular dependencies detected: {', '.join(cycles)}")

        # Validate agent existence
        missing_agents = self._validate_agent_existence(list(agent_names))
        if missing_agents:
            for agent in missing_agents:
                result.warnings.append(f"Agent '{agent}' not found in {self.agents_dir.relative_to(PROJECT_ROOT)}")

        # Validate file patterns if present
        if 'files' in self.sections:
            pattern_errors = self._check_file_patterns(self.sections['files'].rows)
            result.warnings.extend(pattern_errors)

        # Add info
        result.info.append(f"Workflow: {self.sections.get('wf', TOONSection('wf', 0, [], [])).rows[0].get('id', 'UNKNOWN') if 'wf' in self.sections and self.sections['wf'].rows else 'UNKNOWN'}")
        result.info.append(f"Phases: {len(phases)}")
        result.info.append(f"Agents: {len(agent_names)} unique")

        result.valid = len(result.errors) == 0
        return result

    def _parse_row(self, row: str, expected_fields: int) -> list[str]:
        """Parse TOON data row, handling quoted pipe-separated values"""
        values = []
        current = []
        in_quotes = False

        for char in row:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                values.append(''.join(current).strip())
                current = []
                continue
            current.append(char)

        if current:
            values.append(''.join(current).strip())

        return values

    def _parse_array(self, array_str: str) -> list[str]:
        """Parse array notation [1,2,3] into list"""
        array_str = array_str.strip('[]').strip()
        if not array_str:
            return []
        return [v.strip() for v in array_str.split(',')]

    def _check_dag_cycles(self, phases: list[dict]) -> list[str]:
        """Detect circular dependencies using DFS"""
        graph = {}
        for phase in phases:
            phase_id = phase.get('id', '')
            deps = self._parse_array(phase.get('deps', '[]'))
            graph[phase_id] = deps

        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: list[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, path.copy()):
                        return True
                elif neighbor in rec_stack:
                    cycle_path = path[path.index(neighbor):] + [neighbor]
                    cycles.append(' -> '.join(map(str, cycle_path)))
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    def _validate_agent_existence(self, agents: list[str]) -> list[str]:
        """Check all agents exist in .claude/agents/"""
        missing = []
        for agent in agents:
            agent_file = self.agents_dir / f"{agent}.md"
            if not agent_file.exists():
                # Also check moai/ subdirectory
                moai_agent = self.agents_dir / "moai" / f"{agent}.md"
                if not moai_agent.exists():
                    missing.append(agent)
        return missing

    def _check_file_patterns(self, files: list[dict]) -> list[str]:
        """Validate file path patterns (glob syntax, conflicts)"""
        warnings = []
        patterns = {}

        for file_entry in files:
            path = file_entry.get('path', '')
            agent = file_entry.get('agent', '')

            # Check for absolute paths (should be relative)
            if path.startswith('/'):
                warnings.append(f"Absolute path detected: {path} (should be relative)")

            # Check for conflicting patterns
            if path in patterns and patterns[path] != agent:
                warnings.append(
                    f"Conflicting agents for {path}: {patterns[path]} vs {agent}"
                )
            patterns[path] = agent

        return warnings

# ========== SECTION 7: OUTPUT FORMATTERS ==========
def format_json_output(result: ValidationResult) -> str:
    """Format result as JSON"""
    return json.dumps(result.to_dict(), indent=2)

def format_human_readable(result: ValidationResult) -> str:
    """Format result as human-readable text"""
    lines = []

    # Errors
    if result.errors:
        lines.append(f"{'X'} Errors ({len(result.errors)}):")
        for error in result.errors:
            lines.append(f"  - {error}")
        lines.append("")

    # Warnings
    if result.warnings:
        lines.append(f"! Warnings ({len(result.warnings)}):")
        for warning in result.warnings:
            lines.append(f"  - {warning}")
        lines.append("")

    # Info
    if result.info:
        lines.append("Information:")
        for info in result.info:
            lines.append(f"  {info}")
        lines.append("")

    # Summary
    if result.valid:
        if result.warnings:
            lines.append(f"Summary: Valid with {len(result.warnings)} warning(s)")
        else:
            lines.append("Summary: Valid")
    else:
        lines.append(f"Summary: Invalid ({len(result.errors)} error(s))")

    return "\n".join(lines)

# ========== SECTION 8: CLI INTERFACE ==========
@click.command()
@click.argument('workflow_file', type=click.Path(exists=True))
@click.option('--json', 'json_mode', is_flag=True, help='Output in JSON format')
@click.option('--syntax-only', is_flag=True, help='Validate syntax only')
@click.option('--structure-only', is_flag=True, help='Validate structure only')
@click.option('--strict', is_flag=True, help='Warnings treated as errors')
def main(workflow_file: str, json_mode: bool, syntax_only: bool, structure_only: bool, strict: bool):
    """
    Validate TOON workflow definitions for syntax and structure correctness.

    Validates workflow files for:
    - TOON syntax (array counts, field counts, delimiters)
    - Phase dependencies and DAG cycles
    - Agent references
    - File pattern conflicts

    Examples:
        uv run validate_workflow.py workflow.toon
        uv run validate_workflow.py workflow.toon --json
        uv run validate_workflow.py workflow.toon --strict
    """
    try:
        # Read workflow file
        workflow_path = Path(workflow_file).resolve()
        content = workflow_path.read_text()

        # Find agents directory
        agents_dir = PROJECT_ROOT / ".claude" / "agents"
        if not agents_dir.exists():
            if json_mode:
                error_result = ValidationResult(valid=False, errors=[f"Agents directory not found: {agents_dir}"])
                print(format_json_output(error_result))
            else:
                print(f"X Error: Agents directory not found: {agents_dir}", file=sys.stderr)
            sys.exit(EXIT_ERRORS)

        # Create validator
        validator = WorkflowValidator(content, agents_dir)

        # Run validations
        combined_result = ValidationResult(valid=True)

        if not structure_only:
            syntax_result = validator.validate_syntax()
            combined_result.errors.extend(syntax_result.errors)
            combined_result.warnings.extend(syntax_result.warnings)
            combined_result.info.extend(syntax_result.info)

        if not syntax_only and not combined_result.errors:
            structure_result = validator.validate_structure()
            combined_result.errors.extend(structure_result.errors)
            combined_result.warnings.extend(structure_result.warnings)
            combined_result.info.extend(structure_result.info)

        # Determine validity
        combined_result.valid = len(combined_result.errors) == 0
        if strict and combined_result.warnings:
            combined_result.valid = False

        # Output result
        if json_mode:
            print(format_json_output(combined_result))
        else:
            print(format_human_readable(combined_result))

        # Exit with appropriate code
        if not combined_result.valid:
            sys.exit(EXIT_ERRORS)
        elif combined_result.warnings:
            sys.exit(EXIT_WARNINGS)
        else:
            sys.exit(EXIT_SUCCESS)

    except Exception as e:
        if json_mode:
            error_result = ValidationResult(valid=False, errors=[f"Unexpected error: {str(e)}"])
            print(format_json_output(error_result))
        else:
            print(f"X Unexpected error: {e}", file=sys.stderr)
        sys.exit(EXIT_ERRORS)

# ========== SECTION 9: ENTRY POINT ==========
if __name__ == "__main__":
    main()
