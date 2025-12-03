---
id: SPEC-MACOS-OPTIMIZER-001
version: "1.0.0"
status: "draft"
created: "2025-11-29"
updated: "2025-11-29"
author: "manager-spec"
priority: "HIGH"
---

## HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-29 | manager-spec | Initial draft - macOS Resource Optimizer MoAI Wrapper Integration |

# SPEC-MACOS-OPTIMIZER-001: macOS Resource Optimizer MoAI 래퍼 통합

## 개요

기존 macOS Resource Optimizer의 50개 Python 에이전트를 보존하면서, MoAI 생태계와의 통합을 위한 **Additive Wrapper Pattern**을 적용합니다. 8개의 래퍼 에이전트와 6개의 커맨드를 추가하여 성능을 20-40% 개선(2.5초 → 1.5-2.0초)하고, 테스트 커버리지를 73.7%에서 86% 이상으로 향상시킵니다.

---

## Environment (실행 환경 및 전제 조건)

### 시스템 환경

- **운영체제**: macOS 13.0 이상 (Ventura+)
- **Python**: 3.11-3.14 (MoAI-ADK 호환)
- **필수 패키지**:
  - `moai-adk>=0.30.2` - MoAI 프레임워크
  - `asyncio` - 비동기 실행 (표준 라이브러리)
  - `pytest>=8.3.0` - 테스트 프레임워크
  - `pytest-asyncio>=0.24.0` - 비동기 테스트
  - `psutil>=6.1.0` - 시스템 리소스 모니터링
  - `pydantic>=2.10.0` - 데이터 검증

### 프로젝트 구조

```
moai-ir-deck/
├── .claude/
│   ├── agents/
│   │   ├── manager-resource-coordinator.md    # 신규 (메인 조정)
│   │   ├── manager-resource-strategy.md       # 신규 (전략 수립)
│   │   ├── expert-cpu-optimizer.md            # 신규
│   │   ├── expert-memory-optimizer.md         # 신규
│   │   ├── expert-disk-optimizer.md           # 신규
│   │   ├── expert-network-optimizer.md        # 신규
│   │   ├── expert-battery-optimizer.md        # 신규
│   │   └── expert-thermal-optimizer.md        # 신규
│   ├── commands/
│   │   └── macos-resource-optimizer/
│   │       ├── 0-init.md                      # 신규
│   │       ├── 1-analyze.md                   # 신규
│   │       ├── 2-optimize.md                  # 신규
│   │       ├── 3-monitor.md                   # 신규
│   │       ├── 4-report.md                    # 신규
│   │       └── 9-feedback.md                  # 신규
│   └── skills/
│       └── moai-system-macos-resource-optimizer/
│           ├── SKILL.md                       # 신규
│           ├── modules/
│           │   ├── wrapper-layer.md           # 신규
│           │   ├── performance-optimization.md # 신규
│           │   └── testing-strategy.md        # 신규
│           └── examples.md                    # 신규
│
└── existing_engine/                           # 보존 (무수정)
    ├── coordinator.py
    ├── master-orchestrator.py
    └── agents/                                # 50개 Python 에이전트
```

### 기존 코드 베이스

- **기존 엔진**: 50개 Python 에이전트 (~30,622 라인)
- **현재 성능**: 2.5초 (전체 워크플로우 실행)
- **현재 테스트 커버리지**: 73.7%
- **보존 대상**: `coordinator.py`, `master-orchestrator.py`, 모든 Python 에이전트

---

## Assumptions (가정 사항)

### 기술적 가정

1. **기존 엔진 안정성**: 50개 Python 에이전트는 정상 작동하며 내부 로직 수정이 불필요하다고 가정
2. **래퍼 오버헤드**: 래퍼 레이어의 오버헤드는 병렬화로 상쇄 가능하다고 가정 (asyncio 사용)
3. **Python-MoAI 통신**: 기존 Python 코드를 subprocess 또는 API 호출로 실행 가능하다고 가정
4. **macOS 환경**: psutil 라이브러리가 macOS 시스템 메트릭에 정상 접근 가능하다고 가정

### 운영 가정

