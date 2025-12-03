---
id: SPEC-MACOS-OPTIMIZER-001
version: "1.0.0"
status: "draft"
created: "2025-11-29"
updated: "2025-11-29"
---

# SPEC-MACOS-OPTIMIZER-001: 구현 계획

## 개요

macOS Resource Optimizer MoAI 래퍼 통합을 위한 구현 계획입니다. Additive Integration 패턴을 사용하여 기존 50개 Python 에이전트를 보존하면서, 8개의 래퍼 에이전트와 6개의 커맨드를 추가합니다.

---

## 우선순위 기반 마일스톤

### 🎯 Primary Goal: 래퍼 레이어 구현 및 통합

**목표**: 기존 엔진과 통신 가능한 래퍼 레이어 구축

**구현 항목**:
1. **Manager 에이전트 생성** (2개)
   - `manager-resource-coordinator.md` - 메인 조정자
   - `manager-resource-strategy.md` - 전략 수립자

2. **Expert 에이전트 생성** (6개)
   - `expert-cpu-optimizer.md`
   - `expert-memory-optimizer.md`
   - `expert-disk-optimizer.md`
   - `expert-network-optimizer.md`
   - `expert-battery-optimizer.md`
   - `expert-thermal-optimizer.md`

3. **통합 스킬 생성** (1개)
   - `moai-system-macos-resource-optimizer/SKILL.md`
   - `modules/wrapper-layer.md` - 래퍼 인터페이스 패턴
   - `modules/performance-optimization.md` - 성능 최적화
   - `modules/testing-strategy.md` - 테스트 전략

4. **핵심 유틸리티 구현**
   - `PythonEngineWrapper` 클래스 (기존 엔진 호출)
   - `MetricsCache` 클래스 (메트릭 캐싱)
   - `async_gather_tasks()` 함수 (병렬 실행)

**검증 기준**:
- ✅ 8개 에이전트 파일 생성 완료
- ✅ 스킬 SKILL.md + 3개 모듈 완료
- ✅ `PythonEngineWrapper.execute()` 정상 작동
- ✅ 병렬 분석 실행 성공 (asyncio.gather)

---

### 🎯 Secondary Goal: 커맨드 구현 및 워크플로우 연결

**목표**: 6개 커맨드로 전체 워크플로우 실행 가능

**구현 항목**:
1. **Commands 디렉토리 생성**
   - `.claude/commands/macos-resource-optimizer/`

2. **커맨드 파일 생성** (6개)
   - `0-init.md` - 프로젝트 초기화
   - `1-analyze.md` - 시스템 분석
   - `2-optimize.md` - 최적화 실행
   - `3-monitor.md` - 실시간 모니터링
   - `4-report.md` - 보고서 생성
   - `9-feedback.md` - 피드백 수집

3. **워크플로우 연결**
   - `/macos-resource-optimizer:1-analyze` → 병렬 분석 실행 → 전략 생성 → 사용자 승인 요청
   - `/macos-resource-optimizer:2-optimize` → 기존 엔진 호출 → 결과 수집 → 보고서 생성

4. **AskUserQuestion 통합**
   - 최적화 전략 승인 프롬프트
   - 피드백 타입 선택 프롬프트

**검증 기준**:
- ✅ 6개 커맨드 파일 생성 완료
- ✅ `/macos-resource-optimizer:1-analyze` 실행 성공
- ✅ AskUserQuestion 프롬프트 정상 작동
- ✅ 기존 엔진 호출 성공 (coordinator.py)

---

### 🎯 Tertiary Goal: 성능 최적화 및 테스트 커버리지 달성

**목표**: 성능 1.5-2.0초 달성, 테스트 커버리지 86%+ 달성

**구현 항목**:
1. **성능 최적화**
   - asyncio 병렬화 적용 (CPU, Memory, Disk, Network 동시 분석)
   - 메트릭 캐싱 구현 (30초 TTL)
   - 지연 로딩 적용 (필요한 에이전트만 로드)
   - subprocess 최적화 (`asyncio.create_subprocess_exec`)

2. **테스트 작성**
   - `tests/test_macos_optimizer/test_manager_coordinator.py`
   - `tests/test_macos_optimizer/test_manager_strategy.py`
   - `tests/test_macos_optimizer/test_expert_cpu.py`
   - `tests/test_macos_optimizer/test_expert_memory.py`
   - `tests/test_macos_optimizer/test_expert_disk.py`
   - `tests/test_macos_optimizer/test_expert_network.py`
   - `tests/test_macos_optimizer/test_expert_battery.py`
   - `tests/test_macos_optimizer/test_expert_thermal.py`
   - `tests/test_macos_optimizer/test_commands.py`
   - `tests/test_macos_optimizer/test_skill.py`

