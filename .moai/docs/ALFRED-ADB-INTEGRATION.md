# Alfred Integration Guide: ADB AutoPlayer Ecosystem

> **Purpose**: Comprehensive integration guide for Alfred's delegation patterns, agent coordination, and command orchestration in the ADB AutoPlayer ecosystem.
> **Audience**: Alfred (Claude Code Super Agent Orchestrator) and MoAI-ADK developers
> **Last Updated**: 2025-12-01
> **Version**: 1.0.0

---

## Executive Summary

This document defines how Alfred orchestrates ADB automation workflows through specialized agents, slash commands, UV scripts, and skill modules. The ADB ecosystem implements a 5-tier delegation architecture with parallel execution capabilities, zero-context automation scripts, and comprehensive error recovery patterns.

**Key Integration Points:**

- **5 ADB Agents**: Specialized domain agents for device management, bot execution, testing, configuration, and workflow orchestration
- **4 Slash Commands**: `/adb:init`, `/adb:bot`, `/adb:test`, `/adb:deploy` forming a complete CI/CD pipeline
- **7 UV Scripts**: PEP 723-compliant zero-dependency automation tools
- **5 Skill Modules**: Progressive disclosure knowledge base (adb-fundamentals, device-management, game-automation, computer-vision, tauri-integration)
- **Parallel Execution**: 5x concurrent agent execution strategy for complex workflows

---

## Table of Contents

