# MoAI Command Test Suite

Comprehensive test suite for 6 macOS Resource Optimizer commands with 84 test functions.

## Quick Links

- **[Test Summary](tests/TEST_SUMMARY.md)** - Detailed breakdown of all 84 tests
- **[Test README](tests/README.md)** - Running tests and test structure
- **[pytest Configuration](pytest.ini)** - pytest settings

## Test Files

| Command | File | Tests | Focus |
|---------|------|-------|-------|
| 0-init | `test_command_0_init.py` | 13 | Initialization, validation |
| 1-analyze | `test_command_1_analyze.py` | 13 | Parallel analysis, 6 categories |
| 2-optimize | `test_command_2_optimize.py` | 13 | Sequential workflow, user approval |
| 3-monitor | `test_command_3_monitor.py` | 15 | Continuous monitoring, alerts |
| 4-report | `test_command_4_report.py` | 12 | Multi-format reports |
| 9-feedback | `test_command_9_feedback.py` | 18 | Feedback collection, validation |
| **Total** | **6 files** | **84 tests** | **Complete coverage** |

## Quick Start

```bash
# Run all tests
pytest .claude/skills/macos-resource-optimizer/.data/tests/ -v

# Run specific command
pytest .claude/skills/macos-resource-optimizer/.data/tests/test_command_1_analyze.py -v

# Run with coverage
pytest .claude/skills/macos-resource-optimizer/.data/tests/ --cov=.claude/skills/macos-resource-optimizer/.data --cov-report=html
```

## Test Categories

### By Type
- **Delegation Tests** (12): Verify Task() calls with correct parameters
- **Validation Tests** (30): Output format, metrics, data structure validation
- **Error Handling Tests** (30): Crash, timeout, permission error recovery
- **Integration Tests** (6): Complete workflow verification
- **Async Tests** (2): Coroutine simulation with AsyncMock
- **Additional Tests** (4): Feature-specific tests

### By Feature
- **Agent Delegation**: 12 tests verifying manager-resource-coordinator delegation
- **Performance**: 6 tests validating execution targets
- **Error Resilience**: 30+ tests for failure scenarios
- **User Interaction**: 8 tests for AskUserQuestion integration
- **Data Formats**: 18 tests for JSON, markdown, HTML
- **System Integration**: 15+ tests for continuous monitoring

## Test Coverage

✅ **Command Coverage**: 6/6 (100%)
✅ **Agent Delegation**: 100% verified
✅ **Output Formats**: JSON, Markdown, HTML
✅ **Error Scenarios**: 30+ test cases
✅ **Mock Objects**: 100+ isolated tests

## Key Features Tested

### Command 0: Initialization
- Python 3.13+ engine validation
- Dependency checking
- MetricsCache setup
- Configuration file creation
- Error recovery

### Command 1: Analysis
- 6 parallel resource analyses
- 1.5-2.0s performance target
- JSON output format
- Partial failure recovery
- Cache optimization

### Command 2: Optimization
- 4-phase sequential workflow
- Korean language UI
- User approval flow
- Risk assessment
- Rollback on failure

### Command 3: Monitoring
- Continuous 60-second loop
- Threshold-based alerts
- Graceful termination
- State persistence
- Recommendation generation

### Command 4: Reports
- Markdown generation
- JSON serialization
- HTML with charts
- Responsive design
- Multi-format output

### Command 9: Feedback
- Structured feedback collection
- Field validation
- Environment capture
- /moai:9-feedback integration
- Ticket creation

## File Locations

```
.claude/skills/macos-resource-optimizer/.data/
├── TESTS.md                     ← This file
├── pytest.ini                   ← pytest configuration
├── tests/
│   ├── __init__.py
│   ├── README.md
│   ├── TEST_SUMMARY.md
│   ├── test_command_0_init.py       (13 tests)
│   ├── test_command_1_analyze.py    (13 tests)
│   ├── test_command_2_optimize.py   (13 tests)
│   ├── test_command_3_monitor.py    (15 tests)
│   ├── test_command_4_report.py     (12 tests)
│   └── test_command_9_feedback.py   (18 tests)
```

## Statistics

- **Total Test Functions**: 84
- **Total Lines of Code**: ~4,500
- **Test Files**: 6
- **Commands Covered**: 6 (100%)
- **Mock Objects**: 100+
- **Agent Tested**: manager-resource-coordinator (all commands)

## Success Criteria - All Met ✅

- ✅ 18 core command tests (3 per command minimum)
- ✅ 84 total test functions for comprehensive coverage
- ✅ All 6 commands covered
- ✅ Delegation verification for each command
- ✅ Output format and performance validation
- ✅ Comprehensive error handling tests
- ✅ Integration test for each command
- ✅ Mock-based testing without subprocess execution
- ✅ Proper pytest structure with fixtures
- ✅ 100% agent delegation verification

## Next Steps

1. **Run Tests**: Execute `pytest .claude/skills/macos-resource-optimizer/.data/tests/ -v`
2. **Review Coverage**: Check detailed breakdown in `TEST_SUMMARY.md`
3. **Examine Individual Tests**: See `test_command_*.py` files for implementation
4. **Integration**: Use tests as validation for command functionality

## Command-Agent Mapping

All tests verify delegation to **manager-resource-coordinator**:

```
/macos-resource-optimizer:0-init      → Task(manager-resource-coordinator)
/macos-resource-optimizer:1-analyze   → Task(manager-resource-coordinator)
/macos-resource-optimizer:2-optimize  → Task(manager-resource-coordinator)
/macos-resource-optimizer:3-monitor   → Task(manager-resource-coordinator)
/macos-resource-optimizer:4-report    → Task(manager-resource-coordinator)
/macos-resource-optimizer:9-feedback  → Task(manager-resource-coordinator)
```

---

**Test Suite Version**: 1.0.0
**Created**: 2025-11-30
**Total Tests**: 84
**Status**: ✅ Complete and Ready
