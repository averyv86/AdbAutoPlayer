# Quick Test Reference Card

## File Locations

```
.claude/skills/macos-resource-optimizer/.data/tests/
├── test_expert_cpu_optimizer.py        4 classes × 4-5 tests
├── test_expert_memory_optimizer.py     4 classes × 4-5 tests
├── test_expert_disk_optimizer.py       4 classes × 4-5 tests
├── test_expert_network_optimizer.py    4 classes × 4-5 tests
├── test_expert_battery_optimizer.py    4 classes × 4-5 tests
├── test_expert_thermal_optimizer.py    4 classes × 4-5 tests
└── conftest.py                         Configuration & fixtures
```

## Quick Commands

### Run All Tests
```bash
pytest .claude/skills/macos-resource-optimizer/.data/tests/ -v
```

### Run by Agent
```bash
pytest .claude/skills/macos-resource-optimizer/.data/tests/test_expert_cpu_optimizer.py -v        # CPU tests
pytest .claude/skills/macos-resource-optimizer/.data/tests/test_expert_memory_optimizer.py -v     # Memory tests
pytest .claude/skills/macos-resource-optimizer/.data/tests/test_expert_disk_optimizer.py -v       # Disk tests
pytest .claude/skills/macos-resource-optimizer/.data/tests/test_expert_network_optimizer.py -v    # Network tests
pytest .claude/skills/macos-resource-optimizer/.data/tests/test_expert_battery_optimizer.py -v    # Battery tests
pytest .claude/skills/macos-resource-optimizer/.data/tests/test_expert_thermal_optimizer.py -v    # Thermal tests
```

### Run by Category
```bash
pytest .claude/skills/macos-resource-optimizer/.data/tests/ -k "MetricsParsing" -v      # Parsing tests
pytest .claude/skills/macos-resource-optimizer/.data/tests/ -k "Recommendations" -v     # Recommendation tests
pytest .claude/skills/macos-resource-optimizer/.data/tests/ -k "Timeout" -v             # Timeout tests
pytest .claude/skills/macos-resource-optimizer/.data/tests/ -k "Thresholds" -v          # Threshold tests
```

### Coverage Report
```bash
pytest .claude/skills/macos-resource-optimizer/.data/tests/ --cov=.claude/skills/macos-resource-optimizer/.data --cov-report=html
```

## Test Structure

Each agent has 4 test classes:

```
TestXXXMetricsParsing        → JSON parsing validation
TestXXXRecommendations        → Threshold-based suggestions
TestXXXSubprocessTimeout      → Async timeout handling
TestXXXCriticalThresholds     → Emergency state detection
```

## Metrics Dataclasses

### CPU Metrics
- `usage_percent` (0-100): CPU usage
- `core_count` (int): Number of cores
- `per_core_usage` (List): Per-core breakdown
- `temperature` (°C): CPU temperature
- `frequency_mhz` (int): CPU frequency
- `throttling_detected` (bool): Throttle status

### Memory Metrics
- `total_gb` (float): Total RAM
- `used_gb` (float): Used RAM
- `available_gb` (float): Free RAM
- `usage_percent` (0-100): Memory usage
- `swap_used_gb` (float): Swap usage
- `swap_total_gb` (float): Swap size
- `page_faults` (int): Page fault count
- `compression_ratio` (float): Memory compression

### Disk Metrics
- `total_gb` (float): Total capacity
- `used_gb` (float): Used space
- `available_gb` (float): Free space
- `usage_percent` (0-100): Disk usage
- `read_speed_mbs` (float): Read speed
- `write_speed_mbs` (float): Write speed
- `queue_depth` (int): I/O queue depth
- `io_wait_percent` (0-100): I/O wait time

### Network Metrics
- `bytes_sent_mb` (float): Data sent
- `bytes_recv_mb` (float): Data received
- `packets_sent` (int): Packets sent
- `packets_recv` (int): Packets received
- `packets_dropped` (int): Dropped packets
- `latency_ms` (float): Latency in milliseconds
- `packet_loss_percent` (0-100): Packet loss rate
- `bandwidth_usage_percent` (0-100): Bandwidth usage

### Battery Metrics
- `charge_percent` (0-100): Battery charge
- `health_percent` (0-100): Battery health
- `time_remaining_minutes` (int): Estimated runtime
- `is_charging` (bool): Charging status
- `cycle_count` (int): Battery cycles
- `max_capacity_mah` (float): Rated capacity
- `current_capacity_mah` (float): Current capacity
- `temperature_celsius` (float): Battery temperature

### Thermal Metrics
- `cpu_temp_celsius` (float): CPU temperature
- `gpu_temp_celsius` (float): GPU temperature
- `ssd_temp_celsius` (float): SSD temperature
- `ambient_temp_celsius` (float): Ambient temperature
- `max_temp_celsius` (float): Highest temperature
- `throttling_active` (bool): Throttling status
- `fan_speed_rpm` (int): Fan speed
- `fan_speed_percent` (0-100): Fan speed percentage

## Critical Thresholds