3. **pytest-benchmark 통합**
   - End-to-end 성능 측정
   - 병렬화 전후 비교
   - 캐싱 효과 측정

4. **pytest-asyncio 설정**
   - 비동기 테스트 환경 구성
   - Mock 객체 설정 (psutil, subprocess)

**검증 기준**:
- ✅ 전체 워크플로우 실행 시간 ≤2.0초
- ✅ 병렬 분석 실행 시간 ≤0.8초
- ✅ 테스트 커버리지 ≥86%
- ✅ 모든 테스트 통과 (pytest)

---

### 🎯 Final Goal: 문서화 및 품질 검증

**목표**: 완전한 문서화 및 TRUST 5 품질 기준 달성

**구현 항목**:
1. **문서화**
   - `README.md` - 프로젝트 개요
   - `.moai/docs/macos-optimizer-architecture.md` - 아키텍처 문서
   - `.moai/docs/macos-optimizer-performance.md` - 성능 최적화 가이드
   - 각 에이전트 파일에 사용 예시 추가

2. **TRUST 5 검증**
   - **Test-first**: 테스트 커버리지 ≥86%
   - **Readable**: 모든 함수 docstring 작성, Type hints 100%
   - **Unified**: `ruff check` 통과, 일관된 코드 스타일
   - **Secured**: 보안 검토 (기존 엔진 호출 시 입력 검증)
   - **Trackable**: Git 커밋 메시지 규칙 준수

3. **품질 검증**
   - `ruff check .claude/agents/ .claude/commands/ .claude/skills/`
   - `mypy .claude/agents/ .claude/commands/ .claude/skills/`
   - `pytest --cov=. --cov-report=html`
   - Git diff 검증 (기존 Python 에이전트 무수정)

**검증 기준**:
- ✅ 모든 문서 작성 완료
- ✅ TRUST 5 모든 기준 통과
- ✅ `ruff check` 통과
- ✅ `mypy` 타입 검사 통과
- ✅ 기존 에이전트 무수정 확인

---

## 기술 접근 방식

### 아키텍처 패턴

**Additive Integration Pattern**:
```
기존 엔진 (보존) + 래퍼 레이어 (추가)
```

**장점**:
- ✅ 기존 코드 무수정 (안정성 보장)
- ✅ 점진적 통합 가능
- ✅ 롤백 용이 (래퍼만 제거)

**단점**:
- ❌ 래퍼 오버헤드 발생 (병렬화로 상쇄)
- ❌ 두 레이어 간 통신 복잡도 증가

### 성능 최적화 전략

**1. asyncio 병렬화**:
```python
# 순차 실행 (기존): 2.5초
cpu_result = analyze_cpu()        # 0.8초
memory_result = analyze_memory()  # 0.7초
disk_result = analyze_disk()      # 0.6초
network_result = analyze_network()# 0.4초

# 병렬 실행 (목표): 0.8초
results = await asyncio.gather(
    analyze_cpu(),
    analyze_memory(),
    analyze_disk(),
    analyze_network()
)  # 최대 0.8초 (CPU 분석 시간)
```

**2. 메트릭 캐싱**:
```python
# 캐시 미사용: 매번 psutil 호출 (0.1초)
cpu_percent = psutil.cpu_percent()

# 캐시 사용: 30초 내 재사용 (<0.001초)
cache = MetricsCache(ttl=30)
cpu_percent = cache.get("cpu_percent") or psutil.cpu_percent()
```

**3. 지연 로딩**:
```python
# 초기 로딩: 모든 에이전트 로드 (1.0초)
agents = [load_agent(name) for name in all_agent_names]

# 지연 로딩: 필요한 에이전트만 로드 (0.2초)
def get_agent(name):
    if name not in _agent_cache:
        _agent_cache[name] = load_agent(name)
    return _agent_cache[name]
```

### 테스트 전략

**테스트 레벨**:
1. **Unit Tests**: 각 에이전트, 스킬 함수 단위 테스트
2. **Integration Tests**: 래퍼 레이어 + 기존 엔진 통합 테스트
3. **E2E Tests**: 커맨드 실행 전체 워크플로우 테스트
4. **Performance Tests**: pytest-benchmark로 성능 측정

**Mock 전략**:
```python
# psutil Mock (시스템 메트릭 시뮬레이션)
@pytest.fixture
def mock_psutil(monkeypatch):
    monkeypatch.setattr("psutil.cpu_percent", lambda: 75.0)
    monkeypatch.setattr("psutil.virtual_memory", lambda: MockMemory())

# subprocess Mock (기존 엔진 시뮬레이션)
@pytest.fixture
def mock_subprocess(monkeypatch):
    async def mock_exec(*args, **kwargs):
        return MockProcess()
    monkeypatch.setattr("asyncio.create_subprocess_exec", mock_exec)
```