1. [Alfred Delegation Patterns](#1-alfred-delegation-patterns)
2. [ADB Agent Registry](#2-adb-agent-registry)
3. [Slash Command Integration](#3-slash-command-integration)
4. [UV Script Automation](#4-uv-script-automation)
5. [Configuration Management](#5-configuration-management)
6. [Best Practices](#6-best-practices)

---

## 1. Alfred Delegation Patterns

### 1.1 Delegation Architecture

Alfred delegates ADB tasks using a **5-tier hierarchical pattern**:

```
Alfred (Orchestrator)
  ↓
Tier 1: Command Interpretation (/adb:*)
  ↓
Tier 2: Agent Delegation (adb-*)
  ↓
Tier 3: Skill Module Loading (moai-domain-adb)
  ↓
Tier 4: UV Script Execution (PEP 723)
  ↓
Tier 5: ADB Command Execution (Device Communication)
```

### 1.2 5x Parallel Agent Execution Strategy

For complex ADB workflows requiring multi-device or multi-phase operations, Alfred delegates to **5 agents in parallel**:

**Agent Distribution:**

```python
# Example: Complex multi-device bot deployment
Task(
    parallel=[
        # Agent 1: Device Manager (Device Pool Orchestration)
        {
            "subagent_type": "adb-device-manager",
            "prompt": "Validate device pool connectivity and readiness"
        },
        # Agent 2: Config Manager (Configuration Validation)
        {
            "subagent_type": "adb-config-manager",
            "prompt": "Validate ADB.toml and game-specific configuration files"
        },
        # Agent 3: Bot Runner (Bot Preparation)
        {
            "subagent_type": "adb-bot-runner",
            "prompt": "Prepare bot code and load custom routines"
        },
        # Agent 4: Game Tester (Pre-deployment Testing)
        {
            "subagent_type": "adb-game-tester",
            "prompt": "Execute smoke tests on staging device"
        },
        # Agent 5: Workflow Orchestrator (Coordination)
        {
            "subagent_type": "adb-workflow-orchestrator",
            "prompt": "Monitor parallel execution and coordinate dependencies"
        }
    ]
)
```

**Execution Flow:**

```
[T=0s]  Alfred receives /adb:deploy production command
  ↓
[T=1s]  5 agents launch in parallel
  ├─ adb-device-manager     → Validates 3 devices (2s)
  ├─ adb-config-manager     → Parses config files (1s)
  ├─ adb-bot-runner         → Loads bot code (3s)
  ├─ adb-game-tester        → Runs smoke tests (5s)
  └─ adb-workflow-orchestrator → Monitors progress (ongoing)
  ↓
[T=5s]  All agents report status to workflow orchestrator
  ↓
[T=6s]  Workflow orchestrator resolves dependencies
  ↓
[T=7s]  Sequential deployment phase begins (staged rollout)
```

### 1.3 Agent Coordination and Dependency Tracking

**Dependency Matrix:**

| Agent                      | Depends On                    | Blocks                        | Timeout |
|----------------------------|-------------------------------|-------------------------------|---------|
| adb-device-manager         | None (parallel entry)         | adb-bot-runner, adb-game-tester | 30s    |
| adb-config-manager         | None (parallel entry)         | adb-bot-runner                | 15s     |
| adb-bot-runner             | device-manager, config-manager | adb-game-tester               | 60s     |
| adb-game-tester            | bot-runner                    | deployment phase               | 120s    |
| adb-workflow-orchestrator  | None (monitors all)           | None (coordination only)       | N/A     |

**Dependency Resolution Algorithm:**

```python
def resolve_dependencies(agents: List[Agent]) -> List[ExecutionPhase]:
    """
    Resolve agent dependencies and create execution phases.

    Returns:
        List of execution phases with agents grouped by dependency level.
    """
    phases = []

    # Phase 1: Independent agents (no dependencies)
    phase1 = [agent for agent in agents if not agent.depends_on]
    phases.append(ExecutionPhase(agents=phase1, parallel=True))

    # Phase 2: Agents depending on Phase 1 completion
    phase2 = [agent for agent in agents if agent.depends_on in phase1]
    phases.append(ExecutionPhase(agents=phase2, parallel=False))

    # Phase 3: Sequential execution (final deployment)
    phase3 = [agent for agent in agents if agent.execution_mode == "sequential"]
    phases.append(ExecutionPhase(agents=phase3, parallel=False))

    return phases
```

### 1.4 Error Recovery and Rollback Patterns

**Error Handling Strategy:**

```
Error Detected → Classify Severity → Execute Recovery
  ↓                ↓                    ↓
Critical        Halt all agents    → Rollback initiated
  ↓                ↓                    ↓
Medium          Skip failed agent  → Continue with warnings
  ↓                ↓                    ↓
Low             Log and continue   → No interruption
```

**Rollback Execution:**

```python
# Automatic rollback trigger
if deployment_failure_rate > 50%:
    rollback_manager = Task(
        subagent_type="adb-device-manager",
        prompt=f"Rollback to backup snapshot {backup_id}",
        priority="critical"
    )

    # Restore configuration on all deployed devices
    for device in successfully_deployed:
        restore_configuration(device, backup_id)

    # Verify rollback success
    verify_rollback(devices)

    # Generate rollback report
    generate_rollback_report(backup_id, devices)
```

**Error Recovery Hierarchy:**

1. **Device Offline** (Medium): Skip device, continue with others
2. **Configuration Invalid** (Critical): Halt deployment, fix config
3. **Smoke Test Failed** (Critical): Halt deployment, rollback
4. **Performance Degradation** (Low): Log warning, continue monitoring
5. **Partial Deployment Failure** (Medium): Mark partial success, offer retry

### 1.5 Token Optimization Strategies

**Progressive Context Loading:**

```python
# Load only necessary context per phase
Phase 1 (Device Validation):
    - Load: adb-fundamentals module (3K tokens)
    - Skip: game-automation, computer-vision modules

Phase 2 (Bot Preparation):
    - Load: game-automation module (4K tokens)
    - Skip: tauri-integration module (not needed yet)

Phase 3 (Deployment):
    - Load: device-management module (3.5K tokens)
    - Skip: computer-vision (not needed for deployment)
```

**Agent Context Sharing:**

```python
# Share device analysis results across agents (avoid re-analysis)
device_context = adb_device_manager.get_shared_context()

# Pass context to dependent agents
adb_bot_runner.inject_context(device_context)
adb_game_tester.inject_context(device_context)

# Token savings: ~15K tokens (avoid 3x device analysis)
```

---

## 2. ADB Agent Registry

### 2.1 Complete Agent Catalog

**5 Specialized ADB Agents:**

| Agent Name                | Role                          | Tier  | Tools Access              | Skill Dependencies        | Delegation Chains             |
|---------------------------|-------------------------------|-------|---------------------------|---------------------------|-------------------------------|
| adb-device-manager        | Device pool orchestration     | 2     | Read, Bash, TodoWrite     | moai-domain-adb           | → adb-bot-runner              |
| adb-bot-runner            | Bot execution control         | 2     | Read, Write, Bash         | moai-domain-adb, moai-lang-unified | → adb-game-tester      |
| adb-game-tester           | Test execution and validation | 2     | Read, Bash, TodoWrite     | moai-domain-adb, moai-workflow-testing | None (terminal)   |
| adb-config-manager        | Configuration validation      | 2     | Read, Edit, TodoWrite     | moai-domain-adb           | → adb-bot-runner              |
| adb-workflow-orchestrator | Multi-agent coordination      | 2     | Task, TodoWrite, AskUserQuestion | moai-domain-adb, moai-foundation-core | All agents (orchestrates) |

### 2.2 Agent Detailed Specifications

#### Agent 1: adb-device-manager

**Purpose:** Orchestrate device pool management, connection lifecycle, and multi-device operations.

**Capabilities:**
- Device discovery and connectivity validation
- Multi-device batch operations (parallel ADB commands)
- Device state tracking (online, offline, unauthorized)
- Connection pooling and failover strategies
- Device health monitoring

**Tool Access Pattern:**
```python
# Read device configuration
device_pool = Read("src-tauri/Settings/ADB.toml")

# Execute ADB commands
devices = Bash("adb devices -l")

# Track device validation progress
TodoWrite([
    {"content": "Validate device 1/3", "status": "in_progress"},
    {"content": "Validate device 2/3", "status": "pending"},
    {"content": "Validate device 3/3", "status": "pending"}
])
```

**Skill Dependencies:**
- `moai-domain-adb:device-management` (primary module)
- `moai-domain-adb:adb-fundamentals` (core ADB operations)

**Delegation Chains:**
```
adb-device-manager
  ├─ Validates device pool
  ├─ Delegates bot deployment → adb-bot-runner
  └─ Monitors device health → continuous loop
```

**Exit Codes:**
- `0`: Success (all devices validated)
- `1`: Partial success (some devices offline)
- `2`: Critical failure (no devices available)

---

#### Agent 2: adb-bot-runner

**Purpose:** Execute bot automation workflows on configured devices with real-time monitoring.

**Capabilities:**
- Bot code loading and initialization
- Action sequence execution (tap, swipe, OCR)
- Real-time performance monitoring
- Error recovery and retry logic
- Multi-device bot orchestration

**Tool Access Pattern:**
```python
# Load bot configuration
bot_config = Read("src-tauri/src-python/adb_auto_player/games/afk_journey/custom_routine/arena_bot.py")

# Generate bot code (if needed)
generated_bot = Write("generated_bot.py", bot_template)

# Execute bot with monitoring
bot_execution = Bash("uv run generated_bot.py --device emulator-5554 --monitor")
```

**Skill Dependencies:**
- `moai-domain-adb:game-automation` (primary module)
- `moai-domain-adb:computer-vision` (OCR and template matching)
- `moai-lang-unified:python` (bot code generation)

**Delegation Chains:**
```
adb-bot-runner
  ├─ Loads bot code
  ├─ Executes bot → device ADB commands
  ├─ Delegates testing → adb-game-tester
  └─ Reports metrics → adb-workflow-orchestrator
```

**Exit Codes:**
- `0`: Success (bot executed, target achieved)
- `1`: Partial success (some actions failed, bot continues)
- `2`: Critical failure (bot crashed or device disconnected)

---

#### Agent 3: adb-game-tester

**Purpose:** Execute comprehensive testing workflows (unit, integration, E2E) for bot validation.

**Capabilities:**
- Unit test execution (configuration validation)
- Integration test execution (device communication)
- E2E test execution (full bot workflow simulation)
- Coverage report generation
- Performance benchmarking

**Tool Access Pattern:**
```python
# Execute pytest test suite
test_results = Bash("pytest tests/unit/ tests/integration/ -v --cov=adb_auto_player")

# Parse test results
test_report = Read(".moai/temp/tests/test-results.xml")

# Track test progress
TodoWrite([
    {"content": "Unit tests", "status": "completed"},
    {"content": "Integration tests", "status": "in_progress"},
    {"content": "E2E tests", "status": "pending"}
])
```

**Skill Dependencies:**
- `moai-domain-adb:game-automation` (test scenario design)
- `moai-domain-adb:computer-vision` (image recognition validation)
- `moai-workflow-testing` (TDD patterns)

**Delegation Chains:**
```
adb-game-tester
  ├─ Executes test suites → pytest
  ├─ Analyzes test results → test parser
  └─ Generates test report → terminal (no further delegation)
```

**Exit Codes:**
- `0`: Success (all tests passed, coverage >= 85%)
- `1`: Partial success (some tests failed, coverage >= 75%)
- `2`: Critical failure (test pass rate < 70% or coverage < 75%)

---

#### Agent 4: adb-config-manager

**Purpose:** Validate and manage ADB configuration files (ADB.toml, game-specific configs).

**Capabilities:**
- TOML configuration parsing and validation
- Schema validation (required fields, data types)
- Device pool consistency checks
- Configuration backup and versioning
- Migration support (deprecated settings)

**Tool Access Pattern:**
```python
# Read and validate configuration
adb_config = Read("src-tauri/Settings/ADB.toml")
game_config = Read("src-tauri/Settings/AFKJourney.toml")

# Update configuration (if needed)
Edit("src-tauri/Settings/ADB.toml", old_config, new_config)

# Track validation steps
TodoWrite([
    {"content": "Parse ADB.toml", "status": "completed"},
    {"content": "Validate device pool", "status": "in_progress"},
    {"content": "Check schema compliance", "status": "pending"}
])
```

**Skill Dependencies:**
- `moai-domain-adb:adb-fundamentals` (configuration schema)
- `moai-formats-data` (TOML parsing patterns)

**Delegation Chains:**
```
adb-config-manager
  ├─ Validates configuration
  ├─ Delegates bot initialization → adb-bot-runner
  └─ Reports validation status → adb-workflow-orchestrator
```

**Exit Codes:**
- `0`: Success (configuration valid)
- `1`: Warning (deprecated settings found, still usable)
- `2`: Critical failure (invalid configuration, cannot proceed)

---

#### Agent 5: adb-workflow-orchestrator

**Purpose:** Coordinate multi-agent workflows, resolve dependencies, and track execution progress.

**Capabilities:**
- Parallel agent execution coordination
- Dependency resolution and ordering
- Progress tracking and status aggregation
- Error detection and rollback triggering
- User interaction management (AskUserQuestion)

**Tool Access Pattern:**
```python
# Delegate to multiple agents in parallel
Task(parallel=[
    {"subagent_type": "adb-device-manager", "prompt": "..."},
    {"subagent_type": "adb-config-manager", "prompt": "..."},
    {"subagent_type": "adb-bot-runner", "prompt": "..."}
])

# Track overall workflow progress
TodoWrite([
    {"content": "Device validation", "status": "completed"},
    {"content": "Configuration validation", "status": "completed"},
    {"content": "Bot preparation", "status": "in_progress"},
    {"content": "Deployment", "status": "pending"},
    {"content": "Post-deployment monitoring", "status": "pending"}
])

# Request user approval
AskUserQuestion({
    "questions": [{
        "question": "All validations passed. Proceed with deployment?",
        "options": [...]
    }]
})
```

**Skill Dependencies:**
- `moai-domain-adb` (all modules, comprehensive knowledge)
- `moai-foundation-core` (delegation patterns, execution rules)

**Delegation Chains:**
```
adb-workflow-orchestrator
  ├─ Orchestrates all agents → parallel/sequential execution
  ├─ Monitors progress → continuous coordination
  ├─ Handles errors → rollback or recovery
  └─ Reports final status → Alfred
```

**Exit Codes:**
- `0`: Success (workflow completed as planned)
- `1`: Partial success (some phases failed, acceptable)
- `2`: Critical failure (workflow aborted, rollback triggered)

---

### 2.3 Agent Skill Loading Strategy

**Skill Auto-Loading via YAML Frontmatter:**

All ADB agents declare skill dependencies in their YAML frontmatter (when agent definitions are created):

```yaml
---
name: adb-bot-runner
skills: moai-domain-adb, moai-lang-unified
tools: Read, Write, Bash, TodoWrite
---
```

**Alfred's Skill Loading Logic:**

```python
# Alfred automatically loads skills when delegating to agents
def delegate_to_agent(agent_type: str, prompt: str):
    """
    Delegate task to specialized agent with automatic skill loading.
    """
    agent_config = load_agent_config(agent_type)

    # Auto-load declared skills
    for skill in agent_config.skills:
        load_skill(skill)  # Loads skill context for agent

    # Delegate task
    return Task(subagent_type=agent_type, prompt=prompt)
```

**Progressive Skill Module Loading:**

```python
# Load specific modules instead of entire skill (token optimization)
def load_skill_module(skill: str, module: str):
    """
    Load specific skill module for targeted expertise.

    Examples:
        load_skill_module("moai-domain-adb", "adb-fundamentals")
        load_skill_module("moai-domain-adb", "game-automation")
    """
    module_path = f".claude/skills/{skill}/modules/{module}.md"
    return load_module_content(module_path)
```

**Token Cost Analysis:**

| Skill Loading Strategy           | Tokens | Use Case                          |
|----------------------------------|--------|-----------------------------------|
| Full skill (`moai-domain-adb`)   | 12K    | Complex workflows, all modules    |
| Single module (adb-fundamentals) | 3K     | Device validation only            |
| Two modules (device + game)      | 7K     | Bot deployment (focused scope)    |
| Zero modules (Quick Reference)   | 0      | Simple ADB commands               |

---

## 3. Slash Command Integration

### 3.1 Complete Command Workflow

**ADB Command Pipeline:**

```
/adb:init → /adb:bot → /adb:test → /adb:deploy
    ↓           ↓           ↓            ↓
  Setup    Development   Validation   Production
```

### 3.2 Command Execution Patterns

#### `/adb:init` - Project Initialization

**Purpose:** Initialize ADB project, discover devices, generate configuration files.

**Alfred's Execution Strategy:**

```python
# Phase 1: Pre-flight checks (sequential)
device_check = Task(
    subagent_type="adb-device-manager",
    prompt="Verify ADB installation and list connected devices"
)

# Phase 2: Device analysis (parallel if multiple devices)
device_analysis = Task(
    subagent_type="adb-device-manager",
    prompt="Analyze device capabilities and generate hardware report"
)

# Phase 3: Configuration generation (sequential, depends on analysis)
config_generation = Task(
    subagent_type="adb-config-manager",
    prompt="Generate ADB.toml configuration with analyzed devices"
)

# Phase 4: Template initialization (parallel with config validation)
Task(parallel=[
    {"subagent_type": "adb-config-manager", "prompt": "Validate generated configuration"},
    {"subagent_type": "adb-bot-runner", "prompt": "Initialize bot template directories"}
])
```

**UV Script Integration:**

```bash
# Alfred invokes adb_device_analyzer.py via agent
uv run .claude/skills/moai-domain-adb/scripts/adb_device_analyzer.py --json > device_info.json

# Agent parses JSON output and uses it for configuration
```

**Error Handling Chain:**

```
No devices found (exit 1)
  ↓
Alfred detects error → AskUserQuestion
  ↓
"No devices detected. Please connect a device or start an emulator."
  ↓
User connects device → Retry /adb:init
```

**Integration with /moai:* commands:**

```python
# After successful /adb:init, Alfred may suggest:
AskUserQuestion({
    "questions": [{
        "question": "Initialization complete. What would you like to do next?",
        "options": [
            {"label": "/adb:bot", "description": "Generate game bot"},
            {"label": "/moai:0-project", "description": "Configure project settings"},
            {"label": "Manual exploration", "description": "Explore project structure"}
        ]
    }]
})
```

---

#### `/adb:bot` - Bot Generation and Execution

**Purpose:** Generate game-specific bot from templates, configure parameters, deploy, and execute.

**Alfred's Execution Strategy:**

```python
# Phase 1: Template selection (user interaction)
template_selection = AskUserQuestion({
    "questions": [{
        "question": "Select bot template:",
        "options": ["arena", "farming", "quests", "events", "custom"]
    }]
})

# Phase 2: Bot generation (sequential)
bot_generation = Task(
    subagent_type="adb-bot-runner",
    prompt=f"Generate {template_selection} bot with user configuration"
)

# Phase 3: Bot validation (parallel with device check)
Task(parallel=[
    {"subagent_type": "adb-config-manager", "prompt": "Validate bot configuration"},
    {"subagent_type": "adb-device-manager", "prompt": "Verify target device online"}
])

# Phase 4: Bot deployment and execution (sequential, monitored)
bot_execution = Task(
    subagent_type="adb-bot-runner",
    prompt="Deploy bot to device and start execution with real-time monitoring"
)
```

**UV Script Integration:**

```bash
# Bot generation script
uv run .claude/skills/moai-domain-adb/scripts/adb_bot_generator.py \
    --template arena \
    --config bot_config.json \
    --output generated_bot.py

# Configuration validation script
uv run .claude/skills/moai-domain-adb/scripts/adb_config_validator.py \
    --bot generated_bot.py \
    --device emulator-5554
```

**Progress Tracking with TodoWrite:**

```python
TodoWrite([
    {"content": "Select bot template", "status": "completed", "activeForm": "Selecting bot template"},
    {"content": "Configure bot parameters", "status": "completed", "activeForm": "Configuring bot parameters"},
    {"content": "Generate bot code", "status": "completed", "activeForm": "Generating bot code"},
    {"content": "Deploy to device", "status": "in_progress", "activeForm": "Deploying to device"},
    {"content": "Start bot execution", "status": "pending", "activeForm": "Starting bot execution"},
    {"content": "Monitor performance", "status": "pending", "activeForm": "Monitoring performance"}
])
```

**Error Recovery:**

```
Bot generation fails (syntax error)
  ↓
adb-bot-runner detects error → Reports to Alfred
  ↓
Alfred offers fix options via AskUserQuestion:
  - "Auto-fix syntax error"
  - "Use minimal template (safe fallback)"
  - "Review generated code manually"
```

---

#### `/adb:test` - Test Execution and Validation

**Purpose:** Execute comprehensive test suite (unit, integration, E2E) with coverage reporting.

**Alfred's Execution Strategy:**

```python
# Phase 1: Pre-test validation (sequential)
test_setup = Task(
    subagent_type="adb-game-tester",
    prompt="Verify test environment (pytest, devices, configuration)"
)

# Phase 2: Test execution (parallel by test type)
test_results = Task(parallel=[
    {"subagent_type": "adb-game-tester", "prompt": "Execute unit tests"},
    {"subagent_type": "adb-game-tester", "prompt": "Execute integration tests (requires device)"},
    {"subagent_type": "adb-game-tester", "prompt": "Execute E2E tests (requires game)"}
])

# Phase 3: Analysis and reporting (sequential, depends on test results)
test_report = Task(
    subagent_type="adb-game-tester",
    prompt="Analyze test results, generate coverage report, and recommendations"
)
```

**UV Script Integration:**

```bash
# Test execution via pytest (invoked by adb-game-tester agent)
pytest tests/unit/ tests/integration/ tests/e2e/ \
    -v \
    --cov=adb_auto_player \
    --cov-report=html:.moai/temp/coverage/ \
    --junit-xml=.moai/temp/tests/test-results.xml

# Performance profiling script (optional)
uv run .claude/skills/moai-domain-adb/scripts/adb_performance_profiler.py \
    --bot bot.py \
    --iterations 100 \
    --json > performance_metrics.json
```

**Progress Tracking:**

```python
TodoWrite([
    {"content": "Verify test environment", "status": "completed", "activeForm": "Verifying test environment"},
    {"content": "Execute unit tests", "status": "completed", "activeForm": "Executing unit tests"},
    {"content": "Execute integration tests", "status": "in_progress", "activeForm": "Executing integration tests"},
    {"content": "Execute E2E tests", "status": "pending", "activeForm": "Executing E2E tests"},
    {"content": "Generate test report", "status": "pending", "activeForm": "Generating test report"},
    {"content": "Present results", "status": "pending", "activeForm": "Presenting results"}
])
```

**Integration with /moai:* commands:**

```python
# After tests pass, Alfred suggests next steps
if test_pass_rate >= 80% and coverage >= 85%:
    AskUserQuestion({
        "questions": [{
            "question": "Tests passed! Proceed to deployment?",
            "options": [
                {"label": "/adb:deploy", "description": "Deploy to production"},
                {"label": "/moai:3-sync", "description": "Sync documentation first"},
                {"label": "Review test report", "description": "Analyze results before deployment"}
            ]
        }]
    })
```

---

#### `/adb:deploy` - Production Deployment

**Purpose:** Execute staged deployment with backup, rollback, and post-deployment monitoring.

**Alfred's Execution Strategy:**

```python
# Phase 1: Pre-deployment validation (5 agents in parallel)
validation_results = Task(parallel=[
    {"subagent_type": "adb-device-manager", "prompt": "Validate device pool readiness"},
    {"subagent_type": "adb-config-manager", "prompt": "Validate configuration integrity"},
    {"subagent_type": "adb-bot-runner", "prompt": "Validate bot code and dependencies"},
    {"subagent_type": "adb-game-tester", "prompt": "Check test results (must pass)"},
    {"subagent_type": "adb-workflow-orchestrator", "prompt": "Create backup snapshot"}
])

# Phase 2: Staging deployment (sequential)
staging_result = Task(
    subagent_type": "adb-device-manager",
    prompt="Deploy to staging device, run smoke tests, verify success"
)

# Phase 3: Production deployment (sequential with progress tracking)
production_result = Task(
    subagent_type="adb-device-manager",
    prompt="Deploy to production devices sequentially with rollback on failure"
)

# Phase 4: Post-deployment monitoring (parallel)
Task(parallel=[
    {"subagent_type": "adb-device-manager", "prompt": "Monitor device health (15 minutes)"},
    {"subagent_type": "adb-bot-runner", "prompt": "Monitor bot performance metrics"},
    {"subagent_type": "adb-workflow-orchestrator", "prompt": "Generate deployment report"}
])
```

**UV Script Integration:**

```bash
# Deployment helper script
uv run .claude/skills/moai-domain-adb/scripts/adb_deployment_helper.py \
    --bot bot.py \
    --target production \
    --backup-id backup-20251201-213456 \
    --json > deployment_status.json

# Configuration validator (pre-deployment)
uv run .claude/skills/moai-domain-adb/scripts/adb_config_validator.py \
    --config ADB.toml \
    --strict \
    --json > validation_result.json
```

**Error Handling and Rollback:**

```python
# Automatic rollback trigger
if deployment_failure_rate > 50%:
    Alfred.execute("/adb:deploy --rollback backup-20251201-213456")

    # Rollback workflow
    rollback_result = Task(
        subagent_type="adb-device-manager",
        prompt="Restore configuration from backup and verify rollback"
    )

    # Notify user
    AskUserQuestion({
        "questions": [{
            "question": "Automatic rollback completed. What would you like to do?",
            "options": [
                {"label": "Review rollback report", "description": "Analyze rollback details"},
                {"label": "Fix issues and retry", "description": "Address deployment errors"},
                {"label": "Keep rolled back", "description": "Stay on previous version"}
            ]
        }]
    })
```

**Progress Tracking:**

```python
TodoWrite([
    {"content": "Pre-deployment validation", "status": "completed", "activeForm": "Validating pre-deployment"},
    {"content": "Create backup snapshot", "status": "completed", "activeForm": "Creating backup snapshot"},
    {"content": "Deploy to staging", "status": "completed", "activeForm": "Deploying to staging"},
    {"content": "Deploy to production device 1/3", "status": "completed", "activeForm": "Deploying to production device 1/3"},
    {"content": "Deploy to production device 2/3", "status": "in_progress", "activeForm": "Deploying to production device 2/3"},
    {"content": "Deploy to production device 3/3", "status": "pending", "activeForm": "Deploying to production device 3/3"},
    {"content": "Post-deployment monitoring", "status": "pending", "activeForm": "Monitoring post-deployment"},
    {"content": "Generate deployment report", "status": "pending", "activeForm": "Generating deployment report"}
])
```

---

### 3.3 Cross-Command Error Recovery

**Error Propagation Chain:**

```
/adb:init fails (no devices)
  ↓
Alfred detects error, halts pipeline
  ↓
User connects device
  ↓
Alfred suggests: "Retry /adb:init now that device is connected"
  ↓
Success → Alfred suggests: "Proceed to /adb:bot?"
```

**Command Resume Capability:**

```python
# Alfred saves command state on interruption
command_state = {
    "command": "/adb:bot",
    "phase": "bot_generation",
    "completed_steps": ["template_selection", "parameter_configuration"],
    "pending_steps": ["code_generation", "deployment"],
    "context": {...}
}

# On resume, Alfred restores state and continues
Alfred.resume_command(command_state)
```

---

## 4. UV Script Automation

### 4.1 PEP 723 Execution Pattern

**Zero-Context Design Principles:**

All ADB UV scripts follow PEP 723 inline script metadata format:

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.0",
#     "rich>=13.0.0",
# ]
# ///
"""
Script documentation with purpose, usage, and exit codes.
"""
```

**Benefits:**

1. **Zero-Dependency Execution**: No `requirements.txt`, no virtual environment setup
2. **Self-Contained**: All dependencies declared inline
3. **Instant Execution**: `uv run script.py` installs deps and runs in one command
4. **Cross-Platform**: Works on Windows, macOS, Linux without modification

### 4.2 7 UV Scripts Overview

| Script                        | Purpose                                      | Input                          | Output                        | Exit Codes       |
|-------------------------------|----------------------------------------------|--------------------------------|-------------------------------|------------------|
| adb_device_analyzer.py        | Analyze device capabilities                  | --device <serial> --json       | Device specs (JSON/table)     | 0/1/2/3/4        |
| adb_bot_generator.py          | Generate bot code from templates             | --template <type> --config     | Generated bot.py file         | 0/1/2            |
| adb_template_creator.py       | Create action templates from screenshots     | --screenshot <path> --region   | Template image + metadata     | 0/1/2            |
| adb_performance_profiler.py   | Profile bot execution performance            | --bot <path> --iterations      | Performance metrics (JSON)    | 0/1/2            |
| adb_config_validator.py       | Validate configuration files                 | --config <path> --strict       | Validation report (JSON)      | 0/1/2            |
| adb_game_tester.py            | Execute bot tests on devices                 | --bot <path> --device <serial> | Test results (JSON/JUnit)     | 0/1/2            |
| adb_deployment_helper.py      | Automate deployment workflows                | --bot <path> --target <env>    | Deployment status (JSON)      | 0/1/2/3          |

### 4.3 Agent Invocation Pattern

**Agent → UV Script Execution:**

```python
# Agent invokes UV script via Bash tool
def execute_uv_script(script_name: str, args: Dict[str, str]) -> Dict:
    """
    Execute UV script and parse JSON output.

    Args:
        script_name: Name of UV script (e.g., "adb_device_analyzer.py")
        args: Script arguments as dictionary

    Returns:
        Parsed JSON output from script
    """
    # Build command
    script_path = f".claude/skills/moai-domain-adb/scripts/{script_name}"
    arg_string = " ".join([f"--{k} {v}" for k, v in args.items()])
    command = f"uv run {script_path} {arg_string} --json"

    # Execute via Bash tool
    result = Bash(command)

    # Parse JSON output
    return json.loads(result.stdout)
```

**Example: Device Analysis**

```python
# adb-device-manager agent invokes device analyzer
device_info = execute_uv_script("adb_device_analyzer.py", {
    "device": "emulator-5554",
    "json": ""  # Flag (no value needed)
})

# Use parsed device info
api_level = device_info["api_level"]  # 34
resolution = device_info["resolution"]  # "1080x2400"
ram_mb = device_info["ram_mb"]  # 2048
```

### 4.4 Error Codes and Exit Handling

**Exit Code Convention:**

```python
EXIT_SUCCESS = 0      # Operation completed successfully
EXIT_WARNING = 1      # Operation completed with warnings (non-critical)
EXIT_ERROR = 2        # Operation failed (recoverable error)
EXIT_CRITICAL = 3     # Critical failure (cannot recover)
EXIT_INVALID = 4      # Invalid input or configuration
```

**Agent Error Handling:**

```python
def handle_script_exit_code(exit_code: int, script_name: str):
    """
    Handle UV script exit codes and take appropriate action.
    """
    if exit_code == 0:
        return {"status": "success", "action": "continue"}

    elif exit_code == 1:
        # Warning: Log and continue
        log_warning(f"{script_name} completed with warnings")
        return {"status": "warning", "action": "continue"}

    elif exit_code == 2:
        # Error: Retry once, then fail
        log_error(f"{script_name} failed, retrying...")
        return {"status": "error", "action": "retry"}

    elif exit_code == 3 or exit_code == 4:
        # Critical/Invalid: Halt execution
        log_critical(f"{script_name} failed critically")
        return {"status": "critical", "action": "halt"}
```

### 4.5 Dual Output Format (Human + JSON)

**All UV scripts support dual output:**

```bash
# Human-readable table output (default)
uv run adb_device_analyzer.py --device emulator-5554

# Output:
# ┌─────────────────┬───────────────────┐
# │ Property        │ Value             │
# ├─────────────────┼───────────────────┤
# │ Serial          │ emulator-5554     │
# │ API Level       │ 34 (Android 14)   │
# │ Resolution      │ 1080x2400         │
# └─────────────────┴───────────────────┘

# Machine-parseable JSON output (for agents)
uv run adb_device_analyzer.py --device emulator-5554 --json

# Output:
# {
#   "serial": "emulator-5554",
#   "api_level": 34,
#   "android_version": "Android 14",
#   "resolution": "1080x2400",
#   "ram_mb": 2048,
#   "cpu_threads": 8
# }
```

**Agent Parsing Strategy:**

```python
# Agent always uses --json flag for reliable parsing
output = Bash("uv run script.py --json")

# Parse JSON output
try:
    data = json.loads(output.stdout)
    # Process structured data
except json.JSONDecodeError:
    # Fallback: Parse human-readable output (less reliable)
    data = parse_table_output(output.stdout)
```

---

## 5. Configuration Management

### 5.1 ADB.toml Structure

**Primary Configuration File:**

```toml
# src-tauri/Settings/ADB.toml

[device_pool]
# List of configured devices
devices = [
    { serial = "emulator-5554", type = "emulator", api_level = 34, enabled = true },
    { serial = "R58N80ABCDE", type = "physical", api_level = 33, enabled = true },
    { serial = "192.168.1.100:5555", type = "remote", api_level = 32, enabled = false }
]

[adb_settings]
# ADB connection configuration
binary_path = "adb"  # System ADB or custom path
connection_timeout = 30  # seconds
retry_attempts = 3
retry_delay = 2  # seconds

[automation]
# Bot automation settings
default_action_delay = 1500  # milliseconds
screenshot_quality = 80  # 0-100
ocr_confidence_threshold = 0.8  # 0.0-1.0
template_match_threshold = 0.75  # 0.0-1.0

[deployment]
# Deployment configuration
staging_device = "emulator-5554"
backup_enabled = true
backup_directory = ".moai/backups/deployment/"
rollback_on_failure = true
post_deployment_monitoring_duration = 600  # seconds (10 minutes)
```

### 5.2 Game-Specific Configuration

**AFKJourney.toml Example:**

```toml
# src-tauri/Settings/AFKJourney.toml

[game_info]
package_name = "com.farlightgames.afkj"
activity_name = ".MainActivity"
min_api_level = 23
recommended_ram_mb = 2048

[automation]
# Game-specific automation settings
battle_strategy = "balanced"  # offensive, defensive, balanced
auto_collect_rewards = true
retry_on_defeat = true
max_retry_attempts = 3

[custom_routines]
# List of enabled custom routines
enabled = [
    "claim_afk_rewards",
    "arena_battles",
    "daily_quests",
    "legend_trial"
]

[detection_regions]
# Screen regions for OCR and template matching (x, y, width, height)
battle_button = [450, 1800, 180, 80]
opponent_list = [50, 400, 980, 1200]
rewards_popup = [200, 600, 680, 400]
formation_panel = [100, 200, 880, 1600]

[timing]
# Game-specific timing parameters
action_delay_ms = 1200
battle_timeout_s = 300
load_screen_timeout_s = 30
```

### 5.3 Configuration Validation

**Alfred's Configuration Validation Strategy:**

```python
# Phase 1: Load configurations
adb_config = Task(
    subagent_type="adb-config-manager",
    prompt="Load and parse ADB.toml and game-specific configurations"
)

# Phase 2: Schema validation
validation_result = Task(
    subagent_type="adb-config-manager",
    prompt="Validate configuration schema and required fields"
)

# Phase 3: Device pool verification
device_verification = Task(
    subagent_type="adb-device-manager",
    prompt="Verify configured devices are accessible"
)

# If validation fails, offer fixes
if not validation_result.success:
    AskUserQuestion({
        "questions": [{
            "question": f"Configuration validation failed: {validation_result.errors}",
            "options": [
                {"label": "Auto-fix", "description": "Attempt automatic correction"},
                {"label": "Edit manually", "description": "Open configuration file"},
                {"label": "Use defaults", "description": "Reset to default configuration"}
            ]
        }]
    })
```

**Configuration Validator Script:**

```bash
# Invoked by adb-config-manager agent
uv run .claude/skills/moai-domain-adb/scripts/adb_config_validator.py \
    --config src-tauri/Settings/ADB.toml \
    --game-config src-tauri/Settings/AFKJourney.toml \
    --strict \
    --json > validation_report.json
```

### 5.4 Template Management Paths

**Template Directory Structure:**

```
src-tauri/src-python/adb_auto_player/
├── games/                                  # Game-specific implementations
│   ├── afk_journey/                        # AFK Journey game
│   │   ├── __init__.py
│   │   ├── base.py                         # Base bot class
│   │   ├── templates/                      # Image templates for recognition
│   │   │   ├── battle_button.png
│   │   │   ├── rewards_popup.png
│   │   │   └── opponent_list.png
│   │   └── custom_routine/                 # Custom bot routines
│   │       ├── __init__.py
│   │       ├── claim_afk_rewards.py
│   │       ├── arena_battles.py
│   │       └── generated_bot_20251201.py   # Generated bots
│   └── template_base/                      # Generic templates (any game)
│       ├── __init__.py
│       ├── generic_bot.py
│       └── templates/
│           └── generic_button.png
```

**Template Creation Workflow:**

```python
# Agent invokes template creator script
template_result = Bash("""
    uv run .claude/skills/moai-domain-adb/scripts/adb_template_creator.py \
        --screenshot screen.png \
        --region "450,1800,180,80" \
        --name battle_button \
        --output src-tauri/src-python/adb_auto_player/games/afk_journey/templates/
""")

# Script extracts region from screenshot and saves as template
# Output: battle_button.png + battle_button_metadata.json
```

---

## 6. Best Practices

### 6.1 5x Parallel Agent Pattern Usage

**When to Use Parallel Execution:**

✅ **Use Parallel (5x agents)**:
- Independent validation tasks (device check, config check, test check)
- Multi-device operations (deploy to 3 devices simultaneously)
- Pre-deployment preparation (backup, validation, bot prep)
- Post-deployment monitoring (health check, performance tracking, reporting)

❌ **Avoid Parallel**:
- Sequential dependencies (config must be valid before deployment)
- Shared resource access (single device operations)
- User interaction required (one AskUserQuestion at a time)
- Deployment phases (staging → production must be sequential)

**Example: Pre-Deployment Validation (Parallel)**

```python
# Correct: All validations are independent
validation_results = Task(parallel=[
    {"subagent_type": "adb-device-manager", "prompt": "Check device connectivity"},
    {"subagent_type": "adb-config-manager", "prompt": "Validate configuration"},
    {"subagent_type": "adb-bot-runner", "prompt": "Verify bot code syntax"},
    {"subagent_type": "adb-game-tester", "prompt": "Check test results"},
    {"subagent_type": "adb-workflow-orchestrator", "prompt": "Create backup snapshot"}
])
```

**Example: Deployment (Sequential)**

```python
# Correct: Deployment stages have dependencies
staging_result = Task(
    subagent_type="adb-device-manager",
    prompt="Deploy to staging and validate"
)

if staging_result.success:
    production_result = Task(
        subagent_type="adb-device-manager",
        prompt="Deploy to production devices sequentially"
    )
```

### 6.2 Token Optimization Strategies

**Strategy 1: Progressive Module Loading**

```python
# Load only necessary modules per phase
Phase 1 (Init):
    moai-domain-adb:adb-fundamentals (3K tokens)

Phase 2 (Bot Development):
    moai-domain-adb:game-automation (4K tokens)

Phase 3 (Testing):
    moai-domain-adb:computer-vision (3.5K tokens)

Phase 4 (Deployment):
    moai-domain-adb:device-management (3.5K tokens)
    moai-domain-adb:tauri-integration (3K tokens)

# Total: 17K tokens across 4 phases
# Alternative (load all): 22K tokens (5K wasted)
```

**Strategy 2: Context Sharing Between Agents**

```python
# Avoid redundant operations
# ❌ Wrong: Each agent analyzes devices independently
agent1_analysis = analyze_devices()  # 5K tokens + 10s execution
agent2_analysis = analyze_devices()  # 5K tokens + 10s execution
agent3_analysis = analyze_devices()  # 5K tokens + 10s execution

# ✅ Correct: Analyze once, share context
shared_analysis = analyze_devices()  # 5K tokens + 10s execution
agent1.inject_context(shared_analysis)  # 0 tokens, instant
agent2.inject_context(shared_analysis)  # 0 tokens, instant
agent3.inject_context(shared_analysis)  # 0 tokens, instant

# Savings: 10K tokens, 20s execution time
```

**Strategy 3: UV Script Output Caching**

```python
# Cache script output to avoid re-execution
cache_key = f"device_analysis_{device_serial}"

if cache_key in script_cache:
    device_info = script_cache[cache_key]  # 0 tokens, instant
else:
    device_info = execute_uv_script("adb_device_analyzer.py", {"device": device_serial})
    script_cache[cache_key] = device_info  # Cache for 5 minutes
```

### 6.3 Error Recovery Workflows

**Error Classification and Response:**

| Error Type          | Severity | Response Strategy              | Rollback Required |
|---------------------|----------|--------------------------------|-------------------|
| Device offline      | Medium   | Skip device, continue          | No                |
| Config invalid      | Critical | Halt, fix config, retry        | No (not deployed) |
| Staging test fail   | Critical | Halt deployment, rollback      | No (staging only) |
| Deployment partial  | Medium   | Mark partial success, report   | User decides      |
| Deployment majority | Critical | Auto-rollback all devices      | Yes (automatic)   |
| Health check fail   | Medium   | Monitor, warn user             | User decides      |

**Error Recovery Template:**

```python
def handle_error(error: Exception, context: Dict) -> RecoveryAction:
    """
    Classify error and determine recovery action.
    """
    if isinstance(error, DeviceOfflineError):
        # Medium severity: Skip device
        return RecoveryAction(
            severity="medium",
            action="skip_device",
            message=f"Device {context['device_serial']} offline, skipping",
            rollback_required=False
        )

    elif isinstance(error, ConfigValidationError):
        # Critical severity: Halt deployment
        return RecoveryAction(
            severity="critical",
            action="halt_deployment",
            message=f"Configuration invalid: {error.details}",
            rollback_required=False
        )

    elif isinstance(error, DeploymentFailureError):
        # Critical if >50% devices failed
        failure_rate = context["failed_devices"] / context["total_devices"]
        if failure_rate > 0.5:
            return RecoveryAction(
                severity="critical",
                action="auto_rollback",
                message=f"Deployment failed on {failure_rate*100}% of devices",
                rollback_required=True
            )
        else:
            return RecoveryAction(
                severity="medium",
                action="partial_success",
                message=f"Deployment completed with {failure_rate*100}% failures",
                rollback_required=False
            )
```

### 6.4 Performance Tuning Tips

**1. Multi-Device Batch Operations**

```python
# ❌ Slow: Sequential device operations
for device in devices:
    result = execute_adb_command(device, "shell input tap 540 960")  # 500ms each
# Total: 1500ms for 3 devices

# ✅ Fast: Parallel device operations
results = parallel_execute([
    execute_adb_command(device, "shell input tap 540 960")
    for device in devices
])
# Total: 500ms for 3 devices (3x faster)
```

**2. ADB Command Optimization**

```python
# ❌ Slow: Multiple separate ADB commands
adb shell getprop ro.build.version.sdk  # 100ms
adb shell wm size                       # 100ms
adb shell dumpsys battery               # 100ms
# Total: 300ms

# ✅ Fast: Single combined command
adb shell "
    echo SDK: $(getprop ro.build.version.sdk);
    echo SIZE: $(wm size);
    echo BATTERY: $(dumpsys battery | grep level)
"
# Total: 120ms (2.5x faster)
```

**3. Template Matching Optimization**

```python
# ❌ Slow: Full-screen template matching
match = find_template(full_screenshot, template)  # 2000ms

# ✅ Fast: Region-based template matching
region = screenshot[450:530, 1800:1880]  # Crop to expected region
match = find_template(region, template)   # 200ms (10x faster)
```

**4. OCR Performance Tuning**

```python
# ❌ Slow: High-quality OCR on full screen
text = ocr_extract(full_screenshot, quality="high")  # 3000ms

# ✅ Fast: Standard OCR on specific region
region = screenshot[50:1230, 400:1600]  # Crop to text region
text = ocr_extract(region, quality="standard")  # 800ms (3.75x faster)
```

### 6.5 Agent Coordination Best Practices

**1. Clear Responsibility Boundaries**

```python
# ✅ Good: Each agent has clear domain
adb-device-manager:  Device pool management, connectivity
adb-config-manager:  Configuration validation, TOML parsing
adb-bot-runner:      Bot execution, action sequences
adb-game-tester:     Test execution, coverage reporting
adb-workflow-orchestrator: Multi-agent coordination

# ❌ Bad: Overlapping responsibilities
# (Avoid agents performing the same tasks)
```

**2. Explicit Dependency Declaration**

```python
# ✅ Good: Declare dependencies upfront
deployment_workflow = [
    Phase(agents=["adb-device-manager", "adb-config-manager"], parallel=True),  # Phase 1: Independent
    Phase(agents=["adb-bot-runner"], depends_on=["adb-config-manager"]),        # Phase 2: Depends on Phase 1
    Phase(agents=["adb-game-tester"], depends_on=["adb-bot-runner"]),           # Phase 3: Depends on Phase 2
]

# ❌ Bad: Implicit dependencies (unclear execution order)
```

**3. Use TodoWrite for Progress Transparency**

```python
# ✅ Good: Clear progress indicators
TodoWrite([
    {"content": "Validate devices", "status": "completed", "activeForm": "Validating devices"},
    {"content": "Load bot code", "status": "in_progress", "activeForm": "Loading bot code"},
    {"content": "Deploy to staging", "status": "pending", "activeForm": "Deploying to staging"},
    {"content": "Deploy to production", "status": "pending", "activeForm": "Deploying to production"}
])

# ❌ Bad: No progress tracking (user left in the dark)
```

---

## Appendix A: Quick Reference Tables

### A.1 Agent Selection Matrix

| Task Type                     | Primary Agent               | Secondary Agents            | Parallel Execution |
|-------------------------------|-----------------------------|-----------------------------|---------------------|
| Device initialization         | adb-device-manager          | adb-config-manager          | Yes (validation)    |
| Bot generation                | adb-bot-runner              | adb-config-manager          | No (sequential)     |
| Test execution                | adb-game-tester             | None                        | Yes (test types)    |
| Production deployment         | adb-device-manager          | All agents (validation)     | Yes (validation)    |
| Multi-device orchestration    | adb-workflow-orchestrator   | All agents                  | Yes (coordination)  |

### A.2 UV Script Decision Tree

```
Need to analyze device? → adb_device_analyzer.py
Need to generate bot? → adb_bot_generator.py
Need to create template? → adb_template_creator.py
Need to profile performance? → adb_performance_profiler.py
Need to validate config? → adb_config_validator.py
Need to test bot? → adb_game_tester.py
Need to deploy? → adb_deployment_helper.py
```

### A.3 Exit Code Reference

| Exit Code | Meaning           | Agent Response      | Alfred Action       |
|-----------|-------------------|---------------------|---------------------|
| 0         | Success           | Continue workflow   | Proceed to next step|
| 1         | Warning           | Log warning         | Continue with note  |
| 2         | Recoverable error | Retry once          | Retry or skip       |
| 3         | Critical error    | Halt execution      | Rollback or abort   |
| 4         | Invalid input     | Request correction  | Prompt user to fix  |

---

## Appendix B: Integration Checklist

### Pre-Integration Verification

- [ ] All 5 ADB agents defined with YAML frontmatter
- [ ] All 4 slash commands implemented with execution directives
- [ ] All 7 UV scripts follow PEP 723 format
- [ ] `moai-domain-adb` skill created with 5 modules
- [ ] Configuration files (ADB.toml, game configs) structured
- [ ] Agent skill dependencies declared in YAML
- [ ] TodoWrite integration in all agents
- [ ] AskUserQuestion patterns defined for user interaction
- [ ] Error recovery workflows documented
- [ ] Token optimization strategies implemented

### Post-Integration Testing

- [ ] Test `/adb:init` with no devices (error handling)
- [ ] Test `/adb:init` with 1 device (success path)
- [ ] Test `/adb:init` with 3 devices (parallel processing)
- [ ] Test `/adb:bot` bot generation (all templates)
- [ ] Test `/adb:test` with failing tests (error recovery)
- [ ] Test `/adb:deploy` rollback (automatic rollback trigger)
- [ ] Test 5x parallel agent execution (performance validation)
- [ ] Test cross-command error propagation
- [ ] Test UV script exit code handling (all codes 0-4)
- [ ] Test configuration validation (invalid configs)

---

## Document Version History

| Version | Date       | Changes                                           |
|---------|------------|---------------------------------------------------|
| 1.0.0   | 2025-12-01 | Initial comprehensive integration guide           |

---

## References

- **MoAI-ADK Foundation**: `.claude/skills/moai-foundation-core/`
- **ADB Domain Skill**: `.claude/skills/moai-domain-adb/SKILL.md`
- **Slash Commands**: `.claude/commands/adb/*.md`
- **UV Scripts**: `.claude/skills/moai-domain-adb/scripts/*.py`
- **CLAUDE.md**: Main Alfred execution directives

---

**Status**: ✅ Production Ready
**Maintainer**: MoAI-ADK Community
**License**: MIT
