---
name: macos-resource-optimizer:9-feedback
description: "Submit feedback, bug reports, and improvement suggestions"
argument-hint: "[--type=bug|feature|question]"
allowed-tools:
  - Task
  - AskUserQuestion
model: haiku
skills:
  - moai-system-macos-resource-optimizer
---

## 📋 Pre-execution Context

!git status --porceltin
!git branch --show-current

## 📁 Essential Files

@.moai/config/config.json
@SPEC-MACOS-OPTIMIZER-001

# 💬 MoAI macOS Resource Optimizer: Feedback Submission





> **Architecture**: Commands → Agents → Skills. This command orchestrates ONLY through `Task()` tool.
> **Delegation Model**: Command collects user feedback via AskUserQuestion and generates structured feedback report for MoAI-ADK improvement.

## 🎯 Command Purpose

Submit feedback, bug reports, feature requests, and improvement suggestions for macOS Resource Optimizer to contribute to MoAI-ADK enhancement.

**피드백 제출**: $ARGUMENTS

This command provides structured feedback collection, categorization, and optional submission to MoAI-ADK repository via `/moai:9-feedback`.

---

## 🧠 Associated Agents & Skills

| Agent/Skill | Purpose |
|------------|---------|
| **manager-resource-coordinator** | Generate structured feedback report from user input |
| **moai-system-macos-resource-optimizer** | macOS optimizer context and component reference |

---

## 💡 Execution Philosophy: "Continuous Improvement"

`/macos-resource-optimizer:9-feedback` collects and structures user feedback:

```
User Command: /macos-resource-optimizer:9-feedback [--type=bug]
    ↓
Command (Zero Direct Tool Usage)
    ↓
PHASE 1: Feedback Type Selection
AskUserQuestion → User selects: Bug | Feature | Question | Improvement
    ↓
PHASE 2: Category Selection
AskUserQuestion → User selects component:
  - coordinator (manager-resource-coordinator)
  - strategy (manager-resource-strategy)
  - expert-cpu, expert-memory, expert-disk, etc.
  - command (:0-init, :1-analyze, :2-optimize, :3-monitor, :4-report)
  - skill (moai-system-macos-resource-optimizer)
  - general (architecture, performance, documentation)
    ↓
PHASE 3: Detailed Feedback Collection
AskUserQuestion → User provides:
  - Description
  - Steps to reproduce (if bug)
  - Expected vs actual behavior
  - Priority (low/medium/high)
    ↓
PHASE 4: Generate Feedback Report
Task(subagent_type="manager-resource-coordinator",
     prompt="Generate structured feedback report")
    ↓
Output: .moai/reports/feedback/feedback-{timestamp}.md
    ↓
PHASE 5: Optional MoAI-ADK Submission
AskUserQuestion → "Submit to MoAI-ADK?"
  IF yes: Suggest /moai:9-feedback command
```

### Key Principle: Zero Direct Tool Usage

**This command uses ONLY Task() and AskUserQuestion():**

- ❌ No Read (file operations delegated)
- ❌ No Write (report generation delegated)
- ❌ No Bash (command execution delegated)
- ✅ **Task()** for orchestration
- ✅ **AskUserQuestion()** for user interaction

---

## 🚀 PHASE 1: Feedback Type Selection

**Goal**: Identify feedback category and priority

### Step 1.1: Select Feedback Type

Prompt user to select feedback type:

Use AskUserQuestion tool (Korean language, no emojis):
```python
AskUserQuestion({
    "questions": [{
        "question": "제출하실 피드백의 유형을 선택해주세요.",
        "header": "피드백 유형",
        "multiSelect": false,
        "options": [
            {
                "label": "버그 리포트",
                "description": "오류, 크래시, 예상치 못한 동작을 보고합니다"
            },
            {
                "label": "기능 요청",
                "description": "새로운 기능이나 개선사항을 제안합니다"
            },
            {
                "label": "질문",
                "description": "사용법이나 동작 원리에 대해 질문합니다"
            },
            {
                "label": "개선 제안",
                "description": "성능, UX, 문서 등의 개선사항을 제안합니다"
            }
        ]
    }]
})
```

**Type Mapping**:
- "버그 리포트" → type: bug, priority: high (default)
- "기능 요청" → type: feature, priority: medium (default)
- "질문" → type: question, priority: low (default)
- "개선 제안" → type: improvement, priority: medium (default)

---

## 🚀 PHASE 2: Component Selection

**Goal**: Identify specific component related to feedback

### Step 2.1: Select Component Category

Prompt user to select affected component:

Use AskUserQuestion tool:
```python
AskUserQuestion({
    "questions": [{
        "question": "피드백과 관련된 컴포넌트를 선택해주세요.",
        "header": "관련 컴포넌트",
        "multiSelect": true,
        "options": [
            {
                "label": "manager-resource-coordinator",
                "description": "전체 조정 및 병렬 실행 오케스트레이션"
            },
            {
                "label": "manager-resource-strategy",
                "description": "최적화 전략 생성 및 우선순위 계산"
            },
            {
                "label": "expert-cpu-optimizer",
                "description": "CPU 분석 및 최적화"
            },
            {
                "label": "expert-memory-optimizer",
                "description": "메모리 분석 및 최적화"
            },
            {
                "label": "expert-disk-optimizer",
                "description": "디스크 I/O 및 저장공간 최적화"
            },
            {
                "label": "expert-network-optimizer",
                "description": "네트워크 대역폭 및 연결 최적화"
            },
            {
                "label": "expert-battery-optimizer",
                "description": "배터리 건강 및 전력 관리"
            },
            {
                "label": "expert-thermal-optimizer",
                "description": "온도 모니터링 및 열 관리"
            },
            {
                "label": "command-0-init",
                "description": "초기화 및 검증 커맨드"
            },
            {
                "label": "command-1-analyze",
                "description": "시스템 분석 커맨드"
            },
            {
                "label": "command-2-optimize",
                "description": "최적화 실행 커맨드"
            },
            {
                "label": "command-3-monitor",
                "description": "지속적 모니터링 커맨드"
            },
            {
                "label": "command-4-report",
                "description": "리포트 생성 커맨드"
            },
            {
                "label": "skill-macos-optimizer",
                "description": "moai-system-macos-resource-optimizer 스킬"
            },
            {
                "label": "general",
                "description": "전체 아키텍처, 성능, 문서 등"
            }
        ]
    }]
})
```

---

## 🚀 PHASE 3: Detailed Feedback Collection

**Goal**: Collect comprehensive feedback details

### Step 3.1: Collect Feedback Details

Prompt user for detailed feedback information:

**For Bug Reports** (if type == bug):
```python
AskUserQuestion({
    "questions": [
        {
            "question": "버그에 대한 상세 설명을 입력해주세요.",
            "header": "버그 설명",
            "multiSelect": false,
            "options": [
                {"label": "직접 입력", "description": "상세한 버그 설명을 입력합니다"}
            ]
        },
        {
            "question": "버그 재현 단계를 선택하거나 입력해주세요.",
            "header": "재현 단계",
            "multiSelect": false,
            "options": [
                {"label": "커맨드 실행 시 발생", "description": "특정 커맨드 실행 중 발생"},
                {"label": "특정 옵션 사용 시", "description": "특정 파라미터 조합에서 발생"},
                {"label": "모니터링 중 발생", "description": "지속적 모니터링 중 발생"},
                {"label": "직접 입력", "description": "재현 단계를 상세히 입력합니다"}
            ]
        },
        {
            "question": "예상 동작과 실제 동작을 설명해주세요.",
            "header": "예상 vs 실제",
            "multiSelect": false,
            "options": [
                {"label": "직접 입력", "description": "예상 동작과 실제 동작을 입력합니다"}
            ]
        },
        {
            "question": "버그의 우선순위를 선택해주세요.",
            "header": "우선순위",
            "multiSelect": false,
            "options": [
                {"label": "높음 (Critical)", "description": "시스템 크래시, 데이터 손실, 보안 이슈"},
                {"label": "중간 (High)", "description": "주요 기능 불가, 심각한 성능 저하"},
                {"label": "낮음 (Medium)", "description": "사소한 기능 오류, UX 문제"}
            ]
        }
    ]
})
```

**For Feature Requests** (if type == feature):
```python
AskUserQuestion({
    "questions": [
        {
            "question": "요청하실 기능에 대해 설명해주세요.",
            "header": "기능 설명",
            "multiSelect": false,
            "options": [
                {"label": "직접 입력", "description": "새로운 기능에 대한 상세 설명을 입력합니다"}
            ]
        },
        {
            "question": "이 기능이 필요한 이유(use case)를 설명해주세요.",
            "header": "사용 사례",
            "multiSelect": false,
            "options": [
                {"label": "직접 입력", "description": "구체적인 사용 사례를 입력합니다"}
            ]
        },
        {
            "question": "예상되는 효과나 이점을 선택해주세요.",
            "header": "예상 효과",
            "multiSelect": true,
            "options": [
                {"label": "성능 향상", "description": "실행 속도, 리소스 사용 개선"},
                {"label": "사용성 개선", "description": "더 직관적이고 편리한 사용"},
                {"label": "정확도 향상", "description": "분석 및 최적화 정확도 개선"},
                {"label": "기능 확장", "description": "새로운 카테고리 또는 기능 추가"},
                {"label": "직접 입력", "description": "기타 예상 효과"}
            ]
        },
        {
            "question": "기능의 우선순위를 선택해주세요.",
            "header": "우선순위",
            "multiSelect": false,
            "options": [
                {"label": "높음", "description": "필수 기능, 현재 큰 불편함"},
                {"label": "중간", "description": "유용하지만 workaround 가능"},
                {"label": "낮음", "description": "있으면 좋은 기능 (nice-to-have)"}
            ]
        }
    ]
})
```