1. **사용자 환경**: 사용자는 macOS 13.0 이상에서 MoAI-ADK가 설치된 환경을 사용한다고 가정
2. **권한**: 시스템 리소스 모니터링에 필요한 권한(admin 불필요)이 부여되어 있다고 가정
3. **네트워크 독립성**: 최적화 작업은 로컬 시스템에서 실행되며 네트워크 상태와 무관하다고 가정

### 성능 가정

1. **병렬화 효과**: CPU, Memory, Disk 분석을 병렬 실행하여 30-40% 성능 향상 달성 가능하다고 가정
2. **지연 로딩**: 필요한 에이전트만 지연 로딩하여 초기화 시간 단축 가능하다고 가정
3. **캐싱**: 시스템 메트릭 캐싱으로 중복 조회를 방지하여 성능 향상 가능하다고 가정

---

## Requirements (요구사항)

### Ubiquitous Requirements (항상 활성화)

**REQ-OPT-001**: 시스템은 기존 50개 Python 에이전트를 수정 없이 보존해야 한다.
- **조건**: 기존 `coordinator.py`, `master-orchestrator.py`, `agents/` 디렉토리 무수정
- **검증**: Git diff로 기존 파일 변경 없음 확인

**REQ-OPT-002**: 시스템은 8개 래퍼 에이전트를 통해 기존 엔진과 통신해야 한다.
- **래퍼 에이전트 목록**:
  - `manager-resource-coordinator` (메인 조정)
  - `manager-resource-strategy` (전략 수립)
  - `expert-cpu-optimizer`
  - `expert-memory-optimizer`
  - `expert-disk-optimizer`
  - `expert-network-optimizer`
  - `expert-battery-optimizer`
  - `expert-thermal-optimizer`
- **출력**: 각 에이전트는 `.claude/agents/` 디렉토리에 Markdown 파일로 존재

**REQ-OPT-003**: 시스템은 전체 워크플로우 실행 시간을 2.0초 이하로 유지해야 한다.
- **현재 성능**: 2.5초
- **목표 성능**: 1.5-2.0초 (20-40% 개선)
- **측정 방법**: pytest-benchmark로 end-to-end 실행 시간 측정

**REQ-OPT-004**: 시스템은 테스트 커버리지를 86% 이상으로 유지해야 한다.
- **현재 커버리지**: 73.7%
- **목표 커버리지**: 86%+
- **검증**: `pytest --cov` 명령어로 커버리지 측정

### Event-driven Requirements (이벤트 기반)

**REQ-OPT-005**: WHEN 사용자가 `/macos-resource-optimizer:0-init` 실행 시, THEN 시스템은 프로젝트 디렉토리를 초기화하고 설정 파일을 생성해야 한다.
- **이벤트**: `/macos-resource-optimizer:0-init` 명령어 실행
- **액션**: `.moai/config/macos-optimizer.json` 생성, 에이전트 디렉토리 생성
- **출력**: 초기화 성공 메시지 + 생성된 파일 경로

**REQ-OPT-006**: WHEN 사용자가 `/macos-resource-optimizer:1-analyze` 실행 시, THEN 시스템은 CPU/Memory/Disk/Network 상태를 병렬 분석해야 한다.
- **이벤트**: `/macos-resource-optimizer:1-analyze` 명령어 실행
- **액션**:
  - `expert-cpu-optimizer`, `expert-memory-optimizer`, `expert-disk-optimizer`, `expert-network-optimizer` 병렬 실행
  - 각 에이전트는 psutil로 시스템 메트릭 수집
  - 결과를 `.moai/reports/optimization/analysis-{timestamp}.json`에 저장
- **실행 시간**: <0.5초 (병렬 실행)

**REQ-OPT-007**: WHEN 분석 완료 시, THEN 시스템은 최적화 전략을 생성하고 사용자 승인을 요청해야 한다.
- **이벤트**: 분석 완료
- **액션**:
  - `manager-resource-strategy` 에이전트가 분석 결과를 기반으로 최적화 전략 생성
  - AskUserQuestion 도구로 최적화 전략 승인 요청
  - 승인 시 `/macos-resource-optimizer:2-optimize` 자동 실행
- **출력**: 최적화 전략 요약 (Markdown 형식)

