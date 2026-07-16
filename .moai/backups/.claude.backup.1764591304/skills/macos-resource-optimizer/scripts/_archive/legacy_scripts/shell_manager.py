#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click>=8.1.0"
# ]
# ///

"""
Shell State Manager - Track and manage shell lifecycles for safe process termination.

Provides thread-safe shell registry with JSON persistence for coordinating
multi-agent cleanup operations. Supports pre-kill validation to prevent
terminating active work processes.

Usage:
    uv run scripts/shell_manager.py list
    uv run scripts/shell_manager.py check <shell_id>
    uv run scripts/shell_manager.py register <shell_id> --agent <agent_name> --command <cmd>
    uv run scripts/shell_manager.py cleanup --max-age 300
    uv run scripts/shell_manager.py complete <shell_id> --status-code 0
"""

import json
import os
import time
import fcntl
from pathlib import Path
from typing import Dict, List, Literal, Optional
from dataclasses import dataclass, asdict
from contextlib import contextmanager

import click


# Type definitions
ShellStatus = Literal["active", "completed", "failed", "orphaned", "unknown"]


@dataclass
class ShellEntry:
    """Represents a tracked shell process."""
    shell_id: str
    agent_name: str
    command: str
    timestamp: float
    status: ShellStatus = "active"
    status_code: Optional[int] = None
    completed_at: Optional[float] = None


