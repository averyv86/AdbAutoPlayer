---
name: macos-resource-optimizer:2-optimize
description: "Execute optimizations with user approval and rollback support"
argument-hint: "[--dry-run] [--auto-approve=false] [--risk-tolerance=medium]"
allowed-tools:
  - Task
  - AskUserQuestion
  - TodoWrite
model: haiku
skills:
  - moai-system-macos-resource-optimizer
---

## 📋 Pre-execution Context

!git status --porcelain
!git branch --show-current

## 📁 Essential Files

@.moai/config/config.json
@.claude/skills/macos-resource-optimizer/.data/config.json
@SPEC-MACOS-OPTIMIZER-001

# ⚙️ MoAI macOS Resource Optimizer: Optimization Execution


### Optimization Workflow

```python
# Step 1: Dry-run (preview)
result = Bash("uv run .claude/skills/macos-resource-optimizer/scripts/optimize.py --json --dry-run")
optimizations = json.loads(result.stdout)["optimizations"]

# Step 2: Apply (with confirmation)
result = Bash("uv run .claude/skills/macos-resource-optimizer/scripts/optimize.py --json --apply")
```


> **Architecture**: Commands → Agents → Skills. This command orchestrates ONLY through `Task()` tool.
> **Delegation Model**: Command delegates to manager-resource-strategy for strategy generation, then to manager-resource-coordinator for execution with user approval.

## 🎯 Command Purpose

Execute system optimizations with user approval workflow, risk assessment, and rollback support for safe resource optimization.

**최적화 대상**: $ARGUMENTS

This command provides intelligent optimization recommendations with priority scoring, user approval workflow, and before/after metrics comparison.

---

## 🧠 Associated Agents & Skills

| Agent/Skill | Purpose |
|------------|---------|
| **manager-resource-strategy** | Analyze metrics and generate optimization strategy with priority scores (0-100) |
| **manager-resource-coordinator** | Execute approved optimizations and verify results |
| **expert-cpu-optimizer** | CPU optimization (process priority, core affinity) |
| **expert-memory-optimizer** | Memory optimization (cache clearing, swap management) |
| **expert-disk-optimizer** | Disk optimization (TRIM, cache management) |
| **expert-network-optimizer** | Network optimization (connection tuning, buffer sizing) |
| **expert-battery-optimizer** | Battery optimization (power settings, background apps) |
| **expert-thermal-optimizer** | Thermal optimization (fan control, throttling) |
| **moai-system-macos-resource-optimizer** | macOS resource optimization patterns and safety standards |

---

## 💡 Execution Philosophy: "Approve Before Execute"

`/macos-resource-optimizer:2-optimize` performs safe optimization through approval workflow:

```
User Command: /macos-resource-optimizer:2-optimize [--dry-run] [--risk-tolerance=medium]
    ↓
Command (Zero Direct Tool Usage)
    ↓
PHASE 1: Analysis (if no cached results)
Task(subagent_type="manager-resource-coordinator",
     prompt="Execute analysis for optimization planning")
    ↓
PHASE 2: Strategy Generation
Task(subagent_type="manager-resource-strategy",
     prompt="Generate optimization strategy with priority scores")
    ↓
manager-resource-strategy:
  1. Analyze current metrics
  2. Identify optimization opportunities
  3. Calculate priority scores (0-100):
     - Impact: Expected improvement
     - Risk: Low/Medium/High
     - Effort: Execution complexity
  4. Filter by risk_tolerance
    ↓
PHASE 3: User Approval (AskUserQuestion in Korean)
  Optimization recommendations with:
  - Priority score
  - Expected impact
  - Risk level
  - Rollback support
    ↓
User Selection → Approved optimizations
    ↓
PHASE 4: Execution
Task(subagent_type="manager-resource-coordinator",
     prompt="Execute approved optimizations with before/after tracking")
    ↓
Results: Before/After metrics, success rate, rollback info
```

### Key Principle: Zero Direct Tool Usage

**This command uses ONLY Task(), AskUserQuestion(), and TodoWrite():**

