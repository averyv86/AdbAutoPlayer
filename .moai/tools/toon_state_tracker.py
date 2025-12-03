#!/usr/bin/env python3
# /// script
# dependencies = [
#     "click>=8.1.7",
#     "pyyaml>=6.0",
# ]
# ///

"""
TOON State Tracker - Track workflow execution state incrementally using TOON deltas

Track workflow execution state with ultra-compressed TOON delta updates,
achieving 85-90% token reduction vs full snapshots.

Usage:
    uv run toon_state_tracker.py init workflow.toon --output state.toon
    uv run toon_state_tracker.py update state.toon --phase 2 --status running
    uv run toon_state_tracker.py record state.toon --phase 2 --agent expert-backend --status completed --time 45.2
    uv run toon_state_tracker.py checkpoint state.toon --phase 2 --reason phase_complete
    uv run toon_state_tracker.py show state.toon
    uv run toon_state_tracker.py history state.toon
    uv run toon_state_tracker.py apply state.toon delta.toon
    uv run toon_state_tracker.py restore state.toon --checkpoint 1

Examples:
    # Initialize state from workflow definition
    uv run toon_state_tracker.py init SPEC-001/WORKFLOW.toon --output SPEC-001/state.toon

    # Start phase 1
    uv run toon_state_tracker.py update SPEC-001/state.toon --phase 1 --status running

    # Record agent completion
    uv run toon_state_tracker.py record SPEC-001/state.toon --phase 1 --agent manager-strategy --status completed --time 120.5

    # Create checkpoint
    uv run toon_state_tracker.py checkpoint SPEC-001/state.toon --phase 1 --reason phase_complete

    # View current state
    uv run toon_state_tracker.py show SPEC-001/state.toon

    # Export to JSON
    uv run toon_state_tracker.py show SPEC-001/state.toon --output json

    # Restore from checkpoint
    uv run toon_state_tracker.py restore SPEC-001/state.toon --checkpoint 1

Exit Codes:
    0 - Success
    1 - Warning (partial success)
    2 - Error (operation failed)
    3 - Critical (validation failed)

Requirements:
    - Python 3.11+
    - UV package manager
    - Access to project root
    - toon_workflow_parser.py for workflow definitions

Notes:
    - Designed for UV execution only
    - Works from any directory (auto-detects project root)
    - MCP-wrappable for future server integration
    - Delta updates: 50-100 tokens vs 800+ full state (85-90% reduction)
"""

# ========== SECTION 2: IMPORTS ==========
import click
import json
import sys
import yaml
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Literal, Optional

# ========== SECTION 3: CONSTANTS & CONFIGURATION ==========
VALID_STATUSES = ["pending", "running", "completed", "failed", "skipped"]
VALID_TRANSITIONS = {
    "pending": ["running", "skipped"],
    "running": ["completed", "failed"],
    "completed": [],  # Terminal state
    "failed": ["running"],  # Retry allowed
    "skipped": []  # Terminal state
}
DEFAULT_CHECKPOINT_INTERVAL = 3  # Create checkpoint every N phases

