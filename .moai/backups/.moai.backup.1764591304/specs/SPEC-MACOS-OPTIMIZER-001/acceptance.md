---
id: SPEC-MACOS-OPTIMIZER-001
version: "1.0.0"
status: "draft"
created: "2025-11-29"
updated: "2025-11-29"
---

# SPEC-MACOS-OPTIMIZER-001: 수락 기준

## 개요

macOS Resource Optimizer MoAI 래퍼 통합의 수락 기준을 정의합니다. 모든 시나리오는 **Given-When-Then** 형식으로 작성되며, 각 기준은 자동화된 테스트로 검증됩니다.

---

## 기능 수락 기준 (Functional Acceptance Criteria)

### AC-001: 프로젝트 초기화 (/macos-resource-optimizer:0-init)

**Given**: 사용자가 MoAI-ADK가 설치된 macOS 환경에 있을 때
**When**: 사용자가 `/macos-resource-optimizer:0-init` 명령어를 실행할 때
**Then**: 시스템은 다음을 수행해야 한다:
- ✅ `.moai/config/macos-optimizer.json` 설정 파일 생성
- ✅ `.claude/agents/` 디렉토리에 8개 에이전트 파일 확인
- ✅ `.claude/commands/macos-resource-optimizer/` 디렉토리에 6개 커맨드 파일 확인
- ✅ `.claude/skills/moai-system-macos-resource-optimizer/` 스킬 디렉토리 확인
- ✅ 초기화 성공 메시지 출력 (Rich 라이브러리 포맷팅)

**검증 방법**:
```python
# tests/test_macos_optimizer/test_commands.py
def test_init_command():
    """프로젝트 초기화 테스트"""
    # Given
    project_dir = Path(".")

    # When
    result = run_command("/macos-resource-optimizer:0-init")

    # Then
    assert (project_dir / ".moai/config/macos-optimizer.json").exists()
    assert len(list((project_dir / ".claude/agents").glob("*-optimizer.md"))) == 8
    assert len(list((project_dir / ".claude/commands/macos-resource-optimizer").glob("*.md"))) == 6
    assert result.exit_code == 0
```

---

### AC-002: 시스템 분석 실행 (/macos-resource-optimizer:1-analyze)

**Given**: 프로젝트가 초기화되었을 때
**When**: 사용자가 `/macos-resource-optimizer:1-analyze` 명령어를 실행할 때
**Then**: 시스템은 다음을 수행해야 한다:
- ✅ CPU, Memory, Disk, Network 분석을 병렬 실행 (asyncio.gather)
- ✅ 전체 분석 시간 ≤0.8초
- ✅ 분석 결과를 `.moai/reports/optimization/analysis-{timestamp}.json`에 저장
- ✅ Rich 테이블로 분석 결과 출력 (CPU %, Memory %, Disk %, Network %)
- ✅ 최적화 전략 생성 완료 메시지 출력
- ✅ AskUserQuestion으로 전략 승인 요청

**검증 방법**:
```python
# tests/test_macos_optimizer/test_commands.py
@pytest.mark.asyncio
async def test_analyze_command(mock_psutil):
    """시스템 분석 테스트"""
    # Given
    mock_psutil.cpu_percent.return_value = 75.0
    mock_psutil.virtual_memory.return_value = MockMemory(percent=60.0)

    # When
    start_time = time.time()
    result = await run_command_async("/macos-resource-optimizer:1-analyze")
    execution_time = time.time() - start_time

    # Then
    assert execution_time <= 0.8  # 병렬 실행으로 0.8초 이하
    assert Path(".moai/reports/optimization").exists()
    analysis_files = list(Path(".moai/reports/optimization").glob("analysis-*.json"))
    assert len(analysis_files) > 0

    # 분석 결과 검증
    with open(analysis_files[0]) as f:
        data = json.load(f)
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "network" in data
        assert data["cpu"]["percent"] == 75.0
```

---

### AC-003: 최적화 전략 생성 및 승인

**Given**: 시스템 분석이 완료되었을 때
**When**: manager-resource-strategy 에이전트가 전략을 생성할 때
**Then**: 시스템은 다음을 수행해야 한다:
- ✅ CPU, Memory, Disk, Network 메트릭을 기반으로 최적화 우선순위 결정
- ✅ JSON 형식의 전략 생성 (strategy_id, timestamp, priority, optimizations)
- ✅ AskUserQuestion으로 전략 승인 프롬프트 표시
  - 선택지: "승인 및 최적화 실행", "전략 수정", "취소"
- ✅ 사용자 승인 시 `/macos-resource-optimizer:2-optimize` 실행 준비