- ❌ No Read (file operations delegated)
- ❌ No Write (file operations delegated)
- ❌ No Bash (subprocess execution delegated)
- ❌ No Edit (configuration changes delegated)
- ✅ **Task()** for orchestration
- ✅ **AskUserQuestion()** for user approval
- ✅ **TodoWrite()** for progress tracking

---

## 🚀 PHASE 1: Current State Analysis

**Goal**: Analyze current system state to generate optimization strategy

### Step 1.1: Check for Cached Analysis

Verify if recent analysis results are available:

Use TodoWrite tool to track optimization phases:
```python
TodoWrite({
    "todos": [
        {"content": "Check cached analysis results", "status": "in_progress", "activeForm": "Checking cached analysis"},
        {"content": "Generate optimization strategy", "status": "pending", "activeForm": "Generating optimization strategy"},
        {"content": "Request user approval", "status": "pending", "activeForm": "Requesting user approval"},
        {"content": "Execute approved optimizations", "status": "pending", "activeForm": "Executing optimizations"},
        {"content": "Verify results and report", "status": "pending", "activeForm": "Verifying results"}
    ]
})
```

**Cache Decision**:
- If MetricsCache has valid data (TTL < 30s) → Use cached results
- If cache expired or missing → Execute fresh analysis

### Step 1.2: Execute Analysis (if needed)

If no valid cached analysis, delegate to :1-analyze:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Execute system analysis for optimization planning"
- `prompt`: """
  **Task**: System Analysis for Optimization

  **Purpose**: Gather current metrics to inform optimization strategy

  **Execution**:
  Execute full 6-category analysis:
  - CPU, Memory, Disk, Network, Battery, Thermal
  - Use cache if available (TTL: 30s)
  - Performance target: 1.5-2.0s

  **Output Required**:
  - Current metrics for all 6 categories
  - Recommendation scores (0-100)
  - Critical thresholds exceeded
  - Performance baselines for before/after comparison

  **Language**: Korean for user-facing messages

  Note: This is equivalent to running /macos-resource-optimizer:1-analyze
  """

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Check cached analysis results", "status": "completed", "activeForm": "Checking cached analysis"},
        {"content": "Generate optimization strategy", "status": "pending", "activeForm": "Generating optimization strategy"},
        {"content": "Request user approval", "status": "pending", "activeForm": "Requesting user approval"},
        {"content": "Execute approved optimizations", "status": "pending", "activeForm": "Executing optimizations"},
        {"content": "Verify results and report", "status": "pending", "activeForm": "Verifying results"}
    ]
})
```

---

## 🚀 PHASE 2: Optimization Strategy Generation

**Goal**: Generate prioritized optimization recommendations with risk assessment

### Step 2.1: Delegate to Strategy Manager

Generate optimization strategy based on analysis results:

Use Task tool:
- `subagent_type`: "manager-resource-strategy"
- `description`: "Generate prioritized optimization strategy with risk assessment"
- `prompt`: """
  **Task**: Optimization Strategy Generation

  **Input**: Analysis results from Phase 1

  **Risk Tolerance**: {parse from $ARGUMENTS, default: "medium"}
  - low: Only safe optimizations (no system changes)
  - medium: Balanced approach (reversible changes)
  - high: Aggressive optimization (may require restart)

  **Strategy Generation Steps**:

  1. **Identify Optimization Opportunities**:
     For each category (CPU, Memory, Disk, Network, Battery, Thermal):
     - Compare current metrics vs optimal thresholds
     - Identify specific optimization actions
     - Estimate expected improvement

  2. **Calculate Priority Scores** (0-100):
     - Impact (40%): Expected performance improvement
     - Urgency (30%): How critical the issue is
     - Safety (20%): Risk level (higher = safer)
     - Effort (10%): Execution complexity (lower = easier)

  3. **Risk Assessment**:
     - Low: No system changes, user-space only
     - Medium: System preferences, reversible
     - High: Kernel parameters, may require restart

  4. **Filter by Risk Tolerance**:
     - low: Only Low-risk optimizations
     - medium: Low + Medium risk
     - high: All optimizations

  5. **Generate Recommendations**:
     Format each recommendation as:
     ```json
     {
       "id": "opt-cpu-001",
       "category": "cpu",
       "title": "Reduce background process CPU usage",
       "description": "Limit CPU usage for non-essential background processes",
       "priority_score": 85,
       "expected_impact": "+15% CPU availability",
       "risk_level": "low",
       "rollback_supported": true,
       "estimated_time": "5s",
       "actions": [
         "Identify top 5 CPU-consuming background processes",
         "Apply nice level +10 to reduce priority",
         "Monitor for 10s to verify stability"
       ]
     }
     ```

  **Output Format**:
  - Recommendations sorted by priority_score (descending)
  - Grouped by category
  - Include risk distribution (Low: X, Medium: Y, High: Z)
  - Total expected improvement estimate

  **Language**: Korean for user-facing text
  """

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Check cached analysis results", "status": "completed", "activeForm": "Checking cached analysis"},
        {"content": "Generate optimization strategy", "status": "in_progress", "activeForm": "Generating optimization strategy"},
        {"content": "Request user approval", "status": "pending", "activeForm": "Requesting user approval"},
        {"content": "Execute approved optimizations", "status": "pending", "activeForm": "Executing optimizations"},
        {"content": "Verify results and report", "status": "pending", "activeForm": "Verifying results"}
    ]
})
```

