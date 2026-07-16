# Scripts Integration Pattern

**Purpose**: Token-efficient script integration pattern adapted from IndieDevDan's proven approach, achieving 80%+ context savings.

**Last Updated**: 2025-11-30
**Version**: 1.0.0

---

## Core Philosophy: "Don't Read Scripts Unless Needed"

Traditional approach wastes tokens by loading all script source code before execution. The Scripts Integration Pattern achieves 97% token reduction by using progressive disclosure.

### The Problem

**Traditional Approach**:
```
1. Load skill documentation (1,000 tokens)
2. Load all script source code (5,000 tokens)
3. Understand implementation details
4. Execute script

Total: 6,000+ tokens before execution
```

### The Solution

**IndieDevDan Approach**:
```
1. Load SKILL.md (200 tokens) - "When to use" for each script
2. Execute script with --help (0 additional tokens)
3. Call script with options
4. Only read script source if --help insufficient

Total: 200 tokens (97% reduction)
```

---

## Implementation in MoAI

### Directory Structure

```
.claude/skills/{skill-name}/
├── SKILL.md                    # 100-200 lines (not 500)
│   └── scripts: section        # Metadata only
└── scripts/                    # Flat directory (no subdirs)
    ├── script1.py              # 200-300 lines max
    ├── script2.py              # Self-contained
    └── script3.py              # Zero coupling
```

**Key Principles**:
- Flat `scripts/` directory (no subdirectories)
- Each script 200-300 lines (500 hard limit)
- Single-file UV scripts with PEP 723 dependencies
- Self-contained (intentional code duplication)
- Zero coupling between scripts

---

## Script Standards

### 1. UV Script Format (PEP 723)

```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#   "typer>=0.9.0",
#   "rich>=13.0.0"
# ]
# ///

"""
Script Name: lint_korean_docs.py
Purpose: Validate Korean markdown documentation
Usage: uv run lint_korean_docs.py [OPTIONS] PATH
"""

import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def main(
    path: str = typer.Argument(..., help="Documentation directory"),
    json: bool = typer.Option(False, "--json", help="Output JSON format")
):
    """Validate Korean markdown documentation."""
    # Implementation
    pass

if __name__ == "__main__":
    app()
```

### 2. Dual Output Format

**Human-Readable** (default):
```bash
$ uv run lint_korean_docs.py docs/
✓ File 1: docs/README.md (5 issues)
✓ File 2: docs/API.md (2 issues)
Summary: 7 issues found in 2 files
```

**JSON Output** (machine-readable):
```bash
$ uv run lint_korean_docs.py docs/ --json
{
  "files": [
    {"path": "docs/README.md", "issues": 5},
    {"path": "docs/API.md", "issues": 2}
  ],
  "summary": {"total_issues": 7, "total_files": 2}
}
```

### 3. Project-Root Auto-Detection

```python
def find_project_root() -> Path:
    """Auto-detect project root via .git or pyproject.toml"""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists() or (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()
```

### 4. Self-Contained Implementation

**Intentional Code Duplication**:
```python
# ❌ WRONG - External dependency
from ..utils.http_client import HTTPClient

# ✅ CORRECT - Embedded HTTP client
class HTTPClient:
    """Embedded HTTP client for this script"""
    def get(self, url): pass
```

**Zero Coupling**:
- Each script includes its own formatters, HTTP clients, utilities
- No imports from other scripts or shared modules
- Duplication preferred over coupling
- Easier maintenance and debugging

---

## SKILL.md Integration

### YAML Frontmatter with Scripts Metadata

```yaml
---
name: moai-workflow-docs
version: 1.0.0
scripts_enabled: true
scripts:
  - name: lint_korean_docs
    purpose: Comprehensive markdown validation
    command: uv run .claude/skills/moai-workflow-docs/scripts/lint_korean_docs.py
    zero_context: true
  - name: validate_mermaid_diagrams
    purpose: Check Mermaid diagram syntax
    command: uv run .claude/skills/moai-workflow-docs/scripts/validate_mermaid_diagrams.py
    zero_context: true
  - name: generate_quality_report
    purpose: Aggregated quality report
    command: uv run .claude/skills/moai-workflow-docs/scripts/generate_quality_report.py
    zero_context: true
---
```

### "When to Use" Section in SKILL.md

```markdown
## Available Scripts

### `scripts/lint_korean_docs.py`
**When to use:** Validate Korean markdown documentation
**Quick start:** `uv run .claude/skills/moai-workflow-docs/scripts/lint_korean_docs.py --help`

### `scripts/validate_mermaid_diagrams.py`
**When to use:** Check Mermaid diagram syntax and types
**Quick start:** `uv run .claude/skills/moai-workflow-docs/scripts/validate_mermaid_diagrams.py --help`

### `scripts/generate_quality_report.py`
**When to use:** Generate aggregated validation report
**Quick start:** `uv run .claude/skills/moai-workflow-docs/scripts/generate_quality_report.py --help`

---

**Important**: Don't read script source code. Use `--help` flag to understand usage.
All scripts are self-documenting and provide comprehensive help output.
```

