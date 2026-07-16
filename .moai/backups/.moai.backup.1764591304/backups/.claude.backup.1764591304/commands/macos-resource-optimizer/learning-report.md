# macOS Resource Optimizer - Self-Learning System Report

**Purpose**: View self-learning system insights, learned patterns, and optimization history

**Status**: ✅ Active
**Version**: 1.0.0 (claude-flow Pattern)
**Last Updated**: 2025-12-01

---

## Overview

This command displays insights from the self-learning optimization engine, inspired by claude-flow's reflexion memory and auto-consolidation patterns.

**Learning Mechanisms**:
- **Reflexion Memory**: Learn from past optimization results
- **Pattern Recognition**: Identify recurring resource issues
- **Auto-Consolidation**: Build app-specific optimization profiles
- **Adaptive Thresholds**: Learn optimal settings per app
- **Success Metrics**: Track what works best

---

## Usage

```bash
# View comprehensive learning report
/macos-resource-optimizer:learning-report

# View learned patterns only
/macos-resource-optimizer:learning-report --patterns

# View app profiles only
/macos-resource-optimizer:learning-report --profiles

# View adaptive thresholds
/macos-resource-optimizer:learning-report --thresholds
```

---

## Report Sections

### 1. Overview Statistics

**Example Output**:
```
📊 자기 학습 시스템 리포트
════════════════════════════════════════════════════════════

📈 전체 통계:
  • 총 최적화 실행: 15회
  • 성공률: 93.3%
  • 평균 개선율: 38.5%
  • 학습 상태: ✅ 활성화 (충분한 데이터)

🎯 권장사항:
  충분한 학습 데이터, 적응형 최적화 활성화
```

### 2. Top Optimized Apps

**Shows most frequently optimized apps**:
```
🔝 가장 많이 최적화된 앱:
  1. Dia Browser (8회) - 평균 개선: 2.8 GB
  2. VS Code (5회) - 평균 개선: 2.1 GB
  3. Slack (3회) - 평균 개선: 800 MB
  4. Chrome (2회) - 평균 개선: 1.5 GB
```

### 3. Learned Patterns

**Recurring issues identified by AI**:
```
🧠 학습된 패턴 (3개, 고신뢰도 2개):

Pattern: recurring_memory_dia_browser
  • 타입: 반복 이슈
  • 설명: Dia Browser repeatedly consumes high memory
  • 발생 빈도: 8회
  • 성공률: 95.0%
  • 평균 개선: 42.5%
  • 권장 조치: Restart Dia Browser when memory usage exceeds learned threshold
  • 신뢰도: ⭐⭐⭐⭐ (0.80)

Pattern: recurring_memory_vs_code
  • 타입: 반복 이슈
  • 설명: VS Code repeatedly consumes high memory
  • 발생 빈도: 5회
  • 성공률: 100.0%
  • 평균 개선: 35.2%
  • 권장 조치: Restart VS Code when memory usage exceeds learned threshold
  • 신뢰도: ⭐⭐⭐ (0.50)
```

### 4. App-Specific Profiles

**Auto-consolidated app optimization profiles**:
```
📊 앱별 프로필 (4개 앱):

Dia Browser:
  • 평균 메모리 사용: 4,000 MB (4.0 GB)
  • 재시작 시 평균 복구: 2,800 MB (2.8 GB)
  • 평균 재시작 시간: 8.5초
  • 재시작 성공률: 95.0%
  • 일반 헬퍼 수: 50개
  • 최적화 횟수: 8회
  • 마지막 최적화: 2025-12-01 14:23:45
  • 권장 임계값: 3,200 MB (학습됨)
  • 분류: 🔴 고메모리 앱

VS Code:
  • 평균 메모리 사용: 3,100 MB (3.1 GB)
  • 재시작 시 평균 복구: 2,100 MB (2.1 GB)
  • 평균 재시작 시간: 6.2초
  • 재시작 성공률: 100.0%
  • 최적화 횟수: 5회
  • 권장 임계값: 2,480 MB (학습됨)
  • 분류: 🔴 고메모리 앱
```

### 5. Adaptive Thresholds

**Learned optimal thresholds per app**:
```
📏 적응형 임계값 (학습됨):

Dia Browser: 3,200 MB (기본값: 500 MB)
  └─ 이유: 평균 4,000 MB 사용, 고메모리 앱

VS Code: 2,480 MB (기본값: 500 MB)
  └─ 이유: 평균 3,100 MB 사용, 고메모리 앱

Slack: 500 MB (기본값)
  └─ 이유: 평균 600 MB 사용, 일반 앱

Chrome: 1,200 MB (기본값: 500 MB)
  └─ 이유: 평균 1,500 MB 사용, 고메모리 앱
```

### 6. Learning Recommendations

**AI-powered next steps**:
```
💡 AI 권장사항:

✅ 현재 학습 수준: 활성화 (15회 실행)
✅ 적응형 최적화: 사용 가능
✅ 고신뢰도 패턴: 2개 발견

다음 단계:
  1. 적응형 임계값으로 자동 최적화 활성화
  2. monitor 명령어에 학습된 임계값 적용
  3. 10회 추가 실행 시 고도 학습 모드 진입
```

