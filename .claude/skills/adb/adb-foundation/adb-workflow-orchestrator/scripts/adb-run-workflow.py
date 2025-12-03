#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pyyaml>=6.0",
#     "click>=8.1.7",
#     "pillow>=10.0",
# ]
# ///

"""
ADB Workflow Orchestrator: TOON Workflow Execution Engine

Orchestrates TOON (Token-Optimized Object Notation) workflow execution with:
- YAML include resolution for modular workflow definitions
- Loop processing with item substitution
- Parameter substitution and variable resolution
- Display formatting (tables, images, JSON)
- Phase execution tracking and error recovery

Usage:
    uv run adb-run-workflow.py --workflow magisk-setup.toon
    uv run adb-run-workflow.py --workflow magisk-setup.toon --param device_id=127.0.0.1:5555
    uv run adb-run-workflow.py --workflow magisk-setup.toon --dry-run

Examples:
    # Execute workflow
    uv run adb-run-workflow.py --workflow .claude/skills/adb-magisk/workflows/magisk-setup.toon

    # Override parameters
    uv run adb-run-workflow.py --workflow workflows/magisk-setup.toon \
        --param device=192.168.1.100:5555 \
        --param timeout=15

    # Dry run (show execution plan)
    uv run adb-run-workflow.py --workflow magisk-setup.toon --dry-run

Exit Codes:
    0 - Success (workflow completed)
    1 - Partial (workflow completed with warnings)
    2 - Error (workflow failed)
    3 - Critical (invalid YAML or system error)

Author: MoAI-ADK
Version: 2.0.0
"""

# SECTION 1: Shebang + ASTRAL UV (above)

# SECTION 2: Module Docstring (above)

# SECTION 3: Imports
import subprocess
import json
import sys
import time
import glob
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from enum import Enum

import click
import yaml
from PIL import Image

# SECTION 4: Constants & Configuration
WORKFLOW_TIMEOUT = 600  # 10 minutes max
STEP_TIMEOUT = 120     # 2 minutes per step
RETRY_DELAY = 2
MAX_RETRIES = 3


class RecoveryAction(Enum):
    """Recovery actions when step fails."""
    ABORT = "abort"
    CONTINUE = "continue"
    LOG_AND_CONTINUE = "log_and_continue"
    RETRY = "retry"

# SECTION 5: Project Root Auto-Detection
def find_project_root(start_path: Optional[Path] = None) -> Path:
    """Auto-detect project root by searching for markers."""
    current = (start_path or Path.cwd()).resolve()
    while current != current.parent:
        if any((current / marker).exists() for marker in
               [".git", "pyproject.toml", ".moai", ".claude"]):
            return current
        current = current.parent
    return Path.cwd()

def find_script_path(project_root: Path, script_name: str) -> Optional[Path]:
    """Find adb-* script in any skill directory using glob."""
    # Try glob pattern: .claude/skills/*/scripts/{script_name}
    pattern = str(project_root / ".claude/skills/*/scripts" / script_name)
    matches = glob.glob(pattern)

    if matches:
        return Path(matches[0])  # Return first match

    # Alternative: search .claude/skills/ recursively
    for skills_dir in (project_root / ".claude/skills").glob("*/scripts"):
        script_path = skills_dir / script_name
        if script_path.exists():
            return script_path

    return None


# SECTION 6: YAML Include Resolution
class WorkflowParser:
    """Parse TOON workflows with !include directive resolution."""

    def __init__(self, base_path: Path, verbose: bool = False):
        """Initialize parser."""
        self.base_path = base_path
        self.verbose = verbose
        self._include_cache: Dict[str, Any] = {}

    def load_workflow(self, workflow_path: Path) -> Dict[str, Any]:
        """Load TOON workflow file with include resolution."""
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow not found: {workflow_path}")

        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)

        # Resolve includes
        workflow = self._resolve_includes(workflow, workflow_path.parent)
        return workflow

    def _resolve_includes(self, obj: Any, base_path: Path) -> Any:
        """Recursively resolve !include directives."""
        if isinstance(obj, dict):
            resolved = {}
            for key, value in obj.items():
                # Handle !include directive
                if key == "!include" and isinstance(value, str):
                    include_path = base_path / value
                    if include_path not in self._include_cache:
                        if not include_path.exists():
                            raise FileNotFoundError(f"Include not found: {include_path}")
                        with open(include_path) as f:
                            self._include_cache[include_path] = yaml.safe_load(f)
                    return self._resolve_includes(
                        self._include_cache[include_path],
                        include_path.parent
                    )
                resolved[key] = self._resolve_includes(value, base_path)
            return resolved
        elif isinstance(obj, list):
            return [self._resolve_includes(item, base_path) for item in obj]
        return obj


