---
name: macos-resource-optimizer:3-monitor
description: "Continuous monitoring with periodic analysis and alerts"
argument-hint: "[--interval=60] [--alert-threshold=80] [--auto-optimize=false]"
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

# 📡 MoAI macOS Resource Optimizer: Continuous Monitoring


### Continuous Monitoring

```python
# Monitor for 60 seconds with 5-second intervals
result = Bash("uv run .claude/skills/macos-resource-optimizer/scripts/monitor.py --duration 60 --interval 5 --json")
data = json.loads(result.stdout)

# Access monitoring history
samples = data["samples"]
```


> **Architecture**: Commands → Agents → Skills. This command orchestrates ONLY through `Task()` tool.
> **Delegation Model**: Command delegates to manager-resource-coordinator for periodic analysis with alert threshold monitoring and optional auto-optimization.

## 🎯 Command Purpose

Continuous monitoring mode with periodic resource analysis, threshold-based alerts, and optional automatic optimization for proactive system management.

**모니터링 설정**: $ARGUMENTS

This command provides real-time resource monitoring with configurable intervals, alert thresholds, and automatic optimization capabilities.

---

## 🧠 Associated Agents & Skills

| Agent/Skill | Purpose |
|------------|---------|
| **manager-resource-coordinator** | Orchestrates periodic analysis loop with alert detection |
| **manager-resource-strategy** | Generates auto-optimization recommendations when thresholds exceeded |
| **expert-cpu-optimizer** | CPU monitoring and threshold detection |
| **expert-memory-optimizer** | Memory pressure monitoring and alerts |
| **expert-disk-optimizer** | Disk I/O monitoring and space alerts |
| **expert-network-optimizer** | Network bandwidth monitoring and latency alerts |
| **expert-battery-optimizer** | Battery level monitoring and power alerts |
| **expert-thermal-optimizer** | Temperature monitoring and thermal throttling alerts |
| **moai-system-macos-resource-optimizer** | macOS monitoring patterns and alert standards |

---

## 💡 Execution Philosophy: "Monitor and Alert"

`/macos-resource-optimizer:3-monitor` performs continuous monitoring through periodic delegation:

```
User Command: /macos-resource-optimizer:3-monitor --interval=60 --alert-threshold=80
    ↓
Command (Zero Direct Tool Usage)
    ↓
LOOP: While monitoring_active
  ↓
  Task(subagent_type="manager-resource-coordinator",
       description="Execute periodic analysis iteration",
       prompt="Analyze all 6 categories, check thresholds")
    ↓
  manager-resource-coordinator → Python subprocess:
    .claude/skills/macos-resource-optimizer/scripts/monitor.py analyze --categories all --no-cache
      ↓
    Results → Check against thresholds:
      - CPU > 80%
      - Memory > 85%
      - Disk > 90%
      - Network latency > 100ms
      - Battery < 20%
      - Thermal > 85°C
    ↓
  IF threshold_exceeded:
    AskUserQuestion("CPU 사용률이 85%입니다. 최적화하시겠습니까?")
      ↓
    IF user_approves OR auto_optimize_enabled:
      Task(subagent_type="manager-resource-strategy",
           prompt="Generate quick optimization for {category}")
        ↓
      Execute optimization
    ELSE:
      Log alert, continue monitoring
    ↓
  Sleep {interval} seconds
  ↓
UNTIL: User requests stop OR critical_threshold_reached
```

### Key Principle: Zero Direct Tool Usage

**This command uses ONLY Task(), AskUserQuestion(), and TodoWrite():**

- ❌ No Read (file operations delegated)
- ❌ No Write (logging delegated to manager-resource-coordinator)
- ❌ No Bash (subprocess execution delegated)
- ❌ No sleep/timing (handled by Python subprocess)
- ✅ **Task()** for orchestration
- ✅ **AskUserQuestion()** for alert confirmation
- ✅ **TodoWrite()** for monitoring status

---

## 🚀 PHASE 1: Monitoring Configuration

**Goal**: Parse monitoring parameters and initialize monitoring session

