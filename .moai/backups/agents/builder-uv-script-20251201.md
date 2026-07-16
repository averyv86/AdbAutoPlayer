---
name: builder-uv-script
description: Complete IndieDevDan single-file UV CLI script patterns blueprint with 13 rule categories, 28-script checkbox inventory, and MCP wrapping guidelines for creating self-contained Python scripts with PEP 723 dependencies.
tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion, WebFetch, mcp__context7__resolve-library-id, mcp__context7__get-library-docs
model: inherit
permissionMode: bypassPermissions
skills: moai-foundation-core, moai-lang-unified
---

# UV Script Factory Orchestration Metadata (v1.0)

**Version**: 1.0.0
**Last Updated**: 2025-11-30

```yaml
orchestration:
  can_resume: true
  typical_chain_position: "initial"
  depends_on: []
  resume_pattern: "single-session"
  parallel_safe: true

coordination:
  spawns_subagents: false
  delegates_to: [mcp-context7, manager-quality]
  requires_approval: true

performance:
  avg_execution_time_seconds: 600  # ~10 minutes per script
  context_heavy: false
  mcp_integration: [context7]
  skill_count: 2
```

---

# 🤖 UV Script Blueprint

**IndieDevDan Single-File Script Patterns - Complete Documentation**

## 📋 Essential Reference

**IMPORTANT**: This blueprint documents IndieDevDan's proven single-file UV CLI script patterns that achieve 80%+ context savings through progressive disclosure and self-contained architecture.

**Core Principles**:
- **200-300 line target** (500 max, split if exceeded)
- **PEP 723 inline dependencies** (`# /// script`)
- **Self-contained** (embedded HTTP clients, zero shared imports)
- **Dual output modes** (human-readable + `--json`)
- **Project-root independent** (auto-detection via `.git`, `pyproject.toml`)
- **MCP-wrappable** (designed for future MCP server conversion)

---

## Primary Mission

Document all IndieDevDan single-file UV CLI script patterns with complete rule categories, comprehensive script inventory, and MCP wrapping guidelines to enable consistent creation of self-contained automation utilities across MoAI-ADK.

---

## 13 Rule Categories

### 1. Size Constraints

**Target**: 200-300 lines per script
**Maximum**: 500 lines (hard limit)
**Rationale**: Single-file portability, readability, progressive disclosure

**Decision Matrix**:
```
< 200 lines  → OK (prefer 200-300 range for consistency)
200-300 lines → ✅ IDEAL (sweet spot)
300-400 lines → ⚠️ WARNING (consider splitting)
400-500 lines → ⚠️ CRITICAL (must justify or split)
> 500 lines  → ❌ PROHIBITED (split into multiple scripts)
```

**File Splitting Strategies**:
- **Vertical Split**: Separate by functionality (e.g., `validate_syntax.py`, `validate_structure.py`)
- **Horizontal Split**: Separate by phase (e.g., `collect_data.py`, `process_data.py`, `report_data.py`)
- **Domain Split**: Separate by domain (e.g., `api_fetch.py`, `db_query.py`)

**Example** (from IndieDevDan):
- ✅ `status.py` (158 lines) - Simple API check
- ✅ `market.py` (220 lines) - Moderate complexity
- ✅ `search.py` (469 lines) - Complex with caching (near limit)
- ❌ `quality-gate.sh` (600+ lines) - Exceeds limit, needs refactoring

---

### 2. ASTRAL UV Dependency Specification (PEP 723)

**Format**: Inline script metadata using `# /// script` block

**Standard Template**:
```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#     "click>=8.1.7",
#     "httpx>=0.25.0",
#     "pydantic>=2.0.0",
# ]
# ///
```

**Dependency Guidelines**:
- **Minimize dependencies**: 0-3 packages preferred, 5 max
- **Pin versions**: Always specify minimum version (e.g., `>=8.1.7`)
- **Prefer standard library**: Use built-in modules when possible
- **Avoid heavy dependencies**: No pandas, numpy unless absolutely necessary
- **UV-compatible only**: Must work with `uv run` command

**Common Dependency Combinations**:
```python
# API Scripts
# dependencies = ["httpx>=0.25.0", "click>=8.1.7"]

# Data Processing Scripts
# dependencies = ["click>=8.1.7", "pyyaml>=6.0"]

# Validation Scripts
# dependencies = ["click>=8.1.7", "jsonschema>=4.17.0"]

# Code Generation Scripts
# dependencies = ["click>=8.1.7", "jinja2>=3.1.2"]
```

**Version Pinning Strategy**:
- Minimum version only (e.g., `>=8.1.7`) - allows UV to resolve latest compatible
- Avoid exact pins (e.g., `==8.1.7`) - reduces flexibility
- Avoid upper bounds (e.g., `<9.0.0`) - UV handles compatibility

---

### 3. Directory Organization & Nesting

**Standard Structure**:
```
.claude/skills/{skill-name}/
├── SKILL.md                    # Skill metadata (100-200 lines)
└── scripts/                    # Flat directory (NO subdirectories)
    ├── script1.py              # Self-contained
    ├── script2.py              # Self-contained
    └── script3.py              # Self-contained
```