class ShellStateTracker:
    """
    Track shell lifecycle states for safe multi-agent process management.

    Provides thread-safe operations with file locking to prevent race conditions
    during concurrent agent execution. All state is persisted to JSON for
    cross-session recovery.

    Attributes:
        registry_path: Path to the JSON registry file.
        _lock_path: Path to the lock file for thread safety.

    Example:
        tracker = ShellStateTracker()
        tracker.store_shell("shell-123", "coder", "npm run build", time.time())
        status = tracker.check_shell_status("shell-123")
        tracker.mark_shell_complete("shell-123", 0)
    """

    def __init__(self, registry_path: Optional[Path] = None) -> None:
        """
        Initialize the shell state tracker.

        Args:
            registry_path: Custom path for registry file. Defaults to
                          data/shell-registry.json relative to this script.
        """
        if registry_path is None:
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            registry_path = data_dir / "shell-registry.json"

        self.registry_path = Path(registry_path)
        self._lock_path = self.registry_path.with_suffix(".lock")

        # Ensure registry exists with valid JSON
        self._ensure_registry_exists()

    def _ensure_registry_exists(self) -> None:
        """Create registry file if it doesn't exist."""
        if not self.registry_path.exists():
            self._write_registry({"shells": {}, "metadata": {"created_at": time.time()}})

    @contextmanager
    def _file_lock(self):
        """
        Context manager for file-based locking.

        Uses fcntl.flock for POSIX-compliant advisory locking.
        Falls back gracefully if locking is unavailable.
        """
        lock_file = None
        try:
            lock_file = open(self._lock_path, "w")
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            if lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()

    def _read_registry(self) -> Dict:
        """
        Read the registry file with error handling.

        Returns:
            Registry data dictionary or empty structure on error.
        """
        try:
            if self.registry_path.exists():
                content = self.registry_path.read_text()
                if content.strip():
                    return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            # Log error but continue with empty registry
            click.echo(f"Warning: Registry read error: {e}", err=True)

        return {"shells": {}, "metadata": {"created_at": time.time()}}

    def _write_registry(self, data: Dict) -> None:
        """
        Write registry data atomically.

        Uses write-then-rename pattern for crash safety.

        Args:
            data: Registry data to persist.
        """
        # Update metadata timestamp
        data["metadata"]["updated_at"] = time.time()

        # Write to temp file first for atomicity
        temp_path = self.registry_path.with_suffix(".tmp")
        try:
            temp_path.write_text(json.dumps(data, indent=2))
            temp_path.rename(self.registry_path)
        except IOError as e:
            click.echo(f"Warning: Registry write error: {e}", err=True)
            if temp_path.exists():
                temp_path.unlink()

    def store_shell(
        self,
        shell_id: str,
        agent_name: str,
        command: str,
        timestamp: float
    ) -> bool:
        """
        Register a new shell process.

        Args:
            shell_id: Unique identifier for the shell.
            agent_name: Name of the agent that spawned the shell.
            command: Command being executed.
            timestamp: Unix timestamp when shell was started.

        Returns:
            True if registration successful, False otherwise.
        """
        with self._file_lock():
            registry = self._read_registry()

            entry = ShellEntry(
                shell_id=shell_id,
                agent_name=agent_name,
                command=command,
                timestamp=timestamp,
                status="active"
            )

            registry["shells"][shell_id] = asdict(entry)
            self._write_registry(registry)

        return True

    def check_shell_status(self, shell_id: str) -> ShellStatus:
        """
        Get the current status of a shell.

        Args:
            shell_id: Unique identifier for the shell.

        Returns:
            Status string: "active", "completed", "failed", "orphaned", or "unknown".
        """
        with self._file_lock():
            registry = self._read_registry()

            if shell_id not in registry["shells"]:
                return "unknown"

            entry = registry["shells"][shell_id]

            # Check for orphaned shells (active but too old without completion)
            if entry["status"] == "active":
                age = time.time() - entry["timestamp"]
                # Shells active for more than 1 hour without update are orphaned
                if age > 3600:
                    return "orphaned"

            return entry["status"]

    def mark_shell_complete(self, shell_id: str, status_code: int) -> bool:
        """
        Mark a shell as completed with exit status.

        Args:
            shell_id: Unique identifier for the shell.
            status_code: Exit code from the shell process.

        Returns:
            True if shell was found and updated, False otherwise.
        """
        with self._file_lock():
            registry = self._read_registry()

            if shell_id not in registry["shells"]:
                return False

            entry = registry["shells"][shell_id]
            entry["status"] = "completed" if status_code == 0 else "failed"
            entry["status_code"] = status_code
            entry["completed_at"] = time.time()

            self._write_registry(registry)

        return True

    def cleanup_stale_shells(self, max_age_seconds: int = 300) -> int:
        """
        Remove shell entries older than max_age_seconds.

        Args:
            max_age_seconds: Maximum age in seconds before removal. Default 300 (5 min).

        Returns:
            Number of shells removed.
        """
        with self._file_lock():
            registry = self._read_registry()
            current_time = time.time()

            shells_to_remove = []
            for shell_id, entry in registry["shells"].items():
                # Only clean up completed/failed/orphaned shells
                if entry["status"] != "active":
                    timestamp = entry.get("completed_at", entry["timestamp"])
                    if current_time - timestamp > max_age_seconds:
                        shells_to_remove.append(shell_id)
                # Also clean up very old active shells (likely orphaned)
                elif current_time - entry["timestamp"] > max_age_seconds * 12:  # 1 hour default
                    shells_to_remove.append(shell_id)

            for shell_id in shells_to_remove:
                del registry["shells"][shell_id]

            if shells_to_remove:
                self._write_registry(registry)

        return len(shells_to_remove)

    def get_active_shells(self) -> List[Dict]:
        """
        List all currently active shells.

        Returns:
            List of shell entry dictionaries with status "active".
        """
        with self._file_lock():
            registry = self._read_registry()

            active_shells = []
            for shell_id, entry in registry["shells"].items():
                if entry["status"] == "active":
                    # Enrich with computed age
                    entry_copy = entry.copy()
                    entry_copy["age_seconds"] = time.time() - entry["timestamp"]
                    active_shells.append(entry_copy)

            return active_shells

    def validate_shell_exists(self, shell_id: str) -> bool:
        """
        Pre-kill validation to check if shell is tracked.

        Use this before terminating processes to ensure they're
        registered and not actively in use by other agents.

        Args:
            shell_id: Unique identifier for the shell.

        Returns:
            True if shell exists in registry, False otherwise.
        """
        with self._file_lock():
            registry = self._read_registry()
            return shell_id in registry["shells"]

    def get_shell_details(self, shell_id: str) -> Optional[Dict]:
        """
        Get full details for a specific shell.

        Args:
            shell_id: Unique identifier for the shell.

        Returns:
            Shell entry dictionary or None if not found.
        """
        with self._file_lock():
            registry = self._read_registry()

            if shell_id in registry["shells"]:
                entry = registry["shells"][shell_id].copy()
                entry["age_seconds"] = time.time() - entry["timestamp"]
                return entry

            return None