### Step 1.1: Parse Monitoring Parameters

Extract and validate monitoring configuration from $ARGUMENTS:

Use TodoWrite tool to track monitoring session:
```python
TodoWrite({
    "todos": [
        {"content": "Parse monitoring parameters", "status": "in_progress", "activeForm": "Parsing monitoring parameters"},
        {"content": "Initialize monitoring session", "status": "pending", "activeForm": "Initializing monitoring session"},
        {"content": "Execute monitoring loop", "status": "pending", "activeForm": "Executing monitoring loop"},
        {"content": "Handle alerts and optimization", "status": "pending", "activeForm": "Handling alerts"}
    ]
})
```

**Parameter Parsing**:
- `--interval`: Monitoring interval in seconds (default: 60)
  - Valid range: 10-300 seconds
  - Recommended: 60 seconds for balanced monitoring
  - Example: `--interval=30` for more frequent checks

- `--alert-threshold`: Resource usage threshold for alerts (default: 80)
  - Valid range: 50-95
  - Category-specific overrides:
    - `--cpu-threshold=75`
    - `--memory-threshold=85`
    - `--disk-threshold=90`
    - `--battery-threshold=20` (inverted: alert when below)
    - `--thermal-threshold=85` (in Celsius)

- `--auto-optimize`: Enable automatic optimization (default: false)
  - `true`: Auto-execute low-risk optimizations when threshold exceeded
  - `false`: Ask user for approval before optimization
  - `--auto-optimize=true` for hands-free monitoring

**Validation Rules**:
- Interval must be >= 10 seconds (prevent excessive CPU usage)
- Thresholds must be in valid ranges
- Auto-optimize requires risk tolerance setting

If invalid parameters, use AskUserQuestion:
```python
AskUserQuestion({
    "questions": [{
        "question": "모니터링 간격을 선택해주세요.",
        "header": "모니터링 설정",
        "multiSelect": false,
        "options": [
            {"label": "30초", "description": "빈번한 체크 (높은 정확도, CPU 사용 증가)"},
            {"label": "60초", "description": "권장 설정 (균형잡힌 모니터링)"},
            {"label": "120초", "description": "낮은 빈도 (낮은 CPU 사용, 지연된 알림)"},
            {"label": "300초", "description": "최소 빈도 (배터리 절약 모드)"}
        ]
    }]
})
```

### Step 1.2: Initialize Monitoring Session

