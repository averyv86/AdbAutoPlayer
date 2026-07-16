# PROJECT-TREE-RULES.md

> **📝 Template Note**: This document uses generic placeholders for reusability across different moai-adk workspaces:
> - `<workspace-name>` - Replace with your workspace directory name (e.g., `agent-os-v2`, `moai_flow`, `my-project`)
> - `your-workspace/` - Generic workspace name in visual tree diagrams
> - `<your-repo-url>` - Your git repository URL
>
> Simply find-and-replace these placeholders when adapting this guide to your specific workspace.

## Overview

### Purpose

This document provides a comprehensive reference for moai-adk workspace directory structure and file organization rules. Unlike INSTALL.md (which guides you through setup) or the official moai-adk README.md (which explains features and usage), this document focuses on:

- **Complete directory tree** with annotations
- **File organization rules** - What goes where and why
- **Hidden configuration breakdown** - Understanding .claude/, .moai/, etc.
- **Separation rationale** - Workspace vs package architecture

### When to Use This Guide

- **Setting up a new moai-adk workspace** - Reference for file placement
- **Understanding workspace organization** - Learn the architecture
- **Adding new configurations** - Know where files belong
- **Troubleshooting structure issues** - Verify correct organization
- **Onboarding team members** - Quick reference for workspace anatomy

### Document Relationships

| Document | Focus | Audience |
|----------|-------|----------|
| **INSTALL.md** | Installation process, step-by-step setup | New installers |
| **moai-adk/README.md** | Features, usage, concepts, workflows | moai-adk users |
| **PROJECT-TREE-RULES.md** (this) | Structure, organization, placement rules | Workspace architects |

---

## Complete Directory Tree

