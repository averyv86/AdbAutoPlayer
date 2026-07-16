#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
adb-builder-workflows: TOON Workflow Generator for Game Skills

Generates comprehensive TOON workflow definitions for game-specific automation.

Supported games:
  - afk-journey: AFK Journey game automation
  - guitar-girl: Guitar Girl game automation
  - karrot: Karrot marketplace app automation
  - magisk: Magisk root management automation

Usage:
  # Generate AFK Journey battle automation workflow
  uv run adb-builder-workflows.py \
    --game afk-journey \
    --workflow-type battle-automation \
    --output-format yaml

  # Generate Guitar Girl music gameplay workflow
  uv run adb-builder-workflows.py \
    --game guitar-girl \
    --workflow-type music-gameplay \
    --output-format yaml

  # List available workflows for a game
  uv run adb-builder-workflows.py \
    --game afk-journey \
    --list-workflows
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from enum import Enum
import yaml


# ============================================================================
# Constants & Enumerations
# ============================================================================

class GameType(Enum):
    """Supported games"""
    AFK_JOURNEY = "afk-journey"
    GUITAR_GIRL = "guitar-girl"
    KARROT = "karrot"
    MAGISK = "magisk"


class WorkflowType(Enum):
    """Workflow types"""
    BATTLE = "battle-automation"
    QUEST = "quest-automation"
    ARENA = "arena-automation"
    LOGIN = "login-automation"
    MUSIC = "music-gameplay"
    INSTALLER = "installer-automation"


WORKFLOW_TEMPLATES = {
    "afk-journey": {
        "battle-automation": {
            "name": "AFK Journey Battle Automation",
            "description": "Automate battle execution with team formation and skill usage",
            "difficulty": "intermediate",
            "parameters": {
                "device": "127.0.0.1:5555",
                "stage_number": 1,
                "max_battles": 10,
                "auto_formation": True,
                "skill_priority": "balanced",
            }
        },
        "quest-automation": {
            "name": "AFK Journey Quest Automation",
            "description": "Automated quest completion with state tracking",
            "difficulty": "intermediate",
            "parameters": {
                "device": "127.0.0.1:5555",
                "quest_type": "main",
                "auto_equip": True,
                "claim_rewards": True,
            }
        },
        "arena-automation": {
            "name": "AFK Journey Arena Automation",
            "description": "Automated arena battles with opponent analysis",
            "difficulty": "advanced",
            "parameters": {
                "device": "127.0.0.1:5555",
                "opponent_strategy": "strongest",
                "max_attempts": 5,
                "claim_rewards": True,
            }
        },
    },
    "guitar-girl": {
        "music-gameplay": {
            "name": "Guitar Girl Music Gameplay Automation",
            "description": "Automate music gameplay with note detection and rhythm timing",
            "difficulty": "advanced",
            "parameters": {
                "device": "127.0.0.1:5555",
                "difficulty_level": "normal",
                "song_pattern": "auto-detect",
                "timing_tolerance": 50,
                "performance_optimization": True,
            }
        },
    },
    "karrot": {
        "login-automation": {
            "name": "Karrot App Login Automation",
            "description": "Automate login flow to Karrot (당근마켓) app with 2FA support",
            "difficulty": "intermediate",
            "parameters": {
                "device": "127.0.0.1:5555",
                "phone_number": "",
                "timeout": 60,
                "wait_for_sms": False,
                "verification_code": "",
            }
        },
    },
    "magisk": {
        "installer-automation": {
            "name": "Magisk Root Installation Automation",
            "description": "Automate Magisk installation with module management",
            "difficulty": "advanced",
            "parameters": {
                "device": "127.0.0.1:5555",
                "auto_mount": True,
                "safety_mode": True,
                "module_list": "",
            }
        },
    },
}


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class WorkflowParameter:
    """Workflow parameter definition"""
    name: str
    type_: str
    default: Any
    description: str


@dataclass
class WorkflowPhase:
    """Workflow phase definition"""
    id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]


@dataclass
class WorkflowDefinition:
    """Complete TOON workflow definition"""
    name: str
    description: str
    version: str
    game: str
    workflow_type: str
    difficulty: str
    parameters: Dict[str, Any]
    phases: List[WorkflowPhase]
    validation: List[Dict[str, Any]]
    recovery: List[Dict[str, Any]]
    outputs: List[Dict[str, str]]


@dataclass
class GenerationReport:
    """Workflow generation report"""
    timestamp: str
    game: str
    workflow_type: str
    generated_file: str
    file_size: int
    phase_count: int
    step_count: int
    success: bool
    messages: List[str]


# ============================================================================
# TOON Workflow Generator
# ============================================================================