Configure monitoring session with manager-resource-coordinator:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Initialize continuous monitoring session"
- `prompt`: """
  **Task**: Monitoring Session Initialization

  **Configuration**:
  - Interval: {interval} seconds
  - Alert threshold: {threshold}%
  - Auto-optimize: {auto_optimize}
  - Categories: All 6 (CPU, Memory, Disk, Network, Battery, Thermal)

  **Session Setup**:
  1. Create monitoring session ID
  2. Initialize alert log (.moai/logs/monitoring/session-{id}.log)
  3. Set up threshold configuration:
     - CPU: {cpu_threshold}%
     - Memory: {memory_threshold}%
     - Disk: {disk_threshold}%
     - Network: latency > 100ms
     - Battery: < {battery_threshold}%
     - Thermal: > {thermal_threshold}°C

  4. Verify prerequisites:
     - Python engine accessible
     - All 6 expert agents available
     - MetricsCache initialized
     - Sufficient permissions for optimization (if auto_optimize=true)

  5. Display session info to user:
     ```
     모니터링 세션 시작
     세션 ID: {session_id}
     간격: {interval}초
     경고 임계값: {threshold}%
     자동 최적화: {auto_optimize}
     예상 종료: 사용자 요청 또는 중요 임계값 도달
     ```

  **Output Format**:
  - Session ID: session-{timestamp}
  - Configuration: {config_dict}
  - Status: Ready for monitoring loop

  **Language**: Korean for user-facing messages
  """

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Parse monitoring parameters", "status": "completed", "activeForm": "Parsing monitoring parameters"},
        {"content": "Initialize monitoring session", "status": "completed", "activeForm": "Initializing monitoring session"},
        {"content": "Execute monitoring loop", "status": "pending", "activeForm": "Executing monitoring loop"},
        {"content": "Handle alerts and optimization", "status": "pending", "activeForm": "Handling alerts"}
    ]
})
```

---

## 🚀 PHASE 2: Monitoring Loop Execution

**Goal**: Execute continuous monitoring with periodic analysis

### Step 2.1: Periodic Analysis Loop

Execute monitoring loop through manager-resource-coordinator:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Execute monitoring loop with periodic analysis"
- `prompt`: """
  **Task**: Continuous Monitoring Loop

  **Session ID**: {session_id from Phase 1}
  **Configuration**: {monitoring_config}

  **Loop Strategy**:

  **Note**: This is a conceptual workflow. The actual monitoring loop runs in the Python subprocess.
  The command delegates to manager-resource-coordinator who manages the loop internally.

  Python subprocess command:
  ```bash
  python .claude/skills/macos-resource-optimizer/.data/scripts/.claude/skills/macos-resource-optimizer/scripts/monitor.py monitor \\
    --interval {interval} \\
    --alert-threshold {threshold} \\
    --auto-optimize {auto_optimize} \\
    --session-id {session_id} \\
    --interactive true  # Enables callbacks to Claude for user approval
  ```

  **Internal Loop Logic** (handled by Python):

  WHILE monitoring_active:
    1. Execute 6-category analysis (parallel via asyncio.gather)
    2. Compare results against thresholds
    3. Detect threshold violations:
       - CPU: current > cpu_threshold
       - Memory: pressure > memory_threshold
       - Disk: I/O or usage > disk_threshold
       - Network: latency > 100ms OR bandwidth > network_threshold
       - Battery: level < battery_threshold
       - Thermal: temp > thermal_threshold

    4. For each violation:
       IF auto_optimize == true:
         - Generate quick optimization (manager-resource-strategy)
         - Execute low-risk optimization automatically
         - Log action to monitoring log
       ELSE:
         - Callback to Claude via stdout JSON:
           {
             "type": "alert",
             "category": "cpu",
             "current_value": 87,
             "threshold": 80,
             "message": "CPU 사용률이 87%입니다",
             "suggested_action": "백그라운드 프로세스 정리"
           }
         - Wait for user response (approve/dismiss)
         - If approved: Execute optimization

    5. Update monitoring dashboard:
       - Iteration count
       - Total alerts: {count}
       - Auto-optimizations: {count}
       - Current status: [category status grid]

    6. Sleep {interval} seconds

    7. Check exit conditions:
       - User requested stop (Ctrl+C or callback)
       - Critical threshold reached:
         * Thermal > 95°C
         * Battery < 5%
         * Disk > 98%
       - Maximum iterations reached (safety limit: 1000)

  LOOP_END

  **Callback Handling**:
  When Python subprocess outputs alert JSON, the command receives it and uses AskUserQuestion
  to get user approval (see Phase 3).

  **Performance**:
  - Each iteration: 1.5-2.0s analysis time
  - Sleep interval: {interval}s
  - Total iteration time: ~{interval + 2}s

  **Language**: Korean for user-facing messages
  """

**Important Implementation Note**:

The actual monitoring loop runs INSIDE the Python subprocess (.claude/skills/macos-resource-optimizer/scripts/monitor.py monitor).
The command does NOT implement a loop with multiple Task() calls.
Instead, it makes a SINGLE Task() call that delegates to manager-resource-coordinator,
who then runs the monitoring loop internally via Python subprocess.

Alerts are communicated back to the command via stdout JSON, which triggers
AskUserQuestion in Phase 3.

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Parse monitoring parameters", "status": "completed", "activeForm": "Parsing monitoring parameters"},
        {"content": "Initialize monitoring session", "status": "completed", "activeForm": "Initializing monitoring session"},
        {"content": "Execute monitoring loop", "status": "in_progress", "activeForm": "Executing monitoring loop (iteration: {count})"},
        {"content": "Handle alerts and optimization", "status": "pending", "activeForm": "Handling alerts"}
    ]
})
```