```
your-workspace/                              [Total: ~212M]
│
├── 📋 ROOT CONFIGURATION FILES (9 files, ~2.2MB total)
│   ├── pyproject.toml                       [UV workspace config - declares moai-adk as member]
│   ├── uv.lock                              [2,209 lines - unified dependency lockfile]
│   ├── .gitignore                           [Python/Node/.env patterns]
│   ├── .claudeignore                        [Claude Code scan exclusions]
│   ├── .mcp.json                            [4 MCP servers: context7, playwright, figma, sequential-thinking]
│   ├── .python-version                      [Python 3.13.6 pin]
│   ├── CLAUDE.md                            [24K - Mr.Alfred execution directive]
│   ├── CLAUDE.local.md                      [5.5K - Local workspace customizations]
│   └── INSTALL.md                           [26K - Installation guide]
│
├── 🔒 .claude/                              [4.1M - Claude Code workspace configuration]
│   ├── settings.json                        [4.9K - Base Claude Code settings]
│   ├── settings.local.json                  [Local environment overrides - not committed]
│   │
│   ├── agents/                              [2 agents]
│   │   ├── macos-resource/                  [macOS resource optimization agent]
│   │   └── moai/                            [Main MoAI-ADK orchestration agent]
│   │
│   ├── commands/                            [2 command sets]
│   │   ├── macos-resource-optimizer/        [Resource optimization commands]
│   │   └── moai/                            [Core /moai:0-9 commands]
│   │
│   ├── hooks/                               [Lifecycle hooks]
│   │   ├── __init__.py
│   │   └── moai/                            [MoAI-specific hooks]
│   │
│   ├── output-styles/                       [Rendering styles]
│   │   └── moai/                            [MoAI output styling]
│   │
│   └── skills/                              [24 skill modules - 3.9M total]
│       ├── 📡 CONNECTORS (4 skills)
│       │   ├── moai-connector-figma/        [Figma design integration]
│       │   ├── moai-connector-mcp/          [Model Context Protocol bridge]
│       │   ├── moai-connector-nano-banana/  [Nano-banana integration]
│       │   └── moai-connector-notion/       [Notion workspace integration]
│       │
│       ├── 🏗️ FOUNDATIONS (5 skills)
│       │   ├── moai-foundation-claude/      [Claude AI core integration]
│       │   ├── moai-foundation-context/     [Code context & library docs]
│       │   ├── moai-foundation-core/        [Core MOAI framework logic]
│       │   ├── moai-foundation-quality/     [TRUST-5 quality framework]
│       │   └── moai-foundation-uiux/        [UI/UX design patterns]
│       │
│       ├── 🌐 LANGUAGES (1 skill)
│       │   └── moai-lang-unified/           [Universal prompt language]
│       │
│       ├── 📚 LIBRARIES (4 skills)
│       │   ├── moai-library-mermaid/        [Mermaid diagram generation]
│       │   ├── moai-library-nextra/         [Nextra docs framework]
│       │   ├── moai-library-shadcn/         [shadcn/ui components]
│       │   └── moai-library-toon/           [Toon library integration]
│       │
│       ├── ☁️ PLATFORMS (1 skill)
│       │   └── moai-platform-baas/          [Backend-as-a-Service]
│       │
│       ├── 🖥️ SYSTEMS (2 skills)
│       │   ├── moai-system-macos-resource-optimizer/  [macOS optimization]
│       │   └── moai-system-universal/       [Cross-platform system ops]
│       │
│       ├── 🧰 TOOLKITS (1 skill)
│       │   └── moai-toolkit-essentials/     [Essential development tools]
│       │
│       └── 🔄 WORKFLOWS (5 skills)
│           ├── moai-workflow-docs/          [Documentation generation]
│           ├── moai-workflow-jit-docs/      [Just-in-time documentation]
│           ├── moai-workflow-project/       [Project management]
│           ├── moai-workflow-templates/     [Template processing]
│           └── moai-workflow-testing/       [Test orchestration]
│
├── 🤖 .moai/                                [188K - MOAI framework state & configuration]
│   ├── cache/                               [Runtime cache]
│   │   └── git-info.json                    [Git repository metadata cache]
│   │
│   ├── config/                              [Framework configuration]
│   │   ├── config.json                      [10.6K - Main MOAI configuration]
│   │   ├── statusline-config.yaml           [Terminal statusline setup]
│   │   └── presets/                         [Configuration presets]
│   │       ├── manual-local.yaml            [Local manual workflow]
│   │       ├── personal-github.yaml         [Personal GitHub workflow]
│   │       └── team-github.yaml             [Team GitHub workflow]
│   │
│   ├── memory/                              [Session persistence]
│   │   └── last-session-state.json          [Previous session state]
│   │
│   ├── scripts/                             [MOAI automation scripts]
│   │
│   ├── specs/                               [Active project specifications]
│   │   ├── SPEC-MACOS-OPTIMIZER-001/        [macOS optimizer spec]
│   │   └── SPEC-UPDATE-001/                 [Update spec]
│   │
│   └── docs/                                [Generated documentation]
│       └── manager-resource-coordinator-implementation.md
│
├── 🐍 .venv/                                [56M - Python virtual environment]
│   ├── bin/                                 [Executables - python, pip, uv, moai-adk]
│   ├── lib/python3.13/site-packages/        [Installed packages - 55 packages]
│   ├── pyvenv.cfg                           [Virtual environment configuration]
│   ├── .gitignore                           [Excludes venv from git]
│   ├── CACHEDIR.TAG                         [Cache directory marker]
│   └── uv.lock → ../uv.lock                 [Symlink to workspace lockfile]
│
└── 📦 moai-adk/                             [149M - MoAI-ADK Python package]
    ├── .git/                                [Git repository - full history]
    │   └── [Standard git structure]
    │
    ├── .github/                             [GitHub workflows & templates]
    │   ├── ISSUE_TEMPLATE/                  [Issue templates]
    │   ├── scripts/                         [CI/CD scripts]
    │   ├── workflows/                       [GitHub Actions pipelines]
    │   └── dependabot.yml                   [Dependency auto-updates]
    │
    ├── .git-hooks/                          [Git hooks for TDD workflow]
    ├── .gitignore                           [Package-specific git exclusions]
    ├── .coderabbit.yaml                     [AI code review automation]
    │
    ├── 📚 ROOT DOCUMENTATION (moai-adk/)
    │   ├── README.md                        [48K - Official guide (English)]
    │   ├── README.ko.md                     [50K - Korean version]
    │   ├── README.ja.md                     [20K - Japanese version]
    │   ├── README.zh.md                     [12K - Chinese version]
    │   ├── CHANGELOG.md                     [172K - Detailed version history]
    │   ├── CONTRIBUTING.md                  [20K - Development guidelines]
    │   ├── LICENSE                          [MIT License]
    │   ├── MANIFEST.in                      [Package manifest for distribution]
    │   └── pyproject.toml                   [4.9K - Package configuration & dependencies]
    │
    ├── 📁 assets/                           [13M - Images & media]
    │   └── images/                          [PNG, JPEG files for documentation]
    │       ├── architecture-diagrams/
    │       ├── screenshots/
    │       └── logos/
    │
    ├── 🐍 src/moai_adk/                     [5.8M - Python source code, 418 files]
    │   ├── __pycache__/                     [Python bytecode cache]
    │   ├── __main__.py                      [CLI entry point - lazy command loading]
    │   ├── __init__.py                      [Package initialization]
    │   ├── version.py                       [Version string]
    │   │
    │   ├── cli/                             [Command-line interface - 7 files]
    │   │   ├── commands/                    [CLI command implementations]
    │   │   │   ├── init.py                  [moai-adk init]
    │   │   │   ├── analyze.py               [moai-adk analyze]
    │   │   │   ├── doctor.py                [moai-adk doctor]
    │   │   │   ├── language.py              [moai-adk language]
    │   │   │   ├── status.py                [moai-adk status]
    │   │   │   └── update.py                [moai-adk update]
    │   │   └── prompts/                     [Interactive CLI prompts]
    │   │
    │   ├── core/                            [Core functionality - 36 sub-packages]
    │   │   ├── analysis/                    [Session & SPEC analysis]
    │   │   ├── config/                      [Configuration management & auto-spec]
    │   │   ├── diagnostics/                 [System health checks]
    │   │   ├── git/                         [Git operations & commit management]
    │   │   ├── hooks/                       [Git hook management]
    │   │   ├── integration/                 [Integration testing & engine]
    │   │   ├── mcp/                         [Model Context Protocol support]
    │   │   ├── merge/                       [Code merge analysis]
    │   │   ├── migration/                   [Project migration utilities]
    │   │   ├── performance/                 [Performance optimization]
    │   │   ├── project/                     [Project metadata & management]
    │   │   ├── quality/                     [TRUST-5 quality validators]
    │   │   ├── spec/                        [SPEC document processing - EARS engine]
    │   │   ├── template/                    [Template processing & merging]
    │   │   └── [+23 more modules]           [Additional core functionality]
    │   │
    │   ├── foundation/                      [Base frameworks - 13 files]
    │   │   ├── ears.py                      [EARS specification template]
    │   │   ├── testing.py                   [Test framework definitions]
    │   │   ├── langs.py                     [Language support definitions]
    │   │   ├── git/                         [Git operations framework]
    │   │   ├── trust/                       [TRUST-5 quality principles]
    │   │   └── [backend, frontend, database, devops, ml_ops].py
    │   │
    │   ├── project/                         [Project-level utilities - 6 directories]
    │   │
    │   ├── statusline/                      [Claude Code integration - 9 files]
    │   │   ├── main.py                      [Statusline entry point]
    │   │   └── [Rendering, detection, Git integration modules]
    │   │
    │   ├── templates/                       [Project initialization templates]
    │   │   ├── .claude/                     [Agent templates for moai-adk init]
    │   │   ├── .git-hooks/                  [Git hook templates]
    │   │   ├── .github/workflows/           [CI/CD workflow templates]
    │   │   ├── .moai/                       [MoAI config templates]
    │   │   ├── .mcp.json                    [MCP server template]
    │   │   ├── .gitignore                   [Git ignore template]
    │   │   └── CLAUDE.md                    [Documentation template]
    │   │
    │   └── utils/                           [Shared utilities - 7 files]
    │       ├── logger.py                    [Logging infrastructure]
    │       ├── link_validator.py            [URL validation]
    │       ├── safe_file_reader.py          [Safe file operations]
    │       ├── common.py                    [Common utilities]
    │       ├── timeout.py                   [Timeout management]
    │       └── toon_utils.py                [Specialized utilities]
    │
    ├── 🧪 tests/                            [3.5M - Test suite, 204 test files]
    │   ├── ci/                              [CI/CD pipeline tests]
    │   ├── cli/                             [Command-line interface tests]
    │   ├── core/                            [Core module tests]
    │   ├── e2e/                             [End-to-end integration tests]
    │   ├── foundation/                      [Foundation layer tests]
    │   ├── hooks/                           [Git hook tests]
    │   ├── integration/                     [Integration tests]
    │   ├── project/                         [Project structure tests]
    │   ├── shell/                           [Shell command tests]
    │   ├── statusline/                      [Terminal statusline tests]
    │   ├── templates/                       [Template generation tests]
    │   ├── unit/                            [Unit tests]
    │   └── utils/                           [Utility function tests]
    │
    └── 🛠️ scripts/                          [3 files - Build & utility scripts]
        ├── build.py
        ├── release.py
        └── validate.py
```

