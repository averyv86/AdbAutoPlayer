# MoAI-ADK Installation Guide

## Overview

This guide walks you through installing **moai-adk** (MoAI Application Development Kit) into a new workspace using the same approach demonstrated in this project. MoAI-ADK is a SPEC-First TDD framework with AI agent orchestration powered by the Alfred super agent.

**What you'll achieve:**
- Set up moai-adk as a uv workspace member (monorepo structure)
- Install moai-adk in editable mode for local development
- Configure Claude Code with Alfred's 24 specialized AI agents
- Enable parallel agent execution for efficient task processing

## Prerequisites

Before starting, ensure you have:

- **Python 3.11+** (tested with 3.13.6)
- **uv** package manager ([installation guide](https://docs.astral.sh/uv/))
- **Git** for cloning repositories
- **Claude Code CLI** for AI agent orchestration
- **Node.js/npm** (for MCP server integrations)

Verify your setup:
```bash
python --version   # Should be 3.11 or higher
uv --version       # Should be installed
git --version      # Should be installed
```

## Quick Start

For experienced users, here's the TL;DR:

```bash
# Navigate to your workspace directory
cd /path/to/your/workspace

# Clone moai-adk (superdisco-agents fork with custom enhancements)
git clone https://github.com/superdisco-agents/moai-adk.git moai-adk
# Note: Original upstream is https://github.com/modu-ai/moai-adk.git

# Create workspace configuration
cat > pyproject.toml << 'EOF'
[project]
name = "your-workspace-name"
version = "0.1.0"
description = "Workspace containing moai-adk and related projects"
requires-python = ">=3.11"
dependencies = []

[tool.uv.workspace]
members = ["moai-adk"]

[dependency-groups]
dev = []
EOF

# Pin Python version
echo "3.13.6" > .python-version

# Install moai-adk in editable mode
uv pip install -e moai-adk

# Migrate workspace configuration
cp -r moai-adk/.claude ./
cp -r moai-adk/.moai ./
cp moai-adk/.mcp.json ./
cp moai-adk/.claudeignore ./
cp moai-adk/CLAUDE.md ./
cp moai-adk/CLAUDE.local.md ./

# Update paths in CLAUDE.local.md to use $CLAUDE_PROJECT_DIR

# Verify installation
uv run moai-adk --version
```

## Step-by-Step Installation

### 1. Clone the moai-adk Repository

Navigate to your workspace directory and clone moai-adk:

```bash
cd /path/to/your/workspace

# Clone superdisco-agents fork (recommended - includes custom enhancements)
git clone https://github.com/superdisco-agents/moai-adk.git moai-adk

# Optional: Add upstream for syncing with original repo
cd moai-adk
git remote add upstream https://github.com/modu-ai/moai-adk.git
cd ..
```

This creates a `moai-adk/` directory containing the framework source code.

### 2. Create Workspace Configuration

Create a `pyproject.toml` file at your workspace root to define the uv workspace:

```toml
[project]
name = "your-workspace-name"
version = "0.1.0"
description = "Workspace containing moai-adk and related projects"
requires-python = ">=3.11"
dependencies = []

[tool.uv.workspace]
members = ["moai-adk"]

[dependency-groups]
dev = []
```

**Key points:**
- `members = ["moai-adk"]` declares moai-adk as a workspace member
- `requires-python = ">=3.11"` ensures Python version compatibility
- Replace `your-workspace-name` with your actual workspace name

### 3. Pin Python Version

Create a `.python-version` file to ensure consistent Python versions:

```bash
echo "3.13.6" > .python-version
```

Adjust the version number to match your installed Python version (must be ≥3.11).

### 4. Create .gitignore

Create a `.gitignore` file to exclude build artifacts and virtual environments:

```gitignore
# Virtual environments
.venv/
venv/
env/

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Build artifacts
build/
dist/
*.egg-info/
*.egg

# uv
.uv/
uv.lock

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# Backups
.moai-backups/
*.backup
*.bak
```

### 5. Install moai-adk in Editable Mode

Install moai-adk using uv in editable mode:

```bash
uv pip install -e moai-adk
```

This command:
- Installs moai-adk and its 55 dependencies
- Links the moai-adk source code (editable mode)
- Makes the `moai-adk` CLI command available

**Expected output:**
```
Resolved 55 packages in [time]
Installed 55 packages in [time]
...
+ moai-adk==0.30.2 (from file:///path/to/workspace/moai-adk)
```

### 6. Verify Installation

Confirm moai-adk is installed correctly:

```bash
uv run moai-adk --version
```

**Expected output:**
```
MoAI-ADK, version 0.30.2
```

## Workspace Configuration

### Migrate Configuration Files to Workspace Root

MoAI-ADK includes several workspace-level configuration directories and files that should reside at your workspace root (not inside moai-adk/):

```bash
# Copy .claude directory (24 agents, 6 commands, hooks, skills)
cp -r moai-adk/.claude ./

# Copy .moai directory (workspace runtime configuration)
cp -r moai-adk/.moai ./

# Copy MCP server integrations
cp moai-adk/.mcp.json ./

# Copy Claude Code scan exclusions
cp moai-adk/.claudeignore ./

# Copy execution directives
cp moai-adk/CLAUDE.md ./

# Copy local development guide
cp moai-adk/CLAUDE.local.md ./
```

### Update CLAUDE.local.md Paths

Edit `CLAUDE.local.md` to update hard-coded paths to use the `$CLAUDE_PROJECT_DIR` environment variable:

Find lines like:
```markdown
- `/Users/goos/MoAI/MoAI-ADK/` → Replace with `$CLAUDE_PROJECT_DIR/moai-adk/`
```

This ensures documentation is portable across different machines and users.

### Configuration Files Explained

#### `.claude/` Directory (268 files, ~3.6MB)

Claude Code configuration containing:

- **agents/** (24 agents): Specialized AI agents organized by tier
  - `expert-*` (7 agents): Domain experts (codebase, context, git, qa, tdd, tech, testing)
  - `manager-*` (8 agents): Task managers (explorer, investigator, planner, tracker, etc.)
  - `builder-*` (3 agents): Builders (code, spec, test)
  - `mcp-*` (5 agents): MCP integrations (browser, context7, figma, notion, thinking)
  - `ai-*` (1 agent): AI orchestrator

- **commands/** (6 commands): Slash commands for Alfred
  - `/moai:alfred` - Main Alfred orchestrator
  - `/moai:cascade` - Cascade execution mode
  - `/moai:plan` - Planning mode
  - `/moai:review` - Review mode
  - `/moai:spec` - SPEC-first mode
  - `/moai:tdd` - TDD execution mode

- **hooks/**: Lifecycle hooks (on-tool-error, post-tool-call, etc.)
- **skills/**: 22 skill modules (framework integrations, utilities)
- **output-styles/**: Output formatting configurations
- **settings.json**: Main Claude Code settings (4,940 bytes)

#### `.moai/` Directory

Workspace runtime configuration:

```
.moai/
├── config/
│   ├── config.json              # Main configuration
│   ├── statusline-config.yaml   # Status bar configuration
│   └── presets/                 # Git workflow presets
│       ├── manual-local.yaml
│       ├── personal-github.yaml
│       └── team-github.yaml
├── memory/
│   └── last-session-state.json  # Session state persistence
├── specs/                       # SPEC documents
└── scripts/                     # Utility scripts
```

**Key configuration (`config/config.json`):**
```json
{
  "git_strategy": "manual-local",
  "language": "en",
  "tdd_tool": "pytest",
  "spec_update_rule": "auto",
  "session_tracking": true
}
```

#### `.mcp.json`

MCP server integrations for Claude Code:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    },
    "figma-dev-mode-mcp-server": {
      "type": "sse",
      "url": "http://127.0.0.1:3845/sse"
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking@latest"]
    }
  }
}
```

#### `.claudeignore`

Defines what Claude Code excludes from scans:

```
# Build artifacts
build/
dist/
*.egg-info/

# Cache
__pycache__/
.pytest_cache/
node_modules/

# Backups
.moai-backups/
*.backup
*.bak
.mypy_cache/
```

#### `CLAUDE.md` (24KB)

Alfred's execution directive containing:
- 8-step request analysis process
- Agent delegation rules
- Token management strategies
- Operational guidelines for AI agents

#### `CLAUDE.local.md` (5.5KB)

Local development guide with:
- Directory structure overview
- Development workflow
- Testing procedures
- Environment setup

### Clean Up moai-adk Directory (Optional)

After migrating configuration files to workspace root, you can remove duplicates from `moai-adk/`:

```bash
# Remove duplicate .claude directory
rm -rf moai-adk/.claude

# Remove migrated files
rm -rf moai-adk/.moai
rm moai-adk/.mcp.json
rm moai-adk/.claudeignore
rm moai-adk/CLAUDE.md
rm moai-adk/CLAUDE.local.md

# Remove Python cache
find moai-adk -type d -name "__pycache__" -exec rm -rf {} +
```

**Total space reclaimed:** ~3.75MB

Verify moai-adk still works after cleanup:
```bash
uv run moai-adk --version
```

## Understanding the Architecture

### Workspace vs Package Separation

A key concept in this setup is understanding the distinction between **workspace configuration** and **package source code**:

- **Workspace root** (`<workspace-name>/`) - Your local development environment
  - Contains local configuration and customization
  - Files here are specific to your project
  - Not distributed to other users

- **moai-adk package** (`moai-adk/`) - The distributed Python package
  - Contains the framework source code
  - Gets installed via PyPI or editable mode
  - Should remain largely unchanged

This separation allows you to customize your development environment while keeping the core framework intact.

### The moai-adk/src Directory Structure

The `moai-adk/src/moai_adk/` directory is a complete, self-contained Python package (~46,500 lines of code) organized into specialized modules:

```
moai-adk/src/moai_adk/
├── __main__.py          # CLI entry point
├── cli/                 # Command-line interface (7 files)
│   └── commands/        # moai-adk init, doctor, status, etc.
├── core/                # Business logic (36 sub-packages)
│   ├── analysis/        # Session & SPEC analysis
│   ├── config/          # Configuration management
│   ├── git/             # Git operations
│   ├── spec/            # SPEC document processing
│   ├── integration/     # Integration testing
│   └── ...              # + 30 more sub-packages
├── foundation/          # Base frameworks (13 files)
│   ├── ears.py          # EARS specification template
│   ├── trust/           # TRUST-5 quality principles
│   └── langs.py         # Language support
├── statusline/          # Claude Code integration (9 files)
├── templates/           # Project initialization templates
│   ├── .claude/         # Agent templates (for moai-adk init)
│   ├── .moai/           # Config templates (for moai-adk init)
│   └── ...              # Other initialization files
└── utils/               # Shared utilities (7 files)
```

**Key modules explained:**

- **cli/** - User-facing commands like `moai-adk init`, `moai-adk doctor`, `moai-adk status`
- **core/** - The heart of the framework with 36 specialized sub-packages handling everything from SPEC processing to Git integration
- **foundation/** - Base frameworks defining EARS templates, TRUST-5 principles, and language support
- **statusline/** - Integration with Claude Code's status bar, showing real-time project state
- **templates/** - Default templates used when users run `moai-adk init` to bootstrap new projects
- **utils/** - Shared utilities for logging, file operations, validation

### Why moai-adk/src Stays in moai-adk/

**Important:** Everything in `moai-adk/src/moai_adk/` should **stay within moai-adk/** and **not** be moved to workspace root. Here's why:

1. **Standard Python Package Structure**
   - This follows Python's standard package layout
   - The `src/` layout is a best practice for distributable packages
   - Moving it would break the package structure

2. **Package Distribution**
   - moai-adk is distributed via PyPI (Python Package Index)
   - When users install moai-adk, they get this exact structure
   - Modifying the layout breaks installation and updates

3. **Editable Installation**
   - `uv pip install -e moai-adk` links directly to this source
   - Changes to source code immediately reflect in your environment
   - Moving files would break this linkage

4. **Templates vs Configuration**
   - `moai-adk/src/moai_adk/templates/` contains **template files** for new projects
   - When you run `moai-adk init`, these templates are **copied** to your project
   - Your workspace root `.claude/` and `.moai/` are **instances** of these templates
   - The templates themselves stay in the package for future use

### Architecture Diagram

Here's how the workspace is organized:

```
your-workspace/                      # Your workspace root
│
├── pyproject.toml                   # Workspace configuration
├── .python-version                  # Python version pinning
├── .gitignore                       # Git exclusions
│
├── .claude/                         # ✓ Migrated from moai-adk
│   ├── agents/                      # 24 specialized AI agents
│   ├── commands/                    # 6 /moai:* commands
│   ├── hooks/                       # Lifecycle hooks
│   ├── skills/                      # 22 skill modules
│   └── settings.json                # Claude Code configuration
│
├── .moai/                           # ✓ Migrated from moai-adk
│   ├── config/                      # Workspace runtime config
│   ├── memory/                      # Session state
│   └── specs/                       # SPEC documents
│
├── .mcp.json                        # ✓ Migrated - MCP integrations
├── .claudeignore                    # ✓ Migrated - Scan exclusions
├── CLAUDE.md                        # ✓ Migrated - Execution directive
├── CLAUDE.local.md                  # ✓ Migrated - Dev guide
│
└── moai-adk/                        # ✗ Stays here (Python package)
    ├── src/moai_adk/                # Package source code
    │   ├── cli/                     # Don't move
    │   ├── core/                    # Don't move
    │   ├── foundation/              # Don't move
    │   ├── statusline/              # Don't move
    │   ├── templates/               # Don't move (used by moai-adk init)
    │   └── utils/                   # Don't move
    ├── tests/                       # Package tests
    ├── pyproject.toml               # Package metadata
    └── README.md                    # Package documentation
```

### What Gets Migrated vs What Stays

| File/Directory | Location | Migrated? | Reason |
|----------------|----------|-----------|--------|
| `.claude/` | Workspace root | ✓ Yes | Workspace-specific agent configuration |
| `.moai/` | Workspace root | ✓ Yes | Local workspace state and config |
| `.mcp.json` | Workspace root | ✓ Yes | MCP server integrations for workspace |
| `.claudeignore` | Workspace root | ✓ Yes | Workspace scan exclusions |
| `CLAUDE.md` | Workspace root | ✓ Yes | Development documentation |
| `CLAUDE.local.md` | Workspace root | ✓ Yes | Local development notes |
| `moai-adk/src/` | Inside moai-adk/ | ✗ No | Distributed package source |
| `moai-adk/tests/` | Inside moai-adk/ | ✗ No | Package test suite |
| `moai-adk/pyproject.toml` | Inside moai-adk/ | ✗ No | Package metadata for distribution |
| `moai-adk/templates/` | Inside moai-adk/src/ | ✗ No | Templates for `moai-adk init` command |

**Key principle:** Files that customize your workspace go to root. Files that define the moai-adk package stay in moai-adk/.

### Template Workflow

Understanding how templates work clarifies the architecture:

1. **Templates in package** (`moai-adk/src/moai_adk/templates/`)
   - These are the **master copies**
   - Shipped with every moai-adk installation
   - Used by `moai-adk init` command

2. **Workspace instances** (workspace root)
   - Created by copying templates OR manual migration
   - Customized for your specific project
   - Independent from package templates

3. **Example workflow:**
   ```bash
   # When you run moai-adk init, it copies templates:
   moai-adk init
   # Copies moai-adk/src/moai_adk/templates/.claude/ → ./.claude/
   # Copies moai-adk/src/moai_adk/templates/.moai/ → ./.moai/

   # Your workspace copies can be customized freely
   # Package templates remain unchanged for future projects
   ```

## Documentation Guide

This installation guide focuses on getting moai-adk set up and running. For deeper understanding of the workspace architecture:

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **INSTALL.md** (this document) | Installation process and step-by-step setup | First time setup |
| **PROJECT-TREE-RULES.md** | Complete directory structure, file organization rules, and architectural rationale | After installation, before development |

### Why Read PROJECT-TREE-RULES.md?

After completing installation, **PROJECT-TREE-RULES.md** provides essential information for working with your workspace:

- **Understanding the 3-Way MoAI Split** - Learn why .claude/, .moai/, and moai-adk/ are separated and the benefits of this architecture
- **File Placement Rules** - Know where to put new configuration files, agents, skills, and specs
- **Complete Directory Reference** - Full annotated tree of the entire workspace structure
- **Configuration Layering** - Understand how workspace, framework, package, and local configs interact
- **Troubleshooting Guide** - Resolve structure-related issues with confidence

> 💡 **Recommended Next Step**: After installation completes successfully, read **PROJECT-TREE-RULES.md** to understand where to place new files and why the workspace is organized this way. This will save time and prevent organizational mistakes as you develop.

**Quick Example:**
- Need to add a new Claude Code agent? → See PROJECT-TREE-RULES.md § "Hidden Configuration Breakdown" → `.claude/agents/`
- Creating a new SPEC? → See PROJECT-TREE-RULES.md § "Hidden Configuration Breakdown" → `.moai/specs/`
- Adding workspace documentation? → See PROJECT-TREE-RULES.md § "File Placement Cheat Sheet"

## Verification

### Installation Checklist

Verify your installation is complete:

- [ ] `uv run moai-adk --version` returns version 0.30.2
- [ ] `.claude/` directory exists at workspace root with 24 agents
- [ ] `.moai/` directory exists at workspace root
- [ ] `.mcp.json` exists at workspace root
- [ ] `CLAUDE.md` and `CLAUDE.local.md` exist at workspace root
- [ ] Python cache cleaned from moai-adk directory
- [ ] All paths in `CLAUDE.local.md` use `$CLAUDE_PROJECT_DIR`

### Test Alfred Agent System

Test the Alfred orchestrator:

```bash
# In Claude Code, run:
/moai:alfred

# Or delegate to specific agents via Task tool in Claude Code:
# Task(subagent_type="expert-codebase", prompt="Analyze project structure")
```

### Test Parallel Agent Execution

Verify parallel agent execution works:

```python
# In Claude Code, launch multiple agents simultaneously:
# This demonstrates the parallel pattern used throughout moai-adk

# Example: Launch 3 parallel Explore agents
Task(subagent_type="Explore", prompt="Find all Python files", model="haiku")
Task(subagent_type="Explore", prompt="Find all test files", model="haiku")
Task(subagent_type="Explore", prompt="Find all config files", model="haiku")
```

**Expected behavior:** All 3 agents execute concurrently, returning results independently.

## Using Alfred with Parallel Agents

### The Alfred Super Agent

Alfred is the orchestrator managing 24 specialized agents across a 5-tier hierarchy:

**Tier 1: Expert Agents (7)** - Domain specialists
- `expert-codebase` - Codebase architecture analysis
- `expert-context` - Context and requirements analysis
- `expert-git` - Git operations and version control
- `expert-qa` - Quality assurance and testing
- `expert-tdd` - Test-driven development
- `expert-tech` - Technology stack expertise
- `expert-testing` - Testing strategies

**Tier 2: Manager Agents (8)** - Task orchestrators
- `manager-explorer` - Codebase exploration
- `manager-investigator` - Issue investigation
- `manager-planner` - Task planning
- `manager-tracker` - Progress tracking
- `manager-reviewer` - Code review
- `manager-coordinator` - Multi-agent coordination
- `manager-synthesizer` - Information synthesis
- `manager-validator` - Validation and verification

**Tier 3: Builder Agents (3)** - Artifact creators
- `builder-code` - Code implementation
- `builder-spec` - SPEC document creation
- `builder-test` - Test creation

**Tier 4: MCP Agents (5)** - External integrations
- `mcp-browser` - Browser automation (Playwright)
- `mcp-context7` - Documentation lookup
- `mcp-figma` - Figma integration
- `mcp-notion` - Notion integration
- `mcp-thinking` - Sequential thinking

**Tier 5: AI Orchestrator (1)**
- `ai-orchestrator` - Coordinates all agents

### Alfred's 8-Step Request Analysis

When you invoke Alfred, it follows this process:

1. **Analyze request** - Parse user intent and requirements
2. **Decompose** - Break complex tasks into subtasks
3. **Select agents** - Choose appropriate specialized agents
4. **Parallel execution** - Launch 5-10 agents simultaneously when possible
5. **Synthesize results** - Combine agent outputs
6. **Validate** - Verify completeness and correctness
7. **Report** - Present unified results to user
8. **Iterate** - Refine based on feedback

### Parallel Agent Execution Best Practices

**When to use parallel agents:**
- Exploring multiple codebases/directories simultaneously
- Gathering information from independent sources
- Analyzing different aspects of the same problem
- Running independent validation checks

**Example 1: Multi-Directory Exploration**
```python
# Launch 5 parallel agents to explore different parts of codebase
Task(subagent_type="Explore", prompt="Analyze src/ directory structure")
Task(subagent_type="Explore", prompt="Analyze tests/ directory structure")
Task(subagent_type="Explore", prompt="Analyze docs/ directory structure")
Task(subagent_type="Explore", prompt="Find all configuration files")
Task(subagent_type="Explore", prompt="Find all entry points")
```

**Example 2: Comprehensive Code Analysis**
```python
# Launch 7 parallel agents for multi-faceted analysis
Task(subagent_type="expert-codebase", prompt="Analyze architecture patterns")
Task(subagent_type="expert-testing", prompt="Evaluate test coverage")
Task(subagent_type="expert-qa", prompt="Identify code quality issues")
Task(subagent_type="expert-tech", prompt="Review technology choices")
Task(subagent_type="expert-git", prompt="Analyze commit history")
Task(subagent_type="manager-tracker", prompt="Track TODO items")
Task(subagent_type="manager-reviewer", prompt="Review recent changes")
```

**Example 3: SPEC-First TDD Workflow**
```python
# Launch 3 parallel agents for TDD cycle
Task(subagent_type="builder-spec", prompt="Create SPEC for user auth")
Task(subagent_type="builder-test", prompt="Generate test cases")
Task(subagent_type="expert-tdd", prompt="Review TDD best practices")
```

### Agent Delegation via /moai Commands

Use these slash commands to invoke Alfred modes:

- `/moai:alfred` - Full Alfred orchestration with automatic agent selection
- `/moai:spec` - SPEC-first development mode
- `/moai:tdd` - Test-driven development mode
- `/moai:plan` - Planning mode with task decomposition
- `/moai:review` - Code review mode
- `/moai:cascade` - Cascade execution (sequential agent chain)

### Token Management

Alfred optimizes token usage through:
- Selective agent activation (only necessary agents)
- Haiku model for quick exploration tasks
- Sonnet/Opus for complex reasoning
- Parallel execution reduces total conversation length

**Recommended model selection:**
- `model="haiku"` - Quick searches, file listing, simple analysis
- `model="sonnet"` - Default for most tasks
- `model="opus"` - Complex reasoning, architectural decisions

## Troubleshooting

### moai-adk Not Found After Installation

**Symptom:** `uv run moai-adk --version` fails with "No such file or directory"

**Cause:** moai-adk not installed in editable mode

**Fix:**
```bash
uv pip install -e moai-adk
```

### uv sync Doesn't Install moai-adk

**Symptom:** After `uv sync`, moai-adk is not in virtual environment

**Cause:** uv workspace members need explicit editable installation

**Fix:** Always run `uv pip install -e moai-adk` after workspace setup

### Python Version Conflicts

**Symptom:** Installation fails with Python version errors

**Cause:** Python version < 3.11

**Fix:**
```bash
# Install Python 3.11+
# Then update .python-version
echo "3.13.6" > .python-version
uv pip install -e moai-adk
```

### MCP Servers Not Working

**Symptom:** MCP tools unavailable in Claude Code

**Cause:** npm not installed or MCP servers not initialized

**Fix:**
```bash
# Verify npm installed
npm --version

# MCP servers auto-initialize on first use
# Or manually install:
npx -y @upstash/context7-mcp@latest
npx -y @playwright/mcp@latest
```

### Alfred Agents Not Available

**Symptom:** `/moai:alfred` command not found

**Cause:** `.claude/` directory not at workspace root

**Fix:**
```bash
# Verify .claude exists at workspace root
ls -la .claude/commands/

# Should show moai:alfred.md and other commands
# If not, re-copy from moai-adk:
cp -r moai-adk/.claude ./
```

### Outdated Paths in Documentation

**Symptom:** CLAUDE.local.md references wrong directories

**Cause:** Hard-coded paths from original developer

**Fix:** Replace all hard-coded paths with `$CLAUDE_PROJECT_DIR`:
```bash
# Edit CLAUDE.local.md
# Replace: /Users/goos/MoAI/MoAI-ADK/
# With: $CLAUDE_PROJECT_DIR/moai-adk/
```

### Duplicate Files Warning

**Symptom:** Large disk space usage in moai-adk/

**Cause:** Configuration files duplicated between workspace root and moai-adk/

**Fix:** Clean up duplicates (safe to delete after migration):
```bash
rm -rf moai-adk/.claude
rm -rf moai-adk/.moai
rm moai-adk/.mcp.json
rm moai-adk/.claudeignore
find moai-adk -type d -name "__pycache__" -exec rm -rf {} +
```

## Next Steps

After successful installation:

1. **Explore the codebase** - Use `/moai:alfred` to analyze your project structure
2. **Create your first SPEC** - Use `/moai:spec` to document a feature
3. **Write tests** - Use `/moai:tdd` to implement test-driven development
4. **Configure Git workflow** - Edit `.moai/config/config.json` to select your Git strategy
5. **Customize agents** - Modify `.claude/agents/` to add domain-specific expertise
6. **Add custom commands** - Create new slash commands in `.claude/commands/`
7. **Practice parallel execution** - Launch 5-10 agents for complex tasks

### Recommended First Task

Test the full workflow with a simple feature:

```bash
# In Claude Code:
/moai:spec
# Describe a simple feature (e.g., "Add hello world function")

# Alfred will:
# 1. Create SPEC document
# 2. Generate test cases
# 3. Implement code
# 4. Verify tests pass
# 5. Update documentation

# All using parallel agent execution!
```

### Learning Resources

- **CLAUDE.md** - Read Alfred's execution directive to understand agent orchestration
- **CLAUDE.local.md** - Review development workflow and best practices
- **.moai/config/** - Explore configuration options and presets
- **.claude/agents/** - Study agent specializations and capabilities

---

## Summary

You've successfully installed moai-adk in your workspace! You now have:

- ✅ MoAI-ADK v0.30.2 installed in editable mode
- ✅ Alfred super agent with 24 specialized AI agents
- ✅ Parallel agent execution for efficient task processing
- ✅ SPEC-First TDD framework
- ✅ MCP integrations (Context7, Playwright, Notion, Sequential Thinking)
- ✅ Complete workspace configuration

**Key concept:** Always leverage parallel agent execution (5-10 agents) for complex tasks to maximize efficiency and demonstrate the power of the Alfred orchestration system.

Happy developing with MoAI-ADK! 🚀
