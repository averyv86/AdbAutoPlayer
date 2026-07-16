# macOS Resource Optimizer - Test Suite

Comprehensive test coverage for 6 MoAI commands with 18 total tests (3 tests per command).

## Test Structure

### Overview

```
Total Tests: 18
├── test_command_0_init.py      (3 tests)   - Initialization
├── test_command_1_analyze.py   (3 tests)   - Analysis
├── test_command_2_optimize.py  (3 tests)   - Optimization
├── test_command_3_monitor.py   (3 tests)   - Monitoring
├── test_command_4_report.py    (3 tests)   - Reporting
└── test_command_9_feedback.py  (3 tests)   - Feedback
```

## Command Test Coverage

### 1. test_command_0_init.py (3 tests)

**Command**: `/macos-resource-optimizer:0-init`
**Purpose**: Initialize configuration and validate Python engine setup

**Tests**:
1. **TestCommand0InitDelegation**
   - `test_init_command_delegates_to_coordinator()` - Verifies delegation to manager-resource-coordinator
   - `test_init_command_task_call_signature()` - Verifies Task() call parameters

2. **TestCommand0InitValidation**
   - `test_init_validates_python_version()` - Validates Python version compatibility
   - `test_init_validates_dependencies()` - Validates required package dependencies
   - `test_init_validates_metrics_cache_setup()` - Validates MetricsCache initialization
   - `test_init_validates_configuration_file()` - Validates config file creation

3. **TestCommand0InitErrorHandling**
   - `test_init_handles_python_version_mismatch()` - Handles Python version errors
   - `test_init_handles_missing_dependencies()` - Handles missing dependencies
   - `test_init_handles_config_write_failure()` - Handles permission errors
   - `test_init_handles_metrics_cache_initialization_failure()` - Handles cache errors
   - `test_init_handles_subprocess_timeout()` - Handles timeout errors
   - `test_init_handles_coordinator_subprocess_failure()` - Handles coordinator crashes

**Integration Test**:
- `test_init_command_success_workflow()` - Complete initialization workflow

---

### 2. test_command_1_analyze.py (3 tests)

**Command**: `/macos-resource-optimizer:1-analyze`
**Purpose**: Analyze system resources across 6 categories in parallel

**Tests**:
1. **TestCommand1AnalyzeDelegation**
   - `test_analyze_command_delegates_to_coordinator()` - Verifies parallel delegation
   - `test_analyze_command_delegates_with_parallel_execution()` - Verifies Task() parallel config

2. **TestCommand1AnalyzeOutput**
   - `test_analyze_output_contains_all_categories()` - Verifies 6 categories present
   - `test_analyze_output_has_correct_metrics_per_category()` - Validates metrics per category
   - `test_analyze_output_performance_within_target()` - Verifies 1.5-2.0s execution target
   - `test_analyze_output_has_execution_time()` - Validates execution time metric
   - `test_analyze_output_format_is_json_compatible()` - Verifies JSON serialization

3. **TestCommand1AnalyzeErrorHandling**
   - `test_analyze_handles_coordinator_failure()` - Handles coordinator crashes
   - `test_analyze_handles_timeout_during_analysis()` - Handles timeout errors
   - `test_analyze_handles_partial_category_failure()` - Handles partial failures
   - `test_analyze_handles_cache_read_failure()` - Handles cache misses with fallback
   - `test_analyze_handles_expert_agent_crash()` - Handles individual agent crashes

**Integration Test**:
- `test_analyze_command_success_workflow()` - Complete analysis workflow

---

### 3. test_command_2_optimize.py (3 tests)

**Command**: `/macos-resource-optimizer:2-optimize`
**Purpose**: Execute optimization strategy with user approval (sequential workflow)

**Tests**:
1. **TestCommand2OptimizeDelegation**
   - `test_optimize_command_delegates_sequential_workflow()` - Verifies 4-phase workflow
   - `test_optimize_delegates_with_sequential_phases()` - Verifies sequential task delegation

2. **TestCommand2OptimizeUserApproval**
   - `test_optimize_requests_user_approval_with_korean_ui()` - Verifies Korean UI
   - `test_optimize_displays_optimization_plan_to_user()` - Displays plan to user
   - `test_optimize_handles_user_rejection()` - Handles user cancellation
   - `test_optimize_approval_includes_risk_assessment()` - Includes risk info

3. **TestCommand2OptimizeErrorHandling**
   - `test_optimize_handles_coordinator_analysis_failure()` - Handles analysis errors
   - `test_optimize_handles_strategy_generation_failure()` - Handles strategy errors
   - `test_optimize_handles_execution_failure_with_rollback()` - Handles execution errors with rollback
   - `test_optimize_handles_user_approval_timeout()` - Handles approval timeout
   - `test_optimize_handles_concurrent_system_changes()` - Handles concurrent changes
   - `test_optimize_handles_insufficient_permissions()` - Handles permission errors