---

## 🚀 PHASE 3: User Approval Workflow

**Goal**: Present recommendations and get user approval for execution

### Step 3.1: Present Recommendations

Display optimization recommendations and request approval:

Use AskUserQuestion tool (Korean language, no emojis):
```python
AskUserQuestion({
    "questions": [{
        "question": "다음 최적화 작업을 검토하고 실행할 항목을 선택해주세요.",
        "header": "최적화 승인",
        "multiSelect": true,
        "options": [
            # Top 4 recommendations from manager-resource-strategy
            {
                "label": "[CPU] 백그라운드 프로세스 CPU 사용 감소 (우선순위: 85)",
                "description": "예상 효과: +15% CPU 가용성, 위험도: 낮음, 롤백: 지원, 시간: 5초"
            },
            {
                "label": "[메모리] 메모리 캐시 정리 (우선순위: 78)",
                "description": "예상 효과: +1.2GB 메모리 확보, 위험도: 낮음, 롤백: 지원, 시간: 3초"
            },
            {
                "label": "[디스크] TRIM 실행 및 캐시 관리 (우선순위: 72)",
                "description": "예상 효과: +20% I/O 성능, 위험도: 중간, 롤백: 지원, 시간: 15초"
            },
            {
                "label": "[배터리] 전력 설정 최적화 (우선순위: 65)",
                "description": "예상 효과: +30분 배터리 시간, 위험도: 낮음, 롤백: 지원, 시간: 8초"
            }
        ]
    }]
})
```

