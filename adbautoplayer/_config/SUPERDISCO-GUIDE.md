# Superdisco Developer Guide

> **Version**: 1.0.0
> **Last Updated**: 2025-12-01
> **Audience**: Developers working with Superdisco customizations

---

## Table of Contents

1. [Overview](#1-overview)
2. [Project Structure](#2-project-structure)
3. [Builder Ecosystem](#3-builder-ecosystem)
4. [Custom Skills](#4-custom-skills)
5. [Custom Commands](#5-custom-commands)
6. [Standards & Conventions](#6-standards--conventions)
7. [Version Management](#7-version-management)
8. [Quick Reference](#8-quick-reference)

---

## 1. Overview

### What is Superdisco?

Superdisco is a **customized fork** of MoAI-ADK (Modular AI Agent Development Kit) that adds specialized builder tools and workflows for rapid agent development.

### Repository Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                    UPSTREAM (Original)                       │
│            https://github.com/modu-ai/moai-adk              │
│                         │                                    │
│                         │ fork                               │
│                         ▼                                    │
│                    SUPERDISCO FORK                           │
│         https://github.com/superdisco-agents/moai-adk       │
│                         │                                    │
│                         │ clone                              │
│                         ▼                                    │
│                   LOCAL WORKSPACE                            │
│                   your-workspace/moai-adk/                  │
└─────────────────────────────────────────────────────────────┘
```

### Key Differentiators

| Feature | MoAI-ADK (Upstream) | Superdisco (Fork) |
|---------|---------------------|-------------------|
| Builder Agents | 3 (agent, skill, command) | **5** (+reverse-engineer, workflow-designer) |
| UV Scripts | Basic support | **29+ scripts** with IndieDevDan standards |
| Output Format | Standard | **TOON v4.0** (40-60% token savings) |
| Project Structure | Single location | **2-Location Architecture** |
| Fork Management | N/A | **superdisco-moai-sync** skill |

---

## 2. Project Structure

### 2-Location Architecture

Superdisco uses a simplified 2-location structure that separates **source templates** from **deployed customizations**:

```
your-workspace/                            # Workspace Root
│
├── .claude/                               # DESTINATION - Deployed Skills & Commands
│   ├── agents/                            # Agent definitions
│   │   └── moai/
│   │       ├── moai-expert/              # Domain experts (7)
│   │       ├── moai-manager/             # Workflow managers (8)
│   │       ├── moai-builder/             # Meta-generators (5) ← SUPERDISCO
│   │       ├── moai-mcp/                 # MCP integrators (5)
│   │       └── moai-ai/                  # AI services (1)
│   │
│   ├── commands/                          # Slash commands
│   │   ├── moai/                         # Core MoAI commands
│   │   └── builder/                      # SUPERDISCO builder commands (5)
│   │
│   └── skills/                           # Skills (28 total)
│       ├── moai-foundation-*             # Foundation skills (5)
│       ├── moai-lang-*                   # Language skills
│       ├── moai-library-*                # Library skills
│       ├── builder-workflow/             # SUPERDISCO
│       ├── builder-skill-uvscript/       # SUPERDISCO (29 scripts)
│       └── superdisco-moai-sync/         # SUPERDISCO (6 scripts)
│
└── moai-adk/                              # SOURCE - Git Repository
    ├── docs/                              # Documentation
    │   ├── INSTALL.md                    # Installation guide
    │   ├── PROJECT-TREE-RULES.md         # Structure rules
    │   └── SUPERDISCO-GUIDE.md           # This file
    └── src/moai_adk/templates/            # Package templates
        └── .claude/                       # Base skills (22)
            ├── agents/
            ├── commands/
            └── skills/
```

### Color Coding Convention

Throughout documentation and code:

| Color | Meaning | Example |
|-------|---------|---------|
| **Red** | MoAI Official | Core framework agents |
| **Yellow** | Superdisco Custom | Builder ecosystem |
| **Blue** | Claude Default | Built-in capabilities |

---

## 3. Builder Ecosystem

### Overview

The Builder Ecosystem is Superdisco's flagship feature - a complete pipeline for creating agents, skills, and UV scripts from repository analysis.

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BUILDER ECOSYSTEM PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STEP 1              STEP 2              STEP 3              STEP 4         │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐       ┌──────────┐     │
│  │Repository│──────▶│  SPEC    │──────▶│  Skill   │──────▶│  Agent   │     │
│  │ Analysis │       │ Document │       │ Creation │       │Definition│     │
│  └──────────┘       └──────────┘       └──────────┘       └──────────┘     │
│       │                  │                  │                  │            │
│       ▼                  ▼                  ▼                  ▼            │
│  builder-         builder-           builder-           builder-           │
│  reverse-         workflow-          skill              agent              │
│  engineer         designer                                                  │
│       │                                                                     │
│       │              STEP 5                                                 │
│       │         ┌──────────────┐                                           │
│       └────────▶│  UV Scripts  │                                           │
│                 │  Generation  │                                           │
│                 └──────────────┘                                           │
│                       │                                                     │
│                       ▼                                                     │
│                 builder-workflow                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Builder Agents (5 Total)

#### 1. builder-reverse-engineer

**Purpose**: Analyze external repositories and generate TOON-formatted analysis

**Location**: `.claude/agents/moai/moai-builder/builder-reverse-engineer.md`

**Command**: `/builder:reverse-engineer [repo-url]`

**Output**:
- Repository structure analysis
- Technology stack identification
- Architecture patterns
- TOON v4.0 formatted summary

**Example**:
```bash
/builder:reverse-engineer https://github.com/example/repo
```

---

#### 2. builder-workflow-designer

**Purpose**: Create SPEC documents with workflow diagrams

**Location**: `.claude/agents/moai/moai-builder/builder-workflow-designer.md`

**Command**: `/builder:workflow-designer [workflow-name]`

**Output**:
- SPEC document (EARS-style requirements)
- Mermaid workflow diagrams
- Component relationship maps

**Example**:
```bash
/builder:workflow-designer api-testing
```

---

#### 3. builder-skill

**Purpose**: Generate skill directory structure with SKILL.md

**Location**: `.claude/agents/moai/moai-builder/builder-skill.md`

**Command**: `/builder:generate-skill [name] [description]`

**Output**:
```
.claude/skills/{skill-name}/
├── SKILL.md           # Skill definition
├── modules/           # Modular components
└── scripts/           # UV CLI scripts (if applicable)
```

**Example**:
```bash
/builder:generate-skill data-processor "Process and transform data files"
```

---

#### 4. builder-agent

**Purpose**: Create agent definition files

**Location**: `.claude/agents/moai/moai-builder/builder-agent.md`

**Command**: `/builder:generate-workflow [agent-name]`

**Output**:
- Agent YAML frontmatter
- Tool permissions
- Skill associations
- Behavioral instructions

**Example**:
```bash
/builder:generate-workflow report-generator
```

---

#### 5. builder-workflow

**Purpose**: Generate UV CLI scripts following IndieDevDan patterns

**Location**: `.claude/agents/moai/moai-builder/builder-workflow.md`

**Command**: `/builder:generate-script [skill-name] [script-name]`

**Output**:
- PEP 723 compliant UV script
- Click CLI interface
- Dual output mode (stdout/file)
- Comprehensive error handling

**Example**:
```bash
/builder:generate-script data-processor convert_format
```

---

## 4. Custom Skills

### Overview

Superdisco adds 4 custom skills on top of MoAI-ADK's base 22 skills.

### Skill Directory

| Skill | Purpose | Scripts | Location |
|-------|---------|---------|----------|
| `builder-workflow` | UV script orchestration | - | `.claude/skills/builder-workflow/` |
| `builder-skill-uvscript` | UV script library | **29** | `.claude/skills/builder-skill-uvscript/` |
| `superdisco-moai-sync` | Fork management | **6** | `.claude/skills/superdisco-moai-sync/` |
| `moai-library-toon` | TOON v4.0 format | - | `.claude/skills/moai-library-toon/` |

---

### builder-skill-uvscript

**29 UV Scripts Library**:

| Category | Scripts | Purpose |
|----------|---------|---------|
| Analysis | `analyze_*.py` (6) | Code, dependency, security analysis |
| Generation | `generate_*.py` (5) | Code, docs, test generation |
| Validation | `validate_*.py` (4) | Schema, config, code validation |
| Conversion | `convert_*.py` (3) | Format, encoding conversion |
| Utilities | `util_*.py` (11) | File, string, date utilities |

---

### superdisco-moai-sync

**6 Fork Management Scripts**:

| Script | Purpose |
|--------|---------|
| `sync_upstream.py` | Pull changes from modu-ai/moai-adk |
| `compare_versions.py` | Compare fork vs upstream |
| `merge_selective.py` | Selective merge of upstream changes |
| `backup_customizations.py` | Backup Superdisco-specific files |
| `restore_customizations.py` | Restore after upstream merge |
| `status_report.py` | Generate sync status report |

---

### moai-library-toon

**TOON v4.0 Format Specification**:

TOON (Token-Optimized Output Notation) reduces token usage by 40-60%.

**Key Features**:
- Compressed headers (`##` → `#`)
- Abbreviated keywords (`function` → `fn`)
- Minimal whitespace
- Structured data blocks

**Example**:
```
# Standard Output (100 tokens)
## Analysis Results
The function `calculateTotal` in file `utils.js`
has a cyclomatic complexity of 15, which exceeds
the recommended maximum of 10.

# TOON Output (45 tokens)
#AR
fn:calculateTotal|file:utils.js
complexity:15|max:10|status:EXCEEDS
```

---

## 5. Custom Commands

### Command Namespace: `/builder:*`

All Superdisco commands use the `builder:` namespace prefix.

| Command | Arguments | Description |
|---------|-----------|-------------|
| `/builder:reverse-engineer` | `[repo-url]` | Analyze external repository |
| `/builder:workflow-designer` | `[workflow-name]` | Create SPEC + diagrams |
| `/builder:generate-skill` | `[name] [description]` | Generate skill structure |
| `/builder:generate-script` | `[skill] [script-name]` | Create UV CLI script |
| `/builder:generate-workflow` | `[name]` | Full workflow generation |

### Command Location

```
.claude/commands/builder/
├── reverse-engineer.md
├── workflow-designer.md
├── generate-skill.md
├── generate-script.md
└── generate-workflow.md
```

### Usage Examples

```bash
# Analyze a GitHub repository
/builder:reverse-engineer https://github.com/fastapi/fastapi

# Design a new workflow
/builder:workflow-designer user-authentication

# Create a new skill
/builder:generate-skill api-client "HTTP client with retry logic"

# Add a script to existing skill
/builder:generate-script api-client fetch_data

# Generate complete workflow (skill + agent + scripts)
/builder:generate-workflow data-pipeline
```

---

## 6. Standards & Conventions

### TOON v4.0 Format

**Token-Efficient Output Standard**

| Principle | Standard | TOON |
|-----------|----------|------|
| Headers | `## Section Title` | `#ST` |
| Lists | `- Item one\n- Item two` | `items:[one,two]` |
| Status | `Status: Completed` | `s:OK` |
| Errors | `Error: File not found` | `e:NOTFOUND` |

**Savings**: 40-60% token reduction

---

### IndieDevDan 13 Rules

**UV Script Standards**:

1. **PEP 723** - Inline script metadata
2. **Single File** - Self-contained, no external dependencies
3. **Click CLI** - Command-line interface framework
4. **Dual Output** - stdout and file output modes
5. **200-300 Lines** - Optimal script length
6. **Type Hints** - Full typing coverage
7. **Docstrings** - Google-style documentation
8. **Error Handling** - Comprehensive try/except
9. **Logging** - Structured logging support
10. **Testing** - Inline test functions
11. **Configuration** - Environment variable support
12. **Progress** - Rich progress indicators
13. **Exit Codes** - Standard exit code conventions

**Example Header**:
```python
#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click>=8.0",
#     "rich>=13.0",
# ]
# ///
"""
Script description following IndieDevDan standards.
"""
```

---

### Color Coding

Use consistent colors in documentation and UI:

| Color | Code | Usage |
|-------|------|-------|
| Red | `#FF6B6B` | MoAI official components |
| Yellow | `#FFE66D` | Superdisco customizations |
| Blue | `#4ECDC4` | Claude/Anthropic defaults |
| Green | `#95E1A3` | Success/completed states |
| Gray | `#A0A0A0` | Disabled/inactive |

---

## 7. Version Management

### Fork Synchronization

**Upstream**: `https://github.com/modu-ai/moai-adk`
**Fork**: `https://github.com/superdisco-agents/moai-adk`

### Sync Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    SYNC WORKFLOW                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. BACKUP        2. FETCH         3. MERGE       4. RESTORE│
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐│
│  │ Backup  │────▶│  Fetch  │────▶│Selective│────▶│ Restore ││
│  │ Custom  │     │Upstream │     │  Merge  │     │ Custom  ││
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘│
│       │               │               │               │      │
│       ▼               ▼               ▼               ▼      │
│  backup_         git fetch       merge_          restore_   │
│  customizations  upstream        selective       customizations│
│  .py             main            .py             .py         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Git Remotes Setup

```bash
cd moai-adk

# Origin = Superdisco fork
git remote -v
# origin  https://github.com/superdisco-agents/moai-adk.git (fetch)
# origin  https://github.com/superdisco-agents/moai-adk.git (push)

# Upstream = Original MoAI-ADK
git remote add upstream https://github.com/modu-ai/moai-adk.git
```

### Protected Files (Never Overwrite)

```
.claude/agents/moai/moai-builder/builder-reverse-engineer.md
.claude/agents/moai/moai-builder/builder-workflow-designer.md
.claude/commands/builder/*
.claude/skills/builder-*
.claude/skills/superdisco-*
```

---

## 8. Quick Reference

### Commands Cheatsheet

```bash
# Repository Analysis
/builder:reverse-engineer [repo-url]

# Workflow Design
/builder:workflow-designer [name]

# Skill Generation
/builder:generate-skill [name] [description]

# Script Generation
/builder:generate-script [skill] [script]

# Full Workflow
/builder:generate-workflow [name]
```

### File Locations

| Component | Path |
|-----------|------|
| Builder Agents | `.claude/agents/moai/moai-builder/` |
| Builder Commands | `.claude/commands/builder/` |
| Custom Skills | `.claude/skills/builder-*`, `.claude/skills/superdisco-*` |
| UV Scripts | `.claude/skills/*/scripts/` |

### Agent Hierarchy

```
Tier 1: expert-*    (7 agents)  - Domain specialists
Tier 2: manager-*   (8 agents)  - Workflow orchestration
Tier 3: builder-*   (5 agents)  - Meta-generation [SUPERDISCO]
Tier 4: mcp-*       (5 agents)  - External integrations
Tier 5: ai-*        (1 agent)   - AI services
```

### Support

- **Issues**: https://github.com/superdisco-agents/moai-adk/issues
- **Feedback**: `/moai:9-feedback [description]`

---

**Document Version**: 1.0.0
**Maintained By**: Superdisco Team
**Last Updated**: 2025-12-01
