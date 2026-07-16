---
name: macos-resource-optimizer:0-init
description: "Initialize configuration and validate Python engine setup"
argument-hint: "[--validate-only]"
allowed-tools:
  - Task
  - AskUserQuestion
model: haiku
skills:
  - moai-system-macos-resource-optimizer
---

## 📋 Pre-execution Context

!git status --porcelain
!git branch --show-current

## 📁 Essential Files

@.moai/config/config.json
@SPEC-MACOS-OPTIMIZER-001

# ⚙️ MoAI macOS Resource Optimizer: Initialization


### Quick Status Check

```python
# Execute status.py for quick health check
result = Bash("uv run .claude/skills/macos-resource-optimizer/scripts/status.py --json")
data = json.loads(result.stdout)

# Display results
overall_status = data["status"]
cpu_percent = data["cpu_percent"]
memory_percent = data["memory_percent"]
```


> **Architecture**: Commands → Agents → Skills. This command orchestrates ONLY through `Task()` tool.
> **Delegation Model**: Command delegates to manager-resource-coordinator for all validation and setup operations.

## 🎯 Command Purpose

Initialize macOS Resource Optimizer configuration and validate Python engine setup for optimal system resource management.

**초기화 작업**: $ARGUMENTS

This command validates the Python execution engine, checks dependencies, and initializes configuration for the macOS Resource Optimizer system.

---

## 🧠 Associated Agents & Skills

| Agent/Skill | Purpose |
|------------|---------|
| **manager-resource-coordinator** | Python engine validation, dependency checking, MetricsCache initialization |
| **moai-system-macos-resource-optimizer** | macOS resource optimization patterns and configuration standards |

---

## 💡 Execution Philosophy: "Validate Before Execute"

`/macos-resource-optimizer:0-init` performs comprehensive validation through complete agent delegation:

```
User Command: /macos-resource-optimizer:0-init [--validate-only]
    ↓
Command (Zero Direct Tool Usage)
    ↓
Task(subagent_type="manager-resource-coordinator",
     description="Validate Python engine and initialize configuration",
     prompt="Validate UV script setup at .claude/skills/macos-resource-optimizer/scripts/status.py")
    ↓
manager-resource-coordinator:
  1. Check UV scripts exist (.claude/skills/macos-resource-optimizer/scripts/*.py)
  2. Validate UV CLI is installed and functional
  3. Test UV script execution via Bash(uv run scripts/status.py)
  4. Initialize MetricsCache and configuration
  5. Verify 8 wrapper agents are accessible
    ↓
Output: Validation Report → User Confirmation
```

### Key Principle: Zero Direct Tool Usage

**This command uses ONLY Task() and AskUserQuestion():**

- ❌ No Read (file operations delegated)
- ❌ No Write (file operations delegated)
- ❌ No Bash (command execution delegated)
- ❌ No Glob (file discovery delegated)
- ✅ **Task()** for orchestration
- ✅ **AskUserQuestion()** for user interaction

---

## 🚀 PHASE 1: Python Engine Validation

**Goal**: Verify Python execution engine is properly configured and accessible

### Step 1.1: Check Python Engine Existence

Validate that the Python coordinator script exists and is executable:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Validate Python engine setup"
- `prompt`: """
  **Task**: Python Engine Validation

  **Location**: .claude/skills/macos-resource-optimizer/scripts/

  **UV Script Validation Steps**:
  1. Verify UV CLI is installed: `uv --version`
  2. Check UV scripts exist: status.py, analyze_*.py, optimize.py
  3. Validate PEP 723 inline dependencies in script headers
  4. Test UV script execution: `uv run scripts/status.py --json`
  5. Measure execution time (should be < 5s)

  **Output Format**:
  - Status: PASS/FAIL
  - Python version detected
  - Dependencies found: [list]
  - Issues (if any): [list]

  **Language**: Korean for user-facing messages
  """

### Step 1.2: Dependency Validation

Check all required Python dependencies are installed:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Validate Python dependencies"
- `prompt`: """
  **Task**: Dependency Validation

  **Required Dependencies**:
  - psutil >= 5.9.0
  - click >= 8.1.0
  - rich >= 13.0.0

  **Validation Steps**:
  1. Check each package is importable
  2. Verify version compatibility
  3. Test key functionality (psutil.cpu_percent, rich.Console)

  **Output Format**:
  - Installed: [package@version]
  - Missing: [package list]
  - Version conflicts: [details]

  **Language**: Korean for user-facing messages
  """

---

## 🚀 PHASE 2: Subprocess Execution Test

**Goal**: Verify subprocess execution with timeout handling

### Step 2.1: Test Basic Execution

Execute a simple test command to validate subprocess handling:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Test subprocess execution"
- `prompt`: """
  **Task**: Subprocess Execution Test

  **Test Command**: .claude/skills/macos-resource-optimizer/scripts/status.py --test

  **Validation**:
  1. Execute with 5-second timeout
  2. Capture stdout/stderr
  3. Verify exit code == 0
  4. Measure execution time

  **Expected Output**:
  - Execution time: < 2.0s
  - Exit code: 0
  - No stderr warnings

  **Error Handling**:
  - Timeout: Report failure with diagnostic
  - Non-zero exit: Show error details
  - Import errors: List missing dependencies

  **Language**: Korean for user-facing messages
  """

### Step 2.2: Verify Agent Accessibility

