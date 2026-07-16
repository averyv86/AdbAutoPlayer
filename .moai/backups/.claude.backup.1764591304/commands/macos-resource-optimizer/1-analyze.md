---
name: macos-resource-optimizer:1-analyze
description: "Analyze system resources across 6 categories in parallel"
argument-hint: "[--categories cpu,memory,disk] [--cache] [--no-cache]"
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
@.claude/skills/macos-resource-optimizer/config/wrapper-config.json
@SPEC-MACOS-OPTIMIZER-001

# 📊 MoAI macOS Resource Optimizer: System Analysis


### Full System Analysis

```python
# Execute analyze_all.py for comprehensive analysis
result = Bash("uv run .claude/skills/macos-resource-optimizer/scripts/analyze_all.py --json")
data = json.loads(result.stdout)

# Access results
overall = data["overall"]
categories = data["categories"]

for category, cat_data in categories.items():
    metrics = cat_data["metrics"]
    analysis = cat_data["analysis"]
    # Process results
```


> **Architecture**: Commands → Agents → Skills. This command orchestrates ONLY through `Task()` tool.
> **Delegation Model**: Command delegates to manager-resource-coordinator who executes 6 expert agents in parallel via asyncio.gather.

## 🎯 Command Purpose

Analyze system resources across 6 categories (CPU, Memory, Disk, Network, Battery, Thermal) in parallel for comprehensive resource assessment.

**분석 대상**: $ARGUMENTS

This command provides fast parallel analysis with 1.5-2.0s execution time through Python subprocess delegation and MetricsCache optimization.

---

## 🧠 Associated Agents & Skills

| Agent/Skill | Purpose |
|------------|---------|
| **manager-resource-coordinator** | Orchestrates parallel execution across 6 expert agents using asyncio.gather |
| **expert-cpu-optimizer** | CPU usage analysis, process identification, core allocation |
| **expert-memory-optimizer** | Memory pressure, swap usage, memory-intensive processes |
| **expert-disk-optimizer** | Disk I/O, storage usage, filesystem optimization |
| **expert-network-optimizer** | Network bandwidth, connection analysis, latency monitoring |
| **expert-battery-optimizer** | Battery health, power consumption, energy efficiency |
| **expert-thermal-optimizer** | Temperature monitoring, thermal throttling, cooling efficiency |
| **moai-system-macos-resource-optimizer** | macOS resource optimization patterns and analysis standards |

---

## 💡 Execution Philosophy: "Parallel Analysis for Speed"

`/macos-resource-optimizer:1-analyze` performs comprehensive analysis through parallel agent delegation:

```
User Command: /macos-resource-optimizer:1-analyze [--categories cpu,memory,disk] [--cache]
    ↓
Command (Zero Direct Tool Usage)
    ↓
Task(subagent_type="manager-resource-coordinator",
     description="Execute parallel 6-category resource analysis",
     prompt="Analyze: [categories], cache_enabled: true")
    ↓
manager-resource-coordinator → Bash tool delegation:
  Bash("uv run .claude/skills/macos-resource-optimizer/scripts/analyze_all.py --json")
    ↓
UV Script Execution (PEP 723):
  ├─ Auto-installs inline dependencies (psutil, pyyaml, click)
  ├─ Spawns asyncio.gather for parallel category analysis
  ├─ Executes 6 expert analyzers concurrently
  └─ Returns JSON output to stdout
    ↓
Expert Analysis (Parallel, 4-5s total):
  ├─ CPU analysis      (analyze_cpu.py)
  ├─ Memory analysis   (analyze_memory.py)
  ├─ Disk analysis     (analyze_disk.py)
  ├─ Network analysis  (analyze_network.py)
  ├─ Battery analysis  (analyze_battery.py)
  └─ Thermal analysis  (analyze_thermal.py)
    ↓
Aggregation → MetricsCache → JSON Response (4-5s total first run, 2-3s cached)
    ↓
Output: Analysis Report → User Confirmation
```

### Key Principle: Zero Direct Tool Usage

**This command uses ONLY Task(), AskUserQuestion(), and TodoWrite():**