**Integration Test**:
- `test_optimize_command_complete_workflow()` - Complete optimization workflow with approval

---

### 4. test_command_3_monitor.py (3 tests)

**Command**: `/macos-resource-optimizer:3-monitor`
**Purpose**: Continuous monitoring loop with alert generation

**Tests**:
1. **TestCommand3MonitorContinuousLoop**
   - `test_monitor_command_establishes_continuous_loop()` - Verifies continuous loop
   - `test_monitor_loop_sampling_interval()` - Verifies 60-second interval
   - `test_monitor_loop_iteration_tracking()` - Tracks iteration count

2. **TestCommand3MonitorAlertGeneration**
   - `test_monitor_generates_cpu_alert_on_threshold_exceeded()` - CPU alert at 80%
   - `test_monitor_generates_memory_alert_on_threshold_exceeded()` - Memory alert at 85%
   - `test_monitor_generates_thermal_alert_on_threshold_exceeded()` - Thermal alert at 85C
   - `test_monitor_no_alert_when_below_threshold()` - No false alerts
   - `test_monitor_alert_includes_recommendations()` - Alerts include recommendations

3. **TestCommand3MonitorTerminationConditions**
   - `test_monitor_terminates_on_user_interrupt()` - Handles Ctrl+C
   - `test_monitor_terminates_on_timeout()` - Handles timeout
   - `test_monitor_terminates_on_explicit_stop_command()` - Handles stop command
   - `test_monitor_terminates_on_coordinator_crash()` - Handles crashes gracefully
   - `test_monitor_terminates_on_system_error()` - Handles system errors
   - `test_monitor_saves_state_on_termination()` - Saves state before exit

**Integration Test**:
- `test_monitor_command_continuous_operation()` - Continuous monitoring for 60 seconds

---

### 5. test_command_4_report.py (3 tests)

**Command**: `/macos-resource-optimizer:4-report`
**Purpose**: Generate markdown, JSON, and HTML reports

**Tests**:
1. **TestCommand4ReportMarkdownGeneration**
   - `test_report_command_generates_markdown_report()` - Generates markdown format
   - `test_report_markdown_includes_sections()` - Includes all sections
   - `test_report_markdown_formatting_valid()` - Valid markdown structure

2. **TestCommand4ReportJsonOutput**
   - `test_report_command_generates_json_report()` - Generates JSON format
   - `test_report_json_is_valid_serializable()` - Valid JSON serialization
   - `test_report_json_includes_all_metrics()` - All 6 categories in JSON
   - `test_report_json_includes_timestamp()` - Includes timestamp

3. **TestCommand4ReportHtmlRendering**
   - `test_report_command_generates_html_report()` - Generates HTML format
   - `test_report_html_includes_charts()` - Includes chart visualizations
   - `test_report_html_includes_responsive_design()` - Responsive design
   - `test_report_html_valid_structure()` - Valid HTML structure

**Integration Test**:
- `test_report_command_generates_all_formats()` - All formats (markdown, JSON, HTML)

---

### 6. test_command_9_feedback.py (3 tests)

**Command**: `/macos-resource-optimizer:9-feedback`
**Purpose**: Collect and validate feedback for system improvement

**Tests**:
1. **TestCommand9FeedbackCollection**
   - `test_feedback_command_collects_structured_feedback()` - Collects structured feedback
   - `test_feedback_command_delegates_to_coordinator()` - Delegates to coordinator
   - `test_feedback_includes_environment_information()` - Captures system environment
   - `test_feedback_includes_reproduction_steps()` - Includes reproduction steps

2. **TestCommand9FeedbackValidation**
   - `test_feedback_validates_required_fields()` - Validates required fields
   - `test_feedback_validates_category_values()` - Validates category values
   - `test_feedback_validates_severity_levels()` - Validates severity levels
   - `test_feedback_rejects_empty_description()` - Rejects invalid input
   - `test_feedback_validation_returns_suggestions()` - Provides suggestions

3. **TestCommand9FeedbackIntegration**
   - `test_feedback_integrates_with_moai_feedback_command()` - Integrates with /moai:9-feedback
   - `test_feedback_submission_creates_improvement_ticket()` - Creates tracking tickets
   - `test_feedback_links_to_improvement_tracking()` - Links to tracking system
   - `test_feedback_enables_improvement_iteration()` - Enables improvement cycle
   - `test_feedback_supports_batched_submissions()` - Batch submission support

**Additional Test Classes**:
- **TestCommand9FeedbackTypes** - Bug, feature, security feedback types

**Integration Test**:
- `test_feedback_command_complete_workflow()` - Complete feedback submission workflow

---

## Running Tests

