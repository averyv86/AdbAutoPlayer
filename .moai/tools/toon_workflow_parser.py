#!/usr/bin/env python3
# /// script
# dependencies = [
#     "click>=8.1.7",
#     "pyyaml>=6.0",
# ]
# ///

"""
TOON Workflow Parser

Parse compressed TOON (Tabular Object Oriented Notation) workflow definitions
into Python dataclasses for execution engine integration.

Usage:
    uv run toon_workflow_parser.py parse workflow.toon
    uv run toon_workflow_parser.py parse workflow.toon --output json
    uv run toon_workflow_parser.py validate workflow.toon
    uv run toon_workflow_parser.py check-agents workflow.toon
    uv run toon_workflow_parser.py deps workflow.toon

Examples:
    # Parse and display workflow
    uv run toon_workflow_parser.py parse complex-feature.toon

    # Validate syntax only
    uv run toon_workflow_parser.py validate simple-implementation.toon

    # Output as JSON
    uv run toon_workflow_parser.py parse workflow.toon --output json

    # Check agent references exist
    uv run toon_workflow_parser.py check-agents workflow.toon

    # Resolve dependency order
    uv run toon_workflow_parser.py deps workflow.toon --output json

Exit Codes:
    0 - Success
    1 - Warning (partial success)
    2 - Error (operation failed)
    3 - Critical (validation failed)

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
import yaml
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Literal, Optional
from collections import deque

# ========== SECTION 3: CONSTANTS & CONFIGURATION ==========
TOON_SECTION_PATTERN = r'@(\w+)\[(\d+)\]\{([^}]+)\}:'
WORKFLOW_DIR = ".moai/workflows"
TEMPLATES_DIR = f"{WORKFLOW_DIR}/templates"
AGENTS_DIR = ".claude/agents/moai"

# ========== SECTION 4: PROJECT ROOT AUTO-DETECTION ==========
def find_project_root(start_path: Path) -> Path:
    """
    Auto-detect project root by searching for markers.

    Args:
        start_path: Starting directory for search

    Returns:
        Path to project root

    Raises:
        RuntimeError: If project root not found
    """
    current = start_path.resolve()
    while current != current.parent:
        markers = [".git", "pyproject.toml", ".moai", "CLAUDE.md"]
        if any((current / marker).exists() for marker in markers):
            return current
        current = current.parent
    raise RuntimeError("Project root not found (no .git, pyproject.toml, or .moai)")

PROJECT_ROOT = find_project_root(Path.cwd())

# ========== SECTION 5: DATA MODELS ==========
@dataclass
class WorkflowMetadata:
    """Workflow metadata from @metadata section"""
    template_id: str
    name: str
    complexity: str
    file_count: str
    agent_count: str

@dataclass
class Phase:
    """Phase definition from @phases section"""
    id: int
    agents: list[str]  # Can be single or pipe-separated ("backend|frontend")
    mode: Literal["sequential", "parallel"]
    dependencies: list[int]
    max_parallel: int = 1
    description: str = ""

@dataclass
class FileAssignment:
    """File assignment from @example_files or @file_patterns section"""
    path: str
    agent: str
    operation: Literal["create", "modify", "delete", "update"] = "create"
    priority: str = "medium"

@dataclass
class ExecutionStrategy:
    """Execution strategy from @exec_strategy section"""
    mode: str  # sequential, mixed, parallel, hybrid
    parallel_default: int = 1
    parallel_max: int = 1  # Alias for max_concurrent
    dynamic_adjust: bool = False
    max_concurrent: int = 1
    resource_monitoring: bool = False

    def __post_init__(self):
        """Normalize parallel_max and max_concurrent"""
        if not hasattr(self, 'max_concurrent') or self.max_concurrent == 1:
            self.max_concurrent = self.parallel_max

class Agent:
    """Agent definition from @agent_pool section"""

    def __init__(self, **kwargs):
        """Flexible initialization supporting various field combinations"""
        self.agent = kwargs.get('agent', '')
        self.domain = kwargs.get('domain', '')
        self.priority = kwargs.get('priority', 'medium')
        self.parallel_group = kwargs.get('parallel_group', 0)
        self.capabilities = kwargs.get('capabilities', '')
        # Handle both 'workload' (integer) and other fields
        self.workload = kwargs.get('workload', 0)
        if isinstance(self.workload, str):
            # If workload is not an integer, set to 0
            self.workload = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'agent': self.agent,
            'domain': self.domain,
            'priority': self.priority,
            'parallel_group': self.parallel_group,
            'capabilities': self.capabilities,
            'workload': self.workload
        }

@dataclass
class QualityGate:
    """Quality gate from @quality_gates section"""
    gate_id: int
    validator: str
    threshold: int
    required: bool

@dataclass
class FilePattern:
    """File pattern matching rule from @file_patterns section"""
    pattern: str
    agent: str
    priority: str

@dataclass
class ResourceLimits:
    """Resource limits from @resource_limits section"""
    cpu_threshold: int
    memory_threshold: int
    token_threshold: int
    disk_io_threshold: int = 0

@dataclass
class WorkflowDefinition:
    """Complete workflow definition parsed from TOON file"""
    metadata: WorkflowMetadata
    phases: list[Phase] = field(default_factory=list)
    files: list[FileAssignment] = field(default_factory=list)
    exec_strategy: Optional[ExecutionStrategy] = None
    agent_pool: list[Agent] = field(default_factory=list)
    quality_gates: list[QualityGate] = field(default_factory=list)
    file_patterns: list[FilePattern] = field(default_factory=list)
    resource_limits: Optional[ResourceLimits] = None

# ========== SECTION 6: CORE BUSINESS LOGIC ==========

class TOONParseError(Exception):
    """Custom exception for TOON parsing errors"""
    pass

def parse_value(value: str):
    """
    Parse a single value with type inference.

    Args:
        value: String value to parse

    Returns:
        Parsed value with appropriate type (int, bool, list, str)
    """
    value = value.strip()

    # Empty array
    if value == "[]":
        return []

    # Array with items
    if value.startswith("[") and value.endswith("]"):
        items = value[1:-1].split(",")
        return [int(x.strip()) if x.strip().isdigit() else x.strip() for x in items if x.strip()]

    # Boolean
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    # Integer
    if value.isdigit():
        return int(value)

    # Quoted string - remove quotes
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]

    # Pipe-separated multi-value (for agents field)
    if "|" in value:
        return [x.strip() for x in value.split("|")]

    # Plain string
    return value

def parse_tabular_section(section_name: str, header: str, lines: list[str]) -> list[dict]:
    """
    Parse tabular TOON format: items[N]{field1,field2}:val1,val2

    Args:
        section_name: Name of the section (e.g., "phases")
        header: Field names from {field1,field2,...}
        lines: Data lines (comma-separated values)

    Returns:
        List of dictionaries with parsed data

    Raises:
        TOONParseError: If field count mismatch or invalid format

    Example:
        >>> parse_tabular_section("phases", "id,agent,mode,deps",
        ...                       ["1,manager-strategy,sequential,[]"])
        [{"id": 1, "agent": "manager-strategy", "mode": "sequential", "deps": []}]
    """
    fields = [f.strip() for f in header.split(",")]
    results = []

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Split by comma, but respect quoted strings, brackets, and braces
        values = []
        current = ""
        in_quotes = False
        in_square_brackets = False
        in_curly_braces = False

        for char in line:
            if char == '"':
                in_quotes = not in_quotes
                current += char
            elif char == '[':
                in_square_brackets = True
                current += char
            elif char == ']':
                in_square_brackets = False
                current += char
            elif char == '{':
                in_curly_braces = True
                current += char
            elif char == '}':
                in_curly_braces = False
                current += char
            elif char == ',' and not in_quotes and not in_square_brackets and not in_curly_braces:
                values.append(current.strip())
                current = ""
            else:
                current += char

        if current:
            values.append(current.strip())

        if len(values) != len(fields):
            raise TOONParseError(
                f"Field count mismatch in @{section_name} line {line_num}: "
                f"expected {len(fields)} fields ({', '.join(fields)}), "
                f"got {len(values)} values"
            )

        row = {field: parse_value(value) for field, value in zip(fields, values)}
        results.append(row)

    return results

def parse_workflow(toon_content: str) -> WorkflowDefinition:
    """
    Parse TOON workflow file into structured WorkflowDefinition.

    Parse sections:
    - @metadata[N]{fields}:values
    - @phases[N]{fields}:values
    - @example_files[N]{fields}:values
    - @exec_strategy[N]{fields}:values
    - @agent_pool[N]{fields}:values
    - @quality_gates[N]{fields}:values
    - @file_patterns[N]{fields}:values
    - @resource_limits[N]{fields}:values

    Args:
        toon_content: Complete TOON file content as string

    Returns:
        WorkflowDefinition with all parsed sections

    Raises:
        TOONParseError: If required sections missing or invalid format
    """
    lines = toon_content.split("\n")
    sections = {}
    current_section = None
    current_header = None
    current_lines = []

    # Extract all sections
    for line in lines:
        # Check for section header
        match = re.match(TOON_SECTION_PATTERN, line)
        if match:
            # Save previous section
            if current_section:
                sections[current_section] = {
                    "header": current_header,
                    "lines": current_lines
                }

            # Start new section
            current_section = match.group(1)
            current_header = match.group(3)
            current_lines = []
        elif current_section and line.strip() and not line.strip().startswith("#"):
            current_lines.append(line)

    # Save last section
    if current_section:
        sections[current_section] = {
            "header": current_header,
            "lines": current_lines
        }

    # Validate required sections
    if "metadata" not in sections:
        raise TOONParseError("Missing required @metadata section")

    # Parse metadata (required)
    metadata_data = parse_tabular_section("metadata",
                                          sections["metadata"]["header"],
                                          sections["metadata"]["lines"])
    if not metadata_data:
        raise TOONParseError("Empty @metadata section")

    # Try to create WorkflowMetadata, provide helpful error if schema doesn't match
    try:
        metadata = WorkflowMetadata(**metadata_data[0])
    except TypeError as e:
        raise TOONParseError(
            f"Invalid workflow metadata schema: {e}\n"
            f"Expected fields: template_id, name, complexity, file_count, agent_count\n"
            f"This parser is designed for workflow template files (.toon), not assignment rules."
        )

    # Parse phases (optional)
    phases = []
    if "phases" in sections:
        phase_data = parse_tabular_section("phases",
                                           sections["phases"]["header"],
                                           sections["phases"]["lines"])
        for p in phase_data:
            # Handle both 'agent' and 'agents' field names
            agent_field = p.get("agents") or p.get("agent")
            if isinstance(agent_field, str):
                agent_field = [agent_field]

            phases.append(Phase(
                id=p["id"],
                agents=agent_field,
                mode=p.get("mode", "sequential"),
                dependencies=p.get("deps", []),
                max_parallel=p.get("max_parallel", 1),
                description=p.get("description", "")
            ))

    # Parse example_files (optional)
    files = []
    if "example_files" in sections:
        file_data = parse_tabular_section("example_files",
                                          sections["example_files"]["header"],
                                          sections["example_files"]["lines"])
        files = [FileAssignment(**f) for f in file_data]

    # Parse file_patterns (optional)
    file_patterns = []
    if "file_patterns" in sections:
        pattern_data = parse_tabular_section("file_patterns",
                                             sections["file_patterns"]["header"],
                                             sections["file_patterns"]["lines"])
        file_patterns = [FilePattern(**p) for p in pattern_data]

    # Parse exec_strategy (optional)
    exec_strategy = None
    if "exec_strategy" in sections:
        strategy_data = parse_tabular_section("exec_strategy",
                                              sections["exec_strategy"]["header"],
                                              sections["exec_strategy"]["lines"])
        if strategy_data:
            exec_strategy = ExecutionStrategy(**strategy_data[0])

    # Parse agent_pool (optional)
    agent_pool = []
    if "agent_pool" in sections:
        agent_data = parse_tabular_section("agent_pool",
                                           sections["agent_pool"]["header"],
                                           sections["agent_pool"]["lines"])
        for a in agent_data:
            # Create Agent with flexible field handling
            try:
                agent_pool.append(Agent(**a))
            except TypeError:
                # Fallback: create with minimal fields
                agent_pool.append(Agent(
                    agent=a.get('agent', ''),
                    domain=a.get('domain', ''),
                    priority=a.get('priority', 'medium')
                ))

    # Parse quality_gates (optional)
    quality_gates = []
    if "quality_gates" in sections:
        gate_data = parse_tabular_section("quality_gates",
                                          sections["quality_gates"]["header"],
                                          sections["quality_gates"]["lines"])
        quality_gates = [QualityGate(**g) for g in gate_data]

    # Parse resource_limits (optional)
    resource_limits = None
    if "resource_limits" in sections:
        limits_data = parse_tabular_section("resource_limits",
                                            sections["resource_limits"]["header"],
                                            sections["resource_limits"]["lines"])
        if limits_data:
            resource_limits = ResourceLimits(**limits_data[0])

    return WorkflowDefinition(
        metadata=metadata,
        phases=phases,
        files=files,
        exec_strategy=exec_strategy,
        agent_pool=agent_pool,
        quality_gates=quality_gates,
        file_patterns=file_patterns,
        resource_limits=resource_limits
    )

def resolve_dependencies(phases: list[Phase]) -> list[list[int]]:
    """
    Build dependency graph and compute execution order using topological sort.

    Args:
        phases: List of Phase objects with dependencies

    Returns:
        List of execution levels (each level can run in parallel)

    Raises:
        TOONParseError: If circular dependencies detected

    Example:
        >>> phases = [
        ...     Phase(id=1, agents=["a"], mode="seq", dependencies=[]),
        ...     Phase(id=2, agents=["b"], mode="par", dependencies=[1]),
        ...     Phase(id=3, agents=["c"], mode="par", dependencies=[1])
        ... ]
        >>> resolve_dependencies(phases)
        [[1], [2, 3]]
    """
    if not phases:
        return []

    # Build adjacency list and in-degree count
    graph = {p.id: [] for p in phases}
    in_degree = {p.id: 0 for p in phases}

    for phase in phases:
        for dep in phase.dependencies:
            if dep not in graph:
                raise TOONParseError(
                    f"Phase {phase.id} depends on non-existent phase {dep}"
                )
            graph[dep].append(phase.id)
            in_degree[phase.id] += 1

    # Kahn's algorithm for topological sort
    queue = deque([pid for pid, deg in in_degree.items() if deg == 0])
    execution_order = []
    processed = 0

    while queue:
        # All nodes at current level (same depth) can run in parallel
        level = list(queue)
        execution_order.append(level)
        queue.clear()

        for node in level:
            processed += 1
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

    # Check for circular dependencies
    if processed != len(phases):
        raise TOONParseError(
            f"Circular dependency detected: processed {processed}/{len(phases)} phases"
        )

    return execution_order

def validate_agent_references(workflow: WorkflowDefinition) -> list[str]:
    """
    Check all referenced agents exist in .claude/agents/moai/

    Args:
        workflow: Complete workflow definition

    Returns:
        List of missing agent names (empty if all valid)
    """
    agents_dir = PROJECT_ROOT / AGENTS_DIR

    if not agents_dir.exists():
        return ["WARNING: Agents directory not found"]

    # Collect all referenced agents
    referenced = set()

    for phase in workflow.phases:
        for agent in phase.agents:
            # Handle pipe-separated agents (e.g., "backend|frontend|database")
            if isinstance(agent, str) and "|" in agent:
                for sub_agent in agent.split("|"):
                    referenced.add(sub_agent.strip())
            else:
                referenced.add(agent)

    for agent in workflow.agent_pool:
        referenced.add(agent.agent)

    for file_pattern in workflow.file_patterns:
        referenced.add(file_pattern.agent)

    for file in workflow.files:
        referenced.add(file.agent)

    # Check existence
    missing = []
    for agent_name in referenced:
        agent_file = agents_dir / f"{agent_name}.md"
        if not agent_file.exists():
            missing.append(agent_name)

    return missing

# ========== SECTION 7: OUTPUT FORMATTERS ==========

def format_metadata(metadata: WorkflowMetadata) -> str:
    """Format metadata for human-readable output"""
    return f"""Workflow Metadata:
  Template ID: {metadata.template_id}
  Name: {metadata.name}
  Complexity: {metadata.complexity}
  File Count: {metadata.file_count}
  Agent Count: {metadata.agent_count}"""

def format_phases(phases: list[Phase]) -> str:
    """Format phases for human-readable output"""
    if not phases:
        return "Phases: None"

    lines = ["Phases:"]
    for phase in phases:
        agents_str = ", ".join(phase.agents) if isinstance(phase.agents, list) else phase.agents
        deps_str = str(phase.dependencies) if phase.dependencies else "None"
        lines.append(
            f"  Phase {phase.id}: {agents_str} ({phase.mode}, deps={deps_str}, "
            f"max_parallel={phase.max_parallel})"
        )
        if phase.description:
            lines.append(f"    → {phase.description}")

    return "\n".join(lines)

def format_execution_order(execution_order: list[list[int]]) -> str:
    """Format dependency resolution for human-readable output"""
    if not execution_order:
        return "Execution Order: Sequential (no phases)"

    lines = ["Execution Order (Dependency Resolution):"]
    for level_idx, level in enumerate(execution_order, 1):
        phase_list = ", ".join(f"Phase {p}" for p in level)
        parallelism = "parallel" if len(level) > 1 else "sequential"
        lines.append(f"  Level {level_idx} ({parallelism}): {phase_list}")

    return "\n".join(lines)

def format_agent_pool(agents: list[Agent]) -> str:
    """Format agent pool for human-readable output"""
    if not agents:
        return "Agent Pool: None"

    lines = ["Agent Pool:"]
    for agent in agents:
        caps = f", capabilities={agent.capabilities}" if agent.capabilities else ""
        workload = f", workload={agent.workload}%" if agent.workload else ""
        lines.append(
            f"  {agent.agent} ({agent.domain}, priority={agent.priority}, "
            f"group={agent.parallel_group}{caps}{workload})"
        )

    return "\n".join(lines)

def format_quality_gates(gates: list[QualityGate]) -> str:
    """Format quality gates for human-readable output"""
    if not gates:
        return "Quality Gates: None"

    lines = ["Quality Gates:"]
    for gate in gates:
        required = "REQUIRED" if gate.required else "optional"
        lines.append(
            f"  Gate {gate.gate_id}: {gate.validator} "
            f"(threshold={gate.threshold}%, {required})"
        )

    return "\n".join(lines)

def format_workflow(workflow: WorkflowDefinition, include_deps: bool = False) -> str:
    """Format complete workflow for human-readable output"""
    parts = [
        format_metadata(workflow.metadata),
        "",
        format_phases(workflow.phases),
        "",
        format_agent_pool(workflow.agent_pool),
        "",
        format_quality_gates(workflow.quality_gates)
    ]

    if workflow.exec_strategy:
        parts.extend([
            "",
            f"Execution Strategy: {workflow.exec_strategy.mode} "
            f"(parallel_default={workflow.exec_strategy.parallel_default}, "
            f"dynamic={workflow.exec_strategy.dynamic_adjust})"
        ])

    if workflow.files:
        parts.extend(["", f"Example Files: {len(workflow.files)} files"])

    if workflow.file_patterns:
        parts.extend(["", f"File Patterns: {len(workflow.file_patterns)} patterns"])

    if workflow.resource_limits:
        parts.extend([
            "",
            f"Resource Limits: CPU={workflow.resource_limits.cpu_threshold}%, "
            f"Memory={workflow.resource_limits.memory_threshold}%, "
            f"Tokens={workflow.resource_limits.token_threshold}"
        ])

    if include_deps and workflow.phases:
        execution_order = resolve_dependencies(workflow.phases)
        parts.extend(["", format_execution_order(execution_order)])

    return "\n".join(parts)

def workflow_to_dict(workflow: WorkflowDefinition) -> dict:
    """Convert workflow to dictionary for JSON/YAML serialization"""
    result = asdict(workflow)
    # Convert Agent objects to dicts
    result['agent_pool'] = [agent.to_dict() for agent in workflow.agent_pool]
    return result

# ========== SECTION 8: CLI INTERFACE ==========

@click.group()
def cli():
    """TOON Workflow Parser - Parse compressed workflow definitions"""
    pass

@cli.command()
@click.argument('workflow_file', type=click.Path(exists=True))
@click.option('--output', type=click.Choice(['human', 'json', 'yaml']),
              default='human', help='Output format')
@click.option('--show-deps', is_flag=True,
              help='Show dependency resolution')
def parse(workflow_file: str, output: str, show_deps: bool):
    """
    Parse TOON workflow file and display structure.

    Examples:
        uv run toon_workflow_parser.py parse complex-feature.toon
        uv run toon_workflow_parser.py parse workflow.toon --output json
        uv run toon_workflow_parser.py parse workflow.toon --show-deps
    """
    try:
        with open(workflow_file, 'r') as f:
            content = f.read()

        workflow = parse_workflow(content)

        if output == 'json':
            print(json.dumps(workflow_to_dict(workflow), indent=2))
        elif output == 'yaml':
            print(yaml.dump(workflow_to_dict(workflow),
                           default_flow_style=False, sort_keys=False))
        else:
            print(format_workflow(workflow, include_deps=show_deps))

        sys.exit(0)

    except TOONParseError as e:
        if output == 'json':
            print(json.dumps({"error": str(e), "type": "TOONParseError"}))
        else:
            print(f"❌ Parse Error: {e}", file=sys.stderr)
        sys.exit(2)

    except Exception as e:
        if output == 'json':
            print(json.dumps({"error": str(e), "type": type(e).__name__}))
        else:
            print(f"❌ Unexpected Error: {e}", file=sys.stderr)
        sys.exit(3)

@cli.command()
@click.argument('workflow_file', type=click.Path(exists=True))
def validate(workflow_file: str):
    """
    Validate TOON syntax without full parsing.

    Example:
        uv run toon_workflow_parser.py validate simple-implementation.toon
    """
    try:
        with open(workflow_file, 'r') as f:
            content = f.read()

        workflow = parse_workflow(content)

        print(f"✓ Syntax Valid: {workflow.metadata.name}")
        print(f"  Sections: metadata, {len(workflow.phases)} phases, "
              f"{len(workflow.agent_pool)} agents")

        sys.exit(0)

    except TOONParseError as e:
        print(f"❌ Validation Failed: {e}", file=sys.stderr)
        sys.exit(2)

    except Exception as e:
        print(f"❌ Unexpected Error: {e}", file=sys.stderr)
        sys.exit(3)

@cli.command()
@click.argument('workflow_file', type=click.Path(exists=True))
@click.option('--output', type=click.Choice(['human', 'json']),
              default='human', help='Output format')
def check_agents(workflow_file: str, output: str):
    """
    Check all referenced agents exist in .claude/agents/moai/

    Example:
        uv run toon_workflow_parser.py check-agents workflow.toon
    """
    try:
        with open(workflow_file, 'r') as f:
            content = f.read()

        workflow = parse_workflow(content)
        missing = validate_agent_references(workflow)

        if output == 'json':
            result = {
                "workflow": workflow.metadata.name,
                "missing_agents": missing,
                "valid": len(missing) == 0
            }
            print(json.dumps(result, indent=2))
        else:
            if not missing:
                print(f"✓ All agents valid for {workflow.metadata.name}")
            else:
                print(f"❌ Missing agents ({len(missing)}):", file=sys.stderr)
                for agent in missing:
                    print(f"  - {agent}", file=sys.stderr)

        sys.exit(0 if not missing else 1)

    except Exception as e:
        if output == 'json':
            print(json.dumps({"error": str(e)}))
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(2)

@cli.command()
@click.argument('workflow_file', type=click.Path(exists=True))
@click.option('--output', type=click.Choice(['human', 'json']),
              default='human', help='Output format')
def deps(workflow_file: str, output: str):
    """
    Resolve phase dependency order using topological sort.

    Example:
        uv run toon_workflow_parser.py deps workflow.toon --output json
    """
    try:
        with open(workflow_file, 'r') as f:
            content = f.read()

        workflow = parse_workflow(content)
        execution_order = resolve_dependencies(workflow.phases)

        if output == 'json':
            result = {
                "workflow": workflow.metadata.name,
                "execution_order": execution_order,
                "total_levels": len(execution_order)
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"Workflow: {workflow.metadata.name}")
            print(format_execution_order(execution_order))

        sys.exit(0)

    except TOONParseError as e:
        if output == 'json':
            print(json.dumps({"error": str(e), "type": "TOONParseError"}))
        else:
            print(f"❌ Dependency Error: {e}", file=sys.stderr)
        sys.exit(2)

    except Exception as e:
        if output == 'json':
            print(json.dumps({"error": str(e)}))
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(3)

# ========== SECTION 9: ENTRY POINT ==========
if __name__ == "__main__":
    cli()