**REQ-OPT-008**: WHEN 사용자가 `/macos-resource-optimizer:2-optimize` 실행 시, THEN 시스템은 승인된 전략을 기존 Python 엔진에 전달하여 최적화를 실행해야 한다.
- **이벤트**: `/macos-resource-optimizer:2-optimize` 명령어 실행
- **액션**:
  - `manager-resource-coordinator` 에이전트가 기존 `coordinator.py` 호출
  - 최적화 작업 진행 상황을 실시간 표시
  - 완료 시 결과 보고서 생성
- **실행 시간**: <1.0초

**REQ-OPT-009**: WHEN 사용자가 `/macos-resource-optimizer:3-monitor` 실행 시, THEN 시스템은 실시간 리소스 모니터링을 시작해야 한다.
- **이벤트**: `/macos-resource-optimizer:3-monitor` 명령어 실행
- **액션**:
  - `expert-thermal-optimizer`, `expert-battery-optimizer` 에이전트가 주기적(5초) 모니터링 실행
  - 실시간 메트릭을 콘솔에 출력
  - Ctrl+C로 종료 가능
- **출력**: CPU 온도, 배터리 상태, 메모리 사용률 (Rich 라이브러리로 포맷팅)

**REQ-OPT-010**: WHEN 사용자가 `/macos-resource-optimizer:4-report` 실행 시, THEN 시스템은 최적화 결과 보고서를 생성해야 한다.
- **이벤트**: `/macos-resource-optimizer:4-report` 명령어 실행
- **액션**:
  - `.moai/reports/optimization/` 디렉토리의 분석 결과 수집
  - Markdown 형식의 보고서 생성 (before/after 비교, 성능 개선 수치)
  - 보고서를 `.moai/reports/optimization/report-{timestamp}.md`에 저장
- **출력**: 보고서 파일 경로 + 주요 개선 사항 요약

**REQ-OPT-011**: WHEN 사용자가 `/macos-resource-optimizer:9-feedback` 실행 시, THEN 시스템은 피드백 수집 폼을 표시하고 GitHub Issue로 전송해야 한다.
- **이벤트**: `/macos-resource-optimizer:9-feedback` 명령어 실행
- **액션**:
  - AskUserQuestion으로 피드백 타입 선택 (버그, 개선 제안, 기능 요청)
  - 피드백 내용 입력
  - GitHub CLI(`gh issue create`)로 이슈 생성
- **출력**: 생성된 GitHub Issue URL

### State-driven Requirements (상태 기반)

**REQ-OPT-012**: WHILE 테스트 커버리지가 86% 미만일 때, THEN 시스템은 테스트 생성을 권장해야 한다.
- **상태**: 테스트 커버리지 < 86%
- **액션**: pytest 실행 후 커버리지 경고 메시지 출력 + 미커버 모듈 리스트 표시
- **출력**: `[WARNING] Test coverage is {coverage}%. Target: 86%. Missing coverage in: {modules}`

**REQ-OPT-013**: WHILE 기존 Python 엔진 실행 중일 때, THEN 시스템은 래퍼 레이어에서 타임아웃을 관리해야 한다.
- **상태**: Python 엔진 실행 중
- **타임아웃**: 10초 (설정 가능)
- **액션**: 타임아웃 초과 시 `TimeoutError` 발생 + 에러 메시지 표시

**REQ-OPT-014**: WHILE 시스템 메트릭 캐시가 유효한 경우(30초 이내), THEN 시스템은 재조회 없이 캐시 데이터를 사용해야 한다.
- **상태**: 캐시 타임스탬프 < 30초
- **액션**: psutil 호출 대신 캐시된 데이터 반환
- **성능**: 메트릭 조회 시간 90% 감소

### Unwanted Behaviors (금지사항)

**REQ-OPT-015**: 시스템은 기존 Python 에이전트의 내부 로직을 절대 수정해서는 안 된다.
- **금지**: `coordinator.py`, `master-orchestrator.py`, `agents/` 디렉토리 파일 수정
- **검증**: Git diff로 변경 사항 확인 → 변경 감지 시 에러

