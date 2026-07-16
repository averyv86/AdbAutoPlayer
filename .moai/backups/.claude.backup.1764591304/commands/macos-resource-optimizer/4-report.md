---
name: macos-resource-optimizer:4-report
description: "Generate comprehensive optimization reports with metrics and recommendations"
argument-hint: "[--format=markdown|json|html] [--output=.moai/reports/] [--include-charts]"
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
@.claude/skills/macos-resource-optimizer/.data/config.json
@SPEC-MACOS-OPTIMIZER-001

# 📄 MoAI macOS Resource Optimizer: Report Generation


### Report Generation

```python
# Generate Markdown report
Bash("uv run .claude/skills/macos-resource-optimizer/scripts/report.py --format markdown --output report.md")

# Generate HTML report
Bash("uv run .claude/skills/macos-resource-optimizer/scripts/report.py --format html --output report.html")

# Get JSON data
result = Bash("uv run .claude/skills/macos-resource-optimizer/scripts/report.py --format json")
data = json.loads(result.stdout)
```


> **Architecture**: Commands → Agents → Skills. This command orchestrates ONLY through `Task()` tool.
> **Delegation Model**: Command delegates to manager-resource-coordinator for comprehensive report generation from analysis history and monitoring logs.

## 🎯 Command Purpose

Generate comprehensive optimization reports with metrics analysis, recommendations, performance benchmarks, and historical trends for documentation and review.

**리포트 생성**: $ARGUMENTS

This command provides multi-format report generation (Markdown, JSON, HTML) with optional charts and visualizations for thorough system optimization documentation.

---

## 🧠 Associated Agents & Skills

| Agent/Skill | Purpose |
|------------|---------|
| **manager-resource-coordinator** | Aggregate analysis history, generate comprehensive reports |
| **manager-resource-strategy** | Generate recommendations from historical trends |
| **moai-system-macos-resource-optimizer** | macOS reporting patterns and documentation standards |

---

## 💡 Execution Philosophy: "Document and Recommend"

`/macos-resource-optimizer:4-report` performs comprehensive reporting through delegation:

```
User Command: /macos-resource-optimizer:4-report --format=markdown --include-charts
    ↓
Command (Zero Direct Tool Usage)
    ↓
Task(subagent_type="manager-resource-coordinator",
     description="Generate comprehensive optimization report",
     prompt="Collect history, generate report in markdown format with charts")
    ↓
manager-resource-coordinator → Python subprocess:
  .claude/skills/macos-resource-optimizer/scripts/report.py report --format markdown --include-charts
    ↓
Data Collection:
  1. Analysis history from MetricsCache
  2. Monitoring session logs (.moai/logs/monitoring/)
  3. Optimization execution logs
  4. Before/after metrics from all optimizations
    ↓
Report Generation (6 sections):
  1. Executive Summary
  2. 6-Category Breakdown (CPU, Memory, Disk, Network, Battery, Thermal)
  3. Optimization History (executed + pending)
  4. Performance Benchmarks
  5. Historical Trends (charts/graphs if --include-charts)
  6. Recommendations (long-term improvements)
    ↓
Output: .moai/reports/macos-optimizer-{date}.{format}
    ↓
User Confirmation → Next Action
```

### Key Principle: Zero Direct Tool Usage

**This command uses ONLY Task() and AskUserQuestion():**

- ❌ No Read (file operations delegated)
- ❌ No Write (report generation delegated)
- ❌ No Bash (subprocess execution delegated)
- ❌ No Glob (log file discovery delegated)
- ✅ **Task()** for orchestration
- ✅ **AskUserQuestion()** for user interaction

---

## 🚀 PHASE 1: Report Configuration

**Goal**: Parse report parameters and validate configuration

### Step 1.1: Parse Report Parameters

Extract report format and options from $ARGUMENTS:

**Parameter Parsing**:
- `--format`: Report format (default: markdown)
  - `markdown`: Markdown format for documentation (.md)
  - `json`: JSON format for API integration (.json)
  - `html`: HTML format for browser viewing (.html)

- `--output`: Output directory (default: .moai/reports/)
  - Must be within allowed locations from config.json
  - Directory created if missing
  - Example: `--output=.moai/reports/optimizer/`

- `--include-charts`: Include visualizations (default: false for markdown/json, true for html)
  - Charts: CPU/Memory trend lines, Optimization success rates
  - Only available for markdown (ASCII charts) and html (interactive charts)
  - Not supported for json format

- `--time-range`: Historical data range (default: all)
  - `24h`: Last 24 hours
  - `7d`: Last 7 days
  - `30d`: Last 30 days
  - `all`: All available history