**검증 방법**:
```python
# tests/test_macos_optimizer/test_manager_strategy.py
def test_strategy_generation():
    """최적화 전략 생성 테스트"""
    # Given
    analysis_result = {
        "cpu": {"percent": 90.0, "top_processes": [...]},
        "memory": {"percent": 80.0, "available_mb": 2048},
        "disk": {"percent": 70.0, "free_gb": 50},
        "network": {"sent_mb": 100, "recv_mb": 200}
    }

    # When
    strategy = generate_strategy(analysis_result)

    # Then
    assert strategy["strategy_id"] is not None
    assert strategy["priority"] == "HIGH"  # CPU 90% → HIGH
    assert len(strategy["optimizations"]) > 0
    assert strategy["optimizations"][0]["target"] == "CPU"
    assert strategy["optimizations"][0]["urgency"] == "high"
```

---

### AC-004: 최적화 실행 (/macos-resource-optimizer:2-optimize)

**Given**: 사용자가 최적화 전략을 승인했을 때
**When**: 사용자가 `/macos-resource-optimizer:2-optimize` 명령어를 실행할 때
**Then**: 시스템은 다음을 수행해야 한다:
- ✅ 기존 Python 엔진(`coordinator.py`) 호출 (subprocess)
- ✅ 실행 타임아웃 10초 설정
- ✅ 실시간 진행 상황 출력 (Rich Progress Bar)
- ✅ 실행 시간 ≤1.0초
- ✅ 결과 보고서를 `.moai/reports/optimization/report-{timestamp}.md`에 저장
- ✅ 성능 개선 수치 계산 및 표시 (before vs after)

**검증 방법**:
```python
# tests/test_macos_optimizer/test_commands.py
@pytest.mark.asyncio
async def test_optimize_command(mock_subprocess):
    """최적화 실행 테스트"""
    # Given
    strategy = {"strategy_id": "strat-001", "optimizations": [...]}
    mock_subprocess.return_value = MockProcess(returncode=0, stdout=b"Success")

    # When
    start_time = time.time()
    result = await run_command_async("/macos-resource-optimizer:2-optimize", strategy=strategy)
    execution_time = time.time() - start_time

    # Then
    assert execution_time <= 1.0  # 1초 이하
    assert result.exit_code == 0

    # subprocess 호출 검증
    mock_subprocess.assert_called_once()
    args = mock_subprocess.call_args[0]
    assert "coordinator.py" in args
    assert "--strategy" in args

    # 보고서 생성 검증
    report_files = list(Path(".moai/reports/optimization").glob("report-*.md"))
    assert len(report_files) > 0
```

---

### AC-005: 실시간 모니터링 (/macos-resource-optimizer:3-monitor)

**Given**: 최적화가 실행 중이거나 완료되었을 때
**When**: 사용자가 `/macos-resource-optimizer:3-monitor` 명령어를 실행할 때
**Then**: 시스템은 다음을 수행해야 한다:
- ✅ expert-thermal-optimizer, expert-battery-optimizer 에이전트 호출
- ✅ 5초 주기로 메트릭 갱신
- ✅ Rich 라이브러리로 실시간 메트릭 표시:
  - CPU 온도 (℃)
  - 배터리 상태 (%, 남은 시간)
  - 메모리 사용률 (%)
  - 디스크 I/O (MB/s)
- ✅ Ctrl+C로 종료 가능
- ✅ 종료 시 모니터링 요약 출력

**검증 방법**:
```python
# tests/test_macos_optimizer/test_commands.py
@pytest.mark.asyncio
async def test_monitor_command(mock_psutil):
    """실시간 모니터링 테스트"""
    # Given
    mock_psutil.sensors_temperatures.return_value = {"CPU": [MockTemp(current=65.0)]}
    mock_psutil.sensors_battery.return_value = MockBattery(percent=80, secsleft=7200)

    # When
    monitor_task = asyncio.create_task(run_command_async("/macos-resource-optimizer:3-monitor"))
    await asyncio.sleep(2)  # 2초 모니터링
    monitor_task.cancel()

    # Then
    # 최소 1회 메트릭 갱신 확인
    assert mock_psutil.sensors_temperatures.call_count >= 1
    assert mock_psutil.sensors_battery.call_count >= 1
```

---

### AC-006: 보고서 생성 (/macos-resource-optimizer:4-report)