---

## File Organization Rules

### Three-Tier Separation Model

This workspace follows a **three-tier architecture** that separates concerns by scope and mutability:

```
┌─────────────────────────────────────────┐
│  TIER 1: WORKSPACE ROOT                 │  Workspace behavior & integration
│  ├── pyproject.toml (workspace)         │  • Workspace configuration
│  ├── .mcp.json                           │  • Claude Code integration
│  ├── CLAUDE.md / CLAUDE.local.md         │  • Documentation
│  └── .python-version, .gitignore         │  • Environment settings
└─────────────────────────────────────────┘
           ↓ configures
┌─────────────────────────────────────────┐
│  TIER 2: HIDDEN CONFIG DIRECTORIES      │  Framework state & runtime
│  ├── .claude/ (4.1M)                     │  • Agent orchestration
│  ├── .moai/ (188K)                       │  • Framework persistence
│  └── .venv/ (56M)                        │  • Python environment
└─────────────────────────────────────────┘
           ↓ uses
┌─────────────────────────────────────────┐
│  TIER 3: MOAI-ADK PACKAGE               │  Distributable package
│  └── moai-adk/                           │  • Source code (src/)
      ├── src/moai_adk/                    │  • Tests (tests/)
      ├── tests/                           │  • Package config
      └── pyproject.toml (package)         │  • Documentation
└─────────────────────────────────────────┘
```

### Decision Rules

**Place at Workspace Root when:**
- File affects workspace behavior (not just moai-adk package)
- File is workspace-specific configuration
- File is local documentation or guides
- File defines workspace-level dependencies

**Place in Hidden Config (.claude/, .moai/) when:**
- File is runtime state or session data
- File is framework configuration
- File is agent/command/skill definition
- File should not be in distributed packages

**Keep in moai-adk/ when:**
- File is part of the distributable package
- File is package source code or tests
- File is package-level documentation
- File is needed for package distribution (PyPI)

---

## Understanding the 3-Way MoAI Split

### Why is MoAI Separated into Three Directories?

**Design Decision:** MoAI deliberately separates concerns into three distinct layers for flexibility, maintainability, and clean package distribution.

```
.claude/        Claude Code Integration Layer
  ├─ Purpose: AI agent orchestration, commands, skills specific to Claude Code
  ├─ Scope: Workspace-specific development environment
  ├─ Mutability: Fully customizable per workspace
  └─ Portability: Copy-paste template to any workspace using Claude Code

.moai/          MoAI Framework State Layer
  ├─ Purpose: Runtime state, session memory, project specs, framework config
  ├─ Scope: Workspace-specific MoAI behavior and persistence
  ├─ Mutability: Changes during development (specs, memory, cache)
  └─ Portability: Workspace-specific, not shared between projects

moai-adk/       Distributable Package Layer
  ├─ Purpose: Python package source, tests, templates, documentation
  ├─ Scope: Universal framework code distributed via PyPI
  ├─ Mutability: Immutable (update via package manager)
  └─ Portability: Identical code across all installations
```

### The Rationale: Why Not Just One Directory?

**Problem with monolithic structure:** If everything was in `moai-adk/`, you'd face:
- ❌ Workspace clutter included in package distribution
- ❌ Personal configs accidentally committed to package repo
- ❌ Unable to customize Claude Code integration per-project
- ❌ Framework state mixed with immutable package code
- ❌ Difficult to update package without affecting workspace

**Benefits of 3-way separation:**