**Validation Rules**:
- Format must be: markdown, json, or html
- Output directory must be within allowed locations
- Charts only for markdown/html formats
- Time range must be valid

If invalid parameters, use AskUserQuestion:
```python
AskUserQuestion({
    "questions": [{
        "question": "리포트 형식을 선택해주세요.",
        "header": "리포트 설정",
        "multiSelect": false,
        "options": [
            {"label": "Markdown", "description": "문서 형식, 차트 포함 가능 (.md)"},
            {"label": "JSON", "description": "API 통합 형식, 구조화된 데이터 (.json)"},
            {"label": "HTML", "description": "브라우저 뷰, 인터랙티브 차트 (.html)"}
        ]
    }]
})
```

### Step 1.2: Validate Data Availability

Check if sufficient historical data exists for report generation:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Validate historical data availability"
- `prompt`: """
  **Task**: Data Availability Check

  **Time Range**: {time_range from $ARGUMENTS or 'all'}

  **Data Sources to Check**:
  1. MetricsCache (.moai/cache/metrics.json)
     - Analysis history entries
     - Timestamp range
     - Categories covered

  2. Monitoring Logs (.moai/logs/monitoring/)
     - Session count
     - Alert history
     - Optimization actions

  3. Optimization Logs (.moai/logs/optimizations/)
     - Executed optimizations
     - Success/failure records
     - Before/after metrics

  **Validation Criteria**:
  - At least 1 analysis result available
  - Timestamps within requested time range
  - All 6 categories have data
  - No corrupted log files

  **Output**:
  ```json
  {
    "data_available": true/false,
    "analysis_count": 15,
    "monitoring_sessions": 3,
    "optimizations": 8,
    "time_range_start": "2025-11-25T10:00:00",
    "time_range_end": "2025-11-30T15:30:00",
    "missing_categories": [],
    "warnings": []
  }
  ```

  **Error Handling**:
  - No data available → Suggest running :1-analyze first
  - Insufficient data → Warn user about limited report scope
  - Corrupted logs → Skip corrupted entries, continue with valid data

  **Language**: Korean for user-facing messages
  """

If no data available, use AskUserQuestion:
```python
AskUserQuestion({
    "questions": [{
        "question": "분석 기록이 없습니다. 먼저 시스템 분석을 실행하시겠습니까?",
        "header": "데이터 없음",
        "multiSelect": false,
        "options": [
            {"label": "분석 실행", "description": "/macos-resource-optimizer:1-analyze를 먼저 실행합니다"},
            {"label": "빈 리포트 생성", "description": "데이터 없이 템플릿 리포트를 생성합니다"},
            {"label": "취소", "description": "리포트 생성을 취소합니다"}
        ]
    }]
})
```

---

## 🚀 PHASE 2: Data Collection and Aggregation

**Goal**: Collect all historical data and aggregate metrics

### Step 2.1: Collect Historical Data

Gather all available data from logs and cache:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Collect and aggregate historical data"
- `prompt`: """
  **Task**: Historical Data Collection

  **Time Range**: {time_range}
  **Data Sources**: MetricsCache, monitoring logs, optimization logs

  **Collection Steps**:

  **1. Analysis History**:
  - Read MetricsCache entries within time range
  - Extract metrics for all 6 categories per timestamp
  - Calculate statistics:
    * Min/Max/Average for each category
    * Trend direction (improving/degrading)
    * Threshold violation frequency

  **2. Monitoring Sessions**:
  - Read monitoring session logs
  - Extract alert history:
    * Alert count per category
    * Threshold violations timeline
    * Auto-optimization actions
  - Calculate session statistics:
    * Average session duration
    * Alert frequency
    * Optimization success rate

  **3. Optimization History**:
  - Read optimization execution logs
  - Extract before/after metrics for each optimization
  - Calculate effectiveness:
    * Actual improvement vs expected
    * Success rate per category
    * Average execution time
    * Rollback frequency

  **4. Performance Benchmarks**:
  - Analysis execution times (should be 1.5-2.0s)
  - Cache hit rates
  - Optimization execution times
  - System responsiveness during operations

  **Aggregated Data Structure**:
  ```json
  {
    "summary": {
      "total_analyses": 25,
      "total_optimizations": 12,
      "total_monitoring_hours": 48,
      "overall_health_trend": "improving",
      "time_range": {"start": "...", "end": "..."}
    },
    "categories": {
      "cpu": {
        "min": 35, "max": 92, "avg": 58,
        "trend": "stable",
        "optimizations": 4,
        "improvement": "+18%"
      },
      // ... 5 more categories
    },
    "optimizations": [
      {
        "timestamp": "...",
        "category": "cpu",
        "before": 87, "after": 65,
        "improvement": "+22%",
        "success": true
      }
    ],
    "benchmarks": {
      "avg_analysis_time": 1.8,
      "cache_hit_rate": 65,
      "avg_optimization_time": 8.5
    }
  }
  ```

  **Language**: Korean for user-facing messages
  """