---

## Progressive Disclosure Benefits

### Token Budget Comparison

```
Traditional Approach:
├── SKILL.md (1,000 tokens)
├── scripts/ source code (5,000 tokens)
└── Total: 6,000 tokens

Scripts Integration Pattern:
├── SKILL.md (1,000 tokens)
│   ├── Quick Reference (200 tokens)
│   └── Scripts metadata (200 tokens)
├── scripts/ (0 tokens - dormant until invoked)
└── Total: 1,000 tokens (83% reduction)

When Script Needed:
├── Load SKILL.md (1,000 tokens)
├── Execute --help (0 tokens)
├── Run script (0 tokens)
└── Read source if needed (500-800 tokens per script)
Total: 1,000-1,800 tokens (70-83% reduction)
```

### Three-Tier Loading Strategy

```
Tier 0: scripts/ → 0 tokens (dormant until invoked)
Tier 1: SKILL.md → 1,000 tokens (Quick Reference + metadata)
Tier 2: modules/ → 3,000-5,000 tokens (Deep dive implementation)
Tier 3: examples.md → Variable tokens (Working samples)
```

**Context Savings**: 98% for automation tasks (agent reads metadata only, executes immediately).

---

## Key Patterns

### Pattern 1: Metadata-Driven Discovery

```yaml
# In SKILL.md frontmatter
scripts:
  - name: script_name
    purpose: One-line description (max 80 chars)
    command: uv run .claude/skills/{skill}/scripts/script_name.py
    zero_context: true  # Agent executes without reading source
```

**Benefits**:
- Agent knows when to use script (purpose field)
- Agent executes directly (zero_context flag)
- No source code reading required

### Pattern 2: Self-Documenting Scripts

```python
@app.command()
def main(
    path: str = typer.Argument(..., help="Documentation directory to validate"),
    json: bool = typer.Option(False, "--json", help="Output JSON format"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output")
):
    """
    Validate Korean markdown documentation.

    Examples:
        uv run lint_korean_docs.py docs/
        uv run lint_korean_docs.py docs/ --json
        uv run lint_korean_docs.py docs/ --verbose
    """
    pass
```

**Benefits**:
- `--help` provides complete usage guide
- No need to read source code
- Examples embedded in help output

### Pattern 3: Flat Directory Structure

```
scripts/
├── lint_korean_docs.py         # 200-300 lines
├── validate_mermaid_diagrams.py # 200-300 lines
├── validate_korean_typography.py # 200-300 lines
└── generate_quality_report.py  # 200-300 lines

# NO SUBDIRECTORIES
# NO SHARED MODULES
# NO COUPLING
```

**Benefits**:
- Simple discovery (all scripts in one place)
- No navigation complexity
- Easy maintenance

### Pattern 4: Intentional Code Duplication

```python
# Script 1: lint_korean_docs.py
class MarkdownParser:
    """Embedded markdown parser"""
    def parse(self, content): pass

# Script 2: validate_mermaid_diagrams.py
class MarkdownParser:
    """Embedded markdown parser (duplicated)"""
    def parse(self, content): pass
```

**Why Duplicate?**:
- Zero coupling between scripts
- Scripts work independently
- Easier debugging (all code in one file)
- No version conflicts
- Faster execution (no imports)

### Pattern 5: "Don't Read Scripts" Instruction

```markdown
## Quick Reference (30 seconds)

**Scripts Available**: 5 validation and reporting scripts

**Usage Pattern**:
1. Load skill: `Skill("moai-workflow-docs")`
2. Check SKILL.md for "When to use"
3. Execute script with `--help` flag
4. Run script with options
5. **Only read source if --help insufficient**

**Important**: Don't read script source code unless necessary.
All scripts are self-documenting via `--help` flag.
```

---

## Reference Implementation: moai-workflow-docs

### SKILL.md Structure (200 lines)

```markdown
---
name: moai-workflow-docs
scripts_enabled: true
scripts:
  - name: lint_korean_docs
    purpose: Markdown validation
    command: uv run .claude/skills/moai-workflow-docs/scripts/lint_korean_docs.py
    zero_context: true
---

## Quick Reference (30 seconds)
[Metadata only - 200 tokens]

## Available Scripts

### `scripts/lint_korean_docs.py`
**When to use:** Validate markdown documentation
**Quick start:** `--help` flag for usage

---

**Important**: Use `--help` instead of reading source code.
```

### Script Implementation (250 lines)

```python
#!/usr/bin/env python3
# /// script
# dependencies = ["typer>=0.9.0", "rich>=13.0.0"]
# ///

"""
Markdown Documentation Linter
Purpose: Validate markdown syntax, structure, links
Usage: uv run lint_korean_docs.py [OPTIONS] PATH
"""

import typer
from rich.console import Console
from pathlib import Path

app = typer.Typer()
console = Console()

# Embedded utilities (no external imports)
class MarkdownParser:
    """Self-contained markdown parser"""
    pass

class LinkValidator:
    """Self-contained link validator"""
    pass

@app.command()
def main(
    path: str = typer.Argument(..., help="Documentation directory"),
    json: bool = typer.Option(False, "--json", help="JSON output"),
    verbose: bool = typer.Option(False, "-v", help="Verbose output")
):
    """Validate markdown documentation."""
    # Self-contained implementation
    pass

if __name__ == "__main__":
    app()
```