| Layer | Benefit | Example |
|-------|---------|---------|
| **.claude/** | **Claude Code Flexibility** | Customize agents/skills for different projects without modifying package |
| **.moai/** | **Stateful Persistence** | Session memory, project specs persist across package updates |
| **moai-adk/** | **Clean Distribution** | Package published to PyPI contains only source/tests/docs, no workspace clutter |

### Data Flow Between Layers

```
┌──────────────────────────────────────────────────────┐
│                    YOUR WORKFLOW                     │
└──────────────────────────────────────────────────────┘
                          │
                          ↓
         ┌────────────────────────────────┐
         │   .claude/ (Claude Code)       │
         │   Agents execute commands      │
         │   Skills provide capabilities  │
         └────────────┬───────────────────┘
                      │ uses
                      ↓
         ┌────────────────────────────────┐
         │   .moai/ (Framework State)     │
         │   Stores specs, memory, config │
         │   Manages session persistence  │
         └────────────┬───────────────────┘
                      │ calls
                      ↓
         ┌────────────────────────────────┐
         │   moai-adk/ (Package Code)     │
         │   Executes SPEC-First TDD      │
         │   Provides core functionality  │
         └────────────────────────────────┘
```

### Key Architectural Benefits

1. **Clean Separation of Concerns**
   - Each layer has a single, well-defined responsibility
   - Changes in one layer don't affect others
   - Easy to understand what goes where

2. **Package Distribution**
   - `moai-adk/` can be published to PyPI without workspace clutter
   - Users get clean, focused package
   - No personal configs or workspace state in distribution

3. **Workspace Customization**
   - `.claude/` and `.moai/` can be heavily customized per-project
   - Different projects can have different agent setups
   - Customize without modifying core package

4. **Independent Updates**
   - Update `moai-adk` package without losing workspace state
   - `uv pip install --upgrade moai-adk` leaves `.moai/` untouched
   - Workspace configs persist across package versions

5. **Template Reusability**
   - `.claude/` and `.moai/` serve as templates
   - Copy to new workspace and customize
   - Bootstrap new projects quickly

### Practical Example: Multi-Workspace Scenario

Imagine you maintain three different moai-adk workspaces:

```
agent-os-v2/
  ├── .claude/          ← Custom agents for OS automation
  ├── .moai/            ← OS-specific specs and configs
  └── moai-adk/         ← Same package v0.30.2

moai_flow/
  ├── .claude/          ← Custom agents for workflow automation
  ├── .moai/            ← Flow-specific specs and configs
  └── moai-adk/         ← Same package v0.30.2

my-saas-project/
  ├── .claude/          ← Custom agents for web development
  ├── .moai/            ← SaaS-specific specs and configs
  └── moai-adk/         ← Same package v0.30.2
```

**Result:**
- ✅ All three use the same tested `moai-adk` package
- ✅ Each has domain-specific Claude Code agents
- ✅ Each maintains independent project specs and state
- ✅ Update `moai-adk` once, benefits all three workspaces
- ✅ Customize each workspace without affecting others

### Migration Pattern

When you set up a new workspace, the 3-way split means:

**Copy from moai-adk templates:**
```bash
cp -r moai-adk/.claude ./        # Workspace Claude config
cp -r moai-adk/.moai ./          # Workspace MoAI state
```

**Then customize:**
- `.claude/` → Add project-specific agents/skills
- `.moai/` → Create project-specific specs
- `moai-adk/` → Leave unchanged (update via package manager)

This separation ensures clean template usage while allowing full customization.

---

## Configuration Layering

### Four-Layer Configuration System

```
┌────────────────────────────────────────────────┐
│  LAYER 1: WORKSPACE LEVEL                      │  Highest priority
│  ├── pyproject.toml (root)                     │  Workspace members, deps
│  ├── .mcp.json                                 │  MCP server config
│  ├── CLAUDE.md                                 │  Mr.Alfred directives
│  └── uv.lock                                   │  Unified dependency lock
└────────────────────────────────────────────────┘
                   ↓ overrides
┌────────────────────────────────────────────────┐
│  LAYER 2: FRAMEWORK LEVEL                      │
│  ├── .moai/config/config.json                  │  MOAI behavior
│  ├── .moai/config/statusline-config.yaml       │  Statusline rendering
│  └── .moai/config/presets/*.yaml               │  Git workflow presets
└────────────────────────────────────────────────┘
                   ↓ overrides
┌────────────────────────────────────────────────┐
│  LAYER 3: PACKAGE LEVEL                        │
│  ├── moai-adk/pyproject.toml                   │  Package metadata
│  ├── moai-adk/README.md                        │  Package docs
│  └── moai-adk/src/moai_adk/templates/          │  Default templates
└────────────────────────────────────────────────┘
                   ↓ overrides
┌────────────────────────────────────────────────┐
│  LAYER 4: LOCAL OVERRIDES                      │  Lowest priority (highest specificity)
│  ├── .claude/settings.local.json               │  Local Claude settings
│  ├── CLAUDE.local.md                           │  Local dev notes
│  └── .moai/memory/last-session-state.json      │  Session state
└────────────────────────────────────────────────┘
```

### Configuration Priority

When the same setting exists in multiple layers:

1. **Local overrides** (settings.local.json) take precedence
2. **Framework config** (.moai/config.json) next
3. **Package defaults** (moai-adk templates) next
4. **Workspace settings** (root configs) as baseline

**Example:** MCP Server Configuration

```
workspace root/.mcp.json              → Active MCP servers for workspace
moai-adk/templates/.mcp.json          → Default template (used by moai-adk init)
.claude/settings.local.json           → Can override MCP behavior locally
```

---

## Hidden Configuration Breakdown

### .claude/ Directory (4.1M)

**Purpose:** Claude Code workspace integration - agent orchestration, commands, skills, and hooks.

**Structure:**
```
.claude/
├── settings.json               [Base settings - committed to git]
├── settings.local.json         [Local overrides - NOT committed]
├── agents/                     [2 agents: macos-resource, moai]
├── commands/                   [2 command sets: resource optimizer, moai]
├── hooks/                      [Lifecycle hooks for Claude Code events]
├── output-styles/              [Rendering styles for agent output]
└── skills/                     [24 skill modules - 3.9M]
```

**24 Skills by Category:**

| Category | Count | Skills | Purpose |
|----------|-------|--------|---------|
| Connectors | 4 | figma, mcp, nano-banana, notion | External tool integrations |
| Foundations | 5 | claude, context, core, quality, uiux | Core framework capabilities |
| Languages | 1 | unified | Universal prompt language |
| Libraries | 4 | mermaid, nextra, shadcn, toon | Library integrations |
| Platforms | 1 | baas | Backend-as-a-Service |
| Systems | 2 | macos-resource-optimizer, universal | System operations |
| Toolkits | 1 | essentials | Essential dev tools |
| Workflows | 5 | docs, jit-docs, project, templates, testing | Development workflows |

**Key Files:**
- `settings.json` (4.9K) - Hooks, permissions, agent config
- `agents/moai/` - Main MoAI orchestration agent
- `commands/moai/` - /moai:0 through /moai:9 commands
- `skills/moai-foundation-core/` - Core MOAI framework logic

**Git Handling:**
- `settings.json` → Committed (shared team config)
- `settings.local.json` → NOT committed (personal overrides)

---

### .moai/ Directory (188K)

**Purpose:** MOAI framework state, configuration, and session persistence.

**Structure:**
```
.moai/
├── cache/                      [Runtime cache - safe to delete]
│   └── git-info.json
├── config/                     [Framework configuration]
│   ├── config.json             [Main config - git strategy, language, TDD tool]
│   ├── statusline-config.yaml  [Terminal UI config]
│   └── presets/                [Workflow presets]
│       ├── manual-local.yaml
│       ├── personal-github.yaml
│       └── team-github.yaml
├── memory/                     [Session persistence]
│   └── last-session-state.json
├── scripts/                    [MOAI automation scripts]
├── specs/                      [Active project specifications]
│   ├── SPEC-MACOS-OPTIMIZER-001/
│   └── SPEC-UPDATE-001/
└── docs/                       [Generated documentation]
```

**Key Configuration (.moai/config/config.json):**
```json
{
  "git_strategy": "manual-local",     // Git workflow mode
  "language": "en",                   // Interface language
  "tdd_tool": "pytest",               // Testing framework
  "spec_update_rule": "auto",         // SPEC auto-update
  "session_tracking": true            // Session persistence
}
```

**Workflow Presets:**
- `manual-local.yaml` - Local development, manual git
- `personal-github.yaml` - Personal GitHub repo workflow
- `team-github.yaml` - Team collaboration workflow

**Git Handling:**
- `config/` → Committed (shared configuration)
- `cache/` → NOT committed (temporary cache)
- `memory/` → NOT committed (session state)
- `specs/` → Committed (project specifications)

---

### .venv/ Directory (56M)

**Purpose:** Python virtual environment with moai-adk and dependencies.

**Structure:**
```
.venv/
├── bin/                        [Executables]
│   ├── python → python3.13
│   ├── pip
│   ├── uv
│   └── moai-adk               [Installed CLI command]
├── lib/python3.13/
│   └── site-packages/         [55 installed packages]
│       ├── moai_adk/          [Symlink to workspace moai-adk/src/]
│       ├── click/
│       ├── rich/
│       └── [52 more packages]
├── pyvenv.cfg                 [Venv configuration]
├── .gitignore                 [Excludes venv from git]
└── CACHEDIR.TAG               [Cache directory marker]
```

**Key Points:**
- Created by `uv pip install -e moai-adk`
- `moai_adk/` is symlinked (editable install) - changes reflect immediately
- 55 packages total including dependencies
- NOT committed to git (excluded via .gitignore)
- Recreatable via `uv sync` or `uv pip install -e moai-adk`

---

### Root Dotfiles

| File | Purpose | Size | Committed |
|------|---------|------|-----------|
| `.gitignore` | Git exclusions (Python, Node, .env, IDE) | ~1KB | ✓ Yes |
| `.claudeignore` | Claude Code scan exclusions | ~200B | ✓ Yes |
| `.mcp.json` | 4 MCP servers (context7, playwright, figma, sequential-thinking) | ~500B | ✓ Yes |
| `.python-version` | Python version pin (3.13.6) | 7B | ✓ Yes |

**.mcp.json Contents:**
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

---

## moai-adk Package Structure

### Source Code Organization (src/moai_adk/)

```
src/moai_adk/                   [418 Python files, ~46,500 lines of code]
├── cli/                        [User-facing CLI commands]
├── core/                       [Business logic - 11 major sub-packages]
├── foundation/                 [Base frameworks - EARS, TRUST-5, language support]
├── project/                    [Project-level utilities]
├── statusline/                 [Claude Code terminal integration]
├── templates/                  [Project initialization templates]
└── utils/                      [Shared helper functions]
```

**Core Module Breakdown:**

| Module | Sub-packages | Purpose | Key Files |
|--------|--------------|---------|-----------|
| `cli/` | commands, prompts | Command-line interface | init.py, doctor.py, status.py |
| `core/` | 11+ modules | Business logic | analysis, config, git, spec, quality |
| `foundation/` | git, trust | Base frameworks | ears.py, langs.py, testing.py |
| `project/` | 6 directories | Project utilities | Project metadata, management |
| `statusline/` | - | Terminal UI | Statusline rendering, Git integration |
| `templates/` | .claude, .moai, etc | Init templates | Project bootstrap files |
| `utils/` | - | Helpers | logger.py, safe_file_reader.py |

**Core Sub-packages (core/):**
1. `analysis/` - Session & SPEC analysis
2. `config/` - Configuration management & auto-spec
3. `diagnostics/` - System health checks
4. `git/` - Git operations & commit management
5. `hooks/` - Git hook management
6. `integration/` - Integration testing & engine
7. `mcp/` - Model Context Protocol support
8. `merge/` - Code merge analysis
9. `performance/` - Performance optimization
10. `quality/` - TRUST-5 quality validators
11. `spec/` - SPEC document processing (EARS engine)

---

### Test Suite Organization (tests/)

```
tests/                          [204 test files, 3.5M total]
├── unit/                       [Unit tests - isolated function testing]
├── integration/                [Integration tests - module interaction]
├── e2e/                        [End-to-end tests - full workflow]
├── ci/                         [CI/CD pipeline tests]
├── cli/                        [Command-line interface tests]
├── core/                       [Core module tests]
├── foundation/                 [Foundation layer tests]
├── hooks/                      [Git hook tests]
├── project/                    [Project structure tests]
├── shell/                      [Shell command tests]
├── statusline/                 [Terminal statusline tests]
├── templates/                  [Template generation tests]
└── utils/                      [Utility function tests]
```

**Test Categories:**

| Category | Purpose | Example Tests |
|----------|---------|---------------|
| `unit/` | Isolated function testing | Test EARS parser, config validator |
| `integration/` | Module interaction | Test git + spec integration |
| `e2e/` | Full workflow testing | Test complete TDD cycle |
| `ci/` | CI/CD pipeline validation | Test GitHub Actions workflows |
| `cli/` | CLI command testing | Test `moai-adk init` command |
| `core/` | Core business logic | Test SPEC processing engine |
| `foundation/` | Framework foundations | Test TRUST-5 validators |
| `hooks/` | Git hook functionality | Test pre-commit hooks |
| `shell/` | Shell command execution | Test bash/zsh compatibility |
| `statusline/` | Terminal UI rendering | Test statusline display |
| `templates/` | Template generation | Test project init templates |

---

### Documentation & Meta Files

**Multi-Language README:**
- `README.md` (48K) - English (official)
- `README.ko.md` (50K) - Korean
- `README.ja.md` (20K) - Japanese
- `README.zh.md` (12K) - Chinese

**Development Guides:**
- `CHANGELOG.md` (172K) - Detailed version history, release notes
- `CONTRIBUTING.md` (20K) - Development guidelines, PR process
- `LICENSE` - MIT License
- `MANIFEST.in` - Package manifest for distribution

**Configuration:**
- `pyproject.toml` (4.9K) - Package metadata, dependencies, build config
- `.coderabbit.yaml` - AI code review automation settings

**CI/CD:**
- `.github/workflows/` - GitHub Actions pipelines
- `.github/ISSUE_TEMPLATE/` - Issue templates
- `.github/scripts/` - CI/CD scripts

---

## Separation Rationale

### Workspace Root Files

| File | Why at Root | Alternative | Why Not Alternative |
|------|-------------|-------------|---------------------|
| `pyproject.toml` | Declares moai-adk as UV workspace member | Inside moai-adk/ | Would not create workspace context |
| `uv.lock` | Unified lockfile for all workspace deps | Separate locks | Breaks unified dependency management |
| `.mcp.json` | Workspace-level MCP integration | Inside moai-adk/ | MCP servers are workspace-specific |
| `.claudeignore` | Workspace scan exclusions | Inside .claude/ | Claude Code expects root location |
| `CLAUDE.md` | Workspace execution directive | Inside moai-adk/ | Applies to workspace, not just package |
| `.moai/` | Workspace state & configuration | Inside moai-adk/ | State is workspace-specific, not package |
| `.claude/` | Workspace agents/skills/commands | Inside moai-adk/ | Configuration is workspace-specific |

**Key Principle:** Files at root affect workspace behavior and are not part of the distributable package.

---

### moai-adk Package Files

| File/Directory | Why in moai-adk/ | Alternative | Why Not Alternative |
|----------------|------------------|-------------|---------------------|
| `src/moai_adk/` | Distributable package source | At workspace root | Breaks package distribution structure |
| `tests/` | Package test suite | Workspace tests/ | Tests are package-specific quality |
| `pyproject.toml` | Package metadata for PyPI | Only root pyproject | Breaks package distribution |
| `README.md` | Package documentation (PyPI) | Only root README | Package needs own documentation |
| `.git/` | Independent git repository | Share with workspace | Allows submodule/clone flexibility |
| `.github/workflows/` | Package CI/CD | Workspace workflows | Package has own release cycle |
| `CHANGELOG.md` | Package release history | Workspace changelog | Tracks package versions |

**Key Principle:** Files in moai-adk/ are part of the distributable package and needed for PyPI distribution.

---

### Migration Matrix

What gets migrated from moai-adk to workspace root during installation:

| Item | Source | Destination | Reason | Keep Original? |
|------|--------|-------------|--------|----------------|
| `.claude/` | moai-adk/.claude/ | workspace/.claude/ | Workspace-specific config | No - delete after |
| `.moai/` | moai-adk/.moai/ | workspace/.moai/ | Workspace state | No - delete after |
| `.mcp.json` | moai-adk/.mcp.json | workspace/.mcp.json | Workspace MCP servers | No - delete after |
| `.claudeignore` | moai-adk/.claudeignore | workspace/.claudeignore | Workspace scan rules | No - delete after |
| `CLAUDE.md` | moai-adk/CLAUDE.md | workspace/CLAUDE.md | Workspace directives | No - delete after |
| `CLAUDE.local.md` | moai-adk/CLAUDE.local.md | workspace/CLAUDE.local.md | Local dev notes | No - delete after |
| `src/moai_adk/` | - | - | Package source | Yes - KEEP in moai-adk |
| `tests/` | - | - | Package tests | Yes - KEEP in moai-adk |
| `pyproject.toml` (pkg) | - | - | Package metadata | Yes - KEEP in moai-adk |

**Template vs Instance Pattern:**
- `moai-adk/src/moai_adk/templates/.claude/` - Master templates (used by `moai-adk init`)
- `workspace/.claude/` - Instance copy (customizable)
- Package templates remain unchanged for future projects

---

## File Categorization Reference

### By File Type

| Type | Location | Count | Examples |
|------|----------|-------|----------|
| **Workspace Config** | Root | 9 | pyproject.toml, .mcp.json, CLAUDE.md |
| **Agent Definitions** | .claude/agents/ | 2 | macos-resource, moai |
| **Command Definitions** | .claude/commands/ | 2 sets | moai, macos-resource-optimizer |
| **Skill Modules** | .claude/skills/ | 24 | moai-foundation-core, moai-connector-figma |
| **Framework Config** | .moai/config/ | 2 | config.json, statusline-config.yaml |
| **Workflow Presets** | .moai/config/presets/ | 3 | manual-local, personal-github, team-github |
| **Specifications** | .moai/specs/ | 2 | SPEC-MACOS-OPTIMIZER-001, SPEC-UPDATE-001 |
| **Source Code** | moai-adk/src/ | 418 | CLI, core, foundation modules |
| **Test Files** | moai-adk/tests/ | 204 | Unit, integration, e2e tests |
| **Documentation** | moai-adk/ | 7 | 4 READMEs, CHANGELOG, CONTRIBUTING, LICENSE |

---

### By Purpose

| Purpose | Files | Location | Committed |
|---------|-------|----------|-----------|
| **Development Environment** | .python-version, .venv/, uv.lock | Root | .python-version ✓, others ✗ |
| **Workspace Behavior** | pyproject.toml, .mcp.json, CLAUDE.md | Root | ✓ Yes |
| **Agent Orchestration** | .claude/* | .claude/ | settings.json ✓, settings.local.json ✗ |
| **Framework State** | .moai/* | .moai/ | config ✓, memory ✗, specs ✓ |
| **Package Distribution** | src/, pyproject.toml (pkg), README | moai-adk/ | ✓ Yes |
| **Quality Assurance** | tests/, .github/workflows/ | moai-adk/ | ✓ Yes |
| **Local Overrides** | settings.local.json, CLAUDE.local.md | Root/.claude/ | ✗ No |

---

### By Mutability

| Mutability | Files | Reason | Git Handling |
|------------|-------|--------|--------------|
| **Static (Package)** | moai-adk/src/, moai-adk/tests/ | Distributable package code | Committed to git |
| **Semi-Static (Config)** | .claude/skills/, .moai/config/ | Shared team configuration | Committed to git |
| **Dynamic (State)** | .moai/memory/, .moai/cache/ | Runtime state & cache | NOT committed |
| **Dynamic (Environment)** | .venv/, __pycache__/ | Generated environment | NOT committed |
| **Local (Overrides)** | settings.local.json, CLAUDE.local.md | Personal customization | NOT committed |

---

## Size & Statistics

### Workspace Size Breakdown

```
Total Workspace: ~212M
├── moai-adk/                  149M (70%)  Package source, tests, docs
│   ├── .git/                  90M  (42%)  Git repository history
│   ├── assets/                13M  (6%)   Images & media
│   ├── src/                   5.8M (3%)   Python source code
│   ├── tests/                 3.5M (2%)   Test suite
│   └── docs/                  37M  (17%)  Documentation & other
├── .venv/                     56M  (26%)  Python virtual environment
│   ├── site-packages/         55M         Installed dependencies (55 packages)
│   └── bin/                   1M          Executables
├── .claude/                   4.1M (2%)   Claude Code configuration
│   └── skills/                3.9M (95%)  24 skill modules
├── .moai/                     188K (<1%)  Framework state
│   └── specs/                 120K        SPEC documents
└── Root files                 2.2M (1%)   Workspace config & docs
    └── uv.lock                2M          Dependency lockfile
```

### File Count Statistics

```
Python Files:                  2,241 total
├── moai-adk/src/              418 files   Source code
├── moai-adk/tests/            204 files   Test suite
├── .venv/site-packages/       ~1,600      Dependencies
└── .claude/skills/            ~20         Skill modules

Documentation Files:           10 total
├── moai-adk/README*.md        4 files     Multi-language READMEs
├── moai-adk/CHANGELOG.md      1 file      Version history (172K)
├── moai-adk/CONTRIBUTING.md   1 file      Dev guidelines (20K)
├── Root docs                  3 files     CLAUDE.md, CLAUDE.local.md, INSTALL.md
└── LICENSE                    1 file      MIT License

Configuration Files:           30+ total
├── .moai/config/              5 files     Framework config
├── .claude/                   2 files     settings.json, settings.local.json
├── Root dotfiles              4 files     .gitignore, .claudeignore, .mcp.json, .python-version
├── pyproject.toml             2 files     Workspace + package
└── Various                    17+ files   .github/, .git-hooks/, etc.

Total Files:                   ~2,300
```

### Storage Optimization Notes

**Safe to Delete (Regenerable):**
- `.venv/` (56M) - Recreate with `uv sync` or `uv pip install -e moai-adk`
- `__pycache__/` (varies) - Python regenerates on import
- `.moai/cache/` (<1M) - Runtime cache, auto-regenerates
- `moai-adk/.git/` (90M) - Can re-clone if needed (caution: loses local commits)

**Safe to Clean:**
- `find . -type d -name "__pycache__" -exec rm -rf {} +` - Remove all Python cache
- `rm -rf .moai/cache/` - Clear MOAI runtime cache
- `rm -rf .venv/ && uv pip install -e moai-adk` - Rebuild virtual environment

**Never Delete:**
- `.moai/specs/` - Project specifications (active work)
- `.moai/config/` - Framework configuration
- `.claude/` - Agent orchestration (unless migrating)
- `moai-adk/src/` - Package source code
- Root config files (pyproject.toml, .mcp.json, etc.)

---

## Comparison with Official README

### What Official README.md Covers

The official moai-adk README.md (48K, English) documents:

✅ **Features & Concepts**
- SPEC-First development methodology
- TDD workflow integration
- AI agent orchestration (Mr.Alfred)
- Auto-documentation generation
- TRUST-5 quality framework

✅ **Installation & Setup**
- Basic installation commands
- Quick start guide
- Initial configuration

✅ **Usage & Workflows**
- 7 core commands (/moai:0 through /moai:3 range)
- Development workflow (Plan → Run → Sync)
- SPEC creation & management
- Agent delegation patterns

✅ **Reference**
- 26 specialized agents
- 22 skill library overview
- Composition patterns & examples
- MCP server integration
- FAQ & troubleshooting

### What PROJECT-TREE-RULES.md Adds

This document (PROJECT-TREE-RULES.md) uniquely provides:

✅ **Structural Documentation**
- Complete directory tree visualization
- File organization rationale
- Hidden configuration breakdown
- Workspace vs package separation

✅ **Architectural Guidance**
- Three-tier separation model
- Configuration layering strategy
- File placement decision rules
- Migration matrix

✅ **Reference Tables**
- File categorization (by type, purpose, mutability)
- Size & statistics breakdown
- Git handling rules
- Optimization notes

✅ **Workspace Anatomy**
- 24 Claude skills categorized
- .moai/ structure & purpose
- .claude/ organization
- Test suite organization

### When to Use Which Document

| Scenario | Use This Document | Use Official README |
|----------|-------------------|---------------------|
| **Setting up workspace** | PROJECT-TREE-RULES.md + INSTALL.md | For feature overview |
| **Understanding structure** | PROJECT-TREE-RULES.md | - |
| **Learning features** | - | Official README |
| **Using moai-adk commands** | - | Official README |
| **Troubleshooting organization** | PROJECT-TREE-RULES.md | - |
| **Adding new files** | PROJECT-TREE-RULES.md | - |
| **Understanding workflows** | - | Official README |
| **Agent delegation** | - | Official README |
| **File placement decisions** | PROJECT-TREE-RULES.md | - |

---

## Quick Reference

### File Placement Cheat Sheet

```
❓ Where should I put...

📄 New workspace documentation?
   → Workspace root (e.g., ARCHITECTURE.md, DEPLOY.md)

⚙️ New Claude Code agent?
   → .claude/agents/your-agent/

🔧 New moai-adk skill?
   → .claude/skills/moai-[category]-[name]/

📝 New SPEC document?
   → .moai/specs/SPEC-YOUR-FEATURE-001/

🐍 New Python source module?
   → moai-adk/src/moai_adk/[module]/

🧪 New test file?
   → moai-adk/tests/[category]/

📋 New configuration preset?
   → .moai/config/presets/your-preset.yaml

🔌 New MCP server?
   → Add to workspace/.mcp.json

🚫 New gitignore pattern?
   → Workspace .gitignore (workspace) OR moai-adk/.gitignore (package)

🔒 Personal settings override?
   → .claude/settings.local.json OR CLAUDE.local.md
```

### Common Operations

**Clone this workspace:**
```bash
git clone <your-repo-url> <workspace-name>
cd <workspace-name>

# Clone superdisco-agents fork (custom enhancements)
git clone https://github.com/superdisco-agents/moai-adk.git moai-adk

# Optional: Add upstream for syncing
cd moai-adk && git remote add upstream https://github.com/modu-ai/moai-adk.git && cd ..

uv pip install -e moai-adk
```

**Update moai-adk:**
```bash
cd moai-adk
git pull origin main       # From superdisco-agents fork
# git fetch upstream       # Optional: sync from modu-ai upstream
cd ..
uv pip install -e moai-adk
```

**Rebuild environment:**
```bash
rm -rf .venv
uv pip install -e moai-adk
```

**Clean cache:**
```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
rm -rf .moai/cache/*
```

---

## Summary

This workspace follows a **root-level workspace pattern** with **moai-adk as a UV workspace member**:

1. **Workspace Root** - Contains workspace config, Claude Code integration, and MOAI framework state
2. **Hidden Config** - .claude/ (4.1M), .moai/ (188K), .venv/ (56M) manage runtime behavior
3. **moai-adk Package** - Complete distributable package with source, tests, and documentation
4. **Separation Rule** - Files at root affect workspace; files in moai-adk affect package distribution
5. **Configuration Layers** - Workspace → Framework → Package → Local overrides

**Total Size:** ~212M (moai-adk: 149M, .venv: 56M, .claude: 4.1M, .moai: 188K)

**Key Insight:** This structure enables **isolated package development** while providing **workspace-wide agent orchestration** and **configuration management** - the best of both monorepo flexibility and package distribution clarity.

---

*For installation instructions, see INSTALL.md. For moai-adk features and usage, see moai-adk/README.md.*