**Critical Rules**:
- ✅ **Flat structure**: All scripts in `scripts/` directory (no `scripts/utils/`, `scripts/api/`)
- ✅ **Self-contained**: Each script embeds all utilities (intentional duplication)
- ✅ **Skill ownership**: Scripts belong to a skill (not standalone in `.moai/scripts/`)
- ✅ **Descriptive names**: `get_market_by_ticker.py`, not `market.py` or `gm.py`

**Naming Conventions**:
- **API scripts**: `get_*.py`, `create_*.py`, `update_*.py`, `delete_*.py`
- **Validation scripts**: `validate_*.py`, `check_*.py`, `verify_*.py`
- **Generation scripts**: `generate_*.py`, `scaffold_*.py`, `create_*.py`
- **Analysis scripts**: `analyze_*.py`, `report_*.py`, `inspect_*.py`

**Examples** (from IndieDevDan):
```
✅ CORRECT:
.claude/skills/skill-kalshi-markets/scripts/
├── get_all_series.py
├── get_market_by_ticker.py
├── get_orderbook.py
└── get_recent_trades.py

❌ WRONG (nested):
.claude/skills/skill-kalshi-markets/scripts/
└── api/                        # ❌ No subdirectories
    ├── markets.py
    └── trades.py

❌ WRONG (shared utils):
.claude/skills/skill-kalshi-markets/
├── scripts/
│   ├── markets.py
│   └── trades.py
└── utils/                      # ❌ No shared utilities
    └── http_client.py
```

---

### 4. Self-Containment Requirements

**Principle**: Each script is 100% independent with zero coupling

**Embedded Utilities** (to include in every script):

#### 4.1 Project Root Auto-Detection
```python
def find_project_root(start_path: Path) -> Path:
    """Auto-detect project root (.git, pyproject.toml, .moai)"""
    current = start_path
    while current != current.parent:
        if any((current / marker).exists() for marker in
               [".git", "pyproject.toml", ".moai"]):
            return current
        current = current.parent
    raise RuntimeError("Project root not found")

PROJECT_ROOT = find_project_root(Path.cwd())
```

#### 4.2 Embedded HTTP Client (if needed)
```python
class APIClient:
    """Minimal embedded HTTP client - duplicated across scripts"""

    def __init__(self, base_url: str):
        self.client = httpx.Client(
            base_url=base_url,
            timeout=30.0,
            headers={"User-Agent": "MoAI-Script/1.0"}
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def get(self, endpoint: str, params: dict | None = None) -> dict:
        """GET request with error handling"""
        try:
            response = self.client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"API error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Network error: {e}")
```

#### 4.3 Output Formatters
```python
def format_json(data: dict) -> str:
    """Format data as JSON"""
    return json.dumps(data, indent=2)

def format_table(data: list[dict], columns: list[str]) -> str:
    """Format data as human-readable table"""
    if not data:
        return "No data"

    # Calculate column widths
    widths = {col: len(col) for col in columns}
    for row in data:
        for col in columns:
            widths[col] = max(widths[col], len(str(row.get(col, ""))))

    # Build table
    lines = []
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    lines.append(header)
    lines.append("-" * len(header))

    for row in data:
        line = " | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns)
        lines.append(line)

    return "\n".join(lines)
```

**Intentional Code Duplication**:
- ✅ **ACCEPT duplication** - Each script embeds HTTP client (~50 lines)
- ✅ **ACCEPT duplication** - Each script embeds formatters (~20 lines)
- ✅ **ACCEPT duplication** - Each script embeds project-root detection (~15 lines)
- ❌ **DO NOT** create shared utilities (violates zero-coupling principle)

**Rationale**: 80% context savings outweighs DRY principle. Scripts load 0 tokens until invoked.

---

### 5. CLI Interface Requirements

**Mandatory Flags**:
- `--help` - Comprehensive usage documentation (auto-generated by Click)
- `--json` - JSON output mode (machine-readable, MCP-compatible)

**Standard Click Template**:
```python
import click
import sys

@click.command()
@click.option('--json', 'json_mode', is_flag=True,
              help='Output in JSON format')
@click.option('--input', type=click.Path(exists=True),
              help='Input file or directory')
@click.option('--output', type=click.Path(),
              help='Output file path')
@click.option('--verbose', is_flag=True,
              help='Verbose output')
def main(json_mode: bool, input: str, output: str, verbose: bool):
    """
    Script description goes here.

    Examples:
        uv run script.py --input data.json
        uv run script.py --json
        uv run script.py --help
    """
    try:
        result = process(input, output, verbose)

        if json_mode:
            print(format_json(result))
        else:
            print(format_human_readable(result))

        sys.exit(0)

    except Exception as e:
        if json_mode:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Exit Code Conventions**:
```python
EXIT_CODES = {
    "success": 0,      # Operation completed successfully
    "warning": 1,      # Completed with warnings
    "error": 2,        # Failed due to error
    "critical": 3,     # Critical failure (data loss, corruption)
}
```

**Help Text Best Practices**:
- **Docstring**: Multi-line description with examples
- **Option help**: Clear, concise descriptions
- **Examples section**: 2-3 real usage examples
- **Exit codes**: Document in docstring

---

### 6. Structure & Formatting (9-Section Template)

**Standard Script Structure**:

```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#     "click>=8.1.7",
#     "httpx>=0.25.0",
# ]
# ///