**REQ-OPT-016**: 시스템은 래퍼 레이어에서 직접 시스템 최적화 작업을 실행해서는 안 된다.
- **금지**: 래퍼 에이전트가 `os.system()` 또는 `subprocess.run()`으로 시스템 명령 직접 실행
- **대응**: 모든 최적화 작업은 기존 Python 엔진(`coordinator.py`)에 위임

**REQ-OPT-017**: 시스템은 사용자 승인 없이 자동으로 최적화를 실행해서는 안 된다.
- **금지**: `/macos-resource-optimizer:1-analyze` 후 자동으로 `/macos-resource-optimizer:2-optimize` 실행
- **대응**: 반드시 AskUserQuestion으로 사용자 승인 요청 후 실행

### Optional Requirements (선택사항)

**REQ-OPT-018**: 시스템은 실행 결과를 `.moai/reports/optimization/`에 저장할 수 있다.
- **선택사항**: 모든 분석, 최적화 결과를 JSON 및 Markdown 형식으로 저장
- **현재**: 기본 활성화 (설정으로 비활성화 가능)

**REQ-OPT-019**: 시스템은 실행 로그를 `.moai/logs/macos-optimizer/`에 기록할 수 있다.
- **선택사항**: 모든 명령어 실행 로그를 타임스탬프와 함께 저장
- **현재**: 기본 비활성화 (디버그 모드에서 활성화)

**REQ-OPT-020**: 시스템은 성능 메트릭을 시각화하여 HTML 보고서를 생성할 수 있다.
- **선택사항**: Plotly 또는 Matplotlib으로 메트릭 그래프 생성
- **현재**: 추후 확장 (v2.0 목표)

---

## Specifications (기술 사양)

### 아키텍처 설계

```
┌────────────────────────────────────────────────────────────────┐
│                    사용자 인터페이스                            │
│  /macos-resource-optimizer:0-init                              │
│  /macos-resource-optimizer:1-analyze                           │
│  /macos-resource-optimizer:2-optimize                          │
│  /macos-resource-optimizer:3-monitor                           │
│  /macos-resource-optimizer:4-report                            │
│  /macos-resource-optimizer:9-feedback                          │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                  MoAI Wrapper Layer (신규)                      │
├────────────────────────────────────────────────────────────────┤
│ Manager Agents (조정 및 전략):                                  │
│ ├─ manager-resource-coordinator (메인 조정)                    │
│ └─ manager-resource-strategy (전략 수립)                       │
│                                                                 │
│ Expert Agents (도메인 전문):                                    │
│ ├─ expert-cpu-optimizer (CPU 최적화)                           │
│ ├─ expert-memory-optimizer (메모리 최적화)                     │
│ ├─ expert-disk-optimizer (디스크 최적화)                       │
│ ├─ expert-network-optimizer (네트워크 최적화)                  │
│ ├─ expert-battery-optimizer (배터리 최적화)                    │
│ └─ expert-thermal-optimizer (온도 최적화)                      │
│                                                                 │
│ Integration Skill:                                              │
│ └─ moai-system-macos-resource-optimizer                        │
│    ├─ Wrapper Layer Module (래퍼 인터페이스)                   │
│    ├─ Performance Optimization Module (성능 최적화)            │
│    └─ Testing Strategy Module (테스트 전략)                    │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼ (asyncio subprocess 호출)
┌────────────────────────────────────────────────────────────────┐
│            Existing Python Engine (보존, 무수정)                │
├────────────────────────────────────────────────────────────────┤
│ coordinator.py (메인 조정자)                                    │
│ master-orchestrator.py (오케스트레이터)                         │
│ agents/ (50개 Python 에이전트)                                 │
│ ├─ cpu_agent.py                                                │
│ ├─ memory_agent.py                                             │
│ ├─ disk_agent.py                                               │
│ └─ ... (47개 추가 에이전트)                                     │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                    macOS System APIs                            │
│  psutil (CPU, Memory, Disk, Network)                           │
│  macOS IOKit (Battery, Thermal)                                │
└────────────────────────────────────────────────────────────────┘
```

### 데이터 플로우