**Dry-Run Mode**:
If `--dry-run` in $ARGUMENTS, skip AskUserQuestion and simulate execution with detailed preview:
```python
Use Task tool:
- subagent_type: "manager-resource-coordinator"
- description: "Dry-run optimization preview"
- prompt: "Simulate execution and show detailed preview without making changes"
```

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Check cached analysis results", "status": "completed", "activeForm": "Checking cached analysis"},
        {"content": "Generate optimization strategy", "status": "completed", "activeForm": "Generating optimization strategy"},
        {"content": "Request user approval", "status": "completed", "activeForm": "Requesting user approval"},
        {"content": "Execute approved optimizations", "status": "pending", "activeForm": "Executing optimizations"},
        {"content": "Verify results and report", "status": "pending", "activeForm": "Verifying results"}
    ]
})
```

---

## 🚀 PHASE 4: Execute Approved Optimizations

**Goal**: Execute user-approved optimizations with before/after tracking

### Step 4.1: Execute Optimizations

Delegate approved optimizations to manager-resource-coordinator:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Execute approved optimizations with before/after tracking"
- `prompt`: """
  **Task**: Execute Approved Optimizations

  **Approved Optimizations**: {user_selections from AskUserQuestion}

  **Execution Strategy**:

  1. **Pre-Execution**:
     - Capture baseline metrics (CPU, Memory, Disk, etc.)
     - Create rollback checkpoint
     - Verify prerequisites (permissions, dependencies)

  2. **Sequential Execution**:
     For each approved optimization:
     a. Log start time
     b. Execute optimization actions via Python subprocess
     c. Monitor execution (timeout: as specified)
     d. Verify success/failure
     e. Capture post-execution metrics

  3. **Rollback on Failure**:
     If any optimization fails:
     - Stop execution
     - Rollback completed changes
     - Report failure details
     - Ask user to continue or abort

  4. **Post-Execution**:
     - Compare before/after metrics
     - Calculate actual improvement vs expected
     - Generate success report
     - Update MetricsCache

  **Execution Format**:
  ```bash
  python .claude/skills/macos-resource-optimizer/.data/scripts/.claude/skills/macos-resource-optimizer/scripts/optimize.py optimize \\
    --optimizations {','.join(approved_ids)} \\
    --rollback-on-error true \\
    --timeout {sum(estimated_times)}
  ```

  **Output Format**:
  ```json
  {
    "total_optimizations": 4,
    "successful": 3,
    "failed": 1,
    "rollback_performed": false,
    "execution_time": 25.3,
    "before_metrics": {...},
    "after_metrics": {...},
    "improvements": {
      "cpu": {"expected": "+15%", "actual": "+12%"},
      "memory": {"expected": "+1.2GB", "actual": "+1.5GB"}
    },
    "failed_optimizations": [
      {
        "id": "opt-disk-001",
        "error": "Permission denied for TRIM operation",
        "rollback_status": "not_required"
      }
    ]
  }
  ```

  **Error Handling**:
  - Timeout: Terminate subprocess, rollback if needed
  - Permission error: Skip optimization, continue with others
  - System error: Abort execution, rollback all changes
  - Verification failure: Rollback specific optimization

  **Language**: Korean for user-facing messages
  """

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Check cached analysis results", "status": "completed", "activeForm": "Checking cached analysis"},
        {"content": "Generate optimization strategy", "status": "completed", "activeForm": "Generating optimization strategy"},
        {"content": "Request user approval", "status": "completed", "activeForm": "Requesting user approval"},
        {"content": "Execute approved optimizations", "status": "in_progress", "activeForm": "Executing optimizations"},
        {"content": "Verify results and report", "status": "pending", "activeForm": "Verifying results"}
    ]
})
```

---

## 🚀 PHASE 5: Verification and Reporting

**Goal**: Verify results and present comprehensive execution report

### Step 5.1: Generate Execution Report

