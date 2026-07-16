# Pattern: Universal Single-File Rules

**Module**: `pattern-single-file.md`
**Version**: 1.0.0
**Category**: Design Patterns

---

## Purpose

This module defines the universal single-file rules that apply to BOTH UV Python scripts (`.py`) AND Markdown modules (`.md`).

---

## Core Principle

> **Each file must be complete, self-contained, and independently useful.**

A file should not require reading other files to understand or use it.

---

## Universal Rules (Apply to Both)

| Rule | Scripts (.py) | Modules (.md) |
|------|---------------|---------------|
| **Self-Contained** | Zero local imports | Zero file dependencies |
| **Single Responsibility** | One focused function | One focused topic |
| **Size Limit** | 200-500 lines | 100-500 lines |
| **Naming** | `{prefix}_{action}.py` | `{category}-{topic}.md` |
| **Dual Output** | JSON + Human readable | Structured + Plain text |
| **No External Context** | Embed all defaults | Include all information |

---

## Script-Specific Rules (.py)

### 1. ASTRAL UV Pattern (Mandatory)
```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#     "httpx>=0.25.0",
#     "click>=8.1.0",
# ]
# ///
```
**Order**: Shebang → UV block → Docstring → Imports → Code

### 2. Size Constraints
- **Minimum**: 100 lines (complete functionality)
- **Target**: 200-300 lines (optimal)
- **Maximum**: 500 lines (absolute limit)

### 3. Zero Local Imports
```python
# GOOD: Only stdlib and declared dependencies
import json
import sys
from pathlib import Path
import click
import httpx

# BAD: Never import from local files
from .utils import helper        # FORBIDDEN
from shared.client import API    # FORBIDDEN
```

### 4. Embedded HTTP Clients
```python
# GOOD: Client embedded in script
class APIClient:
    def __init__(self, base_url: str):
        self.client = httpx.Client(base_url=base_url)

    def get(self, path: str) -> dict:
        response = self.client.get(path)
        return response.json()

# BAD: Importing shared client
from shared.api import APIClient  # FORBIDDEN
```

### 5. Dual Output Mode
```python
@click.command()
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
def main(json_output: bool):
    result = do_work()

    if json_output:
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(format_human_readable(result))
```

### 6. CLI Help Support
```python
@click.command()
@click.option('--help', is_flag=True, help='Show help message')
def main():
    """
    Script description for --help output.

    Examples:
        uv run script.py --json
        uv run script.py --verbose
    """
```

### 7. Exit Codes
```python
# Standard exit codes
EXIT_SUCCESS = 0    # Operation completed successfully
EXIT_WARNING = 1    # Completed with warnings
EXIT_ERROR = 2      # Operation failed
EXIT_CRITICAL = 3   # Critical failure

sys.exit(EXIT_SUCCESS)
```

### 8. Project Root Detection
```python
def find_project_root(start_path: Path = None) -> Path:
    """Auto-detect project root via markers."""
    markers = ['.git', 'pyproject.toml', '.moai', 'CLAUDE.md']
    current = start_path or Path.cwd()

    for parent in [current] + list(current.parents):
        for marker in markers:
            if (parent / marker).exists():
                return parent
    return current
```

---

## Module-Specific Rules (.md)

### 1. Structured Sections
```markdown
# Module Title

**Module**: `{category}-{topic}.md`
**Version**: X.Y.Z
**Category**: {Category Name}

---

## Purpose
[Brief description]

---

## Content Section 1
[Main content]

---

## Content Section 2
[More content]

---

**Version**: X.Y.Z
**Last Updated**: YYYY-MM-DD
```

### 2. Size Constraints
- **Minimum**: 50 lines (meaningful content)
- **Target**: 100-300 lines (optimal)
- **Maximum**: 500 lines (absolute limit)

### 3. Zero File Dependencies
```markdown
<!-- GOOD: Self-contained content -->
## API Endpoints
- GET /users - List all users
- POST /users - Create user
- GET /users/{id} - Get user by ID

<!-- BAD: References to other files -->
See `api-authentication.md` for auth details  <!-- AVOID -->
Refer to `../shared/endpoints.md`              <!-- FORBIDDEN -->
```

### 4. Complete Information
```markdown
<!-- GOOD: All info in one place -->
## Authentication

### OAuth2 Flow
1. Redirect to /auth/authorize
2. User grants permission
3. Receive code at callback URL
4. Exchange code for token at /auth/token

### Token Format
- Type: Bearer
- Header: Authorization: Bearer {token}
- Expiry: 1 hour

<!-- BAD: Partial info requiring external lookup -->
## Authentication
See OAuth2 specification for details.  <!-- INCOMPLETE -->
```