**For Questions** (if type == question):
```python
AskUserQuestion({
    "questions": [
        {
            "question": "질문 내용을 입력해주세요.",
            "header": "질문",
            "multiSelect": false,
            "options": [
                {"label": "직접 입력", "description": "구체적인 질문을 입력합니다"}
            ]
        },
        {
            "question": "질문 카테고리를 선택해주세요.",
            "header": "질문 카테고리",
            "multiSelect": false,
            "options": [
                {"label": "사용법", "description": "커맨드 사용법, 옵션 설정"},
                {"label": "동작 원리", "description": "내부 동작, 아키텍처 이해"},
                {"label": "문제 해결", "description": "에러 메시지, 트러블슈팅"},
                {"label": "성능", "description": "성능 최적화, 벤치마크"},
                {"label": "통합", "description": "다른 시스템과 통합 방법"}
            ]
        }
    ]
})
```

**For Improvements** (if type == improvement):
```python
AskUserQuestion({
    "questions": [
        {
            "question": "개선 제안 내용을 입력해주세요.",
            "header": "개선 제안",
            "multiSelect": false,
            "options": [
                {"label": "직접 입력", "description": "구체적인 개선 제안을 입력합니다"}
            ]
        },
        {
            "question": "개선 영역을 선택해주세요.",
            "header": "개선 영역",
            "multiSelect": true,
            "options": [
                {"label": "성능", "description": "실행 속도, 메모리 사용 개선"},
                {"label": "UX", "description": "사용성, 인터페이스 개선"},
                {"label": "문서", "description": "문서 명확성, 예제 추가"},
                {"label": "에러 메시지", "description": "더 명확한 에러 메시지"},
                {"label": "로깅", "description": "로그 상세도, 디버깅 정보"},
                {"label": "설정", "description": "설정 옵션, 기본값 개선"}
            ]
        },
        {
            "question": "현재 상태와 개선 후 기대 효과를 설명해주세요.",
            "header": "현재 vs 개선 후",
            "multiSelect": false,
            "options": [
                {"label": "직접 입력", "description": "현재 불편한 점과 개선 후 기대 효과를 입력합니다"}
            ]
        }
    ]
})
```

---

## 🚀 PHASE 4: Generate Feedback Report

**Goal**: Create structured feedback report from user input

### Step 4.1: Generate Structured Report

Delegate to manager-resource-coordinator for report generation:

Use Task tool:
- `subagent_type`: "manager-resource-coordinator"
- `description`: "Generate structured feedback report"
- `prompt`: """
  **Task**: Feedback Report Generation

  **Input**: User feedback from Phase 1-3

  **Report Structure** (Markdown format):

  ```markdown
  # macOS Resource Optimizer Feedback

  **Type**: {type (Bug/Feature/Question/Improvement)}
  **Priority**: {priority (Low/Medium/High)}
  **Submitted**: {timestamp}
  **Component(s)**: {components from Phase 2}

  ---

  ## Description

  {user_description}

  ---

  ## Details

  {type-specific details:
    - Bug: Steps to reproduce, Expected vs Actual
    - Feature: Use case, Expected benefits
    - Question: Category, Specific question
    - Improvement: Area, Current vs Improved
  }

  ---

  ## Priority Justification

  {why this priority level}

  ---

  ## System Context

  - macOS Version: {detect via subprocess}
  - Python Version: {detect}
  - Optimizer Version: 1.0.0 (from SPEC)
  - Last Analysis: {from MetricsCache if available}
  - Last Optimization: {from logs if available}

  ---

  ## Component Details

  {for each selected component:
    - Component: {name}
    - Purpose: {brief description}
    - Related files: {agent/command/skill file paths}
  }

  ---

  ## Suggested Next Steps

  {based on type:
    - Bug: Investigation, Reproduction, Fix
    - Feature: Design, Implementation, Testing
    - Question: Documentation, Clarification
    - Improvement: Analysis, Proposal, Implementation
  }

  ---

  ## Submission Info

  This feedback can be submitted to MoAI-ADK via:
  `/moai:9-feedback "macOS Optimizer - {type}: {brief_description}"`

  **Generated by**: /macos-resource-optimizer:9-feedback
  **Report ID**: feedback-{timestamp}
  ```

  **Save Location**: .moai/reports/feedback/feedback-{timestamp}.md

  **Language**: Korean for user-facing sections, English for technical details
  """