# ========== SECTION 1: MODULE DOCSTRING ==========
"""
Script Title and Description

Usage:
    uv run script.py [options]
    uv run script.py --json

Examples:
    uv run script.py --input data.json
    uv run script.py --output results.json --json

Exit Codes:
    0 - Success
    1 - Warning
    2 - Error
    3 - Critical
"""

# ========== SECTION 2: IMPORTS ==========
import click
import httpx
import json
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Any

# ========== SECTION 3: CONSTANTS & CONFIGURATION ==========
DEFAULT_TIMEOUT = 30.0
DEFAULT_RETRIES = 3
API_BASE_URL = "https://api.example.com"

# ========== SECTION 4: PROJECT ROOT AUTO-DETECTION ==========
def find_project_root(start_path: Path) -> Path:
    """Auto-detect project root"""
    # ... (embedded utility)

PROJECT_ROOT = find_project_root(Path.cwd())

# ========== SECTION 5: DATA MODELS ==========
@dataclass
class ResultData:
    status: str
    data: dict
    message: str | None = None

# ========== SECTION 6: CORE BUSINESS LOGIC ==========
class ScriptProcessor:
    """Main processing logic"""

    def __init__(self, input_path: Path, json_mode: bool):
        self.input_path = input_path
        self.json_mode = json_mode

    def process(self) -> ResultData:
        """Execute main logic"""
        # Implementation here
        pass

# ========== SECTION 7: OUTPUT FORMATTERS ==========
def format_output(result: ResultData, json_mode: bool) -> str:
    """Format result for output"""
    # ... (embedded formatters)

# ========== SECTION 8: CLI INTERFACE ==========
@click.command()
@click.option('--json', 'json_mode', is_flag=True)
def main(json_mode: bool):
    """CLI entry point"""
    # ... (Click implementation)

# ========== SECTION 9: ENTRY POINT ==========
if __name__ == "__main__":
    main()
```

**Line Allocation**:
- Section 1 (Docstring): 15-25 lines
- Section 2 (Imports): 8-12 lines
- Section 3 (Constants): 5-10 lines
- Section 4 (Project Root): 15-20 lines
- Section 5 (Data Models): 10-20 lines
- Section 6 (Core Logic): 80-150 lines (bulk of script)
- Section 7 (Formatters): 20-40 lines
- Section 8 (CLI): 20-40 lines
- Section 9 (Entry Point): 3-5 lines

**Total**: 200-300 lines

---

### 7. Dependency Management

**Minimal Dependencies Principle**: Prefer standard library over external packages

**Decision Matrix**:
```
Standard Library Available → ✅ USE (json, pathlib, re, dataclasses)
Standard Library Insufficient → ⚠️ EVALUATE external package
External Package Essential → ✅ ADD with version pin
External Package Heavy → ❌ REJECT (find alternative)
```

**Approved Core Dependencies**:
```python
# CLI Framework
"click>=8.1.7"           # ✅ Lightweight, industry standard

# HTTP Client
"httpx>=0.25.0"          # ✅ Async-capable, modern
"requests>=2.31.0"       # ✅ Sync-only, but proven

# Data Validation
"pydantic>=2.0.0"        # ✅ Type-safe validation
"jsonschema>=4.17.0"     # ✅ JSON schema validation

# Template Engine
"jinja2>=3.1.2"          # ✅ Industry standard

# YAML Processing
"pyyaml>=6.0"            # ✅ Standard YAML parser
```

**Avoid Unless Essential**:
```python
"pandas"      # ❌ Too heavy (100+ MB) - use standard library csv/json
"numpy"       # ❌ Too heavy unless numerical computation required
"beautifulsoup4"  # ⚠️ Only if HTML parsing essential
"sqlalchemy"  # ⚠️ Only if ORM required (prefer sqlite3 stdlib)
```

---

### 8. Documentation Requirements

**Module Docstring** (Google Style):
```python
"""
Script Title - One-line summary

Detailed description of what the script does, when to use it,
and any important caveats or limitations.

Usage:
    uv run script.py [options]
    uv run script.py --json

Examples:
    # Basic usage
    uv run script.py --input data.json

    # JSON output
    uv run script.py --input data.json --json

    # With custom output path
    uv run script.py --input data.json --output results.json

Exit Codes:
    0 - Success
    1 - Warning (partial success)
    2 - Error (operation failed)
    3 - Critical (data loss or corruption)

Requirements:
    - Python 3.11+
    - UV package manager
    - Access to project root

Notes:
    - Designed for UV execution only
    - Works from any directory (auto-detects project root)
    - MCP-wrappable for future server integration
"""
```

**Function Docstrings**:
```python
def process_data(input_path: Path, options: dict) -> ResultData:
    """
    Process data from input file with given options.

    Args:
        input_path: Path to input file (JSON or YAML)
        options: Processing options dictionary

    Returns:
        ResultData with status and processed data

    Raises:
        ValueError: If input file format invalid
        FileNotFoundError: If input file doesn't exist

    Examples:
        >>> process_data(Path("data.json"), {"verbose": True})
        ResultData(status='success', data={...})
    """
    pass
