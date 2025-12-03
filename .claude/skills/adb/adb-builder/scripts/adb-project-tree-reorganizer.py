#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
adb-project-tree-reorganizer: Automated Project Structure Migration

Migrates existing adb-* skills to the new game-specific structure:
  - Analyzes current flat structure
  - Maps skills to target categories
  - Performs automated migration
  - Updates all references
  - Creates rollback points
  - Validates migration completeness

Modes:
  - dry-run: Analyze and plan migration without execution
  - execute: Perform actual migration with backup

Usage:
  # Dry-run (analysis only)
  uv run adb-project-tree-reorganizer.py \\
    --mode dry-run \\
    --target-structure game-specific \\
    --report json

  # Execute migration
  uv run adb-project-tree-reorganizer.py \\
    --mode execute \\
    --target-structure game-specific \\
    --create-backup \\
    --validate-references
"""

import json
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


# ============================================================================
# Constants & Enumerations
# ============================================================================

class MigrationMode(Enum):
    """Migration execution modes"""
    DRY_RUN = "dry-run"
    EXECUTE = "execute"


class SkillCategory(Enum):
    """Skill categories"""
    FOUNDATION = "adb-foundation"
    GAME = "adb-game"
    UTILITY = "adb-utility"
    BUILDER = "adb-builder"


SKILL_MAPPINGS = {
    # Foundation skills
    "adb-screen-detection": ("foundation", "Core screen detection"),
    "adb-navigation-base": ("foundation", "Navigation patterns"),
    "adb-uiautomator": ("foundation", "UI automation"),
    "adb-skill-generator": ("foundation", "Skill generation"),
    "adb-workflow-orchestrator": ("foundation", "Workflow coordination"),
    "adb-automation-coordinator": ("foundation", "Automation coordination"),

    # Game skills
    "adb-karrot": ("game", "Karrot game bot"),
    "adb-magisk": ("game", "Magisk tools"),
    "adb-magisk-installer": ("game", "Magisk installer"),

    # Utility skills
    "adb-bypass": ("utility", "App bypass tools"),

    # Builder (keeps at root level)
    "adb-builder": ("builder", "Builder meta-generation"),

    # moai domain (keeps in adb/)
    "moai-domain-adb": ("moai", "MoAI ADB domain"),
}


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class SkillMigration:
    """Represents a single skill migration"""
    skill_name: str
    current_path: str
    target_path: str
    category: str
    description: str
    status: str  # "pending", "completed", "failed", "skipped"
    error_message: Optional[str] = None


@dataclass
class MigrationPlan:
    """Complete migration plan"""
    timestamp: str
    mode: str
    target_structure: str
    total_skills: int
    skills_to_migrate: List[SkillMigration]
    foundation_skills: int
    game_skills: int
    utility_skills: int
    builder_skills: int
    moai_skills: int
    estimated_duration_minutes: float
    backups_created: List[str]
    references_updated: int
    validation_passed: bool
    messages: List[str]


# ============================================================================
# Reorganizer Engine
# ============================================================================

class ProjectTreeReorganizer:
    """Main reorganization engine"""

    def __init__(self, base_path: Path):
        """Initialize reorganizer"""
        self.base_path = Path(base_path)
        self.skills_path = self.base_path / ".claude" / "skills" / "adb"
        self.migrations: List[SkillMigration] = []
        self.messages: List[str] = []
        self.backups: List[str] = []

    def analyze(self) -> MigrationPlan:
        """Analyze current structure without making changes"""
        self.messages.append("🔍 Starting analysis of current structure...")

        # Discover all adb-* skills
        self._discover_skills()

        # Create migration plan
        plan = self._create_migration_plan()

        self.messages.append(f"✅ Analysis complete: {len(self.migrations)} skills found")
        return plan

    def execute_migration(self, plan: MigrationPlan, create_backup: bool = True,
                         validate_refs: bool = True) -> MigrationPlan:
        """Execute actual migration"""
        self.messages.append("🚀 Starting migration execution...")

        # Create backups if requested
        if create_backup:
            self._create_backups()

        # Execute migrations
        for migration in plan.skills_to_migrate:
            if migration.status != "pending":
                continue

            try:
                self._migrate_skill(migration)
                migration.status = "completed"
                self.messages.append(f"✅ Migrated: {migration.skill_name}")
            except Exception as e:
                migration.status = "failed"
                migration.error_message = str(e)
                self.messages.append(f"❌ Failed to migrate {migration.skill_name}: {str(e)}")

        # Update references if requested
        if validate_refs:
            self._update_references(plan)

        # Validate migration
        plan.validation_passed = self._validate_migration(plan)

        return plan

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _discover_skills(self):
        """Discover all adb-* skills in current structure"""
        if not self.skills_path.exists():
            self.messages.append(f"⚠️ Skills path not found: {self.skills_path}")
            return

        for item in self.skills_path.iterdir():
            if not item.is_dir():
                continue

            skill_name = item.name

            # Check if it's an adb-* skill
            if skill_name.startswith("adb-"):
                if skill_name in SKILL_MAPPINGS:
                    category, description = SKILL_MAPPINGS[skill_name]
                    target_path = self._get_target_path(skill_name, category)

                    migration = SkillMigration(
                        skill_name=skill_name,
                        current_path=str(item),
                        target_path=str(target_path),
                        category=category,
                        description=description,
                        status="pending"
                    )
                    self.migrations.append(migration)

    def _create_migration_plan(self) -> MigrationPlan:
        """Create comprehensive migration plan"""
        # Count by category
        foundation = sum(1 for m in self.migrations if m.category == "foundation")
        games = sum(1 for m in self.migrations if m.category == "game")
        utilities = sum(1 for m in self.migrations if m.category == "utility")
        builders = sum(1 for m in self.migrations if m.category == "builder")
        moai = sum(1 for m in self.migrations if m.category == "moai")

        # Estimate duration (5 minutes per skill + 10 minutes overhead)
        estimated_duration = (len(self.migrations) * 5) + 10

        return MigrationPlan(
            timestamp=datetime.now().isoformat(),
            mode="dry-run",
            target_structure="game-specific",
            total_skills=len(self.migrations),
            skills_to_migrate=self.migrations,
            foundation_skills=foundation,
            game_skills=games,
            utility_skills=utilities,
            builder_skills=builders,
            moai_skills=moai,
            estimated_duration_minutes=estimated_duration,
            backups_created=[],
            references_updated=0,
            validation_passed=False,
            messages=self.messages
        )

    def _get_target_path(self, skill_name: str, category: str) -> Path:
        """Get target path for skill"""
        if category == "foundation":
            return self.skills_path / "adb-foundation" / skill_name
        elif category == "game":
            # Extract game name from skill (e.g., adb-karrot → adb-game-karrot)
            game_name = skill_name.replace("adb-", "")
            return self.skills_path / f"adb-game-{game_name}" / skill_name
        elif category == "utility":
            return self.skills_path / "adb-utility" / skill_name
        elif category == "builder":
            # Builder stays at root level
            return self.skills_path / skill_name
        else:  # moai
            # moai stays at root level
            return self.skills_path / skill_name

    def _migrate_skill(self, migration: SkillMigration):
        """Migrate a single skill"""
        current = Path(migration.current_path)
        target = Path(migration.target_path)

        if not current.exists():
            raise Exception(f"Source path does not exist: {current}")

        # Create target directory structure
        target.parent.mkdir(parents=True, exist_ok=True)

        # Move skill
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(current), str(target))

    def _create_backups(self):
        """Create backups before migration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.skills_path.parent / f"backup_{timestamp}"

        try:
            backup_path.mkdir(parents=True, exist_ok=True)

            # Backup skills directory
            skills_backup = backup_path / "adb_backup"
            if self.skills_path.exists():
                shutil.copytree(str(self.skills_path), str(skills_backup))

            self.backups.append(str(skills_backup))
            self.messages.append(f"✅ Backup created: {skills_backup}")

        except Exception as e:
            self.messages.append(f"⚠️ Backup failed: {str(e)}")

    def _update_references(self, plan: MigrationPlan):
        """Update references in documentation and config files"""
        references_updated = 0

        # Update SKILL.md files
        for migration in plan.skills_to_migrate:
            if migration.status != "completed":
                continue

            skill_md = Path(migration.target_path) / "SKILL.md"
            if skill_md.exists():
                try:
                    content = skill_md.read_text()
                    # Update any relative paths if needed
                    updated_content = content.replace(
                        migration.current_path,
                        migration.target_path
                    )
                    if updated_content != content:
                        skill_md.write_text(updated_content)
                        references_updated += 1
                except Exception as e:
                    self.messages.append(f"⚠️ Could not update {skill_md}: {str(e)}")

        plan.references_updated = references_updated
        if references_updated > 0:
            self.messages.append(f"✅ Updated {references_updated} references")

    def _validate_migration(self, plan: MigrationPlan) -> bool:
        """Validate migration completeness"""
        completed = sum(1 for m in plan.skills_to_migrate if m.status == "completed")
        total = len(plan.skills_to_migrate)

        if completed == total:
            self.messages.append(f"✅ Migration validation passed: {completed}/{total} skills")
            return True
        else:
            self.messages.append(f"⚠️ Migration incomplete: {completed}/{total} skills")
            return False


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Project Tree Reorganizer - Migrate to game-specific structure"
    )
    parser.add_argument("--mode", required=True, choices=["dry-run", "execute"],
                       help="Execution mode")
    parser.add_argument("--target-structure", default="game-specific",
                       help="Target structure type")
    parser.add_argument("--base-path", default=".",
                       help="Base project path")
    parser.add_argument("--create-backup", action="store_true",
                       help="Create backups before migration")
    parser.add_argument("--validate-references", action="store_true",
                       help="Update references after migration")
    parser.add_argument("--report-format", default="json",
                       help="Report format (json, text)")

    args = parser.parse_args()

    try:
        reorganizer = ProjectTreeReorganizer(args.base_path)

        # Analyze first
        plan = reorganizer.analyze()

        # Execute if not dry-run
        if args.mode == "execute":
            plan.mode = "execute"
            plan = reorganizer.execute_migration(
                plan,
                create_backup=args.create_backup,
                validate_refs=args.validate_references
            )

        # Output report
        if args.report_format == "json":
            print(json.dumps(asdict(plan), indent=2))
        else:
            _print_text_report(plan)

        sys.exit(0 if plan.validation_passed else 1)

    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def _print_text_report(plan: MigrationPlan):
    """Print text format report"""
    print("\n" + "=" * 70)
    print(f"📊 Project Tree Reorganization Report")
    print("=" * 70)
    print(f"Mode: {plan.mode}")
    print(f"Target Structure: {plan.target_structure}")
    print(f"Timestamp: {plan.timestamp}")
    print("\n" + "-" * 70)
    print(f"📈 Statistics:")
    print(f"  Total skills to migrate: {plan.total_skills}")
    print(f"    - Foundation: {plan.foundation_skills}")
    print(f"    - Games: {plan.game_skills}")
    print(f"    - Utilities: {plan.utility_skills}")
    print(f"    - Builder: {plan.builder_skills}")
    print(f"    - MoAI: {plan.moai_skills}")
    print(f"  Estimated duration: {plan.estimated_duration_minutes:.0f} minutes")
    print(f"  References updated: {plan.references_updated}")
    print(f"  Validation: {'✅ PASSED' if plan.validation_passed else '❌ FAILED'}")

    if plan.messages:
        print(f"\n" + "-" * 70)
        print(f"📝 Messages:")
        for msg in plan.messages:
            print(f"  {msg}")

    if plan.skills_to_migrate:
        print(f"\n" + "-" * 70)
        print(f"🔄 Migrations:")
        for migration in plan.skills_to_migrate:
            status_symbol = "✅" if migration.status == "completed" else \
                           "⏳" if migration.status == "pending" else \
                           "❌" if migration.status == "failed" else "⏭️"
            print(f"  {status_symbol} {migration.skill_name} → {migration.category}")
            if migration.error_message:
                print(f"     Error: {migration.error_message}")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