# ========== SECTION 4: PROJECT ROOT AUTO-DETECTION ==========
def find_project_root(start_path: Path | None = None) -> Path:
    """
    Auto-detect project root by searching for markers.

    Args:
        start_path: Starting directory for search (defaults to cwd)

    Returns:
        Path to project root

    Raises:
        RuntimeError: If project root not found
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()
    while current != current.parent:
        markers = [".git", "pyproject.toml", ".moai", "CLAUDE.md"]
        if any((current / marker).exists() for marker in markers):
            return current
        current = current.parent
    raise RuntimeError("Project root not found (no .git, pyproject.toml, or .moai)")

def get_project_root() -> Path:
    """Lazy getter for project root"""
    return find_project_root()

# ========== SECTION 5: DATA MODELS ==========

@dataclass
class AgentResult:
    """Agent execution result"""
    agent: str
    phase_id: int
    status: Literal["success", "failed"]
    execution_time: float  # seconds
    files_modified: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class TOONDelta:
    """
    Incremental state change (50-100 tokens instead of full 800+)

    Ultra-compressed format for state updates:
    @delta[1]{ts,phase,field,new}:
    2025-11-30T10:15:00,2,status,running
    """
    timestamp: str
    phase_id: int
    field: str  # "status" | "agent_result" | "checkpoint"
    old_value: Any
    new_value: Any
    delta_type: str = "update"  # "update" | "add" | "remove"

    def to_toon(self) -> str:
        """
        Convert delta to ultra-compressed TOON format.

        Returns:
            TOON-formatted delta string (single line, ~50-80 tokens)

        Example:
            @delta[1]{ts,phase,field,new}:
            2025-11-30T10:15:00,2,status,running
        """
        # Format values for TOON
        new_val_str = self._format_value(self.new_value)

        if self.field == "status":
            return f"{self.timestamp},{self.phase_id},{self.field},{new_val_str}"
        elif self.field == "agent_result":
            # agent_result format: agent,status,time,files
            if isinstance(self.new_value, AgentResult):
                files_str = "|".join(self.new_value.files_modified) if self.new_value.files_modified else ""
                return (f"{self.timestamp},{self.phase_id},{self.new_value.agent},"
                       f"{self.new_value.status},{self.new_value.execution_time:.1f},{files_str}")
        elif self.field == "checkpoint":
            return f"{self.timestamp},{self.phase_id},checkpoint,{new_val_str}"

        return f"{self.timestamp},{self.phase_id},{self.field},{new_val_str}"

    def _format_value(self, value: Any) -> str:
        """Format value for TOON output"""
        if isinstance(value, list):
            return "|".join(str(v) for v in value)
        elif isinstance(value, bool):
            return str(value).lower()
        elif value is None:
            return ""
        return str(value)

@dataclass
class Checkpoint:
    """Full state checkpoint for rollback"""
    checkpoint_id: int
    phase_id: int
    timestamp: datetime
    state_snapshot: str  # Full TOON state
    reason: Literal["phase_complete", "manual", "error"]

@dataclass
class WorkflowState:
    """Complete workflow execution state"""
    workflow_id: str
    workflow_name: str
    current_phase: int
    phase_statuses: dict[int, str]  # {phase_id: "pending"|"running"|"completed"|"failed"}
    agent_results: dict[str, AgentResult]  # {phase_id-agent: result}
    start_time: datetime
    last_updated: datetime
    checkpoints: list[Checkpoint] = field(default_factory=list)
    deltas: list[TOONDelta] = field(default_factory=list)
    total_phases: int = 0
    completed_phases: int = 0
    failed_phases: int = 0

    def to_toon(self) -> str:
        """
        Convert full state to TOON format (for checkpoints).

        Returns:
            Complete TOON state snapshot (~800-1000 tokens)
        """
        lines = []

        # Metadata section
        lines.append("@state[1]{workflow_id,name,current_phase,start_time,last_updated}:")
        lines.append(
            f"{self.workflow_id},{self.workflow_name},{self.current_phase},"
            f"{self.start_time.isoformat()},{self.last_updated.isoformat()}"
        )
        lines.append("")

        # Phase statuses section
        lines.append(f"@phase_statuses[{len(self.phase_statuses)}]{{phase_id,status}}:")
        for phase_id, status in sorted(self.phase_statuses.items()):
            lines.append(f"{phase_id},{status}")
        lines.append("")

        # Agent results section
        if self.agent_results:
            lines.append(f"@agent_results[{len(self.agent_results)}]{{phase_agent,status,time,files}}:")
            for key, result in sorted(self.agent_results.items()):
                files_str = "|".join(result.files_modified) if result.files_modified else ""
                lines.append(
                    f"{result.phase_id}-{result.agent},{result.status},"
                    f"{result.execution_time:.1f},{files_str}"
                )
            lines.append("")

        # Summary section
        lines.append("@summary[1]{total_phases,completed,failed}:")
        lines.append(f"{self.total_phases},{self.completed_phases},{self.failed_phases}")
        lines.append("")

        # Checkpoint metadata
        if self.checkpoints:
            lines.append(f"@checkpoints[{len(self.checkpoints)}]{{id,phase,timestamp,reason}}:")
            for cp in self.checkpoints:
                lines.append(
                    f"{cp.checkpoint_id},{cp.phase_id},"
                    f"{cp.timestamp.isoformat()},{cp.reason}"
                )

        return "\n".join(lines)

# ========== SECTION 6: CORE BUSINESS LOGIC ==========

class StateValidationError(Exception):
    """Custom exception for state validation errors"""
    pass

def init_state(workflow_path: Path) -> WorkflowState:
    """
    Initialize state tracker for new workflow execution.

    Creates initial state from parsed workflow definition.
    Sets all phases to "pending" status.
    Records start time.

    Args:
        workflow_path: Path to workflow TOON file

    Returns:
        Initialized WorkflowState

    Raises:
        RuntimeError: If workflow parsing fails
    """
    # Import workflow parser (lazy import to avoid circular dependency)
    import subprocess

    # Parse workflow using toon_workflow_parser
    project_root = get_project_root()
    result = subprocess.run(
        ["uv", "run", str(project_root / ".moai/tools/toon_workflow_parser.py"),
         "parse", str(workflow_path), "--output", "json"],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to parse workflow: {result.stderr}")

    workflow_data = json.loads(result.stdout)

    # Extract workflow metadata
    metadata = workflow_data.get("metadata", {})
    phases = workflow_data.get("phases", [])

    # Initialize phase statuses
    phase_statuses = {phase["id"]: "pending" for phase in phases}

    now = datetime.now(timezone.utc)

    return WorkflowState(
        workflow_id=metadata.get("template_id", "UNKNOWN"),
        workflow_name=metadata.get("name", "Unnamed Workflow"),
        current_phase=1,
        phase_statuses=phase_statuses,
        agent_results={},
        start_time=now,
        last_updated=now,
        total_phases=len(phases),
        completed_phases=0,
        failed_phases=0
    )

def update_phase_status(state: WorkflowState, phase_id: int, status: str) -> TOONDelta:
    """
    Update phase status, return only delta.

    Args:
        state: Current workflow state
        phase_id: Phase to update
        status: "pending" | "running" | "completed" | "failed"

    Returns:
        TOONDelta with only changed field (50-100 tokens vs 800+ full state)

    Raises:
        StateValidationError: If phase_id invalid or transition invalid
    """
    # Validate phase exists
    if phase_id not in state.phase_statuses:
        raise StateValidationError(f"Phase {phase_id} does not exist in workflow")

    # Validate status value
    if status not in VALID_STATUSES:
        raise StateValidationError(
            f"Invalid status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}"
        )

    # Validate transition
    current_status = state.phase_statuses[phase_id]
    valid_next = VALID_TRANSITIONS.get(current_status, [])

    if status != current_status and status not in valid_next:
        raise StateValidationError(
            f"Invalid transition from '{current_status}' to '{status}'. "
            f"Valid transitions: {', '.join(valid_next) if valid_next else 'none (terminal state)'}"
        )

    # Create delta
    delta = TOONDelta(
        timestamp=datetime.now(timezone.utc).isoformat(),
        phase_id=phase_id,
        field="status",
        old_value=current_status,
        new_value=status,
        delta_type="update"
    )

    # Apply update
    state.phase_statuses[phase_id] = status
    state.last_updated = datetime.now(timezone.utc)
    state.current_phase = phase_id
    state.deltas.append(delta)

    # Update summary counters
    if status == "completed":
        state.completed_phases += 1
    elif status == "failed":
        state.failed_phases += 1

    return delta

def record_agent_result(
    state: WorkflowState,
    phase_id: int,
    agent: str,
    status: Literal["success", "failed"],
    execution_time: float,
    files_modified: list[str] | None = None,
    errors: list[str] | None = None,
    warnings: list[str] | None = None
) -> TOONDelta:
    """
    Record agent execution result.

    Stores agent output, execution time, errors if any.
    Returns delta update.

    Args:
        state: Current workflow state
        phase_id: Phase the agent belongs to
        agent: Agent name (e.g., "expert-backend")
        status: "success" | "failed"
        execution_time: Execution time in seconds
        files_modified: List of modified file paths
        errors: List of error messages
        warnings: List of warning messages

    Returns:
        TOONDelta with agent result

    Raises:
        StateValidationError: If phase_id invalid
    """
    # Validate phase exists
    if phase_id not in state.phase_statuses:
        raise StateValidationError(f"Phase {phase_id} does not exist in workflow")

    # Create agent result
    result = AgentResult(
        agent=agent,
        phase_id=phase_id,
        status=status,
        execution_time=execution_time,
        files_modified=files_modified or [],
        errors=errors or [],
        warnings=warnings or []
    )

    # Store result
    result_key = f"{phase_id}-{agent}"
    state.agent_results[result_key] = result
    state.last_updated = datetime.now(timezone.utc)

    # Create delta
    delta = TOONDelta(
        timestamp=datetime.now(timezone.utc).isoformat(),
        phase_id=phase_id,
        field="agent_result",
        old_value=None,
        new_value=result,
        delta_type="add"
    )

    state.deltas.append(delta)

    return delta

def create_checkpoint(
    state: WorkflowState,
    checkpoint_id: int,
    phase_id: int,
    reason: Literal["phase_complete", "manual", "error"]
) -> Checkpoint:
    """
    Create state checkpoint for rollback capability.

    Full TOON state snapshot at critical phase boundaries.

    Args:
        state: Current workflow state
        checkpoint_id: Unique checkpoint identifier
        phase_id: Phase at which checkpoint is created
        reason: Reason for checkpoint creation

    Returns:
        Checkpoint with full state snapshot
    """
    checkpoint = Checkpoint(
        checkpoint_id=checkpoint_id,
        phase_id=phase_id,
        timestamp=datetime.now(timezone.utc),
        state_snapshot=state.to_toon(),
        reason=reason
    )

    state.checkpoints.append(checkpoint)
    state.last_updated = datetime.now(timezone.utc)

    return checkpoint

def apply_delta(state: WorkflowState, delta: TOONDelta) -> WorkflowState:
    """
    Apply incremental delta to state.

    Updates state object with delta changes.
    Returns updated state.

    Args:
        state: Current workflow state
        delta: Delta to apply

    Returns:
        Updated WorkflowState
    """
    if delta.field == "status":
        state.phase_statuses[delta.phase_id] = delta.new_value

        # Update counters
        if delta.new_value == "completed" and delta.old_value != "completed":
            state.completed_phases += 1
        elif delta.new_value == "failed" and delta.old_value != "failed":
            state.failed_phases += 1

    elif delta.field == "agent_result" and isinstance(delta.new_value, AgentResult):
        result_key = f"{delta.phase_id}-{delta.new_value.agent}"
        state.agent_results[result_key] = delta.new_value

    state.last_updated = datetime.now(timezone.utc)
    state.deltas.append(delta)

    return state

def load_state(state_file: Path) -> WorkflowState:
    """
    Load state from TOON file.

    Args:
        state_file: Path to state TOON file

    Returns:
        Loaded WorkflowState

    Raises:
        RuntimeError: If file parsing fails
    """
    with open(state_file, 'r') as f:
        content = f.read()

    # Parse TOON format
    lines = content.split("\n")
    sections = {}
    current_section = None
    current_lines = []

    for line in lines:
        line = line.strip()
        if line.startswith("@"):
            # Save previous section
            if current_section:
                sections[current_section] = current_lines

            # Parse section header
            if line.endswith(":"):
                section_name = line.split("[")[0][1:]
                current_section = section_name
                current_lines = []
            else:
                current_section = None
        elif current_section and line and not line.startswith("#"):
            current_lines.append(line)

    # Save last section
    if current_section:
        sections[current_section] = current_lines

    # Parse state metadata
    if "state" not in sections or not sections["state"]:
        raise RuntimeError("Missing @state section in state file")

    state_data = sections["state"][0].split(",")
    workflow_id = state_data[0]
    workflow_name = state_data[1]
    current_phase = int(state_data[2])
    start_time = datetime.fromisoformat(state_data[3])
    last_updated = datetime.fromisoformat(state_data[4])

    # Parse phase statuses
    phase_statuses = {}
    if "phase_statuses" in sections:
        for line in sections["phase_statuses"]:
            parts = line.split(",")
            phase_id = int(parts[0])
            status = parts[1]
            phase_statuses[phase_id] = status

    # Parse agent results
    agent_results = {}
    if "agent_results" in sections:
        for line in sections["agent_results"]:
            parts = line.split(",")
            phase_agent = parts[0]
            phase_id, agent = phase_agent.split("-", 1)
            status = parts[1]
            exec_time = float(parts[2])
            files = parts[3].split("|") if len(parts) > 3 and parts[3] else []

            agent_results[phase_agent] = AgentResult(
                agent=agent,
                phase_id=int(phase_id),
                status=status,
                execution_time=exec_time,
                files_modified=files
            )

    # Parse summary
    total_phases = 0
    completed_phases = 0
    failed_phases = 0
    if "summary" in sections and sections["summary"]:
        summary_data = sections["summary"][0].split(",")
        total_phases = int(summary_data[0])
        completed_phases = int(summary_data[1])
        failed_phases = int(summary_data[2])

    # Parse checkpoints
    checkpoints = []
    if "checkpoints" in sections:
        for line in sections["checkpoints"]:
            parts = line.split(",")
            cp_id = int(parts[0])
            cp_phase = int(parts[1])
            cp_timestamp = datetime.fromisoformat(parts[2])
            cp_reason = parts[3]

            checkpoints.append(Checkpoint(
                checkpoint_id=cp_id,
                phase_id=cp_phase,
                timestamp=cp_timestamp,
                state_snapshot="",  # Not loaded from state file
                reason=cp_reason
            ))

    return WorkflowState(
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        current_phase=current_phase,
        phase_statuses=phase_statuses,
        agent_results=agent_results,
        start_time=start_time,
        last_updated=last_updated,
        checkpoints=checkpoints,
        total_phases=total_phases,
        completed_phases=completed_phases,
        failed_phases=failed_phases
    )

def save_state(state: WorkflowState, state_file: Path):
    """
    Save state to TOON file.

    Args:
        state: WorkflowState to save
        state_file: Output file path
    """
    state_file.parent.mkdir(parents=True, exist_ok=True)

    with open(state_file, 'w') as f:
        f.write(state.to_toon())

# ========== SECTION 7: OUTPUT FORMATTERS ==========

def format_state_human(state: WorkflowState) -> str:
    """Format state for human-readable output"""
    lines = [
        f"Workflow State: {state.workflow_name} ({state.workflow_id})",
        f"Current Phase: {state.current_phase}/{state.total_phases}",
        f"Started: {state.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Last Updated: {state.last_updated.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Progress: {state.completed_phases} completed, {state.failed_phases} failed",
        "",
        "Phase Status:"
    ]

    for phase_id in sorted(state.phase_statuses.keys()):
        status = state.phase_statuses[phase_id]
        status_symbol = {
            "pending": "⏸️",
            "running": "▶️",
            "completed": "✅",
            "failed": "❌",
            "skipped": "⏭️"
        }.get(status, "❓")

        lines.append(f"  Phase {phase_id}: {status_symbol} {status}")

        # Show agent results for this phase
        phase_agents = [
            (key, result) for key, result in state.agent_results.items()
            if result.phase_id == phase_id
        ]

        for key, result in phase_agents:
            time_str = f"{result.execution_time:.1f}s"
            files_count = len(result.files_modified) if result.files_modified else 0
            lines.append(f"    └─ {result.agent}: {result.status} ({time_str}, {files_count} files)")

    if state.checkpoints:
        lines.extend([
            "",
            f"Checkpoints: {len(state.checkpoints)} saved",
        ])
        for cp in state.checkpoints:
            lines.append(
                f"  #{cp.checkpoint_id} at Phase {cp.phase_id} "
                f"({cp.timestamp.strftime('%H:%M:%S')}, {cp.reason})"
            )

    return "\n".join(lines)

def format_delta_human(delta: TOONDelta) -> str:
    """Format delta for human-readable output"""
    ts = datetime.fromisoformat(delta.timestamp).strftime('%H:%M:%S')

    if delta.field == "status":
        return f"[{ts}] Phase {delta.phase_id}: {delta.old_value} → {delta.new_value}"
    elif delta.field == "agent_result" and isinstance(delta.new_value, AgentResult):
        result = delta.new_value
        return (f"[{ts}] Phase {delta.phase_id} - {result.agent}: "
               f"{result.status} ({result.execution_time:.1f}s)")
    else:
        return f"[{ts}] Phase {delta.phase_id}: {delta.field} updated"

def state_to_dict(state: WorkflowState) -> dict:
    """Convert state to dictionary for JSON/YAML serialization"""
    return {
        "workflow_id": state.workflow_id,
        "workflow_name": state.workflow_name,
        "current_phase": state.current_phase,
        "total_phases": state.total_phases,
        "completed_phases": state.completed_phases,
        "failed_phases": state.failed_phases,
        "start_time": state.start_time.isoformat(),
        "last_updated": state.last_updated.isoformat(),
        "phase_statuses": state.phase_statuses,
        "agent_results": {
            key: asdict(result) for key, result in state.agent_results.items()
        },
        "checkpoints": [
            {
                "checkpoint_id": cp.checkpoint_id,
                "phase_id": cp.phase_id,
                "timestamp": cp.timestamp.isoformat(),
                "reason": cp.reason
            }
            for cp in state.checkpoints
        ]
    }

# ========== SECTION 8: CLI INTERFACE ==========

@click.group()
def cli():
    """TOON State Tracker - Track workflow execution state incrementally"""
    pass

@cli.command()
@click.argument('workflow_file', type=click.Path(exists=True))
@click.option('--output', type=click.Path(), required=True,
              help='Output state file path')
def init(workflow_file: str, output: str):
    """
    Initialize state tracker from workflow definition.

    Example:
        uv run toon_state_tracker.py init SPEC-001/WORKFLOW.toon --output SPEC-001/state.toon
    """
    try:
        workflow_path = Path(workflow_file)
        output_path = Path(output)

        state = init_state(workflow_path)
        save_state(state, output_path)

        print(f"✓ State initialized: {state.workflow_name}")
        print(f"  Workflow ID: {state.workflow_id}")
        print(f"  Total Phases: {state.total_phases}")
        print(f"  State file: {output_path}")

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(2)

@cli.command()
@click.argument('state_file', type=click.Path(exists=True))
@click.option('--phase', type=int, required=True, help='Phase ID')
@click.option('--status', type=click.Choice(VALID_STATUSES), required=True,
              help='New status')
def update(state_file: str, phase: int, status: str):
    """
    Update phase status.

    Example:
        uv run toon_state_tracker.py update state.toon --phase 2 --status running
    """
    try:
        state_path = Path(state_file)
        state = load_state(state_path)

        delta = update_phase_status(state, phase, status)
        save_state(state, state_path)

        print(f"✓ Phase {phase} status updated: {delta.old_value} → {status}")
        print(f"  Delta size: ~{len(delta.to_toon())} bytes (vs ~800+ for full state)")

        sys.exit(0)

    except StateValidationError as e:
        print(f"❌ Validation Error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(2)

@cli.command()
@click.argument('state_file', type=click.Path(exists=True))
@click.option('--phase', type=int, required=True, help='Phase ID')
@click.option('--agent', required=True, help='Agent name')
@click.option('--status', type=click.Choice(['success', 'failed']), required=True)
@click.option('--time', 'exec_time', type=float, required=True,
              help='Execution time in seconds')
@click.option('--files', help='Comma-separated list of modified files')
@click.option('--errors', help='Comma-separated list of errors')
@click.option('--warnings', help='Comma-separated list of warnings')
def record(state_file: str, phase: int, agent: str, status: str,
          exec_time: float, files: str | None, errors: str | None,
          warnings: str | None):
    """
    Record agent execution result.

    Example:
        uv run toon_state_tracker.py record state.toon --phase 2 --agent expert-backend --status success --time 45.2 --files "api.py,models.py"
    """
    try:
        state_path = Path(state_file)
        state = load_state(state_path)

        files_list = files.split(",") if files else []
        errors_list = errors.split(",") if errors else []
        warnings_list = warnings.split(",") if warnings else []

        delta = record_agent_result(
            state, phase, agent, status, exec_time,
            files_list, errors_list, warnings_list
        )
        save_state(state, state_path)

        print(f"✓ Agent result recorded: {agent} @ Phase {phase}")
        print(f"  Status: {status}")
        print(f"  Execution Time: {exec_time:.1f}s")
        print(f"  Files Modified: {len(files_list)}")

        sys.exit(0)

    except StateValidationError as e:
        print(f"❌ Validation Error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(2)

@cli.command()
@click.argument('state_file', type=click.Path(exists=True))
@click.option('--phase', type=int, required=True, help='Phase ID')
@click.option('--reason', type=click.Choice(['phase_complete', 'manual', 'error']),
              default='manual', help='Checkpoint reason')
def checkpoint(state_file: str, phase: int, reason: str):
    """
    Create state checkpoint for rollback.

    Example:
        uv run toon_state_tracker.py checkpoint state.toon --phase 2 --reason phase_complete
    """
    try:
        state_path = Path(state_file)
        state = load_state(state_path)

        checkpoint_id = len(state.checkpoints) + 1
        cp = create_checkpoint(state, checkpoint_id, phase, reason)
        save_state(state, state_path)

        # Save checkpoint to separate file
        cp_dir = state_path.parent / "checkpoints"
        cp_dir.mkdir(exist_ok=True)
        cp_file = cp_dir / f"checkpoint-{checkpoint_id:03d}.toon"

        with open(cp_file, 'w') as f:
            f.write(cp.state_snapshot)

        print(f"✓ Checkpoint created: #{checkpoint_id}")
        print(f"  Phase: {phase}")
        print(f"  Reason: {reason}")
        print(f"  File: {cp_file}")

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(2)

@cli.command()
@click.argument('state_file', type=click.Path(exists=True))
@click.option('--output', type=click.Choice(['human', 'json', 'yaml']),
              default='human', help='Output format')
def show(state_file: str, output: str):
    """
    View current state.

    Example:
        uv run toon_state_tracker.py show state.toon
        uv run toon_state_tracker.py show state.toon --output json
    """
    try:
        state_path = Path(state_file)
        state = load_state(state_path)

        if output == 'json':
            print(json.dumps(state_to_dict(state), indent=2))
        elif output == 'yaml':
            print(yaml.dump(state_to_dict(state),
                           default_flow_style=False, sort_keys=False))
        else:
            print(format_state_human(state))

        sys.exit(0)

    except Exception as e:
        if output == 'json':
            print(json.dumps({"error": str(e)}))
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(2)

@cli.command()
@click.argument('state_file', type=click.Path(exists=True))
@click.option('--limit', type=int, help='Limit number of deltas shown')
def history(state_file: str, limit: int | None):
    """
    View delta history.

    Example:
        uv run toon_state_tracker.py history state.toon
        uv run toon_state_tracker.py history state.toon --limit 10
    """
    try:
        state_path = Path(state_file)
        state = load_state(state_path)

        deltas = state.deltas[-limit:] if limit else state.deltas

        print(f"Delta History ({len(deltas)} deltas):")
        print()

        for delta in deltas:
            print(format_delta_human(delta))

        if not deltas:
            print("  No deltas recorded yet")

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(2)

@cli.command()
@click.argument('state_file', type=click.Path(exists=True))
@click.argument('delta_file', type=click.Path(exists=True))
def apply(state_file: str, delta_file: str):
    """
    Apply delta file to state.

    Example:
        uv run toon_state_tracker.py apply state.toon delta.toon
    """
    try:
        state_path = Path(state_file)
        delta_path = Path(delta_file)

        state = load_state(state_path)

        # Parse delta file (TOON format)
        with open(delta_path, 'r') as f:
            delta_content = f.read()

        # Apply each delta line
        for line in delta_content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("@"):
                continue

            parts = line.split(",")
            if len(parts) < 4:
                continue

            timestamp = parts[0]
            phase_id = int(parts[1])
            field = parts[2]
            new_value = parts[3]

            delta = TOONDelta(
                timestamp=timestamp,
                phase_id=phase_id,
                field=field,
                old_value=None,
                new_value=new_value,
                delta_type="update"
            )

            apply_delta(state, delta)

        save_state(state, state_path)

        print(f"✓ Deltas applied from {delta_path}")

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(2)

@cli.command()
@click.argument('state_file', type=click.Path(exists=True))
@click.option('--checkpoint', type=int, required=True,
              help='Checkpoint ID to restore from')
def restore(state_file: str, checkpoint: int):
    """
    Restore from checkpoint.

    Example:
        uv run toon_state_tracker.py restore state.toon --checkpoint 1
    """
    try:
        state_path = Path(state_file)

        # Load checkpoint file
        cp_dir = state_path.parent / "checkpoints"
        cp_file = cp_dir / f"checkpoint-{checkpoint:03d}.toon"

        if not cp_file.exists():
            print(f"❌ Checkpoint #{checkpoint} not found", file=sys.stderr)
            sys.exit(2)

        # Load checkpoint state
        restored_state = load_state(cp_file)

        # Save as current state
        save_state(restored_state, state_path)

        print(f"✓ State restored from checkpoint #{checkpoint}")
        print(f"  Phase: {restored_state.current_phase}")
        print(f"  Completed: {restored_state.completed_phases}/{restored_state.total_phases}")

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(2)

# ========== SECTION 9: ENTRY POINT ==========
if __name__ == "__main__":
    cli()