---

## 🚀 PHASE 3: Alert Handling and Optimization

**Goal**: Handle threshold violations with user approval or auto-optimization

### Step 3.1: Process Alert Callbacks

When monitoring loop detects threshold violation and auto_optimize=false, handle user approval:

Use AskUserQuestion tool (triggered by alert callback from Python subprocess):
```python
AskUserQuestion({
    "questions": [{
        "question": "{category} 사용률이 {current_value}%입니다 (임계값: {threshold}%). 최적화를 실행하시겠습니까?",
        "header": "임계값 경고",
        "multiSelect": false,
        "options": [
            {
                "label": "즉시 최적화",
                "description": "{suggested_action} (예상 시간: {estimated_time}초)"
            },
            {
                "label": "모니터링 계속",
                "description": "최적화하지 않고 모니터링을 계속합니다"
            },
            {
                "label": "모니터링 중지",
                "description": "모니터링을 종료하고 세션을 닫습니다"
            }
        ]
    }]
})
```

**User Response Handling**:
- "즉시 최적화" → Send approval to Python subprocess → Execute optimization
- "모니터링 계속" → Send dismiss to Python subprocess → Continue loop
- "모니터링 중지" → Send stop signal to Python subprocess → Exit monitoring

### Step 3.2: Execute Quick Optimization (if approved)

When user approves or auto_optimize=true, execute optimization:

**Internal Process** (handled by Python subprocess):
1. Delegate to manager-resource-strategy for quick optimization plan
2. Filter for low-risk optimizations only (monitoring mode safety)
3. Execute approved optimization
4. Verify results
5. Log to monitoring session log
6. Continue monitoring loop