**Given**: 최적화가 완료되었을 때
**When**: 사용자가 `/macos-resource-optimizer:4-report` 명령어를 실행할 때
**Then**: 시스템은 다음을 수행해야 한다:
- ✅ `.moai/reports/optimization/` 디렉토리의 분석 결과 수집
- ✅ Markdown 형식의 보고서 생성:
  - 실행 일시
  - Before/After 비교 (CPU, Memory, Disk, Network)
  - 성능 개선 수치 (% 및 절대값)
  - 적용된 최적화 전략
  - 권장사항
- ✅ 보고서를 `.moai/reports/optimization/report-{timestamp}.md`에 저장
- ✅ 주요 개선 사항 요약 출력 (Rich Panel)

**검증 방법**:
```python
# tests/test_macos_optimizer/test_commands.py
def test_report_command():
    """보고서 생성 테스트"""
    # Given
    create_mock_analysis_data()  # 분석 결과 Mock 데이터 생성

    # When
    result = run_command("/macos-resource-optimizer:4-report")

    # Then
    assert result.exit_code == 0

    # 보고서 파일 검증
    report_files = list(Path(".moai/reports/optimization").glob("report-*.md"))
    assert len(report_files) > 0

    # 보고서 내용 검증
    with open(report_files[0]) as f:
        content = f.read()
        assert "# 최적화 보고서" in content
        assert "Before" in content
        assert "After" in content
        assert "성능 개선" in content
```

---

### AC-007: 피드백 수집 (/macos-resource-optimizer:9-feedback)

**Given**: 사용자가 최적화 과정을 경험했을 때
**When**: 사용자가 `/macos-resource-optimizer:9-feedback` 명령어를 실행할 때
**Then**: 시스템은 다음을 수행해야 한다:
- ✅ AskUserQuestion으로 피드백 타입 선택 프롬프트 표시
  - 선택지: "버그 보고", "개선 제안", "기능 요청", "기타"
- ✅ 피드백 내용 입력 (멀티라인 텍스트)
- ✅ GitHub CLI(`gh issue create`)로 이슈 생성
  - 제목: `[FEEDBACK] {피드백 타입}: {요약}`
  - 본문: 사용자 입력 내용 + 시스템 환경 정보
  - 라벨: `feedback`, `macos-optimizer`
- ✅ 생성된 GitHub Issue URL 출력

**검증 방법**:
```python
# tests/test_macos_optimizer/test_commands.py
def test_feedback_command(mock_gh_cli):
    """피드백 수집 테스트"""
    # Given
    feedback_data = {
        "type": "개선 제안",
        "content": "분석 결과를 시각화하면 좋겠습니다."
    }
    mock_gh_cli.return_value = "https://github.com/user/repo/issues/123"

    # When
    result = run_command("/macos-resource-optimizer:9-feedback", **feedback_data)

    # Then
    assert result.exit_code == 0

    # gh issue create 호출 검증
    mock_gh_cli.assert_called_once()
    args = mock_gh_cli.call_args
    assert "[FEEDBACK]" in args["title"]
    assert "개선 제안" in args["title"]
    assert feedback_data["content"] in args["body"]
```

---

## 성능 수락 기준 (Performance Acceptance Criteria)

### AC-008: 전체 워크플로우 실행 시간

**Given**: 프로젝트가 초기화되었을 때
**When**: 사용자가 분석 → 최적화 → 보고서 생성 전체 워크플로우를 실행할 때
**Then**: 시스템은 다음 성능 기준을 만족해야 한다:
- ✅ 전체 실행 시간 ≤2.0초
- ✅ 분석 단계 ≤0.8초 (병렬 실행)
- ✅ 최적화 단계 ≤1.0초 (기존 엔진 호출)
- ✅ 보고서 생성 ≤0.2초

**검증 방법**:
```python
# tests/test_macos_optimizer/test_performance.py
@pytest.mark.benchmark
def test_full_workflow_performance(benchmark):
    """전체 워크플로우 성능 테스트"""
    # Given
    setup_project()

    # When
    result = benchmark(run_full_workflow)

    # Then
    assert result.stats.mean <= 2.0  # 평균 2초 이하
    assert result.stats.max <= 2.5   # 최대 2.5초 이하
```

---

### AC-009: 병렬 분석 성능

**Given**: 시스템 분석을 실행할 때
**When**: CPU, Memory, Disk, Network 분석을 병렬로 실행할 때
**Then**: 시스템은 다음 성능 기준을 만족해야 한다:
- ✅ 병렬 실행 시간 ≤0.8초 (순차 실행 2.5초 대비 68% 감소)
- ✅ 각 에이전트 실행 시간:
  - expert-cpu-optimizer ≤0.8초
  - expert-memory-optimizer ≤0.7초
  - expert-disk-optimizer ≤0.6초
  - expert-network-optimizer ≤0.4초