### 5. Tables for Structured Data
```markdown
| Endpoint | Method | Description |
|----------|--------|-------------|
| /users | GET | List all users |
| /users | POST | Create user |
| /users/{id} | GET | Get user |
| /users/{id} | PUT | Update user |
| /users/{id} | DELETE | Delete user |
```

### 6. Code Blocks with Language Tags
```markdown
```python
# Always specify language
def example():
    pass
```

```json
{
  "key": "value"
}
```

```bash
uv run script.py --json
```
```

---

## Common Anti-Patterns

### Scripts Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Local imports | Breaks independence | Embed all code |
| Shared utils | Creates coupling | Duplicate if needed |
| Config files | External dependency | Embed defaults |
| Env vars required | Won't work standalone | Make optional |
| No --help | Poor discoverability | Add CLI help |
| No --json | Not MCP-ready | Add JSON output |

### Module Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| File references | Breaks independence | Embed all content |
| Incomplete info | Requires lookup | Include everything |
| No structure | Hard to scan | Add clear sections |
| No version | Can't track changes | Add version header |
| Wall of text | Hard to read | Use tables, lists |
| Missing examples | Abstract concepts | Add concrete examples |

---

## Checklist: Before Creating a File

### Script Checklist
- [ ] Has ASTRAL UV shebang and dependencies block
- [ ] Zero local imports (only stdlib + declared deps)
- [ ] Under 500 lines
- [ ] Supports `--help` flag
- [ ] Supports `--json` flag
- [ ] Has proper exit codes
- [ ] Uses project root detection
- [ ] Follows prefix naming: `{skill}_{action}.py`

### Module Checklist
- [ ] Has structured sections with headers
- [ ] Under 500 lines
- [ ] Zero file dependencies
- [ ] Complete information (no "see other file")
- [ ] Uses tables for structured data
- [ ] Has version and date in header/footer
- [ ] Follows prefix naming: `{category}-{topic}.md`

---

## Size Guide

### Scripts
```
Lines    | Assessment
---------|------------
< 100    | Too thin - probably missing features
100-200  | Simple script - ok for basic operations
200-300  | Optimal - full featured, maintainable
300-500  | Complex - consider if can be split
> 500    | Too large - must split functionality
```

### Modules
```
Lines    | Assessment
---------|------------
< 50     | Too thin - probably incomplete
50-100   | Concise - good for simple topics
100-300  | Optimal - comprehensive coverage
300-500  | Detailed - ok for complex topics
> 500    | Too large - split into subtopics
```

---

## Examples

### Good Script Example
```python
#!/usr/bin/env python3
# /// script
# dependencies = ["httpx>=0.25.0", "click>=8.1.0"]
# ///
"""
Fetch market data from Kalshi API.

Examples:
    uv run kalshi_get-market.py --ticker KXBTC --json
    uv run kalshi_get-market.py --help
"""
import json
import sys
import click
import httpx

# Constants (embedded, not from config)
BASE_URL = "https://api.kalshi.com/v2"
DEFAULT_TIMEOUT = 30

# ... rest of implementation (200-300 lines total)
```

### Good Module Example
```markdown
# API: Kalshi Market Endpoints

**Module**: `api-kalshi-endpoints.md`
**Version**: 1.0.0
**Category**: API Reference

---

## Purpose

Complete reference for Kalshi market API endpoints.

---

## Endpoints

| Path | Method | Description |
|------|--------|-------------|
| /markets | GET | List all markets |
| /markets/{ticker} | GET | Get market details |

## Authentication

Bearer token in Authorization header.

## Rate Limits

100 requests per minute per API key.

---

**Version**: 1.0.0
**Last Updated**: 2025-12-02
```

---

## Quick Reference

```
UNIVERSAL RULES:
  - Self-contained (no external dependencies)
  - Single responsibility
  - Proper naming with prefixes
  - Size limits enforced

SCRIPTS (.py):
  - ASTRAL UV pattern mandatory
  - 200-500 lines optimal
  - --help and --json required
  - Zero local imports

MODULES (.md):
  - Structured sections
  - 100-300 lines optimal
  - Complete information
  - Tables for data
```

---

**Version**: 1.0.0
**Last Updated**: 2025-12-02