**분석 워크플로우** (`/macos-resource-optimizer:1-analyze`):
```
1. 사용자 명령어 실행
   ↓
2. manager-resource-coordinator 에이전트 호출
   ↓
3. 병렬 실행 (asyncio.gather):
   ├─ expert-cpu-optimizer → psutil.cpu_percent()
   ├─ expert-memory-optimizer → psutil.virtual_memory()
   ├─ expert-disk-optimizer → psutil.disk_usage()
   └─ expert-network-optimizer → psutil.net_io_counters()
   ↓
4. 결과 수집 및 병합
   ↓
5. JSON 저장 (.moai/reports/optimization/analysis-{timestamp}.json)
   ↓
6. 사용자에게 분석 결과 표시 (Rich 라이브러리 테이블)
   ↓
7. manager-resource-strategy 호출 (전략 생성)
   ↓
8. AskUserQuestion (전략 승인 요청)
```

**최적화 워크플로우** (`/macos-resource-optimizer:2-optimize`):
```
1. 사용자 승인 확인
   ↓
2. manager-resource-coordinator 에이전트 호출
   ↓
3. 기존 Python 엔진 실행 (subprocess):
   ├─ 명령어: python coordinator.py --strategy {strategy_json}
   ├─ 타임아웃: 10초
   └─ 출력: 실시간 진행 상황 스트리밍
   ↓
4. 결과 수집
   ↓
5. 보고서 생성 (.moai/reports/optimization/report-{timestamp}.md)
   ↓
6. 성능 개선 수치 계산 (before vs after)
   ↓
7. 사용자에게 결과 표시
```

### 주요 컴포넌트 명세

#### 1. manager-resource-coordinator 에이전트

**역할**: 전체 최적화 워크플로우 조정 및 기존 Python 엔진 호출

**주요 기능**:
- 병렬 분석 실행 조정 (asyncio.gather)
- 기존 Python 엔진 호출 (`coordinator.py`)
- 타임아웃 관리 및 에러 핸들링
- 실행 결과 보고서 생성

**구현 예시**:
```python
# .claude/agents/manager-resource-coordinator.md
async def coordinate_analysis():
    """병렬 분석 실행 조정"""
    tasks = [
        Task(subagent_type="expert-cpu-optimizer", prompt="Analyze CPU"),
        Task(subagent_type="expert-memory-optimizer", prompt="Analyze Memory"),
        Task(subagent_type="expert-disk-optimizer", prompt="Analyze Disk"),
        Task(subagent_type="expert-network-optimizer", prompt="Analyze Network")
    ]
    results = await asyncio.gather(*tasks)
    return merge_results(results)

async def execute_optimization(strategy: dict):
    """기존 Python 엔진 호출"""
    cmd = ["python", "coordinator.py", "--strategy", json.dumps(strategy)]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        timeout=10
    )
    stdout, stderr = await proc.communicate()
    return parse_output(stdout)
```

**예상 라인 수**: ~200 lines

#### 2. manager-resource-strategy 에이전트

**역할**: 분석 결과를 기반으로 최적화 전략 생성

**주요 기능**:
- 시스템 메트릭 분석 (CPU, Memory, Disk, Network)
- 최적화 우선순위 결정 (긴급도, 영향도)
- 최적화 전략 JSON 생성
- 사용자 승인 요청 (AskUserQuestion)

**전략 JSON 구조**:
```json
{
  "strategy_id": "strat-001",
  "timestamp": "2025-11-29T10:30:00Z",
  "priority": "HIGH",
  "optimizations": [
    {
      "target": "CPU",
      "action": "reduce_background_processes",
      "urgency": "high",
      "impact": "medium"
    },
    {
      "target": "Memory",
      "action": "clear_cache",
      "urgency": "medium",
      "impact": "high"
    }
  ],
  "estimated_improvement": "20-30%"
}
```

**예상 라인 수**: ~180 lines

#### 3. expert-cpu-optimizer 에이전트

**역할**: CPU 상태 분석 및 최적화 권장

**주요 기능**:
- CPU 사용률 측정 (`psutil.cpu_percent()`)
- 프로세스별 CPU 사용량 분석 (`psutil.Process.cpu_percent()`)
- 고사용 프로세스 식별
- 최적화 권장사항 생성

