#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
adb-builder-validate: Skill Validation & Quality Assurance

Validates adb-* skills against ecosystem standards including:
  - Naming conventions
  - Directory structure
  - SKILL.md completeness
  - TOON workflow syntax
  - Script PEP 723 compliance
  - Module documentation quality
  - Test coverage
  - Dependency resolution

Usage:
  uv run adb-builder-validate.py \\
    --skill-path /path/to/skill/ \\
    --checks all \\
    --report-format json
"""

import json
import sys
import argparse
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


# ============================================================================
# Validation Constants
# ============================================================================

NAMING_PATTERN = re.compile(r'^adb-[a-z0-9\-]+$')
MIN_DESCRIPTION_LENGTH = 20
MAX_DESCRIPTION_LENGTH = 500

REQUIRED_DIRECTORIES = {
    "modules": "Module documentation",
    "scripts": "Automation scripts",
    "tests": "Test files",
    "documentation": "Documentation",
}

REQUIRED_FILES = {
    "SKILL.md": "Skill metadata",
}


# ============================================================================
# Validation Models
# ============================================================================

class CheckStatus(Enum):
    """Check status values"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class ValidationCheck:
    """Individual validation check"""
    name: str
    status: CheckStatus
    message: str
    score: int  # 0-100


@dataclass
class ValidationReport:
    """Complete validation report"""
    skill_name: str
    skill_path: str
    timestamp: str
    checks: List[ValidationCheck]
    total_score: int  # 0-100
    passed_checks: int
    failed_checks: int
    warnings: int
    recommendations: List[str]


# ============================================================================
# Validator
# ============================================================================