---

## 🚀 PHASE 3: Report Generation

**Goal**: Generate formatted report with all sections

### Step 3.1: Generate Report Content

Create comprehensive report from aggregated data:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Generate formatted optimization report"
- `prompt`: """
  **Task**: Report Generation

  **Format**: {format from $ARGUMENTS}
  **Include Charts**: {include_charts from $ARGUMENTS}
  **Aggregated Data**: {from Phase 2}

  **Report Sections** (all formats):

  **1. Executive Summary**:
  ```
  macOS Resource Optimizer - 종합 리포트
  생성 일시: {timestamp}
  분석 기간: {time_range.start} ~ {time_range.end}

  전체 시스템 건강도: {overall_health_score}/100
  총 분석 횟수: {total_analyses}
  총 최적화 횟수: {total_optimizations}
  전체 개선율: {overall_improvement}%
  ```

  **2. Category Breakdown** (6 categories):
  For each category (CPU, Memory, Disk, Network, Battery, Thermal):
  - Current Status: {latest_metrics}
  - Historical Range: Min {min} | Max {max} | Avg {avg}
  - Trend: {improving/stable/degrading}
  - Optimizations Executed: {count}
  - Total Improvement: {improvement_percentage}
  - Alert Frequency: {alerts_per_day}

  **3. Optimization History**:
  Table of all executed optimizations:
  | 일시 | 카테고리 | 최적화 작업 | 실행 전 | 실행 후 | 개선율 | 상태 |
  |-----|---------|-----------|--------|--------|-------|------|
  | ... | CPU     | 백그라운드 프로세스 정리 | 87% | 65% | +22% | 성공 |
  | ... | 메모리   | 캐시 정리 | 14.2GB | 11.8GB | +2.4GB | 성공 |

  **4. Performance Benchmarks**:
  - Analysis Performance:
    * Average execution time: {avg_analysis_time}s (target: 1.5-2.0s)
    * Cache hit rate: {cache_hit_rate}%
    * Slowest category: {slowest_category} ({time}s)

  - Optimization Performance:
    * Average execution time: {avg_optimization_time}s
    * Success rate: {success_rate}%
    * Rollback rate: {rollback_rate}%

  **5. Historical Trends** (if --include-charts):

  **Markdown Format**: ASCII art charts
  ```
  CPU Usage Trend (Last 7 Days)
  100% |                    *
   80% |        *     *    * *
   60% |    *  * * * * * *   *
   40% | *  * *
   20% |
    0% +-------------------------
       Mon  Tue  Wed  Thu  Fri  Sat  Sun
  ```

  **HTML Format**: Interactive charts using Chart.js
  - Line charts for metric trends
  - Bar charts for optimization effectiveness
  - Pie charts for alert distribution

  **JSON Format**: No charts, raw data arrays for external visualization

  **6. Recommendations**:
  Based on historical analysis, generate long-term recommendations:
  - Persistent Issues: [issues that recur frequently]
  - Optimization Opportunities: [potential improvements not yet executed]
  - Threshold Adjustments: [suggested threshold changes based on patterns]
  - Maintenance Schedule: [suggested regular optimization schedule]
  - Next Actions: [immediate recommended actions]

  **Format-Specific Rendering**:

  **Markdown (.md)**:
  - Use tables, headers, code blocks
  - ASCII charts if --include-charts
  - GitHub-flavored markdown
  - Save to: {output_dir}/macos-optimizer-{date}.md

  **JSON (.json)**:
  - Structured data with nested objects
  - No formatting, pure data
  - Schema: {provide JSON schema}
  - Save to: {output_dir}/macos-optimizer-{date}.json

  **HTML (.html)**:
  - Bootstrap CSS for styling
  - Chart.js for interactive charts
  - Responsive design
  - Print-friendly CSS
  - Save to: {output_dir}/macos-optimizer-{date}.html

  **Language**: Korean for all user-facing text
  """

---

## 🚀 PHASE 4: Report Finalization and Delivery

**Goal**: Save report and present to user

### Step 4.1: Save Report to Disk

Write generated report to output directory:

Use Task tool (continues from Step 3.1):
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Save generated report to disk"
- `prompt`: """
  **Task**: Report File Output

  **Generated Report**: {from Phase 3}
  **Output Path**: {output_dir}/macos-optimizer-{timestamp}.{format}

  **Save Steps**:
  1. Ensure output directory exists (.moai/reports/)
  2. Generate unique filename: macos-optimizer-2025-11-30-153045.{format}
  3. Write report content to file
  4. Verify file written successfully
  5. Calculate file size
  6. Generate report metadata:
     ```json
     {
       "report_id": "macos-optimizer-2025-11-30-153045",
       "format": "markdown",
       "file_path": ".moai/reports/macos-optimizer-2025-11-30-153045.md",
       "file_size_kb": 45,
       "generated_at": "2025-11-30T15:30:45",
       "time_range": {"start": "...", "end": "..."},
       "sections_included": 6,
       "charts_included": true
     }
     ```
  7. Update report index (.moai/reports/index.json) with new entry

  **Permissions**:
  - Respect document_management settings from config.json
  - Ensure file saved in allowed location
  - Apply appropriate file permissions

  **Language**: Korean for user-facing messages
  """

### Step 4.2: Present Report Summary

Display report summary to user:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Display report summary to user"
- `prompt`: """
  **Task**: Report Summary Display

  **Report Metadata**: {from Step 4.1}

  **Summary to Display** (Korean):
  ```
  리포트 생성 완료

  파일 위치: {file_path}
  파일 크기: {file_size_kb} KB
  형식: {format_full_name}

  리포트 내용:
  - 분석 기간: {time_range}
  - 총 분석 횟수: {total_analyses}
  - 총 최적화 횟수: {total_optimizations}
  - 전체 건강도: {overall_health_score}/100
  - 개선율: {overall_improvement}%

  포함된 섹션:
  1. 요약 정보
  2. 6개 카테고리 상세 분석
  3. 최적화 이력
  4. 성능 벤치마크
  5. 히스토리 트렌드 {if charts: '(차트 포함)'}
  6. 장기 개선 권장사항

  주요 발견사항:
  - {top_finding_1}
  - {top_finding_2}
  - {top_finding_3}
  ```

  **Language**: Korean
  """

---

## 📚 Quick Reference

| Scenario | Entry Point | Key Phases | Expected Outcome |
|----------|-------------|------------|------------------|
| Markdown report | `/macos-resource-optimizer:4-report` | 1-4 (config → collect → generate → save) | Comprehensive .md report in .moai/reports/ |
| JSON export | `/macos-resource-optimizer:4-report --format=json` | 1-4 (structured data export) | API-friendly .json report |
| HTML with charts | `/macos-resource-optimizer:4-report --format=html --include-charts` | 1-4 (interactive browser report) | Browser-viewable .html with charts |
| Last 24 hours | `/macos-resource-optimizer:4-report --time-range=24h` | 1-4 (recent data only) | Report covering last 24 hours |

**Version**: 1.0.0
**Last Updated**: 2025-11-30
**Architecture**: Commands → Agents → Skills (Complete delegation)

---

## Final Step: Next Action Selection

After 리포트 생성 completes, use AskUserQuestion tool to guide user to next action:

```python
AskUserQuestion({
    "questions": [{
        "question": "리포트가 생성되었습니다. 다음 작업을 선택해주세요.",
        "header": "다음 단계",
        "multiSelect": false,
        "options": [
            {
                "label": "리포트 열기",
                "description": "생성된 리포트 파일을 엽니다 ({file_path})"
            },
            {
                "label": "추가 최적화",
                "description": "/macos-resource-optimizer:2-optimize를 실행하여 권장사항을 적용합니다"
            },
            {
                "label": "시스템 재분석",
                "description": "/macos-resource-optimizer:1-analyze를 실행하여 최신 상태를 확인합니다"
            },
            {
                "label": "다른 형식으로 재생성",
                "description": "같은 데이터를 다른 형식으로 리포트를 생성합니다"
            }
        ]
    }]
})
```

**Important**:
- Use conversation language from config (Korean)
- No emojis in any AskUserQuestion fields
- Always provide clear next step options
- Include file path in options for easy access

---

## ⚡️ EXECUTION DIRECTIVE

**You must NOW execute the command following the "Document and Recommend" philosophy described above.**

1. Parse $ARGUMENTS for format, output, include-charts, and time-range options
2. Validate parameters and use AskUserQuestion if invalid
3. Call Task with `subagent_type="manager-resource-coordinator"` to check data availability
4. If no data available, offer to run :1-analyze first
5. Collect historical data from all sources (MetricsCache, logs)
6. Generate formatted report with all 6 sections
7. Save report to .moai/reports/ directory
8. Present report summary to user
9. Use AskUserQuestion to guide next action
10. Do NOT just describe what you will do. DO IT.
