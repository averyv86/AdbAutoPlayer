#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=5.9.0"]
# ///

"""
Production Error Handling & Validation System

Provides:
- Centralized error handling
- System health validation
- Recovery mechanisms
- Graceful degradation
- Detailed error reporting

Author: MoAI-ADK
Version: 3.0.0 (Phase 3 - Production)
Date: 2025-12-01
"""

import json
import sys
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import psutil


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    SYSTEM = "system"              # System-level errors (permissions, resources)
    EXTENSION = "extension"        # Chrome extension errors
    PROCESS = "process"            # Process-related errors
    MEMORY = "memory"              # Memory-related errors
    NETWORK = "network"            # Network/connection errors
    VALIDATION = "validation"      # Input validation errors
    CONFIGURATION = "configuration"  # Config file errors
    UNKNOWN = "unknown"            # Unclassified errors


@dataclass
class ErrorRecord:
    """Detailed error record for logging and analysis."""
    timestamp: str
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    user_impact: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "context": self.context,
            "stack_trace": self.stack_trace,
            "recovery_attempted": self.recovery_attempted,
            "recovery_successful": self.recovery_successful,
            "user_impact": self.user_impact
        }


class SystemValidator:
    """
    System health and requirement validation.

    Validates prerequisites before optimization.
    """

    @staticmethod
    def validate_memory_available() -> Tuple[bool, Optional[str]]:
        """
        Validate sufficient memory is available.

        Returns:
            (is_valid, error_message)
        """
        try:
            mem = psutil.virtual_memory()

            # Need at least 2GB available
            if mem.available < 2 * 1024 * 1024 * 1024:
                return False, f"Insufficient memory: {mem.available / 1024 / 1024:.0f} MB available (need 2GB)"

            return True, None

        except Exception as e:
            return False, f"Memory validation error: {e}"

    @staticmethod
    def validate_disk_space() -> Tuple[bool, Optional[str]]:
        """
        Validate sufficient disk space.

        Returns:
            (is_valid, error_message)
        """
        try:
            disk = psutil.disk_usage('/')

            # Need at least 1GB free
            if disk.free < 1 * 1024 * 1024 * 1024:
                return False, f"Insufficient disk space: {disk.free / 1024 / 1024:.0f} MB free (need 1GB)"

            return True, None

        except Exception as e:
            return False, f"Disk validation error: {e}"

    @staticmethod
    def validate_process_access() -> Tuple[bool, Optional[str]]:
        """
        Validate process enumeration access.

        Returns:
            (is_valid, error_message)
        """
        try:
            # Try to enumerate processes
            accessible_count = 0
            total_count = 0

            for proc in psutil.process_iter(['name']):
                total_count += 1
                try:
                    _ = proc.info['name']
                    accessible_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            if accessible_count < total_count * 0.5:
                return False, f"Limited process access: {accessible_count}/{total_count} accessible"

            return True, None

        except Exception as e:
            return False, f"Process access validation error: {e}"

    @staticmethod
    def validate_chrome_extension(extension_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Chrome extension installation.

        Args:
            extension_id: Chrome extension ID

        Returns:
            (is_valid, error_message)
        """
        manifest_paths = [
            Path.home() / "Library/Application Support/Google/Chrome/NativeMessagingHosts/com.moai.tab_suspender.json",
            Path.home() / "Library/Application Support/Dia Browser/NativeMessagingHosts/com.moai.tab_suspender.json",
        ]

        for path in manifest_paths:
            if path.exists():
                try:
                    with open(path) as f:
                        manifest = json.load(f)

                    # Validate manifest structure
                    if "name" not in manifest:
                        return False, f"Invalid manifest: missing 'name' field"

                    if "path" not in manifest:
                        return False, f"Invalid manifest: missing 'path' field"

                    if "allowed_origins" not in manifest:
                        return False, f"Invalid manifest: missing 'allowed_origins' field"

                    # Validate host script exists
                    host_path = Path(manifest["path"])
                    if not host_path.exists():
                        return False, f"Host script not found: {host_path}"

                    # Validate extension ID in allowed_origins
                    origins = manifest["allowed_origins"]
                    if not any(extension_id in origin for origin in origins):
                        return False, f"Extension ID {extension_id} not in allowed_origins"

                    return True, None

                except json.JSONDecodeError:
                    return False, f"Invalid JSON in manifest: {path}"
                except Exception as e:
                    return False, f"Manifest validation error: {e}"

        return False, "No Native Messaging manifest found"

    @classmethod
    def validate_all(cls) -> Tuple[bool, List[str]]:
        """
        Run all validations.

        Returns:
            (all_valid, error_messages)
        """
        errors = []

        # Memory validation
        valid, error = cls.validate_memory_available()
        if not valid:
            errors.append(f"❌ Memory: {error}")

        # Disk space validation
        valid, error = cls.validate_disk_space()
        if not valid:
            errors.append(f"❌ Disk: {error}")

        # Process access validation
        valid, error = cls.validate_process_access()
        if not valid:
            errors.append(f"⚠️  Process Access: {error}")

        return len(errors) == 0, errors


class ErrorHandler:
    """
    Centralized error handling with recovery mechanisms.

    Provides graceful error handling and recovery strategies.
    """

    def __init__(self, log_path: Optional[Path] = None):
        """
        Initialize error handler.

        Args:
            log_path: Path to error log file
        """
        self.log_path = log_path or (Path(__file__).parent.parent / ".moai/logs/errors.json")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.error_records: List[ErrorRecord] = []

    def handle_error(
        self,
        error: Exception,
        severity: ErrorSeverity,
        category: ErrorCategory,
        context: Optional[Dict] = None,
        recovery_fn: Optional[Callable] = None
    ) -> bool:
        """
        Handle an error with optional recovery.

        Args:
            error: Exception object
            severity: Error severity level
            category: Error category
            context: Additional context information
            recovery_fn: Optional recovery function to attempt

        Returns:
            True if recovery successful or error handled, False otherwise
        """
        context = context or {}

        # Create error record
        record = ErrorRecord(
            timestamp=datetime.now().isoformat(),
            severity=severity,
            category=category,
            message=str(error),
            context=context,
            stack_trace=traceback.format_exc() if severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL] else None,
            recovery_attempted=recovery_fn is not None,
            recovery_successful=False,
            user_impact=self._assess_user_impact(severity, category)
        )

        # Attempt recovery if provided
        if recovery_fn:
            try:
                recovery_fn()
                record.recovery_successful = True
                print(f"✅ 복구 성공: {category.value} 오류 해결", file=sys.stderr)
            except Exception as recovery_error:
                print(f"❌ 복구 실패: {recovery_error}", file=sys.stderr)

        # Log error
        self.error_records.append(record)
        self._log_error(record)

        # Print user-friendly message
        self._print_error_message(record)

        return record.recovery_successful or severity in [ErrorSeverity.INFO, ErrorSeverity.WARNING]

    def _assess_user_impact(self, severity: ErrorSeverity, category: ErrorCategory) -> str:
        """Assess user impact of error."""
        if severity == ErrorSeverity.CRITICAL:
            return "서비스 중단 가능"
        elif severity == ErrorSeverity.ERROR:
            return "기능 제한적 사용 가능"
        elif severity == ErrorSeverity.WARNING:
            return "일부 기능 영향"
        else:
            return "영향 없음"

    def _log_error(self, record: ErrorRecord):
        """Log error to file."""
        try:
            # Load existing errors
            if self.log_path.exists():
                with open(self.log_path) as f:
                    errors = json.load(f)
            else:
                errors = []

            # Append new error
            errors.append(record.to_dict())

            # Keep only last 1000 errors
            if len(errors) > 1000:
                errors = errors[-1000:]

            # Save
            with open(self.log_path, 'w') as f:
                json.dump(errors, f, indent=2)

        except Exception as e:
            print(f"⚠️  Error logging failed: {e}", file=sys.stderr)

    def _print_error_message(self, record: ErrorRecord):
        """Print user-friendly error message."""
        severity_icons = {
            ErrorSeverity.INFO: "ℹ️",
            ErrorSeverity.WARNING: "⚠️",
            ErrorSeverity.ERROR: "❌",
            ErrorSeverity.CRITICAL: "🚨"
        }

        icon = severity_icons.get(record.severity, "❓")
        print(f"\n{icon} {record.severity.value.upper()}: {record.message}", file=sys.stderr)

        if record.user_impact:
            print(f"   영향: {record.user_impact}", file=sys.stderr)

        if record.recovery_attempted:
            status = "성공" if record.recovery_successful else "실패"
            print(f"   복구 시도: {status}", file=sys.stderr)

    def get_error_summary(self) -> Dict:
        """Get summary of errors."""
        return {
            "total_errors": len(self.error_records),
            "by_severity": {
                severity.value: sum(1 for r in self.error_records if r.severity == severity)
                for severity in ErrorSeverity
            },
            "by_category": {
                category.value: sum(1 for r in self.error_records if r.category == category)
                for category in ErrorCategory
            },
            "recovery_rate": (
                sum(1 for r in self.error_records if r.recovery_successful) /
                sum(1 for r in self.error_records if r.recovery_attempted)
                if sum(1 for r in self.error_records if r.recovery_attempted) > 0
                else 0
            )
        }


def main():
    """CLI for testing validation."""
    validator = SystemValidator()

    print("🔍 System Validation")
    print("=" * 60)

    valid, errors = validator.validate_all()

    if valid:
        print("✅ All validations passed")
        return 0
    else:
        print("❌ Validation failures:")
        for error in errors:
            print(f"   {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