---

## 리스크 및 대응 방안

### 리스크 #1: 래퍼 오버헤드로 인한 성능 저하

**확률**: 중간 (40%)
**영향**: 높음 (성능 목표 미달성)

**대응 방안**:
- 병렬화로 오버헤드 상쇄 (asyncio.gather)
- 메트릭 캐싱으로 중복 조회 제거
- pytest-benchmark로 조기 성능 측정
- 목표 미달 시 래퍼 레이어 최적화 (C extension 고려)

### 리스크 #2: 기존 Python 엔진과의 통신 오류

**확률**: 낮음 (20%)
**영향**: 높음 (통합 실패)

**대응 방안**:
- subprocess 타임아웃 설정 (10초)
- 에러 핸들링 및 재시도 로직 구현
- 통합 테스트로 조기 검증
- 기존 엔진 인터페이스 문서화 필요 시 요청

### 리스크 #3: 테스트 커버리지 목표 미달 (86%)

**확률**: 낮음 (15%)
**영향**: 중간 (품질 저하)

**대응 방안**:
- TDD 방식으로 테스트 우선 작성
- pytest-cov로 실시간 커버리지 모니터링
- 미커버 코드 자동 탐지 및 테스트 생성
- manager-quality 에이전트로 테스트 자동 생성

### 리스크 #4: macOS 시스템 권한 문제

**확률**: 낮음 (10%)
**영향**: 중간 (일부 기능 제한)

**대응 방안**:
- psutil은 admin 권한 불필요 (일반 사용자 권한으로 실행 가능)
- 권한 부족 시 명확한 에러 메시지 표시
- 권한 요구사항을 README에 명시

---

## 종속성 및 제약사항

### 기술 종속성

**필수 패키지**:
```toml
# pyproject.toml
[project]
dependencies = [
    "moai-adk>=0.30.2",
    "psutil>=6.1.0",
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-benchmark>=4.0.0",
    "pydantic>=2.10.0",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]
```

**최신 버전 확인 필요**:
- `psutil`: macOS 호환성 확인 (2025년 최신 버전)
- `pytest-asyncio`: 비동기 테스트 지원 버전
- `pydantic`: V2 API 사용

### 제약사항

**시스템 요구사항**:
- macOS 13.0 이상 (Ventura+)
- Python 3.11-3.14
- 최소 8GB RAM (메트릭 수집 및 분석)

**기존 엔진 제약**:
- Python 에이전트 수정 불가 (Additive 패턴)
- coordinator.py 인터페이스 변경 불가
- 기존 엔진 실행 타임아웃 10초 (설정 가능)

**MoAI 프레임워크 제약**:
- 에이전트 명명 규칙 준수 (`manager-*`, `expert-*`)
- 커맨드 접두사 규칙 (`/macos-resource-optimizer:*`)
- EARS 형식 SPEC 준수

---

## Git 브랜치 전략

**현재 Git 전략**: Manual Mode (로컬 전용)

**브랜치 생성 여부**: 사용자 선택에 따름
- `config.json`의 `git_strategy.branch_creation.prompt_always: true`에 따라 SPEC 생성 시 확인

**권장 브랜치명**:
```bash
# Feature branch
feature/SPEC-MACOS-OPTIMIZER-001-wrapper-integration

# Or direct commit (develop_direct)
git commit -m "feat(macos-optimizer): Add MoAI wrapper layer integration"
```

**커밋 메시지 규칙** (Conventional Commits):
```
feat(macos-optimizer): Add manager-resource-coordinator agent
feat(macos-optimizer): Add expert-cpu-optimizer agent
test(macos-optimizer): Add unit tests for wrapper layer
docs(macos-optimizer): Add architecture documentation
perf(macos-optimizer): Optimize asyncio parallel execution
```

---

## 다음 단계

### 즉시 실행 가능

1. **SPEC 승인 완료 후**:
   - `/moai:2-run SPEC-MACOS-OPTIMIZER-001` 실행
   - manager-tdd 에이전트가 RED-GREEN-REFACTOR 사이클 실행

2. **구현 완료 후**:
   - `/moai:3-sync SPEC-MACOS-OPTIMIZER-001` 실행
   - manager-docs 에이전트가 문서 동기화

3. **문서화 필요 시**:
   - `/macos-resource-optimizer:4-report` 실행
   - 보고서 생성 및 성능 측정 결과 확인

### 추가 고려사항

**Expert 에이전트 협의 (선택)**:
- **expert-backend**: Python 엔진 인터페이스 설계 검토
- **expert-devops**: macOS 환경 배포 전략 검토
- **expert-security**: 기존 엔진 호출 시 보안 검증

**참고**: 협의는 선택사항이며, SPEC이 명확하므로 즉시 구현 진행 가능

---

**END OF PLAN**