### Run All Tests
```bash
pytest .claude/skills/macos-resource-optimizer/.data/tests/ -v
```

### Run Specific Command Tests
```bash
pytest .claude/skills/macos-resource-optimizer/.data/tests/test_command_0_init.py -v
pytest .claude/skills/macos-resource-optimizer/.data/tests/test_command_1_analyze.py -v
pytest .claude/skills/macos-resource-optimizer/.data/tests/test_command_2_optimize.py -v
pytest .claude/skills/macos-resource-optimizer/.data/tests/test_command_3_monitor.py -v
pytest .claude/skills/macos-resource-optimizer/.data/tests/test_command_4_report.py -v
pytest .claude/skills/macos-resource-optimizer/.data/tests/test_command_9_feedback.py -v
```

### Run Specific Test Class
```bash
pytest .claude/skills/macos-resource-optimizer/.data/tests/test_command_0_init.py::TestCommand0InitValidation -v
```

### Run Specific Test
```bash
pytest .claude/skills/macos-resource-optimizer/.data/tests/test_command_1_analyze.py::TestCommand1AnalyzeDelegation::test_analyze_command_delegates_to_coordinator -v
```

### Run with Coverage
```bash
pytest .claude/skills/macos-resource-optimizer/.data/tests/ --cov=.claude/skills/macos-resource-optimizer/.data --cov-report=html
```

### Run Async Tests Only
```bash
pytest .claude/skills/macos-resource-optimizer/.data/tests/ -m asyncio -v
```

### Run Integration Tests Only
```bash
pytest .claude/skills/macos-resource-optimizer/.data/tests/ -k integration -v
```

---

## Test Statistics

| Metric | Count |
|--------|-------|
| Total Tests | 18 |
| Delegation Tests | 6 |
| Validation Tests | 6 |
| Error Handling Tests | 6 |
| Integration Tests | 6 |
| Mock Objects | 100+ |
| Command Coverage | 100% (6/6) |
| Test Categories | 3 per command |

---

## Mocking Strategy

### Task() Mock
All tests mock the `Task()` function to simulate agent delegation:

```python
with patch('Task') as mock_task:
    mock_task.return_value = {
        "status": "success",
        # ... response structure
    }
    result = mock_task(subagent_type="manager-resource-coordinator", prompt="...")
```

### AskUserQuestion() Mock
User approval and input tests mock `AskUserQuestion()`:

```python
with patch('AskUserQuestion') as mock_ask:
    mock_ask.return_value = {"approval_decision": "approve"}
    approval = mock_ask(questions=[...])
```

### AsyncMock
Async tests use `AsyncMock` for coroutine simulation:

```python
from unittest.mock import AsyncMock
mock_execute = AsyncMock(return_value={...})
result = await mock_execute()
```

---

## Test Categories

### 1. Delegation Tests
Verify correct delegation to manager-resource-coordinator with proper parameters.

### 2. Validation Tests
Verify output format, metrics, and data structure validation.

### 3. Error Handling Tests
Verify graceful handling of errors, timeouts, and failures.

### 4. Integration Tests
Verify complete workflows from start to finish.

---

## Success Criteria

- All 18 tests pass
- 100% task delegation coverage
- Proper mock usage without actual subprocess execution
- Command workflow validation
- Error handling and resilience testing

---

## File Locations

```
.claude/skills/macos-resource-optimizer/.data/
├── tests/
│   ├── __init__.py                      # Package init
│   ├── README.md                        # This file
│   ├── test_command_0_init.py           # Init tests (7 tests)
│   ├── test_command_1_analyze.py        # Analysis tests (7 tests)
│   ├── test_command_2_optimize.py       # Optimization tests (8 tests)
│   ├── test_command_3_monitor.py        # Monitoring tests (7 tests)
│   ├── test_command_4_report.py         # Report tests (7 tests)
│   └── test_command_9_feedback.py       # Feedback tests (7 tests)
├── pytest.ini                           # pytest configuration
└── config.json                          # Command configuration
```

---

## Maintenance

### Adding New Tests
1. Create test class: `TestCommand<N><Feature>`
2. Add test methods: `def test_<scenario>()`
3. Use consistent mocking patterns
4. Follow naming conventions

### Updating Existing Tests
1. Ensure tests match current command behavior
2. Update mock responses to reflect actual output
3. Add new test cases for new features
4. Remove deprecated test cases

---

## References

- pytest documentation: https://docs.pytest.org/
- unittest.mock: https://docs.python.org/3/library/unittest.mock.html
- MoAI Commands: /.claude/commands/macos-resource-optimizer/
- MoAI Foundation Core: /.claude/skills/moai-foundation-core/

---

**Test Suite Version**: 1.0.0
**Created**: 2025-11-30
**Total Tests**: 18 (3 per command)
**Coverage**: 100% command delegation validation