---

## Execution Flow

### Phase 1: Load Learning Data (1 second)

```bash
# Load optimization history
uv run scripts/learning_engine.py --report
```

### Phase 2: Generate Insights (1-2 seconds)

**Data processing**:
- Calculate statistics from history
- Identify high-confidence patterns
- Generate app profiles
- Compute adaptive thresholds

### Phase 3: Format Report (1 second)

**Output generation**:
- Summary statistics
- Top apps ranking
- Pattern descriptions
- Profile details
- Threshold recommendations

---

## Data Storage

**Learning Database Locations**:
```
.moai/memory/
├── optimization-history.json    # All optimization records
├── learned-patterns.json         # Identified patterns
└── app-profiles.json             # App-specific profiles
```

**Data Retention**:
- History: 30 days by default
- Patterns: Permanent (confidence-based)
- Profiles: Permanent (continuously updated)

**Cleanup**:
```bash
# Clear records older than 30 days
uv run scripts/learning_engine.py --clear-old 30
```

---

## Learning Progress Levels

**Level 1: Initial Learning** (0-4 executions)
- Status: 학습 데이터 수집 중
- Capabilities: Basic history recording
- Recommendation: Continue using optimizer

**Level 2: Pattern Formation** (5-9 executions)
- Status: 패턴 학습 중
- Capabilities: Pattern recognition starting
- Recommendation: Review patterns forming

**Level 3: Active Learning** (10-19 executions)
- Status: 적응형 최적화 활성화
- Capabilities: Adaptive thresholds, AI recommendations
- Recommendation: Enable adaptive optimization

**Level 4: Advanced Learning** (20+ executions)
- Status: 고도 학습 완료
- Capabilities: Full AI-powered auto-optimization
- Recommendation: Enable full auto-optimization

---

## Integration

**Works with**:
- `/macos-resource-optimizer:quick-optimize` - Records results automatically
- `/macos-resource-optimizer:full-optimize` - Records multi-category results
- `/macos-resource-optimizer:monitor` - Uses learned thresholds

**Data Flow**:
```
Optimization Execution
    ↓
Record Results (learning_engine.py --record)
    ↓
Pattern Recognition (automatic)
    ↓
Profile Updates (automatic)
    ↓
Learning Report (this command)
    ↓
AI Recommendations
```

---

## Example Session

**User runs optimization**:
```bash
/macos-resource-optimizer:quick-optimize
# Result: Memory 82.6% → 40.1%
# Automatically records to learning system
```

**User views learning insights**:
```bash
/macos-resource-optimizer:learning-report

📊 자기 학습 시스템 리포트
════════════════════════════════════════════════════════════

📈 전체 통계:
  • 총 최적화 실행: 1회
  • 성공률: 100.0%
  • 평균 개선율: 42.5%
  • 학습 상태: 🟡 초기 학습 중 (더 많은 데이터 필요)

🎯 권장사항:
  더 많은 데이터 수집 필요 (5회 미만)
  4회 추가 실행 시 패턴 인식 시작
```

**After 10 optimizations**:
```bash
/macos-resource-optimizer:learning-report

📊 자기 학습 시스템 리포트
════════════════════════════════════════════════════════════

📈 전체 통계:
  • 총 최적화 실행: 10회
  • 성공률: 95.0%
  • 평균 개선율: 38.5%
  • 학습 상태: ✅ 적응형 최적화 활성화

🧠 학습된 패턴 (2개, 고신뢰도 1개)

📊 앱별 프로필 (3개 앱)

📏 적응형 임계값:
  Dia Browser: 3,200 MB (학습됨)
  VS Code: 2,480 MB (학습됨)

💡 AI 권장사항:
  ✅ 적응형 임계값으로 자동 최적화 활성화 가능
  ✅ monitor 명령어에 학습된 임계값 적용 권장
```

---

## Benefits

**Continuous Improvement**:
- ✅ System learns from every optimization
- ✅ Adapts to your specific usage patterns
- ✅ Improves recommendations over time
- ✅ Reduces false positives
- ✅ Optimizes thresholds per app

**Token Efficiency**:
- Learning data stored locally (not in prompts)
- Only queries when needed
- TOON format + Learning = 75-85% token reduction

**AI-Powered Insights**:
- Identifies recurring issues
- Predicts optimization success
- Recommends optimal thresholds
- Auto-consolidates successful patterns

---

## Related Commands

- `/macos-resource-optimizer:quick-optimize` - Fast memory optimization (records results)
- `/macos-resource-optimizer:full-optimize` - Comprehensive optimization (records results)
- `/macos-resource-optimizer:monitor` - Continuous monitoring (uses learned thresholds)

---

**Command Status**: ✅ Ready for Use
**Learning Status**: claude-flow Pattern (Reflexion Memory + Auto-Consolidation)
**Data Privacy**: All learning data stored locally
**Token Optimized**: TOON + Learning = 75-85% reduction

---

**Execution**: Delegate to `manager-resource-coordinator` with learning report prompt