- ❌ No Read (file operations delegated)
- ❌ No Write (file operations delegated)
- ❌ No Bash (subprocess execution delegated to manager-resource-coordinator)
- ❌ No Glob (file discovery delegated)
- ✅ **Task()** for orchestration
- ✅ **AskUserQuestion()** for user interaction
- ✅ **TodoWrite()** for progress tracking

---

## 🚀 PHASE 1: Parse Analysis Parameters

**Goal**: Extract user-specified categories and caching preferences

### Step 1.1: Parse Arguments

Extract categories and options from $ARGUMENTS:

Use TodoWrite tool to track analysis phases:
```python
TodoWrite({
    "todos": [
        {"content": "Parse user-specified categories", "status": "in_progress", "activeForm": "Parsing categories"},
        {"content": "Execute parallel analysis across 6 categories", "status": "pending", "activeForm": "Executing parallel analysis"},
        {"content": "Aggregate and cache results", "status": "pending", "activeForm": "Aggregating results"},
        {"content": "Generate user-facing report", "status": "pending", "activeForm": "Generating report"}
    ]
})
```

**Parameter Parsing**:
- `--categories`: Comma-separated list (default: all)
  - Valid: cpu, memory, disk, network, battery, thermal
  - Example: `--categories cpu,memory,disk`
- `--cache`: Enable MetricsCache (default: true)
- `--no-cache`: Disable cache, force fresh analysis

**Internal Decision**:
```python
if "--no-cache" in $ARGUMENTS:
    cache_enabled = false
elif "--cache" in $ARGUMENTS or not specified:
    cache_enabled = true

if "--categories" in $ARGUMENTS:
    categories = extract_comma_list($ARGUMENTS)
else:
    categories = ["cpu", "memory", "disk", "network", "battery", "thermal"]
```

### Step 1.2: Validate Categories

Ensure all specified categories are valid:

**Validation Rules**:
- Category names must match: cpu, memory, disk, network, battery, thermal
- At least 1 category required
- Maximum 6 categories (all)
- Invalid categories → AskUserQuestion for clarification

If invalid categories detected, use AskUserQuestion:
```python
AskUserQuestion({
    "questions": [{
        "question": "잘못된 카테고리가 지정되었습니다. 올바른 카테고리를 선택해주세요.",
        "header": "카테고리 선택",
        "multiSelect": true,
        "options": [
            {"label": "CPU", "description": "CPU 사용률 및 프로세스 분석"},
            {"label": "메모리", "description": "메모리 압력 및 스왑 사용량 분석"},
            {"label": "디스크", "description": "디스크 I/O 및 저장공간 분석"},
            {"label": "네트워크", "description": "네트워크 대역폭 및 연결 분석"},
            {"label": "배터리", "description": "배터리 건강 및 전력 소비 분석"},
            {"label": "온도", "description": "시스템 온도 및 열 관리 분석"}
        ]
    }]
})
```

---

## 🚀 PHASE 2: Execute Parallel Analysis

**Goal**: Invoke manager-resource-coordinator for parallel 6-category analysis

### Step 2.1: Delegate to Coordinator