# SECTION 7: Variable Substitution
class VariableSubstitutor:
    """Handle parameter substitution and variable resolution."""

    PATTERN = re.compile(r"\{\{\s*([^}]+)\s*\}\}")

    @staticmethod
    def substitute(value: Any, variables: Dict[str, Any]) -> Any:
        """Recursively substitute {{ variable }} placeholders."""
        if isinstance(value, str):
            return VariableSubstitutor._substitute_string(value, variables)
        elif isinstance(value, dict):
            return {
                k: VariableSubstitutor.substitute(v, variables)
                for k, v in value.items()
            }
        elif isinstance(value, list):
            return [
                VariableSubstitutor.substitute(item, variables)
                for item in value
            ]
        return value

    @staticmethod
    def _substitute_string(s: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in string."""
        def replace_var(match: re.Match) -> str:
            var_path = match.group(1).strip()
            value = VariableSubstitutor._get_nested_value(variables, var_path)
            return str(value) if value is not None else match.group(0)

        return VariableSubstitutor.PATTERN.sub(replace_var, s)

    @staticmethod
    def _get_nested_value(obj: Any, path: str) -> Any:
        """Get value from nested object using dot notation."""
        keys = path.split(".")
        current = obj

        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif hasattr(current, key):
                current = getattr(current, key)
            else:
                return None

        return current


# SECTION 8: Output Formatting
class OutputFormatter:
    """Format execution results for display."""

    @staticmethod
    def format_as_table(data: List[Dict[str, Any]], columns: List[str]) -> str:
        """Format data as ASCII table."""
        if not data or not columns:
            return str(data)

        header = " | ".join(columns)
        separator = "-" * len(header)
        rows = [header, separator]

        for item in data:
            row_values = [str(item.get(col, "")) for col in columns]
            rows.append(" | ".join(row_values))

        return "\n".join(rows)

    @staticmethod
    def format_as_image(data: Any) -> str:
        """Format data as image display."""
        if isinstance(data, str):
            image_path = Path(data)
            if image_path.exists():
                try:
                    img = Image.open(image_path)
                    return f"Image ({img.size[0]}x{img.size[1]}): {image_path}"
                except Exception as e:
                    return f"Could not load image: {e}"
        return str(data)

    @staticmethod
    def format_output(data: Any, display_config: Dict[str, Any]) -> str:
        """Format output based on configuration."""
        format_type = display_config.get("type", "json")

        if format_type == "table":
            return OutputFormatter.format_as_table(
                data, display_config.get("columns", [])
            )
        elif format_type == "image":
            return OutputFormatter.format_as_image(data)
        elif format_type == "json":
            return json.dumps(data, indent=2)
        else:
            return str(data)


# SECTION 9: Data Models
@dataclass
class StepResult:
    """Result of single step execution."""
    step_id: str
    action: str
    success: bool = False
    duration: float = 0.0
    error: str = None
    attempts: int = 1
    output: dict = field(default_factory=dict)

@dataclass
class PhaseResult:
    """Result of phase execution."""
    phase_id: str
    phase_name: str
    success: bool = False
    duration: float = 0.0
    steps: list = field(default_factory=list)
    error: str = None

@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    workflow_name: str
    success: bool = False
    duration: float = 0.0
    phases: list = field(default_factory=list)
    error: str = None
    total_steps: int = 0
    completed_steps: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "workflow_name": self.workflow_name,
            "success": self.success,
            "duration": round(self.duration, 2),
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "phases": [asdict(p) for p in self.phases],
            "error": self.error
        }

# SECTION 10: Core Business Logic - Workflow Execution

def load_workflow(workflow_path: Path) -> dict:
    """Load TOON YAML workflow file."""
    if not workflow_path.exists():
        raise RuntimeError(f"Workflow not found: {workflow_path}")

    try:
        with open(workflow_path, 'r') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise RuntimeError(f"YAML parse error: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to load workflow: {e}")

def substitute_parameters(obj: any, params: dict) -> any:
    """Recursively substitute {{ param }} in object using VariableSubstitutor."""
    return VariableSubstitutor.substitute(obj, params)

def execute_step(step: Dict[str, Any], project_root: Path, dry_run: bool = False,
                verbose: bool = False, attempt: int = 1) -> StepResult:
    """Execute single automation step with subprocess."""
    step_id = step.get('id', 'unknown')
    action = step.get('action', 'unknown')
    params = step.get('params', {})

    result = StepResult(step_id=step_id, action=action)
    result.attempts = attempt

    if dry_run:
        result.success = True
        result.output = {"dry_run": True, "action": action, "params": params}
        return result

    # Step 1: Find script path
    script_name = f"adb-{action.replace('-', '_')}.py"
    script_path = find_script_path(project_root, script_name)

    if not script_path:
        result.error = f"Script not found: {script_name}"
        return result

    # Step 2: Build command
    cmd = ["uv", "run", str(script_path)]

    # Add parameters as CLI arguments
    for key, value in params.items():
        if isinstance(value, bool):
            if value:
                cmd.append(f"--{key}")
        else:
            cmd.append(f"--{key}")
            cmd.append(str(value))

    # Add JSON output flag
    cmd.append("--json")

    if verbose:
        click.echo(f"    Command: {' '.join(cmd)}", err=True)

    # Step 3: Execute subprocess
    start_time = time.time()
    try:
        process_result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=STEP_TIMEOUT,
            cwd=project_root
        )

        result.duration = time.time() - start_time

        # Check exit code
        if process_result.returncode == 0:
            result.success = True
            # Try to parse JSON output
            try:
                result.output = json.loads(process_result.stdout)
            except json.JSONDecodeError:
                result.output = {"stdout": process_result.stdout}
        else:
            result.success = False
            result.error = f"Script exited with code {process_result.returncode}"
            if process_result.stderr:
                result.error += f": {process_result.stderr[:200]}"

    except subprocess.TimeoutExpired:
        result.error = f"Script timeout (>{STEP_TIMEOUT}s)"
        result.duration = time.time() - start_time
    except Exception as e:
        result.error = str(e)
        result.duration = time.time() - start_time

    return result

def execute_phase(phase: Dict[str, Any], params: Dict[str, Any], project_root: Path,
                 recovery_rules: Optional[List[Dict[str, Any]]] = None,
                 dry_run: bool = False, verbose: bool = False) -> PhaseResult:
    """Execute automation phase (collection of steps) with error recovery."""
    phase_id = phase.get('id', 'unknown')
    phase_name = phase.get('name', phase_id)
    steps = phase.get('steps', [])

    result = PhaseResult(phase_id=phase_id, phase_name=phase_name)

    start_time = time.time()

    for step in steps:
        # Substitute parameters
        step = substitute_parameters(step, params)

        # Handle loop steps
        if "loop" in step:
            loop_config = step["loop"]
            items = loop_config.get("items", [])
            count = loop_config.get("count", len(items))

            for idx, item in enumerate(items[:count]):
                # Create loop variables
                loop_vars = params.copy()
                loop_vars["item"] = item
                loop_vars["index"] = idx

                # Substitute in step params
                loop_step = substitute_parameters(step, loop_vars)

                # Execute loop iteration
                step_result = None
                for attempt in range(1, MAX_RETRIES + 1):
                    step_result = execute_step(
                        loop_step, project_root, dry_run=dry_run,
                        verbose=verbose, attempt=attempt
                    )

                    if step_result.success:
                        break

                    if attempt < MAX_RETRIES:
                        if verbose:
                            click.echo(f"    Retry {attempt}/{MAX_RETRIES-1} in {RETRY_DELAY}s...", err=True)
                        time.sleep(RETRY_DELAY)

                result.steps.append(step_result)
        else:
            # Regular step execution
            step_result = None
            for attempt in range(1, MAX_RETRIES + 1):
                step_result = execute_step(step, project_root, dry_run=dry_run,
                                          verbose=verbose, attempt=attempt)

                if step_result.success:
                    break

                if attempt < MAX_RETRIES:
                    if verbose:
                        click.echo(f"    Retry {attempt}/{MAX_RETRIES-1} in {RETRY_DELAY}s...", err=True)
                    time.sleep(RETRY_DELAY)

            result.steps.append(step_result)

        if verbose:
            status = "✅" if step_result.success else "❌"
            click.echo(f"  {status} {step_result.step_id}: {step_result.action} "
                      f"({step_result.duration:.1f}s, attempt {step_result.attempts})")

        if not step_result.success:
            # Check for recovery rules
            handled = False
            if recovery_rules:
                for rule in recovery_rules:
                    if rule.get('on_error') == step_result.step_id:
                        if verbose:
                            click.echo(f"    🔄 Recovery rule triggered: {rule.get('action')}", err=True)
                        # Recovery action found but not executed (would need deeper integration)
                        # In full implementation, would execute recovery action here
                        handled = rule.get('then') == 'continue'
                        break

            if not handled:
                result.error = step_result.error
                break

    result.success = all(s.success for s in result.steps)
    result.duration = time.time() - start_time

    return result

def execute_workflow(workflow_data: Dict[str, Any], user_params: Optional[Dict[str, str]] = None,
                    dry_run: bool = False, verbose: bool = False) -> WorkflowResult:
    """Execute complete workflow with error recovery."""
    workflow_name = workflow_data.get('name', 'Unknown')
    result = WorkflowResult(workflow_name=workflow_name)

    # Find project root
    project_root = find_project_root()

    # Merge parameters
    params = workflow_data.get('parameters', {})
    if user_params:
        params.update(user_params)

    # Get recovery rules
    recovery_rules = workflow_data.get('recovery', [])

    # Count total steps
    phases = workflow_data.get('phases', [])
    result.total_steps = sum(len(p.get('steps', [])) for p in phases)

    start_time = time.time()

    # Validate workflow
    if not phases:
        result.error = "Workflow has no phases defined"
        result.exit_code = 3
        result.duration = time.time() - start_time
        return result

    if verbose:
        click.echo(f"🚀 Starting workflow: {workflow_name}")
        click.echo(f"   Parameters: {json.dumps(params, indent=4)}")
        click.echo(f"   Total steps: {result.total_steps}")
        click.echo()

    # Execute phases sequentially
    for i, phase in enumerate(phases, 1):
        if verbose:
            click.echo(f"📋 Phase {i}/{len(phases)}: {phase.get('name', phase.get('id'))}")

        phase_result = execute_phase(phase, params, project_root,
                                    recovery_rules=recovery_rules,
                                    dry_run=dry_run, verbose=verbose)
        result.phases.append(phase_result)
        result.completed_steps += len(phase_result.steps)

        if verbose:
            status = "✅" if phase_result.success else "❌"
            click.echo(f"{status} Phase {phase_result.phase_id}: {phase_result.phase_name} "
                      f"({phase_result.duration:.1f}s)")
            click.echo()

        if not phase_result.success:
            result.error = phase_result.error
            if not dry_run:  # Only break on real execution, continue for dry-run
                break

    result.success = all(p.success for p in result.phases)
    result.duration = time.time() - start_time

    if verbose:
        click.echo(f"✅ Workflow completed in {result.duration:.1f}s" if result.success
                  else f"❌ Workflow failed after {result.duration:.1f}s")

    return result

# SECTION 11: Display and Output Formatting
def format_human_output(result: WorkflowResult) -> str:
    """Format result for human-readable output."""
    lines = []

    # Header
    if result.success:
        lines.append(f"✅ WORKFLOW SUCCESS: {result.workflow_name}")
    else:
        lines.append(f"❌ WORKFLOW FAILED: {result.workflow_name}")

    lines.append("")

    # Phase details
    for i, phase in enumerate(result.phases, 1):
        status = "✅" if phase.success else "❌"
        lines.append(f"{status} Phase {i}: {phase.phase_name}")
        lines.append(f"   Duration: {phase.duration:.1f}s")

        # Step details
        for step in phase.steps:
            step_status = "✅" if step.success else "❌"
            attempt_str = f"({step.attempts} attempts)" if step.attempts > 1 else ""
            lines.append(f"   {step_status} {step.step_id}: {step.action} "
                        f"[{step.duration:.1f}s] {attempt_str}")

            if step.error:
                lines.append(f"      Error: {step.error[:100]}")

        lines.append("")

    # Summary
    lines.append(f"Summary:")
    lines.append(f"  Steps completed: {result.completed_steps}/{result.total_steps}")
    lines.append(f"  Total duration: {result.duration:.1f}s")
    lines.append(f"  Status: {'✅ SUCCESS' if result.success else '❌ FAILED'}")

    if result.error:
        lines.append(f"  Final error: {result.error}")

    return "\n".join(lines)

def format_json_output(result: WorkflowResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2)

# SECTION 12: CLI Interface + Entry Point
@click.command()
@click.option(
    '--workflow',
    type=click.Path(exists=False),
    required=True,
    help='Path to TOON workflow YAML file (e.g., .claude/skills/adb-magisk/workflows/magisk-setup.toon)'
)
@click.option(
    '--param',
    multiple=True,
    nargs=1,
    help='Override parameter (--param device=127.0.0.1:5555 --param timeout=30)'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show execution plan without executing'
)
@click.option(
    '--verbose',
    is_flag=True,
    help='Detailed execution logging'
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Output as JSON'
)
def cli(workflow: str, param: tuple, dry_run: bool, verbose: bool,
        output_json: bool) -> None:
    """
    Execute TOON YAML automation workflow.

    Coordinates multiple ADB scripts across phases with error recovery
    and state tracking. Uses glob patterns to find scripts across all skills.

    Examples:
        # Execute Magisk setup
        uv run adb-run-workflow.py \\
            --workflow .claude/skills/adb-magisk/workflows/magisk-setup.toon

        # Execute with parameters
        uv run adb-run-workflow.py \\
            --workflow .claude/skills/adb-magisk/workflows/magisk-setup.toon \\
            --param device=127.0.0.1:5555 \\
            --param timeout=15

        # Master Karrot bypass (7-phase orchestration)
        uv run adb-run-workflow.py \\
            --workflow .claude/skills/adb-karrot/workflows/karrot-bypass-playintegrity.toon \\
            --param device=127.0.0.1:5555 \\
            --param module_path=/sdcard/PlayIntegrityFork.zip \\
            --param test_email=user@example.com \\
            --param test_password=password \\
            --verbose

        # Dry run to see execution plan
        uv run adb-run-workflow.py \\
            --workflow workflows/magisk-setup.toon \\
            --dry-run
    """
    # Parse parameters
    user_params = {}
    for p in param:
        if '=' in p[0]:
            key, value = p[0].split('=', 1)
            user_params[key] = value
        else:
            click.echo(f"❌ Error: Parameter format should be key=value", err=True)
            sys.exit(3)

    result = WorkflowResult(workflow_name=workflow)

    try:
        # Load workflow
        workflow_path = Path(workflow)
        if not workflow_path.is_absolute():
            # Try relative to project root
            project_root = find_project_root()
            workflow_path = project_root / workflow_path

        workflow_data = load_workflow(workflow_path)

        # Execute
        result = execute_workflow(workflow_data, user_params, dry_run=dry_run,
                                 verbose=verbose)

        # Output
        if output_json:
            click.echo(format_json_output(result))
        else:
            click.echo(format_human_output(result))

        # Determine exit code
        if result.success:
            sys.exit(0)
        elif result.error:
            sys.exit(2)  # Error
        else:
            sys.exit(1)  # Warning/partial success

    except RuntimeError as e:
        result.error = str(e)
        if output_json:
            click.echo(format_json_output(result), err=True)
        else:
            click.echo(f"❌ Error: {e}", err=True)
        sys.exit(2)
    except Exception as e:
        result.error = f"Unexpected error: {e}"
        if output_json:
            click.echo(format_json_output(result), err=True)
        else:
            click.echo(f"❌ Fatal: {e}", err=True)
        sys.exit(3)

# SECTION 13: Entry Point (IndieDevDan Pattern)
if __name__ == "__main__":
    cli()