Create detailed before/after comparison report:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Generate optimization execution report"
- `prompt`: """
  **Task**: Optimization Execution Report

  **Input**: Execution results from Phase 4

  **Report Sections**:

  **1. Executive Summary** (Korean):
  ```
  최적화 완료: {successful}/{total} 작업 성공
  총 실행 시간: {execution_time}초
  전체 시스템 개선: {overall_improvement}%
  롤백 수행: {rollback_performed}
  ```

  **2. Before/After Comparison**:
  | 카테고리 | 실행 전 | 실행 후 | 개선율 | 목표 달성 |
  |---------|--------|--------|-------|----------|
  | CPU     | 65.2%  | 52.1%  | +13.1% | 87% (목표: +15%) |
  | 메모리   | 12.3GB | 10.8GB | +1.5GB | 125% (목표: +1.2GB) |
  | ...     | ...    | ...    | ...    | ...      |

  **3. Optimization Details**:
  For each executed optimization:
  - ID: opt-cpu-001
  - Title: 백그라운드 프로세스 CPU 사용 감소
  - Status: 성공 / 실패
  - Execution time: 5.2초
  - Expected impact: +15% CPU
  - Actual impact: +12% CPU
  - Achievement: 80%

  **4. Failed Optimizations** (if any):
  - ID: opt-disk-001
  - Title: TRIM 실행 및 캐시 관리
  - Error: Permission denied for TRIM operation
  - Rollback: Not required
  - Suggestion: Run with sudo or adjust permissions

  **5. Recommendations**:
  - Monitor system for next 30 minutes
  - Re-analyze to verify sustained improvements
  - Consider scheduling failed optimizations with proper permissions
  - Next suggested action: /macos-resource-optimizer:3-monitor or :4-report

  **Language**: Korean for all user-facing text
  """

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Check cached analysis results", "status": "completed", "activeForm": "Checking cached analysis"},
        {"content": "Generate optimization strategy", "status": "completed", "activeForm": "Generating optimization strategy"},
        {"content": "Request user approval", "status": "completed", "activeForm": "Requesting user approval"},
        {"content": "Execute approved optimizations", "status": "completed", "activeForm": "Executing optimizations"},
        {"content": "Verify results and report", "status": "completed", "activeForm": "Verifying results"}
    ]
})
```

---

## 📚 Quick Reference

| Scenario | Entry Point | Key Phases | Expected Outcome |
|----------|-------------|------------|------------------|
| Full optimization | `/macos-resource-optimizer:2-optimize` | 1-5 (analysis → strategy → approval → execute → verify) | User-approved optimizations with before/after metrics |
| Dry-run preview | `/macos-resource-optimizer:2-optimize --dry-run` | 1-3 (analysis → strategy → preview only) | Optimization preview without execution |
| Conservative mode | `/macos-resource-optimizer:2-optimize --risk-tolerance=low` | 1-5 (only low-risk optimizations) | Safe optimizations only |
| Aggressive mode | `/macos-resource-optimizer:2-optimize --risk-tolerance=high` | 1-5 (all optimizations) | Maximum performance improvements |

**Version**: 1.0.0
**Last Updated**: 2025-11-30
**Architecture**: Commands → Agents → Skills (Complete delegation)
**Safety**: Rollback support, user approval required, risk assessment

---

## Final Step: Next Action Selection

After 최적화 completes, use AskUserQuestion tool to guide user to next action:

```python
AskUserQuestion({
    "questions": [{
        "question": "최적화가 완료되었습니다. 다음 작업을 선택해주세요.",
        "header": "다음 단계",
        "multiSelect": false,
        "options": [
            {
                "label": "시스템 재분석",
                "description": "/macos-resource-optimizer:1-analyze를 실행하여 최적화 효과를 검증합니다"
            },
            {
                "label": "모니터링 시작",
                "description": "/macos-resource-optimizer:3-monitor를 실행하여 지속적인 모니터링을 시작합니다"
            },
            {
                "label": "리포트 생성",
                "description": "/macos-resource-optimizer:4-report를 실행하여 최적화 리포트를 생성합니다"
            },
            {
                "label": "추가 최적화",
                "description": "다른 위험도 레벨로 추가 최적화를 실행합니다"
            }
        ]
    }]
})
```

**Important**:
- Use conversation language from config (Korean)
- No emojis in any AskUserQuestion fields
- Always provide clear next step options
- Include rollback information if failures occurred

---

## ⚡️ EXECUTION DIRECTIVE

**You must NOW execute the command following the "Approve Before Execute" philosophy described above.**

1. Parse $ARGUMENTS for dry-run and risk-tolerance options
2. Execute Phase 1: Check cached analysis or run fresh analysis
3. Call Task with `subagent_type="manager-resource-strategy"` for strategy generation
4. Use AskUserQuestion to request user approval (Korean, no emojis)
5. Call Task with `subagent_type="manager-resource-coordinator"` for execution
6. Use TodoWrite to track progress across all 5 phases
7. Generate comprehensive before/after report
8. Use AskUserQuestion to guide next action based on results
9. Do NOT just describe what you will do. DO IT.