class TOONWorkflowGenerator:
    """Generates TOON workflow definitions for games"""

    def __init__(self, game: str):
        """Initialize generator for specific game"""
        self.game = game
        self.templates = WORKFLOW_TEMPLATES.get(game, {})
        self.messages: List[str] = []

    def generate_workflow(self, workflow_type: str) -> Optional[WorkflowDefinition]:
        """Generate workflow definition"""
        if workflow_type not in self.templates:
            self.messages.append(f"❌ Workflow type '{workflow_type}' not supported for {self.game}")
            return None

        template = self.templates[workflow_type]
        self.messages.append(f"🔨 Generating {workflow_type} workflow for {self.game}")

        # Generate phases based on game and workflow type
        phases = self._generate_phases(workflow_type)

        workflow = WorkflowDefinition(
            name=template["name"],
            description=template["description"],
            version="1.0.0",
            game=self.game,
            workflow_type=workflow_type,
            difficulty=template["difficulty"],
            parameters=template["parameters"],
            phases=phases,
            validation=self._generate_validation(len(phases)),
            recovery=self._generate_recovery(),
            outputs=self._generate_outputs(workflow_type)
        )

        self.messages.append(f"✅ Generated {len(phases)} phases with {sum(len(p.steps) for p in phases)} steps")
        return workflow

    def _generate_phases(self, workflow_type: str) -> List[WorkflowPhase]:
        """Generate workflow phases based on type"""
        phases = []

        if self.game == "afk-journey":
            if workflow_type == "battle-automation":
                phases = [
                    self._create_phase("prepare_team", "Prepare Battle Team", "Setup team formation and equipment", 4),
                    self._create_phase("enter_battle", "Enter Battle", "Navigate to battle screen", 3),
                    self._create_phase("execute_battle", "Execute Battle", "Execute battle with skill usage", 6),
                    self._create_phase("collect_rewards", "Collect Rewards", "Claim battle rewards", 3),
                ]
            elif workflow_type == "quest-automation":
                phases = [
                    self._create_phase("select_quest", "Select Quest", "Choose quest objective", 3),
                    self._create_phase("travel_map", "Travel Map", "Navigate to quest location", 4),
                    self._create_phase("complete_objective", "Complete Objective", "Execute quest tasks", 5),
                    self._create_phase("return_base", "Return to Base", "Return and claim rewards", 3),
                ]
            elif workflow_type == "arena-automation":
                phases = [
                    self._create_phase("analyze_opponents", "Analyze Opponents", "Scan opponent formations", 4),
                    self._create_phase("select_formation", "Select Formation", "Choose optimal team formation", 3),
                    self._create_phase("battle_opponent", "Battle Opponent", "Execute arena battle", 5),
                    self._create_phase("claim_ranking_rewards", "Claim Rewards", "Get arena rewards", 2),
                ]

        elif self.game == "guitar-girl":
            if workflow_type == "music-gameplay":
                phases = [
                    self._create_phase("select_song", "Select Song", "Choose music track", 3),
                    self._create_phase("detect_notes", "Detect Notes", "Analyze note patterns", 4),
                    self._create_phase("play_song", "Play Song", "Execute note hits with timing", 7),
                    self._create_phase("score_calculation", "Calculate Score", "Determine performance rating", 2),
                ]

        elif self.game == "karrot":
            if workflow_type == "login-automation":
                phases = [
                    self._create_phase("launch_app", "Launch Karrot App", "Start the Karrot application", 4),
                    self._create_phase("enter_credentials", "Enter Credentials", "Input phone number", 4),
                    self._create_phase("wait_verification", "Wait Verification", "Handle 2FA verification", 4),
                    self._create_phase("enter_verification", "Enter Verification Code", "Input 2FA code", 3),
                    self._create_phase("complete_login", "Complete Login", "Verify successful login", 3),
                ]

        elif self.game == "magisk":
            if workflow_type == "installer-automation":
                phases = [
                    self._create_phase("device_check", "Check Device State", "Verify device and permissions", 4),
                    self._create_phase("mount_system", "Mount System", "Prepare system partition", 3),
                    self._create_phase("install_root", "Install Root", "Execute Magisk installation", 5),
                    self._create_phase("module_management", "Module Management", "Install required modules", 4),
                    self._create_phase("verify_installation", "Verify Installation", "Confirm successful installation", 3),
                ]

        return phases

    def _create_phase(self, phase_id: str, name: str, description: str, step_count: int) -> WorkflowPhase:
        """Create a workflow phase with steps"""
        steps = []
        for i in range(step_count):
            step_id = f"{phase_id}_step{i+1}"
            steps.append({
                "id": step_id,
                "name": f"{name} - Step {i+1}",
                "action": "adb-automation",
                "params": {
                    "device": "{{ device }}",
                    "timeout": 30,
                },
                "on_success": "continue",
                "on_failure": "continue" if i < step_count - 1 else "abort"
            })

        return WorkflowPhase(
            id=phase_id,
            name=name,
            description=description,
            steps=steps
        )

    def _generate_validation(self, phase_count: int) -> List[Dict[str, Any]]:
        """Generate validation rules"""
        validation = []
        for i in range(phase_count):
            validation.append({
                "phase": f"phase_{i+1}",
                "condition": f"phase_{i+1}_complete == true",
                "on_failure": "continue" if i < phase_count - 1 else "abort"
            })
        return validation

    def _generate_recovery(self) -> List[Dict[str, Any]]:
        """Generate recovery strategies"""
        return [
            {
                "on_error": "any",
                "action": "retry",
                "max_attempts": 3
            },
            {
                "on_error": "timeout",
                "action": "reset_and_retry",
                "max_attempts": 2
            },
            {
                "on_error": "device_disconnected",
                "action": "abort",
                "max_attempts": 1
            }
        ]

    def _generate_outputs(self, workflow_type: str) -> List[Dict[str, str]]:
        """Generate output specifications"""
        return [
            {
                "name": f"{workflow_type}_status",
                "format": "json",
                "description": "Workflow execution status"
            },
            {
                "name": f"{workflow_type}_log",
                "format": "text",
                "description": "Detailed execution log"
            },
            {
                "name": f"{workflow_type}_metrics",
                "format": "table",
                "description": "Performance metrics"
            }
        ]

    def save_workflow(self, workflow: WorkflowDefinition, output_path: Path) -> bool:
        """Save workflow to YAML file"""
        try:
            # Convert to dict with proper formatting
            workflow_dict = {
                "name": workflow.name,
                "description": workflow.description,
                "version": workflow.version,
                "metadata": {
                    "game": workflow.game,
                    "workflow_type": workflow.workflow_type,
                    "difficulty": workflow.difficulty,
                },
                "parameters": workflow.parameters,
                "phases": [
                    {
                        "id": phase.id,
                        "name": phase.name,
                        "description": phase.description,
                        "steps": phase.steps
                    }
                    for phase in workflow.phases
                ],
                "validation": workflow.validation,
                "recovery": workflow.recovery,
                "outputs": workflow.outputs,
            }

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write YAML
            with open(output_path, 'w') as f:
                yaml.dump(workflow_dict, f, default_flow_style=False, sort_keys=False)

            self.messages.append(f"✅ Workflow saved to {output_path}")
            return True

        except Exception as e:
            self.messages.append(f"❌ Failed to save workflow: {str(e)}")
            return False


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="TOON Workflow Generator for Game Skills"
    )
    parser.add_argument("--game", required=True, choices=["afk-journey", "guitar-girl", "karrot", "magisk"],
                       help="Target game")
    parser.add_argument("--workflow-type", help="Workflow type to generate")
    parser.add_argument("--output-format", default="yaml", choices=["yaml", "json"],
                       help="Output format")
    parser.add_argument("--output-path", help="Output file path")
    parser.add_argument("--skills-dir", default="./.claude/skills/adb",
                       help="Skills directory path")
    parser.add_argument("--list-workflows", action="store_true",
                       help="List available workflows for game")

    args = parser.parse_args()

    try:
        generator = TOONWorkflowGenerator(args.game)

        # List workflows if requested
        if args.list_workflows:
            print(f"\n📋 Available workflows for {args.game}:")
            templates = WORKFLOW_TEMPLATES.get(args.game, {})
            for wf_type, config in templates.items():
                print(f"  • {wf_type}: {config.get('name', 'N/A')}")
            print()
            return 0

        # Generate workflow
        if not args.workflow_type:
            print(f"❌ Error: --workflow-type required")
            return 1

        workflow = generator.generate_workflow(args.workflow_type)
        if not workflow:
            print(f"❌ Failed to generate workflow")
            for msg in generator.messages:
                print(f"  {msg}")
            return 1

        # Determine output path
        if args.output_path:
            output_path = Path(args.output_path)
        else:
            # Use default path based on game
            game_skill_name = f"adb-game-{args.game}" if args.game != "karrot" else "adb-game-karrot"
            output_path = Path(args.skills_dir) / game_skill_name / f"adb-{args.game}" / "workflows" / f"{args.workflow_type}.toon"

        # Save workflow
        if not generator.save_workflow(workflow, output_path):
            return 1

        # Generate report
        total_steps = sum(len(phase.steps) for phase in workflow.phases)
        report = GenerationReport(
            timestamp=datetime.now().isoformat(),
            game=args.game,
            workflow_type=args.workflow_type,
            generated_file=str(output_path),
            file_size=output_path.stat().st_size if output_path.exists() else 0,
            phase_count=len(workflow.phases),
            step_count=total_steps,
            success=True,
            messages=generator.messages
        )

        # Output report
        if args.output_format == "json":
            print(json.dumps(asdict(report), indent=2))
        else:
            print(f"\n✅ Workflow Generation Complete!")
            print(f"  Game: {report.game}")
            print(f"  Workflow Type: {report.workflow_type}")
            print(f"  Phases: {report.phase_count}")
            print(f"  Steps: {report.step_count}")
            print(f"  File: {report.generated_file}")
            print(f"  Size: {report.file_size} bytes\n")

        return 0

    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