Execute parallel analysis through manager-resource-coordinator:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Execute parallel resource analysis across 6 categories"
- `prompt`: """
  **Task**: Parallel System Resource Analysis

  **Categories to Analyze**: {categories}
  **Cache Enabled**: {cache_enabled}
  **Performance Target**: 1.5-2.0s execution time

  **Execution Strategy**:
  1. Check MetricsCache for valid cached results (TTL: 30s)
  2. For uncached categories, execute Python subprocess:
     ```bash
     python .claude/skills/macos-resource-optimizer/.data/scripts/.claude/skills/macos-resource-optimizer/scripts/analyze_all.py analyze \\
       --categories {','.join(categories)} \\
       --cache {cache_enabled} \\
       --timeout 5
     ```
  3. Python coordinator uses asyncio.gather for parallel execution:
     - expert-cpu-optimizer → CPU metrics
     - expert-memory-optimizer → Memory metrics
     - expert-disk-optimizer → Disk metrics
     - expert-network-optimizer → Network metrics
     - expert-battery-optimizer → Battery metrics
     - expert-thermal-optimizer → Thermal metrics
  4. Aggregate results into JSON response
  5. Cache results with 30s TTL

  **Expected Output Format**:
  ```json
  {
    "execution_time": 1.8,
    "categories": {
      "cpu": {
        "usage_percent": 45.2,
        "top_processes": [...],
        "recommendation_score": 75
      },
      "memory": {
        "pressure": "nominal",
        "swap_used_gb": 2.1,
        "recommendation_score": 68
      },
      ...
    },
    "cache_hit": ["cpu", "memory"],
    "cache_miss": ["disk", "network", "battery", "thermal"]
  }
  ```

  **Error Handling**:
  - Timeout (>5s): Report timeout with partial results
  - Subprocess failure: Retry once, then fail gracefully
  - Missing dependencies: Report missing packages
  - Invalid category: Skip and continue with valid categories

  **Language**: Korean for user-facing messages
  """

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Parse user-specified categories", "status": "completed", "activeForm": "Parsing categories"},
        {"content": "Execute parallel analysis across 6 categories", "status": "in_progress", "activeForm": "Executing parallel analysis"},
        {"content": "Aggregate and cache results", "status": "pending", "activeForm": "Aggregating results"},
        {"content": "Generate user-facing report", "status": "pending", "activeForm": "Generating report"}
    ]
})
```

---

## 🚀 PHASE 3: Aggregate and Cache Results

**Goal**: Process analysis results and update MetricsCache

### Step 3.1: Validate Analysis Results

Verify response completeness and data quality:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Validate and aggregate analysis results"
- `prompt`: """
  **Task**: Result Validation and Aggregation

  **Input**: Analysis JSON from Phase 2

  **Validation Checks**:
  1. Execution time < 5.0s (target: 1.5-2.0s)
  2. All requested categories present
  3. Each category has recommendation_score (0-100)
  4. No null or missing critical fields
  5. Cache hit/miss ratio logged

  **Aggregation Steps**:
  1. Calculate overall system health score (weighted average):
     - CPU: 20%
     - Memory: 25%
     - Disk: 15%
     - Network: 10%
     - Battery: 15%
     - Thermal: 15%

  2. Identify top 3 optimization priorities:
     - Lowest recommendation scores
     - Critical thresholds exceeded
     - User-specified focus areas

  3. Generate executive summary:
     - Overall health: [score]/100
     - Critical issues: [count]
     - Optimization opportunities: [count]
     - Performance: [execution_time]s

  **Cache Update**:
  - Write validated results to MetricsCache
  - Update TTL to 30s
  - Log cache statistics (hit rate, entries)

  **Language**: Korean for user-facing messages
  """

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Parse user-specified categories", "status": "completed", "activeForm": "Parsing categories"},
        {"content": "Execute parallel analysis across 6 categories", "status": "completed", "activeForm": "Executing parallel analysis"},
        {"content": "Aggregate and cache results", "status": "in_progress", "activeForm": "Aggregating results"},
        {"content": "Generate user-facing report", "status": "pending", "activeForm": "Generating report"}
    ]
})
```

---

## 🚀 PHASE 4: Generate User Report

**Goal**: Present analysis results in user-friendly format

### Step 4.1: Format Analysis Report

