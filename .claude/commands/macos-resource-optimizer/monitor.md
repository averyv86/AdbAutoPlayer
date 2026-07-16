# macOS Resource Monitor - Continuous System Monitoring

**Purpose**: Continuous monitoring with periodic analysis, threshold alerts, and optional auto-optimization

**Status**: ✅ Active
**Version**: 1.0.0
**Last Updated**: 2025-12-01

---

## Overview

This command provides continuous system resource monitoring with:
- Periodic analysis (configurable interval)
- Threshold-based alerts
- Optional auto-optimization
- TOON-formatted progress
- Background daemon mode

**Workflow**: Initialize → Monitor Loop → Alert → [Auto-Optimize] → Report → Repeat

---

## 🚫 Protected Apps (Never Touched)

**CRITICAL GUARANTEE**: The following apps are **PERMANENTLY PROTECTED** and will **NEVER** be:
- Restarted, quit, killed, or terminated (even during auto-optimization)
- Included in optimization recommendations
- Analyzed for memory optimization

**Protected Apps**:
- **Ghostty** (your terminal - closing = session loss)
- **Visual Studio Code** (your editor - closing = work loss)
- All variants: `Code`, `code`, `ghostty`, `Visual Studio Code Helper`

**Why**: These are your active work environment. All monitoring and optimization operations (including auto-optimize triggers) have built-in BLACKLIST protection to ensure these apps are completely excluded.

**Auto-Optimization Safety**: Even when auto-optimize is enabled and memory thresholds are exceeded, Ghostty and VS Code will NEVER be touched. The system will optimize other apps only.

---

## Usage

```bash
# Start monitoring with defaults (60s interval, alert at 80%)
/macos-resource-optimizer:monitor

# Custom interval and threshold
/macos-resource-optimizer:monitor --interval=30 --threshold=75

# With auto-optimization enabled
/macos-resource-optimizer:monitor --auto-optimize

# Monitor specific categories only
/macos-resource-optimizer:monitor --categories=memory,cpu
```

**Options**:
- `--interval=<seconds>`: Analysis interval (default: 60, min: 10, max: 600)
- `--threshold=<percent>`: Alert threshold (default: 80)
- `--auto-optimize`: Enable automatic optimization when threshold exceeded
- `--categories=<list>`: Monitor specific categories (default: all)
- `--duration=<minutes>`: Total monitoring duration (default: unlimited)

---

## Execution Flow

### Phase 1: Initialization (5 seconds)

**Objective**: Initialize monitoring daemon and validate configuration

1. **Configuration Validation**
   ```python
   config = {
       "interval": 60,  # seconds
       "threshold": 80,  # percent
       "auto_optimize": False,
       "categories": ["memory", "cpu", "disk", "network", "battery", "thermal"],
       "duration": None,  # unlimited
       "alert_cooldown": 300  # 5 minutes between alerts
   }
   ```

2. **Baseline Analysis**
   ```bash
   # Initial system snapshot
   uv run scripts/analyze_all.py --categories all --format=toon
   ```

3. **User Confirmation**
   ```
   🔍 모니터링 시작

   설정:
   • 분석 주기: 60초
   • 경고 임계값: 80%
   • 자동 최적화: 비활성화
   • 모니터링 카테고리: 전체 (6개)
   • 지속 시간: 제한 없음

   현재 상태:
   • Memory: 78.8% ⚠️
   • CPU: 42.0% ✅
   • Disk: 120 MB/s ✅
   • Network: 25 Mbps ✅
   • Battery: 6.7h ✅
   • Thermal: 65°C ✅

   모니터링을 시작합니다...
   종료하려면 Ctrl+C를 누르세요
   ```

### Phase 2: Monitoring Loop (Continuous)

**Objective**: Periodic analysis and threshold checking

**Loop Structure**:
```python
while True:
    # 1. Periodic analysis
    results = analyze_all_categories()

    # 2. Threshold check
    alerts = check_thresholds(results, config.threshold)

    # 3. TOON progress
    report_progress(results, alerts)

    # 4. Alert handling
    if alerts:
        handle_alerts(alerts, config)

    # 5. Auto-optimization (if enabled and threshold exceeded)
    if config.auto_optimize and has_critical_alerts(alerts):
        execute_optimization()

    # 6. Sleep until next interval
    sleep(config.interval)
```

**Periodic Analysis**:
```bash
# Execute every <interval> seconds
uv run scripts/analyze_all.py --categories all --format=toon
```

**TOON Progress** (every interval):
```
monitor|cycle:1|time:12:34:56|mem:78.8|cpu:42.0|disk:120|net:25|bat:6.7h|temp:65
monitor|cycle:2|time:12:35:56|mem:79.2|cpu:45.0|disk:125|net:28|bat:6.5h|temp:67
monitor|cycle:3|time:12:36:56|mem:82.1|cpu:48.0|disk:130|net:32|bat:6.3h|temp:70|alert:memory
```

### Phase 3: Threshold Alerts