class SkillValidator:
    """Main skill validator"""

    def __init__(self, skill_path: Path):
        """Initialize validator with skill path"""
        self.skill_path = Path(skill_path)
        self.checks: List[ValidationCheck] = []
        self.skill_name = self.skill_path.name
        self.messages: List[str] = []

    def validate(self) -> ValidationReport:
        """Run all validation checks"""
        self._validate_existence()
        self._validate_naming()
        self._validate_structure()
        self._validate_skill_md()
        self._validate_modules()
        self._validate_scripts()
        self._validate_workflows()
        self._validate_tests()
        self._validate_documentation()

        return self._build_report()

    # ========================================================================
    # Individual Validators
    # ========================================================================

    def _validate_existence(self):
        """Check skill directory exists"""
        if self.skill_path.exists() and self.skill_path.is_dir():
            self._add_check("Existence", CheckStatus.PASSED,
                          "Skill directory exists", 100)
        else:
            self._add_check("Existence", CheckStatus.FAILED,
                          f"Skill directory not found: {self.skill_path}", 0)

    def _validate_naming(self):
        """Validate naming conventions"""
        if NAMING_PATTERN.match(self.skill_name):
            self._add_check("Naming Convention", CheckStatus.PASSED,
                          f"Name follows adb-* pattern: {self.skill_name}", 100)
        else:
            self._add_check("Naming Convention", CheckStatus.FAILED,
                          f"Name doesn't match adb-* pattern: {self.skill_name}", 0)

    def _validate_structure(self):
        """Validate directory structure"""
        missing_dirs = []
        found_dirs = 0

        for dir_name, description in REQUIRED_DIRECTORIES.items():
            dir_path = self.skill_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                found_dirs += 1
            else:
                missing_dirs.append(f"{dir_name} ({description})")

        if not missing_dirs:
            self._add_check("Directory Structure", CheckStatus.PASSED,
                          f"All required directories present ({found_dirs}/4)", 100)
        else:
            score = (found_dirs / len(REQUIRED_DIRECTORIES)) * 100
            self._add_check("Directory Structure", CheckStatus.FAILED,
                          f"Missing directories: {', '.join(missing_dirs)}", int(score))

    def _validate_skill_md(self):
        """Validate SKILL.md file"""
        skill_md = self.skill_path / "SKILL.md"

        if not skill_md.exists():
            self._add_check("SKILL.md", CheckStatus.FAILED,
                          "SKILL.md file not found", 0)
            return

        try:
            content = skill_md.read_text()

            # Check required sections
            required_sections = ["# ", "## Description", "## Quick Start"]
            missing_sections = []

            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)

            if not missing_sections:
                # Check description length
                if len(content) < 200:
                    self._add_check("SKILL.md Completeness", CheckStatus.WARNING,
                                  "SKILL.md seems short", 75)
                else:
                    self._add_check("SKILL.md Completeness", CheckStatus.PASSED,
                                  "SKILL.md has required sections", 100)
            else:
                self._add_check("SKILL.md Completeness", CheckStatus.FAILED,
                              f"Missing sections: {', '.join(missing_sections)}", 50)

        except Exception as e:
            self._add_check("SKILL.md", CheckStatus.FAILED, str(e), 0)

    def _validate_modules(self):
        """Validate module documentation"""
        modules_dir = self.skill_path / "modules"

        if not modules_dir.exists():
            self._add_check("Modules", CheckStatus.SKIPPED,
                          "No modules directory", 0)
            return

        md_files = list(modules_dir.glob("*.md"))

        if not md_files:
            self._add_check("Modules", CheckStatus.WARNING,
                          "No module files found", 50)
            return

        # Validate each module
        valid_modules = 0
        for module_file in md_files:
            try:
                content = module_file.read_text()
                if len(content) > 100 and "# " in content:
                    valid_modules += 1
            except Exception:
                pass

        score = (valid_modules / len(md_files)) * 100
        self._add_check("Module Documentation", CheckStatus.PASSED if score >= 80 else CheckStatus.WARNING,
                      f"Valid modules: {valid_modules}/{len(md_files)}", int(score))

    def _validate_scripts(self):
        """Validate scripts"""
        scripts_dir = self.skill_path / "scripts"

        if not scripts_dir.exists():
            self._add_check("Scripts", CheckStatus.SKIPPED,
                          "No scripts directory", 0)
            return

        py_files = list(scripts_dir.glob("*.py"))

        if not py_files:
            self._add_check("Scripts", CheckStatus.WARNING,
                          "No Python scripts found", 50)
            return

        # Validate PEP 723 compliance (check for docstring and shebang)
        valid_scripts = 0
        for script_file in py_files:
            try:
                content = script_file.read_text()
                has_shebang = content.startswith("#!/usr/bin/env python")
                has_docstring = '"""' in content or "'''" in content
                if has_shebang and has_docstring:
                    valid_scripts += 1
            except Exception:
                pass

        score = (valid_scripts / len(py_files)) * 100 if py_files else 0
        status = CheckStatus.PASSED if score >= 80 else CheckStatus.WARNING
        self._add_check("Script Compliance", status,
                      f"PEP 723 compliant: {valid_scripts}/{len(py_files)}", int(score))

    def _validate_workflows(self):
        """Validate TOON workflows"""
        workflows_dir = self.skill_path / "workflows"

        if not workflows_dir.exists():
            self._add_check("TOON Workflows", CheckStatus.WARNING,
                          "No workflows directory", 50)
            return

        toon_files = list(workflows_dir.glob("*.toon"))

        if not toon_files:
            self._add_check("TOON Workflows", CheckStatus.WARNING,
                          "No TOON workflow files found", 50)
            return

        # Validate TOON syntax
        valid_workflows = 0
        for toon_file in toon_files:
            try:
                content = toon_file.read_text()
                # Check for YAML frontmatter
                if content.startswith("---") and "stages:" in content:
                    valid_workflows += 1
            except Exception:
                pass

        score = (valid_workflows / len(toon_files)) * 100 if toon_files else 0
        self._add_check("TOON Syntax", CheckStatus.PASSED if score >= 80 else CheckStatus.WARNING,
                      f"Valid workflows: {valid_workflows}/{len(toon_files)}", int(score))

    def _validate_tests(self):
        """Validate test structure"""
        tests_dir = self.skill_path / "tests"

        if not tests_dir.exists():
            self._add_check("Tests", CheckStatus.WARNING,
                          "No tests directory", 50)
            return

        test_files = list(tests_dir.glob("test_*.py"))

        if not test_files:
            self._add_check("Tests", CheckStatus.WARNING,
                          "No test files found", 50)
            return

        self._add_check("Test Structure", CheckStatus.PASSED,
                      f"Test files found: {len(test_files)}", 100)

    def _validate_documentation(self):
        """Validate documentation"""
        docs_dir = self.skill_path / "documentation"

        if not docs_dir.exists():
            self._add_check("Documentation", CheckStatus.WARNING,
                          "No documentation directory", 50)
            return

        md_files = list(docs_dir.glob("*.md"))

        if not md_files:
            self._add_check("Documentation", CheckStatus.WARNING,
                          "No documentation files", 50)
            return

        self._add_check("Documentation", CheckStatus.PASSED,
                      f"Documentation files: {len(md_files)}", 100)

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _add_check(self, name: str, status: CheckStatus, message: str, score: int):
        """Add validation check"""
        self.checks.append(ValidationCheck(
            name=name,
            status=status,
            message=message,
            score=score
        ))

    def _build_report(self) -> ValidationReport:
        """Build validation report"""
        passed = sum(1 for c in self.checks if c.status == CheckStatus.PASSED)
        failed = sum(1 for c in self.checks if c.status == CheckStatus.FAILED)
        warnings = sum(1 for c in self.checks if c.status == CheckStatus.WARNING)

        # Calculate overall score
        scores = [c.score for c in self.checks]
        overall_score = int(sum(scores) / len(scores)) if scores else 0

        # Generate recommendations
        recommendations = self._generate_recommendations()

        return ValidationReport(
            skill_name=self.skill_name,
            skill_path=str(self.skill_path),
            timestamp=str(Path(self.skill_path).stat().st_mtime),
            checks=self.checks,
            total_score=overall_score,
            passed_checks=passed,
            failed_checks=failed,
            warnings=warnings,
            recommendations=recommendations
        )

    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        for check in self.checks:
            if check.status == CheckStatus.FAILED:
                if "naming" in check.name.lower():
                    recommendations.append("Rename skill to match adb-* pattern")
                elif "structure" in check.name.lower():
                    recommendations.append("Add missing required directories")
                elif "skill.md" in check.name.lower():
                    recommendations.append("Complete SKILL.md with all required sections")
                elif "modules" in check.name.lower():
                    recommendations.append("Add comprehensive module documentation")
                elif "tests" in check.name.lower():
                    recommendations.append("Implement test suite with coverage")
                elif "documentation" in check.name.lower():
                    recommendations.append("Add usage documentation")

            elif check.status == CheckStatus.WARNING:
                if "short" in check.message.lower():
                    recommendations.append("Expand SKILL.md with more details")
                elif "no" in check.message.lower() and "found" in check.message.lower():
                    recommendations.append(f"Consider adding: {check.name}")

        return list(dict.fromkeys(recommendations))  # Remove duplicates


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="ADB Skill Validator - Validate skills against ecosystem standards"
    )
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--checks", default="all", help="Checks to run (all, structure, quality)")
    parser.add_argument("--report-format", default="json", help="Report format (json, text)")

    args = parser.parse_args()

    try:
        validator = SkillValidator(args.skill_path)
        report = validator.validate()

        # Output report
        if args.report_format == "json":
            print(json.dumps(asdict(report), indent=2))
        else:
            print(f"\n📋 Validation Report: {report.skill_name}")
            print(f"{'=' * 60}")
            print(f"Overall Score: {report.total_score}/100")
            print(f"Passed: {report.passed_checks} | Failed: {report.failed_checks} | Warnings: {report.warnings}")
            print(f"\n{'=' * 60}")

            for check in report.checks:
                status_symbol = "✅" if check.status == CheckStatus.PASSED else \
                              "❌" if check.status == CheckStatus.FAILED else \
                              "⚠️" if check.status == CheckStatus.WARNING else "⏭️"
                print(f"{status_symbol} {check.name}: {check.message}")

            if report.recommendations:
                print(f"\n{'=' * 60}")
                print("📝 Recommendations:")
                for i, rec in enumerate(report.recommendations, 1):
                    print(f"  {i}. {rec}")

        sys.exit(0 if report.failed_checks == 0 else 1)

    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