| Agent | Critical Condition |
|-------|-------------------|
| CPU | `usage > 95% OR throttling` |
| Memory | `usage > 85% OR (swap > 30% AND page_faults > 5M)` |
| Disk | `usage > 90% AND (read < 100 MBps OR write < 50 MBps)` |
| Network | `(loss > 2% OR latency > 200ms) AND bandwidth > 70%` |
| Battery | `(charge < 15% OR health < 80%) AND (cycles > 500 OR temp > 45°C)` |
| Thermal | `(cpu > 95°C OR gpu > 90°C) AND throttling_active` |

## Recommendation Priority Ranges

| Range | Severity | Action |
|-------|----------|--------|
| 0-20 | Normal | No action needed |
| 21-40 | Low | Monitor situation |
| 41-60 | Medium | Take action soon |
| 61-80 | High | Take action now |
| 81-100 | Critical | Take action immediately |

## Test Count Summary

```
CPU Optimizer:      17 tests (4 classes)
Memory Optimizer:   17 tests (4 classes)
Disk Optimizer:     18 tests (4 classes)
Network Optimizer:  18 tests (4 classes)
Battery Optimizer:  20 tests (4 classes)
Thermal Optimizer:  19 tests (4 classes)
─────────────────────────────────────
TOTAL:              109 tests (24 classes)
```

## Fixture Reference

### MockMetricsFactory
```python
@pytest.fixture
def metrics_factory():
    factory.cpu_metrics(usage_percent=85.0, core_count=8, ...)
    factory.memory_metrics(usage_percent=63.75, total_gb=16.0, ...)
    factory.disk_metrics(usage_percent=80.0, total_gb=256.0, ...)
    factory.network_metrics(bandwidth_usage_percent=65.0, ...)
    factory.battery_metrics(charge_percent=85.0, health_percent=95.0, ...)
    factory.thermal_metrics(cpu_temp_celsius=65.0, gpu_temp_celsius=58.0, ...)
```

### Mock Fixtures
```python
@pytest.fixture
def mock_subprocess_success()    # Successful execution

@pytest.fixture
def mock_subprocess_timeout()    # Timeout execution

@pytest.fixture
def mock_subprocess_error()      # Error execution

@pytest_asyncio.fixture
async def mock_wrapper()         # Full wrapper mock

@pytest_asyncio.fixture
async def mock_analyzer_timeout()  # Timeout simulator
```

## Common Assertions

### Metrics Parsing
```python
assert metrics.usage_percent == 45.2
assert metrics.core_count == 8
assert len(metrics.per_core_usage) == 8
assert abs(expected - actual) < 0.1  # Float comparison
```

### Recommendations
```python
assert len(recommendations) > 0
assert recommendations[0]["priority"] >= 70
assert "usage" in recommendations[0]["issue"].lower()
assert recommendations[0]["category"] == "cpu"
```

### Timeout Handling
```python
with pytest.raises(asyncio.TimeoutError):
    await asyncio.wait_for(slow_analysis(), timeout=0.1)
```

### Thresholds
```python
assert metrics.usage_percent > 95
assert metrics.throttling_detected is True
assert all(critical_indicators.values())
```

## Documentation Files

| File | Purpose |
|------|---------|
| `TEST_SUMMARY.md` | Detailed test reference (test structure, coverage, examples) |
| `TEST_IMPLEMENTATION_REPORT.md` | Complete implementation report (statistics, validation, checklist) |
| `README.md` | Test execution guide (how to run tests, integration examples) |
| `QUICK_TEST_REFERENCE.md` | This file (quick lookup, common commands) |

## Notes

- All tests use pytest-asyncio for async support
- Mock data factories in conftest.py generate realistic test data
- No actual coordinator.py execution in tests (all mocked)
- Tests are deterministic (no timing dependencies)
- Coverage target: 100% of critical paths
- All dataclasses properly typed and validated

## Example Test Run

```
$ pytest .claude/skills/macos-resource-optimizer/.data/tests/test_expert_cpu_optimizer.py -v

test_cpu_metrics_parsing_success PASSED
test_cpu_metrics_parsing_with_different_core_counts PASSED
test_cpu_metrics_parsing_invalid_json PASSED
test_cpu_metrics_parsing_missing_fields PASSED
test_cpu_recommendations_high_usage PASSED
test_cpu_recommendations_normal_usage PASSED
test_cpu_recommendations_temperature_warning PASSED
test_cpu_recommendations_multiple_high_core_usage PASSED
test_cpu_analysis_timeout PASSED
test_cpu_analysis_timeout_recovery PASSED
test_cpu_analysis_timeout_with_retry PASSED
test_cpu_subprocess_execution_error PASSED
test_cpu_critical_usage_detection PASSED
test_cpu_critical_all_cores_maxed PASSED
test_cpu_threshold_boundaries PASSED
test_cpu_throttling_detection PASSED
test_cpu_combined_critical_indicators PASSED

================== 17 passed in 0.32s ==================
```

---

**Total**: 109 tests ready for execution across 6 expert agents