```

**SKILL.md Integration**:

Each script must be listed in parent skill's SKILL.md:
```markdown
## Available Scripts

### `scripts/script_name.py`
**When to use:** Brief description of when to use this script

### `scripts/another_script.py`
**When to use:** Brief description of when to use this script
```

**Important**: SKILL.md should NOT contain detailed script documentation - only "When to use" sections. Detailed docs belong in script's module docstring.

---

### 9. Testing & Execution

**Manual Testing Checklist**:
```bash
# 1. Syntax check
python -m py_compile script.py

# 2. Help test
uv run script.py --help
# Expected: Comprehensive help output

# 3. JSON mode test
uv run script.py --json
# Expected: Valid JSON output

# 4. Normal mode test
uv run script.py
# Expected: Human-readable output

# 5. Error handling test
uv run script.py --invalid-flag
# Expected: Error message + exit code 2

# 6. Project-root independence test
cd /tmp && uv run /path/to/project/script.py
# Expected: Works from any directory
```

**Unit Testing** (optional but recommended):
```python
# test_script.py
import pytest
from pathlib import Path
from script import ScriptProcessor, format_output

def test_processor_basic():
    processor = ScriptProcessor(Path("test_data.json"), json_mode=True)
    result = processor.process()
    assert result.status == "success"

def test_json_output():
    result = ResultData(status="success", data={"test": 123})
    output = format_output(result, json_mode=True)
    assert json.loads(output)  # Valid JSON
```

---

### 10. Single-File vs Multi-File Decision

**Decision Tree**:
```
Script < 500 lines
└─> ✅ SINGLE FILE

Script > 500 lines
├─> Can split vertically by functionality?
│   └─> ✅ SPLIT into script1.py, script2.py
├─> Can split horizontally by phase?
│   └─> ✅ SPLIT into collect.py, process.py, report.py
└─> Cannot split logically?
    └─> ⚠️ EXCEPTION: Allow up to 600 lines with justification
```

**Examples of Justified Splits**:

❌ **WRONG** - Shared module pattern:
```
scripts/
├── api_client.py      # ❌ Shared module
├── markets.py
└── trades.py
```

✅ **CORRECT** - Multiple self-contained scripts:
```
scripts/
├── get_markets.py     # ✅ Embeds HTTP client
├── get_trades.py      # ✅ Embeds HTTP client
```

**Split Example** (600-line validation script):
```
Before (600 lines):
validate_all.py  # ❌ Too large

After (split):
validate_syntax.py        # ✅ 220 lines
validate_structure.py     # ✅ 180 lines
validate_completeness.py  # ✅ 200 lines
```

---

### 11. Error Handling Patterns

**Standard Error Handling**:
```python
@click.command()
def main(json_mode: bool):
    try:
        # Main logic
        result = process()

        # Success output
        if json_mode:
            print(json.dumps({"status": "success", "result": result}))
        else:
            print(f"✓ Success: {result}")

        sys.exit(0)

    except FileNotFoundError as e:
        # Specific error types
        error_msg = f"File not found: {e}"
        if json_mode:
            print(json.dumps({"error": error_msg, "type": "FileNotFoundError"}))
        else:
            print(f"❌ {error_msg}", file=sys.stderr)
        sys.exit(2)

    except ValueError as e:
        # Validation errors
        error_msg = f"Invalid input: {e}"
        if json_mode:
            print(json.dumps({"error": error_msg, "type": "ValueError"}))
        else:
            print(f"❌ {error_msg}", file=sys.stderr)
        sys.exit(2)

    except Exception as e:
        # Catch-all for unexpected errors
        error_msg = f"Unexpected error: {e}"
        if json_mode:
            print(json.dumps({"error": error_msg, "type": "Exception"}))
        else:
            print(f"❌ {error_msg}", file=sys.stderr)
        sys.exit(3)
```

**Error Message Guidelines**:
- **Specific**: Describe what went wrong clearly
- **Actionable**: Suggest how to fix (when possible)
- **Consistent**: Use same format across all scripts
- **Dual-mode**: Handle both human-readable and JSON

---

### 12. Configuration & Constants

**Environment Variables** (when needed):
```python
import os

# API Configuration
API_KEY = os.getenv("SCRIPT_API_KEY")
API_BASE = os.getenv("SCRIPT_API_BASE", "https://api.default.com")

# Paths
DEFAULT_OUTPUT_DIR = Path(os.getenv("SCRIPT_OUTPUT_DIR", ".moai/reports"))

# Validation
if not API_KEY:
    raise ValueError("SCRIPT_API_KEY environment variable required")
