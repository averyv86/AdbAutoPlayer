#!/usr/bin/env python3
"""
Mermaid diagram type and syntax validation.

Scans markdown files for Mermaid diagram blocks and validates:
- Diagram types (flowchart, sequence, class, state, etc.)
- Basic syntax errors
- Required elements per diagram type

Usage:
    uv run validate_mermaid_diagrams.py [--input PATH] [--output PATH] [--json]
    uv run validate_mermaid_diagrams.py --help

Exit Codes:
    0 - All diagrams valid
    1 - Warnings found
    2 - Invalid diagrams found
    3 - Fatal error
"""
# /// script
# dependencies = [
#     "click>=8.0.0",
# ]
# ///

import json
import re
import sys
from collections import defaultdict
from pathlib import Path


# Auto-detect project root (based on pyproject.toml or .git)
def find_project_root(start_path: Path) -> Path:
    current = start_path
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            return current
        current = current.parent
    raise RuntimeError("Project root not found")


# Find project root
SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = find_project_root(SCRIPT_PATH.parent)

# Default path configuration
DEFAULT_DOCS_PATH = PROJECT_ROOT / "docs" / "src"


class MermaidValidator:
    # Supported diagram types
    DIAGRAM_TYPES = {
        "flowchart": r"^flowchart\s+(TD|BT|LR|RL)",
        "graph": r"^graph\s+(TD|BT|LR|RL)",
        "sequenceDiagram": r"^sequenceDiagram",
        "classDiagram": r"^classDiagram",
        "stateDiagram": r"^stateDiagram(-v2)?",
        "erDiagram": r"^erDiagram",
        "gantt": r"^gantt",
        "pie": r"^pie",
    }

    def __init__(self, docs_path: str):
        self.docs_path = Path(docs_path)
        self.errors = []
        self.warnings = []
        self.info = []
        self.file_count = 0
        self.diagram_count = 0
        self.diagrams_by_type = defaultdict(int)

    def validate_all(self):
        """Validate all markdown files"""
        md_files = sorted(self.docs_path.rglob("*.md"))
        self.file_count = len(md_files)

        print(f"Starting Mermaid diagram validation: {self.file_count} files")
        print("=" * 80)

        for md_file in md_files:
            self.validate_file(md_file)

        return self.generate_report()

    def validate_file(self, file_path: Path):
        """Validate individual file"""
        try:
            content = file_path.read_text(encoding="utf-8")
            rel_path = file_path.relative_to(self.docs_path.parent)

            # Extract and validate mermaid blocks
            self.extract_and_validate_mermaid(rel_path, content)

        except Exception as e:
            self.errors.append(
                {
                    "file": str(file_path),
                    "line": "N/A",
                    "type": "file_error",
                    "message": f"File read error: {str(e)}",
                }
            )

    def extract_and_validate_mermaid(self, file_path, content):
        """Extract mermaid blocks and validate"""
        lines = content.split("\n")
        i = 0

        while i < len(lines):
            if lines[i].strip() == "```mermaid":
                block_start = i + 1  # Line number (1-indexed)
                block_lines = []
                i += 1

                # Collect until block end
                while i < len(lines) and lines[i].strip() != "```":
                    block_lines.append(lines[i])
                    i += 1

                if i >= len(lines):
                    self.errors.append(
                        {
                            "file": str(file_path),
                            "line": block_start,
                            "type": "syntax",
                            "message": "Unclosed Mermaid block (missing closing ```)",
                        }
                    )
                else:
                    self.diagram_count += 1
                    block_content = "\n".join(block_lines)
                    self.validate_mermaid_content(file_path, block_start, block_content)
            i += 1

    def validate_mermaid_content(self, file_path, line_no, content):
        """Validate Mermaid diagram content"""
        if not content.strip():
            self.errors.append(
                {
                    "file": str(file_path),
                    "line": line_no,
                    "type": "empty_block",
                    "message": "Empty Mermaid block",
                }
            )
            return

        lines = content.strip().split("\n")
        first_line = lines[0].strip()

        # Check diagram type
        diagram_type = self.detect_diagram_type(first_line)

        if not diagram_type:
            self.warnings.append(
                {
                    "file": str(file_path),
                    "line": line_no,
                    "type": "unknown_type",
                    "message": f'Unrecognized diagram type: "{first_line[:60]}"',
                }
            )
            return

        # Count by type
        self.diagrams_by_type[diagram_type] += 1

        # Validate by type
        if diagram_type in ["flowchart", "graph"]:
            self.validate_flowchart(file_path, line_no, content)
        elif diagram_type == "sequenceDiagram":
            self.validate_sequence_diagram(file_path, line_no, content)
        elif diagram_type == "classDiagram":
            self.validate_class_diagram(file_path, line_no, content)
        elif diagram_type == "stateDiagram":
            self.validate_state_diagram(file_path, line_no, content)
        elif diagram_type == "erDiagram":
            self.validate_er_diagram(file_path, line_no, content)

    def detect_diagram_type(self, first_line: str) -> str:
        """Detect diagram type from first line"""
        # Check for config block
        if "%%{init:" in first_line:
            return "config_block"

        # Match diagram types
        for dtype, pattern in self.DIAGRAM_TYPES.items():
            if re.match(pattern, first_line):
                return dtype

        return None

    def validate_flowchart(self, file_path, line_no, content):
        """Validate flowchart/graph diagram"""
        # Check for nodes (pattern: ID[Text] or ID(Text) or ID{Text})
        nodes = set(re.findall(r"(\w+)[\[\(\{]", content))

        # Check for edges (arrows: -->, ---, -.>, ==>, etc.)
        edges = re.findall(r"(\w+)\s*(?:-->|---|\.->|==>|-.->|-\.-)", content)

        if not nodes:
            self.warnings.append(
                {
                    "file": str(file_path),
                    "line": line_no,
                    "type": "flowchart",
                    "message": "No nodes found (expected pattern: ID[Text])",
                }
            )

        if not edges:
            self.warnings.append(
                {
                    "file": str(file_path),
                    "line": line_no,
                    "type": "flowchart",
                    "message": "No edges found (expected arrows: -->, ---, etc.)",
                }
            )

        # Check for undefined edge sources
        for edge_src in edges:
            if edge_src and edge_src not in nodes and not re.match(r"^[A-Z]+$", edge_src):
                self.info.append(
                    {
                        "file": str(file_path),
                        "line": line_no,
                        "type": "flowchart",
                        "message": f"Edge source '{edge_src}' not defined as node",
                    }
                )

    def validate_sequence_diagram(self, file_path, line_no, content):
        """Validate sequence diagram"""
        # Check for participants
        participants = re.findall(r"participant\s+(\w+)", content)

        # Check for messages (arrows: ->, ->>, ->>+, etc.)
        messages = re.findall(r"(\w+)\s*-[->]+\s*(\w+)", content)

        if not participants and not messages:
            self.warnings.append(
                {
                    "file": str(file_path),
                    "line": line_no,
                    "type": "sequence",
                    "message": "No participants or messages found",
                }
            )

        if messages and not participants:
            self.info.append(
                {
                    "file": str(file_path),
                    "line": line_no,
                    "type": "sequence",
                    "message": "Messages found but no explicit participants defined",
                }
            )

    def validate_class_diagram(self, file_path, line_no, content):
        """Validate class diagram"""
        # Check for class definitions
        classes = re.findall(r"class\s+(\w+)", content)

        # Check for relationships
        relationships = re.findall(r"(\w+)\s*[<|o*]+[-\.][|>o*]+\s*(\w+)", content)

        if not classes:
            self.warnings.append(
                {
                    "file": str(file_path),
                    "line": line_no,
                    "type": "class",
                    "message": "No class definitions found",
                }
            )

        if not relationships and len(classes) > 1:
            self.info.append(
                {
                    "file": str(file_path),
                    "line": line_no,
                    "type": "class",
                    "message": "Multiple classes but no relationships defined",
                }
            )

    def validate_state_diagram(self, file_path, line_no, content):
        """Validate state diagram"""
        # Check for state transitions
        transitions = re.findall(r"(\w+)\s*-->\s*(\w+)", content)

        # Check for state definitions
        states = re.findall(r"state\s+\"?([^\"]+)\"?\s+as\s+(\w+)", content)

        if not transitions:
            self.warnings.append(
                {
                    "file": str(file_path),
                    "line": line_no,
                    "type": "state",
                    "message": "No state transitions found (expected: State1 --> State2)",
                }
            )

    def validate_er_diagram(self, file_path, line_no, content):
        """Validate ER diagram"""
        # Check for entity definitions
        entities = re.findall(r"(\w+)\s*\{", content)

        # Check for relationships
        relationships = re.findall(r"(\w+)\s*[|o}][|o]-*[|o][|o}]\s*(\w+)", content)

        if not entities:
            self.warnings.append(
                {
                    "file": str(file_path),
                    "line": line_no,
                    "type": "er",
                    "message": "No entity definitions found",
                }
            )

        if not relationships and len(entities) > 1:
            self.info.append(
                {
                    "file": str(file_path),
                    "line": line_no,
                    "type": "er",
                    "message": "Multiple entities but no relationships defined",
                }
            )

    def generate_report(self, as_json: bool = False):
        """Generate validation report"""
        if as_json:
            return self._generate_json_report()
        else:
            return self._generate_human_report()

    def _generate_json_report(self) -> str:
        """Generate JSON format report"""
        result = {
            "summary": {
                "total_files": self.file_count,
                "total_diagrams": self.diagram_count,
                "diagrams_by_type": dict(self.diagrams_by_type),
                "total_issues": len(self.errors) + len(self.warnings) + len(self.info),
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "info": len(self.info),
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
        }
        return json.dumps(result, indent=2, ensure_ascii=False)

    def _generate_human_report(self) -> str:
        """Generate human-readable report"""
        report = []

        # Header
        report.append("=" * 80)
        report.append("Mermaid Diagram Validation Report")
        report.append("=" * 80)
        report.append("")

        # Statistics
        report.append("## Validation Statistics")
        report.append(f"- Files scanned: {self.file_count}")
        report.append(f"- Diagrams found: {self.diagram_count}")
        report.append("")

        report.append("### Diagrams by Type:")
        for dtype in sorted(self.diagrams_by_type.keys()):
            count = self.diagrams_by_type[dtype]
            report.append(f"  - {dtype}: {count}")
        report.append("")

        report.append(f"- Errors (Invalid): {len(self.errors)}")
        report.append(f"- Warnings (Fix Recommended): {len(self.warnings)}")
        report.append(f"- Info (Review): {len(self.info)}")
        report.append("")

        # Errors
        if self.errors:
            report.append("## Errors (Invalid - Must Fix)")
            report.append("")
            error_by_type = defaultdict(list)
            for err in self.errors:
                error_by_type[err["type"]].append(err)

            for err_type in sorted(error_by_type.keys()):
                errors = error_by_type[err_type]
                report.append(f"### {err_type.upper()} ({len(errors)} items)")
                for err in sorted(errors, key=lambda x: str(x["file"])):
                    line_info = f":{err['line']}" if err["line"] != "N/A" else ""
                    report.append(f"  - {err['file']}{line_info}")
                    report.append(f"    {err['message']}")
                report.append("")

        # Warnings
        if self.warnings:
            report.append("## Warnings (Fix Recommended)")
            report.append("")
            warn_by_type = defaultdict(list)
            for warn in self.warnings:
                warn_by_type[warn["type"]].append(warn)

            for warn_type in sorted(warn_by_type.keys()):
                warnings = warn_by_type[warn_type]
                report.append(f"### {warn_type.upper()} ({len(warnings)} items)")

                # Group by file
                by_file = defaultdict(list)
                for warn in warnings:
                    by_file[warn["file"]].append(warn)

                for file_path in sorted(by_file.keys()):
                    report.append(f"  {file_path}:")
                    for warn in by_file[file_path]:
                        line_info = f":{warn['line']}" if warn["line"] != "N/A" else ""
                        report.append(f"    [{line_info}] {warn['message']}")
                report.append("")

        # Info
        if self.info:
            report.append("## Info (Review Recommended)")
            report.append("")
            info_by_type = defaultdict(list)
            for inf in self.info:
                info_by_type[inf["type"]].append(inf)

            for info_type in sorted(info_by_type.keys()):
                infos = info_by_type[info_type]
                report.append(f"### {info_type.upper()} ({len(infos)} items)")

                # Group by file
                by_file = defaultdict(list)
                for inf in infos:
                    by_file[inf["file"]].append(inf)

                for file_path in sorted(by_file.keys()):
                    count = len(by_file[file_path])
                    report.append(f"  {file_path} ({count} found)")
                report.append("")

        # Summary
        report.append("=" * 80)
        report.append("## Summary")
        report.append("")

        if self.errors:
            report.append(f"**ERRORS**: {len(self.errors)} invalid diagrams require immediate fix")
        elif self.warnings:
            report.append(f"**WARNINGS**: {len(self.warnings)} diagrams should be reviewed")
        elif self.info:
            report.append(f"**INFO**: {len(self.info)} items for review")
        else:
            report.append("**SUCCESS**: All Mermaid diagrams are valid!")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)


def main():
    """Main entry point with Click CLI"""
    import click

    @click.command()
    @click.option(
        "--input",
        type=click.Path(exists=True),
        default=None,
        help="Input path (file or directory). Defaults to docs/src/",
    )
    @click.option(
        "--output",
        type=click.Path(),
        default=None,
        help="Output file path. If not specified, prints to stdout.",
    )
    @click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
    def cli(input, output, output_json):
        """Mermaid diagram type and syntax validation."""

        # Determine input path
        input_path = Path(input) if input else DEFAULT_DOCS_PATH

        if not input_path.exists():
            click.echo(f"Error: Path does not exist: {input_path}", err=True)
            sys.exit(3)

        # Run validation
        validator = MermaidValidator(str(input_path))
        validator.validate_all()

        # Generate report
        report_text = validator.generate_report(as_json=output_json)

        # Write output
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report_text, encoding="utf-8")
            click.echo(f"Report written to: {output}")
        else:
            click.echo(report_text)

        # Exit with appropriate code
        if validator.errors:
            sys.exit(2)  # Invalid diagrams found
        elif validator.warnings:
            sys.exit(1)  # Warnings found
        else:
            sys.exit(0)  # All diagrams valid

    cli()


# Execution
if __name__ == "__main__":
    main()