**검증 방법**:
```python
# tests/test_macos_optimizer/test_performance.py
@pytest.mark.asyncio
async def test_parallel_analysis_performance():
    """병렬 분석 성능 테스트"""
    # Given
    agents = [
        "expert-cpu-optimizer",
        "expert-memory-optimizer",
        "expert-disk-optimizer",
        "expert-network-optimizer"
    ]

    # When
    start_time = time.time()
    results = await asyncio.gather(*[run_agent(name) for name in agents])
    execution_time = time.time() - start_time

    # Then
    assert execution_time <= 0.8  # 병렬 실행으로 최대값만 소요
    assert all(r.status == "success" for r in results)
```

---

### AC-010: 메트릭 캐싱 효과

**Given**: 시스템 메트릭을 조회할 때
**When**: 30초 이내에 동일 메트릭을 재조회할 때
**Then**: 시스템은 다음 성능 기준을 만족해야 한다:
- ✅ 캐시 히트율 ≥90%
- ✅ 캐시 조회 시간 ≤0.001초 (psutil 호출 대비 99% 감소)
- ✅ 메모리 사용량 증가 ≤10MB

**검증 방법**:
```python
# tests/test_macos_optimizer/test_performance.py
def test_metrics_cache_performance():
    """메트릭 캐싱 성능 테스트"""
    # Given
    cache = MetricsCache(ttl=30)

    # When (첫 조회)
    start_time = time.time()
    cpu_percent = cache.get("cpu_percent") or psutil.cpu_percent()
    cache.set("cpu_percent", cpu_percent)
    first_query_time = time.time() - start_time

    # When (캐시 조회)
    start_time = time.time()
    cached_cpu_percent = cache.get("cpu_percent")
    cache_query_time = time.time() - start_time

    # Then
    assert cached_cpu_percent is not None
    assert cache_query_time <= 0.001  # 1ms 이하
    assert cache_query_time < first_query_time * 0.01  # 99% 감소
```

---

## 품질 수락 기준 (Quality Acceptance Criteria)

### AC-011: 테스트 커버리지

**Given**: 모든 구현이 완료되었을 때
**When**: pytest --cov 명령어를 실행할 때
**Then**: 시스템은 다음 품질 기준을 만족해야 한다:
- ✅ 전체 테스트 커버리지 ≥86%
- ✅ 에이전트 코드 커버리지 ≥90%
- ✅ 커맨드 코드 커버리지 ≥90%
- ✅ 스킬 코드 커버리지 ≥85%

**검증 방법**:
```bash
pytest --cov=.claude/agents --cov=.claude/commands --cov=.claude/skills \
       --cov-report=html --cov-report=term-missing
```

**최소 커버리지 기준**:
```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
.claude/agents/manager-resource-coordinator.md   200     18    91%
.claude/agents/expert-cpu-optimizer.md          120     10    92%
.claude/commands/1-analyze.md                   150     12    92%
.claude/skills/moai-system-macos-resource-optimizer/SKILL.md  500     70    86%
-----------------------------------------------------------
TOTAL                                          3000    240    92%
```

---

### AC-012: 코드 품질 (Linting)

**Given**: 모든 구현이 완료되었을 때
**When**: ruff check 명령어를 실행할 때
**Then**: 시스템은 다음 품질 기준을 만족해야 한다:
- ✅ ruff check 에러 0개
- ✅ 경고 ≤5개 (정당한 사유가 있는 경우만)
- ✅ 모든 함수 docstring 작성 완료
- ✅ Type hints 100% 적용

**검증 방법**:
```bash
ruff check .claude/agents/ .claude/commands/ .claude/skills/
```

**허용 가능한 경고 예시**:
- `# noqa: E501` (라인 길이 초과, Markdown 코드 블록)
- `# type: ignore` (타입 검사 예외, 정당한 사유)

---

### AC-013: 타입 안전성 (mypy)

**Given**: 모든 구현이 완료되었을 때
**When**: mypy 명령어를 실행할 때
**Then**: 시스템은 다음 품질 기준을 만족해야 한다:
- ✅ mypy 타입 에러 0개
- ✅ Type hints 100% 적용
- ✅ 모든 함수 반환 타입 명시
- ✅ 모든 함수 파라미터 타입 명시

**검증 방법**:
```bash
mypy .claude/agents/ .claude/commands/ .claude/skills/ --strict
```

---

### AC-014: 기존 Python 에이전트 보존