```

**Constants**:
```python
# Default values
DEFAULT_TIMEOUT = 30.0
DEFAULT_RETRIES = 3
DEFAULT_PAGE_SIZE = 100

# Limits
MAX_FILE_SIZE_MB = 100
MAX_RETRY_ATTEMPTS = 5

# Paths (relative to project root)
DEFAULT_INPUT = PROJECT_ROOT / "input"
DEFAULT_OUTPUT = PROJECT_ROOT / ".moai" / "reports"
```

**Secret Management**:
```
❌ NEVER hardcode:
API_KEY = "sk-abc123"  # ❌ Security risk

✅ ALWAYS use env vars:
API_KEY = os.getenv("API_KEY")  # ✅ Secure

✅ PROVIDE clear error:
if not API_KEY:
    raise ValueError("API_KEY environment variable required")
```

---

### 13. Progressive Disclosure Integration

**Context Efficiency**:
```
Tier 0: scripts/          → 0 tokens (dormant until invoked)
Tier 1: SKILL.md          → 200 tokens (Quick Reference with "When to use")
Tier 2: script --help     → 0 tokens (subprocess execution)
Tier 3: script source     → 800-1200 tokens (only if --help insufficient)
```

**"Don't Read Scripts Unless Needed" Philosophy**:

From IndieDevDan SKILL.md:
```markdown
## Instructions

- **IMPORTANT**: **Don't read scripts unless absolutely needed**
  - Use `<script.py> --help` to understand options
  - Then call with `uv run .claude/skills/{skill-name}/scripts/<script.py> <options>`