---

## 🚀 PHASE 5: Optional MoAI-ADK Submission

**Goal**: Offer to submit feedback to MoAI-ADK repository

### Step 5.1: Ask for MoAI-ADK Submission

Prompt user to submit to MoAI-ADK:

Use AskUserQuestion tool:
```python
AskUserQuestion({
    "questions": [{
        "question": "피드백 리포트가 생성되었습니다. MoAI-ADK 저장소에 제출하시겠습니까?",
        "header": "MoAI-ADK 제출",
        "multiSelect": false,
        "options": [
            {
                "label": "MoAI-ADK에 제출",
                "description": "/moai:9-feedback를 실행하여 공식 저장소에 제출합니다"
            },
            {
                "label": "로컬에만 저장",
                "description": ".moai/reports/feedback/에 저장하고 나중에 제출합니다"
            },
            {
                "label": "리포트 확인",
                "description": "생성된 리포트를 먼저 확인합니다"
            }
        ]
    }]
})
```

**Response Handling**:
- "MoAI-ADK에 제출" → Suggest command:
  ```
  다음 커맨드를 실행하여 제출해주세요:
  /moai:9-feedback "macOS Optimizer - {type}: {brief_description}"

  리포트 파일: {file_path}
  ```

- "로컬에만 저장" → Inform:
  ```
  피드백이 저장되었습니다: {file_path}
  나중에 /moai:9-feedback를 통해 제출할 수 있습니다.
  ```

- "리포트 확인" → Display file path:
  ```
  리포트 위치: {file_path}
  파일을 확인 후 다시 /macos-resource-optimizer:9-feedback를 실행하여 제출할 수 있습니다.
  ```

---

## 📚 Quick Reference

| Scenario | Entry Point | Key Phases | Expected Outcome |
|----------|-------------|------------|------------------|
| Bug report | `/macos-resource-optimizer:9-feedback --type=bug` | 1-5 (type → component → details → report → submit) | Structured bug report in .moai/reports/feedback/ |
| Feature request | `/macos-resource-optimizer:9-feedback --type=feature` | 1-5 (feature details collection) | Feature request report with use cases |
| General feedback | `/macos-resource-optimizer:9-feedback` | 1-5 (interactive selection) | General feedback report |
| Quick question | `/macos-resource-optimizer:9-feedback --type=question` | 1-5 (question collection) | Question report with context |

**Version**: 1.0.0
**Last Updated**: 2025-11-30
**Architecture**: Commands → Agents → Skills (Complete delegation)

---

## Final Step: Next Action Selection

After 피드백 제출 completes, use AskUserQuestion tool to guide user to next action:

```python
AskUserQuestion({
    "questions": [{
        "question": "피드백이 저장되었습니다. 다음 작업을 선택해주세요.",
        "header": "다음 단계",
        "multiSelect": false,
        "options": [
            {
                "label": "시스템 계속 사용",
                "description": "분석, 최적화 등 다른 커맨드를 실행합니다"
            },
            {
                "label": "추가 피드백 제출",
                "description": "다른 피드백을 추가로 제출합니다"
            },
            {
                "label": "피드백 리포트 확인",
                "description": "생성된 피드백 리포트를 확인합니다 ({file_path})"
            },
            {
                "label": "완료",
                "description": "피드백 제출을 완료하고 종료합니다"
            }
        ]
    }]
})
```

**Important**:
- Use conversation language from config (Korean)
- No emojis in any AskUserQuestion fields
- Always provide clear next step options
- Thank user for contributing to improvement

---

## ⚡️ EXECUTION DIRECTIVE

**You must NOW execute the command following the "Continuous Improvement" philosophy described above.**

1. Parse $ARGUMENTS for --type option (pre-select feedback type if provided)
2. Use AskUserQuestion to collect feedback type (Phase 1)
3. Use AskUserQuestion to select affected components (Phase 2)
4. Use AskUserQuestion to collect detailed feedback based on type (Phase 3)
5. Call Task with `subagent_type="manager-resource-coordinator"` to generate report (Phase 4)
6. Use AskUserQuestion to offer MoAI-ADK submission (Phase 5)
7. Present feedback report location and next steps
8. Use AskUserQuestion to guide user to next action
9. Do NOT just describe what you will do. DO IT.