**Objective**: Notify user when thresholds are exceeded

**Alert Conditions**:
| Category | Threshold | Alert Level |
|----------|-----------|-------------|
| Memory | >80% | Warning |
| Memory | >90% | Critical |
| CPU | >70% | Warning |
| CPU | >85% | Critical |
| Disk I/O | >400 MB/s | Warning |
| Network | >80 Mbps | Warning |
| Battery | <2 hours | Warning |
| Battery | <1 hour | Critical |
| Thermal | >80°C | Warning |
| Thermal | >90°C | Critical |

**Alert Display** (osascript popup):
```bash
osascript -e 'display notification "메모리 사용: 82.1% (경고)" with title "시스템 리소스 경고" sound name "Basso"'
```

**Alert Cooldown**:
- Same alert won't trigger again for 5 minutes
- Prevents alert spam
- Critical alerts bypass cooldown

### Phase 4: Auto-Optimization (Optional)

**Objective**: Automatically optimize when critical thresholds exceeded

**Trigger Conditions**:
```python
if config.auto_optimize:
    if results.memory_percent > 85:
        execute_memory_optimization()
    elif results.cpu_percent > 80:
        execute_cpu_optimization()
    elif results.battery_hours < 1.5:
        execute_battery_optimization()
```

**User Approval** (first time only):
```
⚠️  메모리 사용 85% 초과 (자동 최적화 트리거)

자동 최적화를 실행하시겠습니까?

[예] 지금 실행하고 앞으로도 자동 실행
[아니오] 지금만 건너뜀
[다시 묻지 않음] 자동 최적화 비활성화

선택하세요:
```

**Optimization Execution**:
```bash
# Delegate to quick-optimize workflow
/macos-resource-optimizer:quick-optimize --auto-approve
```

**TOON Progress**:
```
monitor|cycle:5|alert:memory|auto_optimize:triggered
optimize|status:start|category:memory
optimize|status:complete|mem_before:85.2|mem_after:42.1|improvement:43.1
monitor|cycle:6|mem:42.1|auto_optimize:success
```

### Phase 5: Periodic Reporting

**Objective**: Summarize monitoring session periodically

**Report Frequency**: Every 10 cycles or when alert triggered

**TOON Report**:
```
report|session:1|duration:10min|cycles:10
mem|avg:75.3|min:68.2|max:82.1|alerts:2
cpu|avg:43.5|min:38.0|max:52.0|alerts:0
disk|avg:118|min:95|max:145|alerts:0
net|avg:22|min:15|max:35|alerts:0
bat|avg:6.8h|min:6.3h|max:7.2h|alerts:0
temp|avg:66|min:62|max:72|alerts:0
actions|auto_optimize:1|alerts_triggered:2
```

**User-Friendly Summary** (every 10 minutes):
```
📊 모니터링 요약 (10분)

평균 사용률:
• Memory: 75.3% (최고: 82.1%)
• CPU: 43.5% (최고: 52.0%)
• Battery: 6.8시간 (최저: 6.3시간)
• Thermal: 66°C (최고: 72°C)

경고 발생: 2회
• Memory >80%: 2회 (12:36, 12:42)

자동 최적화 실행: 1회
• Memory 최적화: 85.2% → 42.1%

시스템 상태: 안정적
```

### Phase 6: Session End

**Objective**: Gracefully end monitoring session

**Triggered by**:
- User Ctrl+C
- Duration limit reached
- Critical error

**Final Report**:
```
🔍 모니터링 세션 종료

세션 통계:
• 지속 시간: 1시간 25분
• 분석 주기: 85회
• 경고 발생: 5회
• 자동 최적화: 2회

카테고리별 평균:
• Memory: 72.4%
• CPU: 45.2%
• Battery: 6.5시간
• Thermal: 67°C

리소스 트렌드:
• Memory: 안정적 (±5%)
• CPU: 안정적 (±8%)
• Battery: 점진적 감소 (정상)

권장사항:
• Memory: 정기적 최적화 권장 (주 1회)
• CPU: 안정적, 조치 불필요
• Battery: 정상 소모 패턴

모니터링 로그: .moai/logs/monitor-2025-12-01-12-34.log
```

---

## Error Handling

### Monitoring Interrupted

```
⚠️  모니터링 중단됨

원인: 사용자 중단 (Ctrl+C)
지속 시간: 15분 32초
완료된 주기: 15회

마지막 상태:
• Memory: 74.2%
• CPU: 43.0%
• Battery: 6.8시간

모니터링을 재개하시겠습니까?
[예] 모니터링 계속
[아니오] 세션 종료
```

### Auto-Optimization Failed

```
❌ 자동 최적화 실패

시간: 12:45:23
트리거: Memory 85.2% (임계값: 85%)
오류: osascript permission denied

시스템 상태: 변경 없음
Memory: 85.2% (여전히 높음)

조치:
1. 권한 설정 확인
2. 수동 최적화 실행: /macos-resource-optimizer:quick-optimize
3. 모니터링 계속 중...

다음 확인: 60초 후
```