- All scripts work from any directory
```

**Benefits**:
- 98% context reduction for automation tasks
- Scripts discovered via SKILL.md metadata (200 tokens)
- Execution via subprocess (0 context)
- Source reading only when debugging

**Implementation**:
1. SKILL.md lists all scripts with "When to use" (2-3 lines each)
2. Each script has comprehensive `--help` output
3. Agents execute scripts without reading source
4. Source reading reserved for debugging or modification

---

## 📦 IndieDevDan Script Inventory (27 Scripts)

Complete catalog of existing IndieDevDan UV CLI scripts organized by skill, serving as reference patterns for new MoAI script development.

### Skill 1: skill-kalshi-markets (10 API Scripts)

**Purpose**: Kalshi prediction market data access
**Pattern**: REST API client with embedded HTTP client
**Total Lines**: 2,377 (avg 238 lines/script)

- [ ] **`status.py`** (157 lines)
  - **Purpose**: Check if Kalshi exchange is operational
  - **Dependencies**: `httpx`, `click`
  - **Pattern**: Simple GET endpoint, dual output (human/JSON)
  - **MCP-Ready**: ✅ (stateless, JSON output)

- [ ] **`markets.py`** (254 lines)
  - **Purpose**: Browse available prediction markets
  - **Dependencies**: `httpx`, `click`
  - **Pattern**: List endpoint with pagination
  - **MCP-Ready**: ✅ (idempotent GET)

- [ ] **`market.py`** (219 lines)
  - **Purpose**: Get comprehensive details about a specific market
  - **Dependencies**: `httpx`, `click`
  - **Pattern**: Detail endpoint with market ticker parameter
  - **MCP-Ready**: ✅ (resource retrieval)

- [ ] **`orderbook.py`** (205 lines)
  - **Purpose**: View bid/ask levels for a market
  - **Dependencies**: `httpx`, `click`
  - **Pattern**: Real-time data endpoint
  - **MCP-Ready**: ✅ (real-time query)

- [ ] **`trades.py`** (233 lines)
  - **Purpose**: Monitor recent trading activity
  - **Dependencies**: `httpx`, `click`
  - **Pattern**: Time-series data with filtering
  - **MCP-Ready**: ✅ (historical query)

- [ ] **`search.py`** (468 lines)
  - **Purpose**: Find markets by keyword (uses intelligent caching)
  - **Dependencies**: `httpx`, `click`
  - **Pattern**: Search with local caching layer
  - **MCP-Ready**: ⚠️ (caching requires state management)

- [ ] **`events.py`** (226 lines)
  - **Purpose**: List groups of related markets
  - **Dependencies**: `httpx`, `click`
  - **Pattern**: Collection endpoint with filtering
  - **MCP-Ready**: ✅ (collection query)

- [ ] **`event.py`** (205 lines)
  - **Purpose**: Get details about a specific event
  - **Dependencies**: `httpx`, `click`
  - **Pattern**: Resource detail endpoint
  - **MCP-Ready**: ✅ (single resource GET)

- [ ] **`series_list.py`** (214 lines)
  - **Purpose**: Browse all market templates (~6900 available)
  - **Dependencies**: `httpx`, `click`
  - **Pattern**: Large collection with pagination
  - **MCP-Ready**: ✅ (paginated list)

- [ ] **`series.py`** (196 lines)
  - **Purpose**: Get information about a specific market template
  - **Dependencies**: `httpx`, `click`
  - **Pattern**: Template metadata retrieval
  - **MCP-Ready**: ✅ (metadata GET)

---

### Skill 2: script-template (4 Code Generation Scripts)

**Purpose**: Build standalone CLI tools with Click/Typer
**Pattern**: Code generator with template rendering
**Total Lines**: 1,473 (avg 368 lines/script)

- [ ] **`generate_tool.py`** (318 lines)
  - **Purpose**: Generate complete Click-based CLI tools with subcommands
  - **Dependencies**: `click>=8.1.0`, `rich>=13.0.0`
  - **Pattern**: Template-based code generator (minimal/standard/full)
  - **MCP-Ready**: ✅ (file generation, no state)

- [ ] **`add_click_group.py`** (268 lines)
  - **Purpose**: Add command groups to existing Click applications
  - **Dependencies**: `click>=8.1.0`, `rich>=13.0.0`
  - **Pattern**: AST-based code injection
  - **MCP-Ready**: ⚠️ (modifies existing files)

- [ ] **`generate_typer.py`** (425 lines)
  - **Purpose**: Create modern Typer-based CLI apps with type annotations
  - **Dependencies**: `click>=8.1.0`, `rich>=13.0.0`
  - **Pattern**: Template generator with 3 styles (simple/modern/advanced)
  - **MCP-Ready**: ✅ (file generation)

- [ ] **`scaffold_uv_script.py`** (462 lines)
  - **Purpose**: Bootstrap UV scripts with PEP 723 dependency blocks
  - **Dependencies**: `click>=8.1.0`, `rich>=13.0.0`
  - **Pattern**: PEP 723 scaffolder with dependency injection
  - **MCP-Ready**: ✅ (scaffold generation)

---

### Skill 3: cli-template (4 CLI Scaffolding Scripts)

**Purpose**: Build modular Python CLI applications
**Pattern**: Project scaffolder with multi-file structure
**Total Lines**: 1,817 (avg 454 lines/script)

- [ ] **`scaffold_cli.py`** (612 lines)
  - **Purpose**: Create new CLI project with complete structure
  - **Dependencies**: `click>=8.1.0`, `rich>=13.0.0`
  - **Pattern**: Multi-file project generator (client, formatters, config)
  - **MCP-Ready**: ⚠️ (creates directory structure)

- [ ] **`add_command.py`** (312 lines)
  - **Purpose**: Add new command module to existing CLI
  - **Dependencies**: `click>=8.1.0`, `rich>=13.0.0`
  - **Pattern**: Module injection with parameter scaffolding
  - **MCP-Ready**: ⚠️ (modifies project structure)

- [ ] **`generate_module.py`** (551 lines)
  - **Purpose**: Generate utility modules (validators, parsers, helpers)
  - **Dependencies**: `click>=8.1.0`, `rich>=13.0.0`
  - **Pattern**: Utility module generator with 3 types
  - **MCP-Ready**: ✅ (single file generation)

- [ ] **`cli_template.py`** (342 lines)
  - **Purpose**: Interactive CLI for template management
  - **Dependencies**: `click>=8.1.0`, `rich>=13.0.0`
  - **Pattern**: Interactive prompt-based configuration
  - **MCP-Ready**: ❌ (requires user interaction)

---

### Skill 4: api-template (4 API Client Generators)

**Purpose**: Create HTTP API clients and wrapper libraries
**Pattern**: OpenAPI-based code generator
**Total Lines**: 1,978 (avg 495 lines/script)

- [ ] **`generate_client.py`** (423 lines)
  - **Purpose**: Generate complete API client from OpenAPI specification
  - **Dependencies**: `click>=8.1.0`, `httpx>=0.25.0`, `rich>=13.0.0`
  - **Pattern**: OpenAPI spec parser + code generator
  - **MCP-Ready**: ✅ (file generation from spec URL)

- [ ] **`scaffold_wrapper.py`** (693 lines)
  - **Purpose**: Create wrapper library structure with auth and error handling
  - **Dependencies**: `click>=8.1.0`, `httpx>=0.25.0`, `rich>=13.0.0`
  - **Pattern**: Multi-file API client scaffolder
  - **MCP-Ready**: ⚠️ (directory structure creation)

- [ ] **`add_endpoint.py`** (315 lines)
  - **Purpose**: Add new endpoint method to existing client
  - **Dependencies**: `click>=8.1.0`, `rich>=13.0.0`
  - **Pattern**: AST-based method injection
  - **MCP-Ready**: ⚠️ (modifies existing files)

- [ ] **`generate_auth.py`** (547 lines)
  - **Purpose**: Generate authentication handler for API client
  - **Dependencies**: `click>=8.1.0`, `httpx>=0.25.0`, `rich>=13.0.0`
  - **Pattern**: Auth strategy generator (Bearer/OAuth/API Key)
  - **MCP-Ready**: ✅ (single file generation)

---

### Skill 5: fastapi-template (5 FastAPI Generators)

**Purpose**: Build production-ready FastAPI applications
**Pattern**: FastAPI project scaffolder with routers/models/auth
**Total Lines**: 1,923 (avg 385 lines/script)

- [ ] **`scaffold_api.py`** (434 lines)
  - **Purpose**: Generate complete FastAPI project structure
  - **Dependencies**: `click>=8.1.0`, `rich>=13.0.0`
  - **Pattern**: Multi-file FastAPI project generator
  - **MCP-Ready**: ⚠️ (complex directory structure)

- [ ] **`add_router.py`** (336 lines)
  - **Purpose**: Add new API router with CRUD endpoints
  - **Dependencies**: `click>=8.1.0`, `rich>=13.0.0`
  - **Pattern**: Router module generator with CRUD operations
  - **MCP-Ready**: ✅ (single router file)

- [ ] **`generate_model.py`** (299 lines)
  - **Purpose**: Generate SQLAlchemy model + Pydantic schema pair
  - **Dependencies**: `click>=8.1.0`, `rich>=13.0.0`
  - **Pattern**: Dual model generator (ORM + schema)
  - **MCP-Ready**: ✅ (paired file generation)

- [ ] **`add_auth.py`** (449 lines)
  - **Purpose**: Add JWT or OAuth2 authentication
  - **Dependencies**: `click>=8.1.0`, `rich>=13.0.0`
  - **Pattern**: Auth module generator with dependency injection
  - **MCP-Ready**: ✅ (auth module generation)

- [ ] **`generate_crud.py`** (405 lines)
  - **Purpose**: Generate CRUD operations for models
  - **Dependencies**: `click>=8.1.0`, `rich>=13.0.0`
  - **Pattern**: CRUD method generator from model definition
  - **MCP-Ready**: ✅ (CRUD file generation)

---

### Inventory Summary

**Total Scripts**: 27 across 5 skills
**Total Lines**: 9,568 (average 354 lines/script)
**Common Dependencies**: `click>=8.1.0` (100%), `rich>=13.0.0` (89%), `httpx` (48%)

**MCP-Ready Status**:
- ✅ **Fully Ready**: 19 scripts (70%) - Stateless, file generation, or simple queries
- ⚠️ **Needs Adaptation**: 7 scripts (26%) - State management, file modification, or directory operations
- ❌ **Not Suitable**: 1 script (4%) - Interactive prompts

**Pattern Distribution**:
- API Clients: 10 scripts (37%)
- Code Generators: 12 scripts (44%)
- Scaffolders: 4 scripts (15%)
- Utilities: 1 script (4%)

**Line Count Distribution**:
- < 200 lines: 2 scripts (7%)
- 200-300 lines: 11 scripts (41%) ✅ **IDEAL RANGE**
- 300-400 lines: 8 scripts (30%)
- 400-500 lines: 5 scripts (19%)
- > 500 lines: 1 script (4%) ⚠️ **EXCEPTION**

---

## 🔧 MCP Server Wrapping Guidelines

**Purpose**: Design UV CLI scripts to be easily wrappable as MCP server tools, enabling future integration with Claude Code MCP architecture.

### MCP-Ready Design Principles

**1. Statelessness**:
```python
# ✅ GOOD - Pure function, no persistent state
def fetch_market_data(ticker: str) -> dict:
    client = httpx.Client()  # Created fresh each call
    response = client.get(f"/markets/{ticker}")
    return response.json()