**메트릭 수집**:
```python
import psutil

def analyze_cpu():
    """CPU 상태 분석"""
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()

    # 고사용 프로세스 식별 (상위 5개)
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        processes.append(proc.info)
    top_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:5]

    return {
        "cpu_percent": cpu_percent,
        "cpu_count": cpu_count,
        "cpu_freq_mhz": cpu_freq.current,
        "top_processes": top_processes
    }
```

**예상 라인 수**: ~120 lines (유사 에이전트: memory, disk, network)

#### 4. moai-system-macos-resource-optimizer 스킬

**역할**: 래퍼 레이어 공통 로직 및 유틸리티 제공

**모듈 구성**:
- `SKILL.md`: 스킬 개요 및 사용법
- `modules/wrapper-layer.md`: 래퍼 인터페이스 패턴
- `modules/performance-optimization.md`: 병렬화 및 캐싱 전략
- `modules/testing-strategy.md`: 테스트 작성 가이드
- `examples.md`: 코드 예시

**주요 유틸리티**:
```python
# Wrapper Layer Interface
class PythonEngineWrapper:
    """기존 Python 엔진 호출 래퍼"""

    async def execute(self, command: str, args: dict, timeout: int = 10):
        """비동기 엔진 호출"""
        cmd = ["python", "coordinator.py", f"--{command}", json.dumps(args)]
        proc = await asyncio.create_subprocess_exec(*cmd, ...)
        return await proc.communicate()

# Metrics Cache
class MetricsCache:
    """시스템 메트릭 캐싱 (30초 TTL)"""

    def __init__(self, ttl: int = 30):
        self._cache = {}
        self._ttl = ttl

    def get(self, key: str):
        """캐시 조회"""
        if key in self._cache:
            timestamp, value = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return value
        return None

    def set(self, key: str, value):
        """캐시 저장"""
        self._cache[key] = (time.time(), value)
```

**예상 라인 수**: ~500 lines (스킬 전체)

### 성능 특성

**현재 성능** (기존 엔진):
- 전체 워크플로우: 2.5초
- CPU 분석: 0.8초
- Memory 분석: 0.7초
- Disk 분석: 0.6초
- Network 분석: 0.4초

**목표 성능** (래퍼 레이어 추가):
- 전체 워크플로우: 1.5-2.0초 (20-40% 개선)
- 병렬 분석 (4개 동시): 0.8초 (병렬화로 최대값만 소요)
- 래퍼 오버헤드: <0.2초
- 최적화 실행: <1.0초

**성능 최적화 기법**:
1. **asyncio 병렬화**: CPU, Memory, Disk, Network 분석 동시 실행
2. **지연 로딩**: 필요한 에이전트만 로드
3. **메트릭 캐싱**: 30초 TTL로 중복 조회 방지
4. **subprocess 최적화**: `asyncio.create_subprocess_exec` 사용

---

## Traceability (추적성)

### TAG System

- **SPEC-MACOS-OPTIMIZER-001**: 본 명세서
- **IMPL-MACOS-OPTIMIZER-001**: `.claude/agents/`, `.claude/commands/`, `.claude/skills/` 구현
- **TEST-MACOS-OPTIMIZER-001**: `tests/test_macos_optimizer/` 테스트

### Cross-References

- **관련 SPEC**:
  - SPEC-UPDATE-001 (moai-adk update 백업/복원 기능 - 참고)
- **의존 모듈**:
  - `moai-adk>=0.30.2`: MoAI 프레임워크
  - `psutil>=6.1.0`: 시스템 메트릭
  - `pytest>=8.3.0`, `pytest-asyncio>=0.24.0`: 테스트
  - `pydantic>=2.10.0`: 데이터 검증

### 검증 기준

- ✅ 모든 함수 docstring 작성 완료
- ✅ Type hints 100% 적용
- ✅ 테스트 커버리지 ≥86%
- ✅ `ruff check` 통과
- ✅ `mypy` 타입 검사 통과
- ✅ 성능 목표 달성 (1.5-2.0초)
- ✅ 기존 Python 에이전트 무수정 (Git diff 검증)

---

**END OF SPECIFICATION**