**No additional Task() call needed** - optimization is handled internally by the running subprocess.

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Parse monitoring parameters", "status": "completed", "activeForm": "Parsing monitoring parameters"},
        {"content": "Initialize monitoring session", "status": "completed", "activeForm": "Initializing monitoring session"},
        {"content": "Execute monitoring loop", "status": "in_progress", "activeForm": "Executing monitoring loop (alerts: {alert_count})"},
        {"content": "Handle alerts and optimization", "status": "in_progress", "activeForm": "Handling alert for {category}"}
    ]
})
```

---

## 🚀 PHASE 4: Monitoring Session Completion

**Goal**: Gracefully terminate monitoring and generate session report

### Step 4.1: Terminate Monitoring Session

When monitoring exits (user request or critical threshold), generate session report:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Generate monitoring session completion report"
- `prompt`: """
  **Task**: Monitoring Session Completion

  **Session ID**: {session_id}

  **Termination Reason**:
  - User requested stop
  - Critical threshold reached: {critical_category} = {critical_value}
  - Maximum iterations reached (safety limit)

  **Session Report Sections**:

  **1. Session Summary** (Korean):
  ```
  모니터링 세션 종료
  세션 ID: {session_id}
  시작 시간: {start_time}
  종료 시간: {end_time}
  총 실행 시간: {duration}
  총 반복 횟수: {iteration_count}
  ```

  **2. Alert Statistics**:
  | 카테고리 | 경고 횟수 | 최대값 | 평균값 | 임계값 초과율 |
  |---------|----------|-------|--------|-------------|
  | CPU     | 15       | 92%   | 68%    | 23%         |
  | 메모리   | 8        | 88%   | 72%    | 12%         |
  | 디스크   | 2        | 85%   | 65%    | 3%          |
  | ...     | ...      | ...   | ...    | ...         |

  **3. Optimization Actions**:
  - Auto-optimizations executed: {auto_count}
  - User-approved optimizations: {user_count}
  - Dismissed alerts: {dismissed_count}
  - Success rate: {success_rate}%

  **4. System Health Trend**:
  - Overall health score: {start_score} → {end_score} ({trend})
  - Improved categories: [list]
  - Degraded categories: [list]
  - Critical incidents: {critical_count}

  **5. Recommendations**:
  Based on monitoring session results:
  - Long-term optimizations needed: [list]
  - Threshold adjustments: [list]
  - Next suggested action: /macos-resource-optimizer:4-report or :2-optimize

  **6. Session Log Location**:
  - Full log: .moai/logs/monitoring/session-{session_id}.log
  - Metrics history: .moai/cache/monitoring-history.json

  **Language**: Korean for all user-facing text
  """

Update TodoWrite:
```python
TodoWrite({
    "todos": [
        {"content": "Parse monitoring parameters", "status": "completed", "activeForm": "Parsing monitoring parameters"},
        {"content": "Initialize monitoring session", "status": "completed", "activeForm": "Initializing monitoring session"},
        {"content": "Execute monitoring loop", "status": "completed", "activeForm": "Executed {iteration_count} iterations"},
        {"content": "Handle alerts and optimization", "status": "completed", "activeForm": "Handled {alert_count} alerts"}
    ]
})
```

---

## 📚 Quick Reference

| Scenario | Entry Point | Key Phases | Expected Outcome |
|----------|-------------|------------|------------------|
| Standard monitoring | `/macos-resource-optimizer:3-monitor` | 1-4 (config → loop → alerts → report) | 60-second intervals, manual approval for optimizations |
| Frequent monitoring | `/macos-resource-optimizer:3-monitor --interval=30` | 1-4 (30s intervals) | More frequent checks, faster alert detection |
| Auto-optimization | `/macos-resource-optimizer:3-monitor --auto-optimize=true` | 1-4 (automatic low-risk optimizations) | Hands-free monitoring with automatic fixes |
| Conservative alerts | `/macos-resource-optimizer:3-monitor --alert-threshold=90` | 1-4 (only critical alerts) | Fewer alerts, only severe issues |

**Version**: 1.0.0
**Last Updated**: 2025-11-30
**Architecture**: Commands → Agents → Skills (Complete delegation)
**Performance**: 1.5-2.0s per iteration analysis time

---

## Final Step: Next Action Selection

After 모니터링 completes, use AskUserQuestion tool to guide user to next action:

```python
AskUserQuestion({
    "questions": [{
        "question": "모니터링 세션이 종료되었습니다. 다음 작업을 선택해주세요.",
        "header": "다음 단계",
        "multiSelect": false,
        "options": [
            {
                "label": "세션 리포트 생성",
                "description": "/macos-resource-optimizer:4-report를 실행하여 상세 리포트를 생성합니다"
            },
            {
                "label": "추가 최적화",
                "description": "/macos-resource-optimizer:2-optimize를 실행하여 추가 최적화를 진행합니다"
            },
            {
                "label": "재분석",
                "description": "/macos-resource-optimizer:1-analyze를 실행하여 현재 상태를 재분석합니다"
            },
            {
                "label": "모니터링 재시작",
                "description": "다른 설정으로 모니터링을 재시작합니다"
            }
        ]
    }]
})
```

**Important**:
- Use conversation language from config (Korean)
- No emojis in any AskUserQuestion fields
- Always provide clear next step options
- Include monitoring statistics in session report

---

## ⚡️ EXECUTION DIRECTIVE

**You must NOW execute the command following the "Monitor and Alert" philosophy described above.**

1. Parse $ARGUMENTS for interval, alert-threshold, and auto-optimize options
2. Validate parameters and use AskUserQuestion if invalid
3. Call Task with `subagent_type="manager-resource-coordinator"` to initialize session
4. Delegate monitoring loop to manager-resource-coordinator (single Task call, not loop)
5. Handle alert callbacks with AskUserQuestion for user approval (if auto_optimize=false)
6. Use TodoWrite to track monitoring status (iterations, alerts handled)
7. When monitoring exits, generate session completion report
8. Use AskUserQuestion to guide next action based on monitoring results
9. Do NOT just describe what you will do. DO IT.

**CRITICAL**: Do NOT implement a loop with multiple Task() calls in the command.
The monitoring loop runs INSIDE the Python subprocess via a single delegation to manager-resource-coordinator.