**Given**: 구현이 완료되었을 때
**When**: Git diff로 기존 파일을 확인할 때
**Then**: 시스템은 다음 기준을 만족해야 한다:
- ✅ `coordinator.py` 파일 무수정 (Git diff 0줄)
- ✅ `master-orchestrator.py` 파일 무수정
- ✅ `agents/` 디렉토리의 50개 Python 파일 무수정
- ✅ 기존 엔진 테스트 모두 통과

**검증 방법**:
```bash
# Git diff 검증
git diff existing_engine/ | wc -l  # 0줄이어야 함

# 기존 엔진 테스트 실행
pytest existing_engine/tests/ -v  # 모두 통과해야 함
```

---

## 통합 수락 기준 (Integration Acceptance Criteria)

### AC-015: 래퍼 레이어 + 기존 엔진 통합

**Given**: 래퍼 레이어와 기존 엔진이 모두 준비되었을 때
**When**: `/macos-resource-optimizer:2-optimize` 실행 시
**Then**: 시스템은 다음을 수행해야 한다:
- ✅ 래퍼 레이어가 기존 엔진(`coordinator.py`)를 정상 호출
- ✅ subprocess로 기존 엔진 실행 (타임아웃 10초)
- ✅ 기존 엔진 실행 결과를 래퍼 레이어로 반환
- ✅ 통합 에러 발생 시 명확한 에러 메시지 표시

**검증 방법**:
```python
# tests/test_macos_optimizer/test_integration.py
@pytest.mark.integration
def test_wrapper_engine_integration():
    """래퍼 레이어 + 기존 엔진 통합 테스트"""
    # Given
    strategy = generate_mock_strategy()

    # When
    wrapper = PythonEngineWrapper()
    result = wrapper.execute("optimize", strategy, timeout=10)

    # Then
    assert result.returncode == 0
    assert result.stdout is not None
    assert "Success" in result.stdout.decode()
```

---

### AC-016: AskUserQuestion 통합

**Given**: 사용자 승인이 필요한 단계에 도달했을 때
**When**: AskUserQuestion 도구를 호출할 때
**Then**: 시스템은 다음을 수행해야 한다:
- ✅ questionary 라이브러리로 프롬프트 표시
- ✅ 선택지 정확히 표시 (멀티셀렉트 지원)
- ✅ 사용자 응답을 올바르게 파싱
- ✅ 응답에 따라 다음 단계 실행

**검증 방법**:
```python
# tests/test_macos_optimizer/test_integration.py
def test_ask_user_question_integration(monkeypatch):
    """AskUserQuestion 통합 테스트"""
    # Given
    monkeypatch.setattr("questionary.select", lambda **kwargs: MockSelect("승인 및 최적화 실행"))

    # When
    response = ask_strategy_approval(strategy)

    # Then
    assert response == "승인 및 최적화 실행"
```

---

## Definition of Done (완료 기준)

모든 수락 기준(AC-001 ~ AC-016)이 통과되었을 때, 이 SPEC은 완료된 것으로 간주됩니다.

**최종 검증 체크리스트**:

**기능 완료** (AC-001 ~ AC-007):
- [ ] `/macos-resource-optimizer:0-init` 정상 작동
- [ ] `/macos-resource-optimizer:1-analyze` 정상 작동 (≤0.8초)
- [ ] `/macos-resource-optimizer:2-optimize` 정상 작동 (≤1.0초)
- [ ] `/macos-resource-optimizer:3-monitor` 정상 작동
- [ ] `/macos-resource-optimizer:4-report` 정상 작동
- [ ] `/macos-resource-optimizer:9-feedback` 정상 작동
- [ ] 최적화 전략 생성 및 승인 프로세스 정상 작동

**성능 완료** (AC-008 ~ AC-010):
- [ ] 전체 워크플로우 ≤2.0초
- [ ] 병렬 분석 ≤0.8초
- [ ] 메트릭 캐싱 효과 검증 (≥90% 히트율)

**품질 완료** (AC-011 ~ AC-014):
- [ ] 테스트 커버리지 ≥86%
- [ ] ruff check 통과 (에러 0개)
- [ ] mypy 타입 검사 통과
- [ ] 기존 Python 에이전트 무수정 (Git diff 0줄)

**통합 완료** (AC-015 ~ AC-016):
- [ ] 래퍼 레이어 + 기존 엔진 통합 정상 작동
- [ ] AskUserQuestion 통합 정상 작동

**문서화 완료**:
- [ ] README.md 작성 완료
- [ ] 아키텍처 문서 작성 완료
- [ ] 모든 에이전트 파일에 사용 예시 포함

---

**END OF ACCEPTANCE CRITERIA**