Create comprehensive user-facing report:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Generate user-facing analysis report"
- `prompt`: """
  **Task**: User Report Generation

  **Input**: Validated analysis results from Phase 3

  **Report Sections**:

  **1. Executive Summary** (Korean):
  ```
  시스템 건강도: [score]/100
  실행 시간: [time]s
  캐시 활용: [hit_count]/[total] 카테고리
  최적화 우선순위: [top 3]
  ```

  **2. Category Breakdown** (Table format):
  | 카테고리 | 현재 상태 | 추천 점수 | 조치 필요 |
  |---------|----------|----------|----------|
  | CPU     | 45.2%    | 75/100   | 낮음     |
  | 메모리   | 압력 보통 | 68/100   | 중간     |
  | 디스크   | I/O 높음  | 55/100   | 높음     |
  | ...     | ...      | ...      | ...      |

  **3. Top 3 Optimization Opportunities**:
  - [Priority 1]: [Category] - [Issue] - [Expected Impact]
  - [Priority 2]: [Category] - [Issue] - [Expected Impact]
  - [Priority 3]: [Category] - [Issue] - [Expected Impact]

  **4. Performance Metrics**:
  - Total execution time: [time]s
  - Cache hit rate: [percentage]%
  - Categories analyzed: [count]/6
  - Critical alerts: [count]

  **5. Next Steps Suggestion**:
  Based on analysis results, suggest next action:
  - If critical issues → Recommend /macos-resource-optimizer:2-optimize
  - If monitoring needed → Recommend /macos-resource-optimizer:3-monitor
  - If generate report → Recommend /macos-resource-optimizer:4-report

  **Language**: Korean for all user-facing text
  """

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Parse user-specified categories", "status": "completed", "activeForm": "Parsing categories"},
        {"content": "Execute parallel analysis across 6 categories", "status": "completed", "activeForm": "Executing parallel analysis"},
        {"content": "Aggregate and cache results", "status": "completed", "activeForm": "Aggregating results"},
        {"content": "Generate user-facing report", "status": "completed", "activeForm": "Generating report"}
    ]
})
```

---

## 📚 Quick Reference

| Scenario | Entry Point | Key Phases | Expected Outcome |
|----------|-------------|------------|------------------|
| Full analysis (all 6 categories) | `/macos-resource-optimizer:1-analyze` | 1-4 (parse → execute → cache → report) | Comprehensive 6-category analysis in 1.5-2.0s |
| Specific categories | `/macos-resource-optimizer:1-analyze --categories cpu,memory` | 1-4 (2 categories only) | Faster targeted analysis |
| Force fresh analysis | `/macos-resource-optimizer:1-analyze --no-cache` | 1-4 (bypass cache) | Real-time metrics without cache |
| Cached analysis | `/macos-resource-optimizer:1-analyze --cache` | 1-4 (use cache if valid) | Instant results if cache hit |

**Version**: 1.0.0
**Last Updated**: 2025-11-30
**Architecture**: Commands → Agents → Skills (Complete delegation)
**Performance**: 1.5-2.0s with cache, 2.5s without cache

---

## Final Step: Next Action Selection

After 분석 completes, use AskUserQuestion tool to guide user to next action:

```python
AskUserQuestion({
    "questions": [{
        "question": "분석이 완료되었습니다. 다음 작업을 선택해주세요.",
        "header": "다음 단계",
        "multiSelect": false,
        "options": [
            {
                "label": "최적화 실행",
                "description": "/macos-resource-optimizer:2-optimize를 실행하여 시스템 최적화를 시작합니다"
            },
            {
                "label": "모니터링 시작",
                "description": "/macos-resource-optimizer:3-monitor를 실행하여 지속적인 모니터링을 시작합니다"
            },
            {
                "label": "리포트 생성",
                "description": "/macos-resource-optimizer:4-report를 실행하여 상세 리포트를 생성합니다"
            },
            {
                "label": "재분석",
                "description": "다른 옵션으로 재분석을 실행합니다"
            }
        ]
    }]
})
```

**Important**:
- Use conversation language from config (Korean)
- No emojis in any AskUserQuestion fields
- Always provide clear next step options
- Include expected execution time in descriptions

---

## ⚡️ EXECUTION DIRECTIVE

**You must NOW execute the command following the "Parallel Analysis for Speed" philosophy described above.**

1. Parse $ARGUMENTS for categories and cache options
2. Validate categories and handle invalid inputs
3. Call the `Task` tool with `subagent_type="manager-resource-coordinator"`
4. Execute all 4 phases sequentially (parse → execute → cache → report)
5. Use TodoWrite to track progress across phases
6. Present analysis report to user with performance metrics
7. Use AskUserQuestion to guide next action based on analysis results
8. Do NOT just describe what you will do. DO IT.