# CLI Interface
@click.group()
def cli():
    """Shell State Manager - Track and manage shell lifecycles."""
    pass


@cli.command()
@click.option("--format", "output_format", type=click.Choice(["json", "table"]),
              default="table", help="Output format")
def list(output_format: str):
    """List all active shells."""
    tracker = ShellStateTracker()
    shells = tracker.get_active_shells()

    if output_format == "json":
        click.echo(json.dumps(shells, indent=2))
    else:
        if not shells:
            click.echo("No active shells found.")
            return

        click.echo(f"\n{'Shell ID':<20} {'Agent':<15} {'Age (s)':<10} {'Command':<40}")
        click.echo("-" * 85)
        for shell in shells:
            cmd = shell["command"][:37] + "..." if len(shell["command"]) > 40 else shell["command"]
            click.echo(f"{shell['shell_id']:<20} {shell['agent_name']:<15} {shell['age_seconds']:<10.0f} {cmd:<40}")


@cli.command()
@click.argument("shell_id")
@click.option("--format", "output_format", type=click.Choice(["json", "text"]),
              default="text", help="Output format")
def check(shell_id: str, output_format: str):
    """Check status of a specific shell."""
    tracker = ShellStateTracker()
    status = tracker.check_shell_status(shell_id)
    details = tracker.get_shell_details(shell_id)

    if output_format == "json":
        result = {"shell_id": shell_id, "status": status}
        if details:
            result["details"] = details
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Shell ID: {shell_id}")
        click.echo(f"Status: {status}")
        if details:
            click.echo(f"Agent: {details['agent_name']}")
            click.echo(f"Command: {details['command']}")
            click.echo(f"Age: {details['age_seconds']:.0f} seconds")


@cli.command()
@click.argument("shell_id")
@click.option("--agent", required=True, help="Agent name that owns this shell")
@click.option("--command", required=True, help="Command being executed")
def register(shell_id: str, agent: str, command: str):
    """Register a new shell process."""
    tracker = ShellStateTracker()
    success = tracker.store_shell(shell_id, agent, command, time.time())

    if success:
        click.echo(f"Registered shell: {shell_id}")
    else:
        click.echo(f"Failed to register shell: {shell_id}", err=True)


@cli.command()
@click.argument("shell_id")
@click.option("--status-code", type=int, default=0, help="Exit status code")
def complete(shell_id: str, status_code: int):
    """Mark a shell as completed."""
    tracker = ShellStateTracker()
    success = tracker.mark_shell_complete(shell_id, status_code)

    if success:
        status = "completed" if status_code == 0 else "failed"
        click.echo(f"Marked shell {shell_id} as {status} (code: {status_code})")
    else:
        click.echo(f"Shell not found: {shell_id}", err=True)


@cli.command()
@click.option("--max-age", type=int, default=300, help="Max age in seconds (default: 300)")
def cleanup(max_age: int):
    """Remove stale shell entries."""
    tracker = ShellStateTracker()
    removed = tracker.cleanup_stale_shells(max_age)
    click.echo(f"Removed {removed} stale shell entries (max age: {max_age}s)")


@cli.command()
@click.argument("shell_id")
def validate(shell_id: str):
    """Validate if a shell exists (pre-kill check)."""
    tracker = ShellStateTracker()
    exists = tracker.validate_shell_exists(shell_id)

    if exists:
        status = tracker.check_shell_status(shell_id)
        click.echo(f"Shell {shell_id} exists (status: {status})")
        # Return success for active shells
        raise SystemExit(0 if status == "active" else 1)
    else:
        click.echo(f"Shell {shell_id} not found in registry")
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