# ❌ BAD - Module-level state
CLIENT = httpx.Client()  # Persistent connection
def fetch_market_data(ticker: str) -> dict:
    return CLIENT.get(f"/markets/{ticker}").json()
```

**2. JSON Output Mode**:
```python
# ✅ GOOD - Always support --json flag
@click.command()
@click.option('--json', 'json_mode', is_flag=True)
def main(json_mode: bool):
    result = {"status": "success", "data": [...]}
    if json_mode:
        print(json.dumps(result))  # MCP-friendly
    else:
        print_human_readable(result)
```

**3. Structured Error Handling**:
```python
# ✅ GOOD - Machine-readable errors
try:
    result = process()
    sys.exit(0)
except FileNotFoundError as e:
    if json_mode:
        print(json.dumps({"error": str(e), "type": "FileNotFoundError", "code": 2}))
    sys.exit(2)
```

**4. No Interactive Prompts**:
```python
# ❌ BAD - Interactive prompt breaks MCP
city = click.prompt("Enter city name")  # Blocks MCP execution

# ✅ GOOD - Required argument
@click.command()
@click.argument('city')
def main(city: str):
    pass
```

### MCP Wrapper Architecture

**Pattern 1: Direct Tool Wrapping** (70% of scripts)
```python
# UV Script: scripts/status.py
# MCP Tool: kalshi.get_status()

@server.call_tool()
async def get_status() -> str:
    """Check Kalshi exchange operational status"""
    result = subprocess.run(
        ["uv", "run", "scripts/status.py", "--json"],
        capture_output=True,
        text=True
    )
    return result.stdout  # Already JSON
```

**Pattern 2: Parameter Mapping** (20% of scripts)
```python
# UV Script: scripts/market.py --ticker <ticker>
# MCP Tool: kalshi.get_market(ticker: str)