### Token Budget Analysis

```
Traditional Approach:
├── SKILL.md (1,000 tokens)
├── All 5 scripts source (5,000 tokens)
└── Total: 6,000 tokens

Scripts Integration Pattern:
├── SKILL.md (1,000 tokens)
│   ├── Metadata (200 tokens)
│   └── "When to use" (200 tokens)
├── scripts/ (0 tokens - not loaded)
└── Total: 1,000 tokens

When Script Needed:
├── Execute --help (0 tokens)
├── Run script (0 tokens)
└── Total: 1,000 tokens (83% reduction)
```

---

## Best Practices

### DO ✅

1. **Keep scripts 200-300 lines** (500 hard limit)
2. **Use flat scripts/ directory** (no subdirectories)
3. **Embed utilities** (HTTP clients, formatters, parsers)
4. **Provide --help flag** (comprehensive usage guide)
5. **Support --json output** (machine-readable format)
6. **Auto-detect project root** (.git or pyproject.toml)
7. **Use UV script format** (PEP 723 dependencies)
8. **Document in SKILL.md frontmatter** (metadata only)
9. **Include "When to use"** (purpose description)
10. **Add "Don't read scripts" instruction** (save tokens)

### DON'T ❌

1. **Create subdirectories** (keep flat structure)
2. **Import from other scripts** (zero coupling)
3. **Share modules** (intentional duplication)
4. **Exceed 500 lines** (split into multiple scripts)
5. **Require source reading** (self-documenting via --help)
6. **Use external dependencies** (embed utilities)
7. **Load scripts in SKILL.md** (metadata only)
8. **Document implementation details** (--help only)
9. **Create complex CLI** (simple, clear options)
10. **Forget JSON output** (always provide --json)

---

## Migration Guide

### Converting Existing Skills to Scripts Pattern

**Before** (traditional approach):
```
.claude/skills/skill-name/
├── SKILL.md (500 lines - includes script documentation)
└── modules/
    └── scripts-reference.md (1,000 lines - script details)
```

**After** (scripts integration pattern):
```
.claude/skills/skill-name/
├── SKILL.md (200 lines - metadata only)
│   ├── scripts: frontmatter (metadata)
│   └── "When to use" section
└── scripts/
    ├── script1.py (250 lines - self-documenting)
    ├── script2.py (250 lines - self-documenting)
    └── script3.py (250 lines - self-documenting)
```

**Migration Steps**:
1. Extract script metadata to SKILL.md frontmatter
2. Move scripts to flat `scripts/` directory
3. Add "When to use" section to SKILL.md
4. Ensure scripts have --help flag
5. Remove script documentation from modules/
6. Add "Don't read scripts" instruction
7. Test with --help flag execution

**Token Savings**: 4,000+ tokens (80% reduction)

---

## Performance Metrics

### Token Efficiency

| Metric | Traditional | Scripts Pattern | Savings |
|--------|-------------|-----------------|---------|
| Skill loading | 6,000 tokens | 1,000 tokens | 83% |
| Script execution | +0 tokens | +0 tokens | N/A |
| Source reading | Always (5,000) | If needed (500) | 90% |
| **Total (typical)** | 6,000 | 1,000 | **83%** |
| **Total (with source)** | 6,000 | 1,500 | **75%** |

### Execution Speed

- Flat directory: 0ms navigation overhead
- Zero imports: 50-100ms faster execution
- Self-contained: No dependency resolution
- UV scripts: Fast cold starts

### Maintenance Benefits

- Single-file scripts: Easier debugging
- Zero coupling: Independent updates
- Self-documenting: No external docs needed
- Intentional duplication: No version conflicts

---

## Works Well With

**Skills**:
- **moai-workflow-docs** - Reference implementation
- **moai-foundation-core** - Core patterns integration
- **moai-cc-claude-md** - Documentation standards

**Agents**:
- **workflow-docs** - Script execution orchestration
- **core-quality** - Quality validation scripts
- **workflow-spec** - SPEC generation scripts

**Commands**:
- `/moai:3-sync` - Documentation scripts
- `/moai:9-feedback` - Feedback collection scripts

---

## References

- **IndieDevDan SKILL.md** - Original pattern inspiration
- **IndieDevDan STRUCTURE.md** - Directory structure guide
- **IndieDevDan prime_file_system_scripts.md** - Script implementation patterns
- **PEP 723** - UV script format specification
- **Typer Documentation** - CLI framework best practices

---

**Version**: 1.0.0
**Last Updated**: 2025-11-30
**Status**: ✅ Active
**Token Budget**: 200 tokens (metadata only)

---

**End of Module** | Scripts Integration Pattern for 80%+ token savings