Check all 8 wrapper agents are loadable:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Validate wrapper agent accessibility"
- `prompt`: """
  **Task**: Wrapper Agent Validation

  **Required Agents** (8 total):
  1. manager-resource-coordinator
  2. manager-resource-strategy
  3. expert-cpu-optimizer
  4. expert-memory-optimizer
  5. expert-disk-optimizer
  6. expert-network-optimizer
  7. expert-battery-optimizer
  8. expert-thermal-optimizer

  **Validation Steps**:
  1. Verify each agent file exists in .claude/agents/
  2. Check YAML frontmatter is valid
  3. Confirm skill reference: moai-system-macos-resource-optimizer

  **Output Format**:
  - Found: [agent list]
  - Missing: [agent list]
  - Invalid YAML: [agent list]

  **Language**: Korean for user-facing messages
  """

---

## 🚀 PHASE 3: Configuration Initialization

**Goal**: Initialize MetricsCache and configuration files

### Step 3.1: Initialize MetricsCache

Create MetricsCache with default configuration:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Initialize MetricsCache"
- `prompt`: """
  **Task**: MetricsCache Initialization

  **Configuration**:
  - cache_ttl_seconds: 30
  - max_cache_entries: 100
  - cache_location: .claude/skills/macos-resource-optimizer/.data/cache/metrics.json

  **Initialization Steps**:
  1. Create cache directory if missing
  2. Initialize empty metrics.json
  3. Set default thresholds:
     - CPU: 80%
     - Memory: 85%
     - Disk: 90%
     - Network: 75%
     - Battery: 20%
     - Thermal: 85°C

  **Output Format**:
  - Cache initialized: ✅/❌
  - Location: [path]
  - Default thresholds: [list]

  **Language**: Korean for user-facing messages
  """

### Step 3.2: Create Configuration File

Generate default optimizer configuration:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Create optimizer configuration"
- `prompt`: """
  **Task**: Configuration File Creation

  **File**: .claude/skills/macos-resource-optimizer/.data/config.json

  **Configuration Sections**:
  1. analysis_settings:
     - parallel_execution: true
     - timeout_seconds: 5
     - cache_enabled: true

  2. optimization_settings:
     - auto_approve: false
     - dry_run_default: true
     - risk_tolerance: "medium"

  3. monitoring_settings:
     - interval_seconds: 60
     - alert_threshold: 80
     - auto_optimize: false

  4. report_settings:
     - format: "markdown"
     - output_dir: ".moai/reports/"
     - include_charts: true

  **Language**: Korean for user-facing messages
  """

---

## 🚀 PHASE 4: Validation Report

**Goal**: Present comprehensive validation results to user

### Step 4.1: Generate Validation Report

Aggregate all validation results:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Generate validation report"
- `prompt`: """
  **Task**: Validation Report Generation

  **Report Sections**:
  1. Python Engine Status
     - Version: [detected]
     - Location: [path]
     - Executable: ✅/❌

  2. Dependencies Status
     - psutil: [version] ✅/❌
     - click: [version] ✅/❌
     - rich: [version] ✅/❌

  3. Agent Availability
     - Found: [count]/8
     - Missing: [list if any]

  4. Configuration Status
     - MetricsCache: ✅/❌
     - config.json: ✅/❌
     - Thresholds: [configured]

  5. Performance Test
     - Execution time: [seconds]
     - Timeout handling: ✅/❌

  **Output Format**: Markdown table with color indicators
  **Language**: Korean for user-facing messages
  """

---

## 📚 Quick Reference

| Scenario | Entry Point | Key Phases | Expected Outcome |
|----------|-------------|------------|------------------|
| First-time setup | `/macos-resource-optimizer:0-init` | 1-4 (full validation) | Python engine validated, config initialized |
| Validate only | `/macos-resource-optimizer:0-init --validate-only` | 1-2 (engine + deps) | Validation report only, no config changes |
| Re-initialization | `/macos-resource-optimizer:0-init` | 3-4 (config only) | Existing config preserved, thresholds updated |
| Dependency check | `/macos-resource-optimizer:0-init --validate-only` | 1.2 (dependencies) | Dependency status report |

**Version**: 1.0.0
**Last Updated**: 2025-11-30
**Architecture**: Commands → Agents → Skills (Complete delegation)

---

## Final Step: Next Action Selection

After 초기화 completes, use AskUserQuestion tool to guide user to next action:

```python
AskUserQuestion({
    "questions": [{
        "question": "초기화가 완료되었습니다. 다음 작업을 선택해주세요.",
        "header": "다음 단계",
        "multiSelect": false,
        "options": [
            {
                "label": "시스템 분석 시작",
                "description": "/macos-resource-optimizer:1-analyze를 실행하여 6개 카테고리 분석을 시작합니다"
            },
            {
                "label": "설정 파일 확인",
                "description": ".claude/skills/macos-resource-optimizer/.data/config.json 설정을 검토합니다"
            },
            {
                "label": "문서 확인",
                "description": "SPEC-MACOS-OPTIMIZER-001 문서를 확인합니다"
            }
        ]
    }]
})
```

**Important**:
- Use conversation language from config (Korean)
- No emojis in any AskUserQuestion fields
- Always provide clear next step options

---

## ⚡️ EXECUTION DIRECTIVE

**You must NOW execute the command following the "Validate Before Execute" philosophy described above.**

1. Parse $ARGUMENTS for --validate-only flag
2. Call the `Task` tool with `subagent_type="manager-resource-coordinator"`.
3. Execute all 4 phases sequentially (validation → testing → configuration → reporting)
4. Present validation report to user
5. Use AskUserQuestion to guide next action
6. Do NOT just describe what you will do. DO IT.
