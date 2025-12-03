"""Magisk Installation Orchestrator Package.

Complete 7-phase Magisk installation workflow with orchestration,
error handling, and state verification.

Author: MoAI-ADK
Version: 1.0.0
"""

from .adb_magisk_orchestrator import (
    MagiskOrchestrator,
    PhaseStatus,
    PhaseResult,
    InstallationResult,
    StateVerifier
)

__all__ = [
    "MagiskOrchestrator",
    "PhaseStatus",
    "PhaseResult",
    "InstallationResult",
    "StateVerifier",
]

__version__ = "1.0.0"
__author__ = "MoAI-ADK"