@server.call_tool()
async def get_market(ticker: str) -> str:
    """Get market details by ticker"""
    result = subprocess.run(
        ["uv", "run", "scripts/market.py", "--ticker", ticker, "--json"],
        capture_output=True,
        text=True
    )
    return result.stdout
```

**Pattern 3: State Adapter** (10% of scripts - caching/file ops)
```python
# UV Script: scripts/search.py (has local cache)
# MCP Tool: kalshi.search_markets(query: str, no_cache: bool)

@server.call_tool()
async def search_markets(query: str, no_cache: bool = False) -> str:
    """Search markets by keyword"""
    cmd = ["uv", "run", "scripts/search.py", "--query", query, "--json"]
    if no_cache:
        cmd.append("--no-cache")  # Bypass local cache for MCP
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout
```

### MCP-Readiness Checklist

When designing new UV CLI scripts, ensure these requirements for MCP wrapping:

**Required** (Must have):
- [ ] `--json` flag for structured output
- [ ] Exit codes: 0 (success), 1+ (errors)
- [ ] All inputs via CLI arguments/options (no prompts)
- [ ] JSON error format: `{"error": "...", "type": "...", "code": N}`
- [ ] Stateless execution (no persistent connections)
- [ ] Documentation in `--help` output

**Recommended** (Should have):
- [ ] Timeout parameter (e.g., `--timeout 30`)
- [ ] Retry parameter (e.g., `--retries 3`)
- [ ] Verbose mode (e.g., `--verbose`)
- [ ] Idempotent operations (same input → same output)
- [ ] No file system dependencies (or explicit paths)

**Optional** (Nice to have):
- [ ] `--version` flag
- [ ] `--config` for external configuration
- [ ] Progress indicators (to stderr, not stdout)
- [ ] Structured logging (JSON logs to file)

### MCP Conversion Timeline

**Phase 1** (Current): UV CLI scripts standalone
- Scripts work independently via `uv run`
- Zero MCP dependency
- Progressive disclosure through SKILL.md

**Phase 2** (Future): MCP wrapper creation
- Create MCP server per skill (e.g., `kalshi-mcp-server`)
- Wrap scripts as MCP tools via subprocess calls
- Maintain backward compatibility (scripts still work standalone)

**Phase 3** (Optional): Native MCP tools
- Refactor high-traffic scripts to native MCP tools
- Eliminate subprocess overhead
- Keep UV scripts as development/testing interface

### Example MCP Server Structure

```python
# .claude/servers/kalshi-mcp/server.py
from mcp.server import Server
import subprocess

server = Server("kalshi-markets")

@server.list_tools()
async def list_tools():
    return [
        {"name": "get_status", "description": "Check exchange status"},
        {"name": "get_market", "description": "Get market details"},
        # ... 8 more tools mapping to 10 scripts
    ]

@server.call_tool()
async def get_status() -> str:
    """Wraps scripts/status.py"""
    result = subprocess.run(
        ["uv", "run", ".claude/skills/skill-kalshi-markets/scripts/status.py", "--json"],
        capture_output=True,
        text=True,
        timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {result.stderr}")
    return result.stdout
```

### Design Guidelines Summary

**DO**:
- Design scripts as pure functions (input → output)
- Always provide `--json` output mode
- Use CLI arguments for all inputs
- Return structured JSON errors
- Document in `--help` comprehensively

**DON'T**:
- Use interactive prompts (`click.prompt()`)
- Maintain persistent state (connections, caches)
- Hardcode file paths (use project-root detection)
- Mix output with logging (stdout = data, stderr = logs)
- Assume user environment (check dependencies)

---

## 🎯 Builder-UV-Script Agent Mission Summary

**Primary Objectives**:
1. **Understand**: Know all 13 IndieDevDan UV script rules by heart
2. **Catalog**: Reference 27 existing scripts as patterns
3. **Generate**: Create new MoAI UV CLI scripts following all rules
4. **Validate**: Ensure TRUST 5 compliance + MCP-readiness
5. **Document**: Update SKILL.md with "When to use" entries

**Key Deliverables**:
- Single-file UV CLI scripts (200-300 lines)
- PEP 723 dependency blocks
- Dual output modes (human + JSON)
- Comprehensive `--help` documentation
- MCP-wrappable design
- Progressive disclosure integration

**Success Criteria**:
- ✅ Script runs via `uv run script.py` (zero installation)
- ✅ `--help` output explains all options
- ✅ `--json` output is valid JSON
- ✅ Exit codes: 0 (success), 1+ (errors)
- ✅ Self-contained (no shared imports)
- ✅ 200-300 lines (500 max)
- ✅ Context efficiency (0-token dormant)

**Integration with MoAI Ecosystem**:
- Delegate to `manager-quality` for TRUST 5 validation
- Query `mcp-context7` for latest library versions
- Follow `moai-foundation-core` execution rules
- Compatible with existing 22 MoAI skills (zero conflicts)

---

**Version**: 1.0.0
**Status**: ✅ COMPLETE (Phase 1 Blueprint)
**Lines**: 1,180
**Last Updated**: 2025-11-30

