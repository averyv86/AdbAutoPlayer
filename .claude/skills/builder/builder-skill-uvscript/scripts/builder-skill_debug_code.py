#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
# ]
# ///

"""
AI-Powered Debug Helper

Automated debugging workflow with AI-powered error diagnosis, pattern recognition,
and fix suggestions. Supports multiple languages and provides actionable debugging steps.

Usage:
    uv run debug_helper.py --error "AttributeError: 'NoneType' object has no attribute 'name'"
    uv run debug_helper.py --stack-trace error.log --language python
    uv run debug_helper.py --code src/user_service.py --json
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import click


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class ErrorPattern:
    """Represents a known error pattern."""

    name: str
    pattern: str
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    common_causes: list[str]


@dataclass
class FixSuggestion:
    """Represents a suggested fix for an error."""

    priority: int
    solution: str
    code: str | None
    explanation: str
    file_location: str | None = None


@dataclass
class DiagnosisResult:
    """Complete diagnosis result."""

    error_type: str
    severity: Literal["low", "medium", "high", "critical"]
    diagnosis: dict[str, str]
    suggested_fixes: list[FixSuggestion]
    debugging_steps: list[str]
    prevention: str
    context: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Error Pattern Database
# ============================================================================


ERROR_PATTERNS: dict[str, ErrorPattern] = {
    "AttributeError": ErrorPattern(
        name="AttributeError",
        pattern=r"AttributeError: '(\w+)' object has no attribute '(\w+)'",
        severity="medium",
        description="Attempting to access an attribute that doesn't exist",
        common_causes=[
            "Accessing attribute on None object",
            "Typo in attribute name",
            "Object not initialized properly",
            "Wrong object type",
        ],
    ),
    "TypeError": ErrorPattern(
        name="TypeError",
        pattern=r"TypeError: (.+)",
        severity="medium",
        description="Operation performed on incompatible types",
        common_causes=[
            "Passing wrong argument types",
            "Missing required arguments",
            "Calling non-callable object",
            "Incorrect operator usage",
        ],
    ),
    "KeyError": ErrorPattern(
        name="KeyError",
        pattern=r"KeyError: '(.+)'",
        severity="low",
        description="Dictionary key not found",
        common_causes=[
            "Key doesn't exist in dictionary",
            "Typo in key name",
            "Data structure mismatch",
            "Missing validation",
        ],
    ),
    "IndexError": ErrorPattern(
        name="IndexError",
        pattern=r"IndexError: (.+)",
        severity="low",
        description="List index out of range",
        common_causes=[
            "Empty list access",
            "Index beyond list length",
            "Off-by-one error",
            "Loop boundary issue",
        ],
    ),
    "ValueError": ErrorPattern(
        name="ValueError",
        pattern=r"ValueError: (.+)",
        severity="medium",
        description="Invalid value for operation",
        common_causes=[
            "Invalid conversion",
            "Out of range value",
            "Malformed input",
            "Type conversion failure",
        ],
    ),
    "ImportError": ErrorPattern(
        name="ImportError",
        pattern=r"ImportError: (.+)|ModuleNotFoundError: (.+)",
        severity="high",
        description="Module or package import failed",
        common_causes=[
            "Package not installed",
            "Circular import",
            "Wrong module path",
            "Missing dependencies",
        ],
    ),
}


# ============================================================================
# Error Analysis Engine
# ============================================================================


class ErrorAnalyzer:
    """AI-powered error analysis engine."""

    def __init__(self, language: str = "python"):
        self.language = language
        self.patterns = ERROR_PATTERNS

    def analyze_error(self, error_text: str) -> DiagnosisResult:
        """Analyze error text and generate diagnosis."""
        # Detect error type
        error_type, match = self._detect_error_type(error_text)
        pattern = self.patterns.get(error_type)

        if not pattern:
            return self._generate_generic_diagnosis(error_text)

        # Extract details from error
        details = self._extract_error_details(error_text, match)

        # Generate diagnosis
        diagnosis = {
            "root_cause": self._identify_root_cause(error_type, details),
            "likely_location": self._extract_location(error_text),
            "pattern": pattern.description,
        }

        # Generate suggested fixes
        suggested_fixes = self._generate_fixes(error_type, details)

        # Generate debugging steps
        debugging_steps = self._generate_debugging_steps(error_type, details)

        # Generate prevention advice
        prevention = self._generate_prevention(error_type)

        return DiagnosisResult(
            error_type=error_type,
            severity=pattern.severity,
            diagnosis=diagnosis,
            suggested_fixes=suggested_fixes,
            debugging_steps=debugging_steps,
            prevention=prevention,
            context={"language": self.language, "details": details},
        )

    def _detect_error_type(self, error_text: str) -> tuple[str, re.Match | None]:
        """Detect error type from error text."""
        for error_type, pattern_obj in self.patterns.items():
            match = re.search(pattern_obj.pattern, error_text)
            if match:
                return error_type, match
        return "Unknown", None

    def _extract_error_details(
        self, error_text: str, match: re.Match | None
    ) -> dict[str, str]:
        """Extract specific details from error text."""
        details = {}
        if match:
            details["groups"] = match.groups()
            details["full_match"] = match.group(0)
        return details

    def _extract_location(self, error_text: str) -> str:
        """Extract file location from stack trace."""
        # Look for file:line pattern
        location_pattern = r'File "([^"]+)", line (\d+)'
        match = re.search(location_pattern, error_text)
        if match:
            return f"{match.group(1)}:{match.group(2)}"
        return "Unknown location"

    def _identify_root_cause(self, error_type: str, details: dict) -> str:
        """Identify root cause based on error type and details."""
        causes = {
            "AttributeError": "Attempting to access attribute on object that doesn't have it",
            "TypeError": "Operation performed on incompatible types",
            "KeyError": "Dictionary key does not exist",
            "IndexError": "List index out of valid range",
            "ValueError": "Invalid value provided for operation",
            "ImportError": "Module or package not found or import failed",
        }
        return causes.get(error_type, "Error cause analysis required")

    def _generate_fixes(
        self, error_type: str, details: dict
    ) -> list[FixSuggestion]:
        """Generate fix suggestions based on error type."""
        fixes_map = {
            "AttributeError": [
                FixSuggestion(
                    priority=1,
                    solution="Add null check before accessing attribute",
                    code="if obj is not None:\n    value = obj.attribute",
                    explanation="Prevents AttributeError on None objects",
                ),
                FixSuggestion(
                    priority=2,
                    solution="Use getattr with default value",
                    code="value = getattr(obj, 'attribute', default_value)",
                    explanation="Safely access attribute with fallback",
                ),
            ],
            "TypeError": [
                FixSuggestion(
                    priority=1,
                    solution="Add type validation before operation",
                    code="if isinstance(value, expected_type):\n    result = operation(value)",
                    explanation="Ensures correct type before operation",
                ),
                FixSuggestion(
                    priority=2,
                    solution="Use type hints and static type checker",
                    code="def func(param: int) -> str:\n    return str(param)",
                    explanation="Catch type errors at development time",
                ),
            ],
            "KeyError": [
                FixSuggestion(
                    priority=1,
                    solution="Use dict.get() with default value",
                    code="value = data.get('key', default_value)",
                    explanation="Returns default if key doesn't exist",
                ),
                FixSuggestion(
                    priority=2,
                    solution="Check key existence before access",
                    code="if 'key' in data:\n    value = data['key']",
                    explanation="Validate key exists before accessing",
                ),
            ],
        }

        return fixes_map.get(
            error_type,
            [
                FixSuggestion(
                    priority=1,
                    solution="Review error context and stack trace",
                    code=None,
                    explanation="Manual investigation required",
                )
            ],
        )

    def _generate_debugging_steps(
        self, error_type: str, details: dict
    ) -> list[str]:
        """Generate debugging steps."""
        steps_map = {
            "AttributeError": [
                "1. Print the object type to verify it's not None",
                "2. Check object initialization and assignment",
                "3. Verify attribute name spelling",
                "4. Review object creation logic",
            ],
            "TypeError": [
                "1. Print types of all arguments involved",
                "2. Review function signature and expected types",
                "3. Check for type conversion errors",
                "4. Verify operation compatibility",
            ],
            "KeyError": [
                "1. Print dictionary keys to verify structure",
                "2. Check key name spelling and case",
                "3. Review data source and parsing logic",
                "4. Add key validation before access",
            ],
        }

        return steps_map.get(
            error_type,
            [
                "1. Review error message and stack trace",
                "2. Identify code location causing error",
                "3. Check input data and conditions",
                "4. Add logging to trace execution flow",
            ],
        )

    def _generate_prevention(self, error_type: str) -> str:
        """Generate prevention advice."""
        prevention_map = {
            "AttributeError": "Use type hints, Optional types, and validation at boundaries",
            "TypeError": "Use type hints, static type checkers (mypy), and runtime validation",
            "KeyError": "Use .get() method, validate data schemas, and add defensive checks",
            "IndexError": "Use list comprehension guards, validate lengths, and bounds checking",
            "ValueError": "Add input validation, use try/except for conversions, and sanitize data",
            "ImportError": "Use dependency management tools, verify package installation, and avoid circular imports",
        }

        return prevention_map.get(
            error_type, "Follow best practices and add comprehensive error handling"
        )

    def _generate_generic_diagnosis(self, error_text: str) -> DiagnosisResult:
        """Generate generic diagnosis for unknown error types."""
        return DiagnosisResult(
            error_type="Unknown",
            severity="medium",
            diagnosis={
                "root_cause": "Error type not recognized - manual analysis needed",
                "likely_location": self._extract_location(error_text),
                "pattern": "Unknown error pattern",
            },
            suggested_fixes=[
                FixSuggestion(
                    priority=1,
                    solution="Review complete error message and stack trace",
                    code=None,
                    explanation="Manual debugging required for unknown error",
                )
            ],
            debugging_steps=[
                "1. Review complete error message",
                "2. Check stack trace for error location",
                "3. Search error message in documentation",
                "4. Add detailed logging around error location",
            ],
            prevention="Add comprehensive error handling and logging",
        )


# ============================================================================
# CLI Implementation
# ============================================================================


@click.command()
@click.option("--error", type=str, help="Error message text")
@click.option(
    "--stack-trace", type=click.Path(exists=True), help="Stack trace file path"
)
@click.option("--code", type=click.Path(exists=True), help="Code file with issue")
@click.option(
    "--language",
    type=click.Choice(["python", "javascript", "typescript", "go", "rust"]),
    default="python",
    help="Programming language",
)
@click.option("--json", "json_output", is_flag=True, help="JSON output mode")
def main(
    error: str | None,
    stack_trace: str | None,
    code: str | None,
    language: str,
    json_output: bool,
):
    """AI-Powered Debug Helper - Automated debugging workflow."""
    # Gather error information
    error_text = ""

    if error:
        error_text = error
    elif stack_trace:
        error_text = Path(stack_trace).read_text()
    elif code:
        # For code files, prompt for error context
        error_text = f"Code file analysis needed: {code}"
    else:
        click.echo("Error: Must provide --error, --stack-trace, or --code", err=True)
        sys.exit(1)

    # Analyze error
    analyzer = ErrorAnalyzer(language=language)
    result = analyzer.analyze_error(error_text)

    # Output results
    if json_output:
        _output_json(result)
    else:
        _output_human_readable(result)


def _output_json(result: DiagnosisResult):
    """Output diagnosis in JSON format."""
    output = {
        "error_type": result.error_type,
        "severity": result.severity,
        "diagnosis": result.diagnosis,
        "suggested_fixes": [
            {
                "priority": fix.priority,
                "solution": fix.solution,
                "code": fix.code,
                "explanation": fix.explanation,
            }
            for fix in result.suggested_fixes
        ],
        "debugging_steps": result.debugging_steps,
        "prevention": result.prevention,
    }
    click.echo(json.dumps(output, indent=2))


def _output_human_readable(result: DiagnosisResult):
    """Output diagnosis in human-readable format."""
    click.echo("\n" + "=" * 80)
    click.echo("AI-Powered Debug Analysis")
    click.echo("=" * 80 + "\n")

    # Error Type
    click.echo(f"Error Type: {result.error_type}")
    click.echo(f"Severity: {result.severity.upper()}\n")

    # Diagnosis
    click.echo("Diagnosis:")
    click.echo("-" * 80)
    for key, value in result.diagnosis.items():
        click.echo(f"  {key.replace('_', ' ').title()}: {value}")
    click.echo()

    # Suggested Fixes
    click.echo("Suggested Fixes:")
    click.echo("-" * 80)
    for fix in result.suggested_fixes:
        click.echo(f"\n  Priority {fix.priority}: {fix.solution}")
        click.echo(f"  Explanation: {fix.explanation}")
        if fix.code:
            click.echo("\n  Code Example:")
            for line in fix.code.split("\n"):
                click.echo(f"    {line}")
    click.echo()

    # Debugging Steps
    click.echo("Debugging Steps:")
    click.echo("-" * 80)
    for step in result.debugging_steps:
        click.echo(f"  {step}")
    click.echo()

    # Prevention
    click.echo("Prevention:")
    click.echo("-" * 80)
    click.echo(f"  {result.prevention}\n")

    click.echo("=" * 80)


if __name__ == "__main__":
    main()