### High Resource Consumption Detected

```
🚨 심각한 리소스 사용 감지!

Memory: 92.4% (위험!)
Swap: 98.2% (심각!)
CPU: 78.3% (경고)

시스템이 매우 느려질 수 있습니다.

즉시 최적화를 실행하시겠습니까?
[예] 지금 최적화
[아니오] 모니터링 계속
[중단] 모니터링 종료
```

---

## Integration with Scripts

### background_monitor.py

**Monitoring daemon script**:
```bash
uv run scripts/background_monitor.py \
    --interval=60 \
    --threshold=80 \
    --categories=all \
    --format=toon \
    --auto-optimize=false
```

**Features**:
- Daemon mode (background execution)
- Configurable intervals and thresholds
- TOON-formatted progress
- Alert notifications via osascript
- Optional auto-optimization
- Session logging

### analyze_all.py

**Periodic analysis**:
```bash
# Execute every interval
uv run scripts/analyze_all.py --categories all --format=toon
```

### quick-optimize (Auto-Optimization)

**Triggered when thresholds exceeded**:
```bash
# Auto-approved optimization
/macos-resource-optimizer:quick-optimize --auto-approve
```

---

## Performance Expectations

**Resource Usage**:
- CPU overhead: <2% (during analysis)
- Memory footprint: ~50MB
- Disk writes: ~100KB per cycle (logging)

**Analysis Speed**:
- Single cycle: 1-2 seconds
- Impact on system: Minimal
- Background execution: Yes

**Alert Latency**:
- Threshold detection: <5 seconds
- Notification delivery: <1 second
- Total: <6 seconds from threshold breach to alert

---

## Use Cases

### Use Case 1: Continuous Development Monitoring

**Scenario**: Developer wants to monitor system during long build/test cycles

```bash
# Monitor memory and CPU during development
/macos-resource-optimizer:monitor --categories=memory,cpu --interval=30
```

**Benefits**:
- Early detection of memory leaks
- CPU spike alerts
- Prevents system slowdown during builds

### Use Case 2: Battery Life Optimization

**Scenario**: User on battery wants maximum runtime

```bash
# Monitor battery with aggressive optimization
/macos-resource-optimizer:monitor --categories=battery,cpu --auto-optimize --threshold=70
```

**Benefits**:
- Automatic power-saving actions
- Suspend background apps when battery low
- Extended battery life

### Use Case 3: Thermal Management

**Scenario**: Prevent thermal throttling during intensive tasks

```bash
# Monitor thermal and auto-optimize CPU when hot
/macos-resource-optimizer:monitor --categories=thermal,cpu --threshold=75
```

**Benefits**:
- Prevent overheating
- Reduce CPU load automatically
- Maintain performance without throttling

---

## Comparison with One-Time Commands

| Feature | quick-optimize | full-optimize | monitor |
|---------|----------------|---------------|---------|
| Execution | One-time | One-time | Continuous |
| Categories | Memory | All 6 | Configurable |
| Time | 52s | 87s | Unlimited |
| Auto-Optimization | No | No | Optional |
| Alerts | No | No | Yes |
| Use Case | Quick fix | Comprehensive | Prevention |

**When to use**:
- **quick-optimize**: Memory spike, need immediate fix
- **full-optimize**: System-wide slowness, comprehensive cleanup
- **monitor**: Continuous monitoring, prevent issues before they occur

---

## Configuration Options

### Basic Configuration

```json
{
  "interval": 60,
  "threshold": 80,
  "auto_optimize": false,
  "categories": ["all"],
  "duration": null
}
```

### Advanced Configuration

```json
{
  "interval": 30,
  "threshold": {
    "memory": 80,
    "cpu": 70,
    "battery": 2.0,
    "thermal": 80
  },
  "auto_optimize": {
    "enabled": true,
    "approval_required": "first_time",
    "cooldown": 600
  },
  "categories": ["memory", "cpu", "battery"],
  "duration": 480,
  "alerts": {
    "enabled": true,
    "sound": true,
    "cooldown": 300
  },
  "logging": {
    "enabled": true,
    "location": ".moai/logs/monitor/",
    "retention_days": 7
  }
}
```

---

## Related Commands

- `/macos-resource-optimizer:quick-optimize` - Fast memory optimization
- `/macos-resource-optimizer:full-optimize` - Comprehensive optimization
- `/macos-resource-optimizer:1-analyze` - One-time analysis
- `/macos-resource-optimizer:4-report` - Generate monitoring report

---

**Command Status**: ✅ Ready for Use
**Expected Overhead**: <2% CPU, ~50MB RAM
**User Approval**: Optional (auto-optimize)
**Token Optimized**: TOON format throughout
**Daemon Mode**: Yes (background execution)

---

**Execution**: Delegate to `manager-resource-coordinator` with monitoring workflow prompt + `background_monitor.py` daemon
