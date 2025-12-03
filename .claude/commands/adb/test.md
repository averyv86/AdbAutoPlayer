---
name: adb:test
description: "Test bot configuration and verify functionality"
argument-hint: "[unit|integration|e2e|--all|--coverage]"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, TodoWrite, AskUserQuestion, Task
model: inherit
---

## Pre-execution Context

!adb devices
!git status --porcelain
!ls -la "$CLAUDE_PROJECT_DIR"/src-tauri/Settings/
!ls -la "$CLAUDE_PROJECT_DIR"/src-tauri/src-python/adb_auto_player/games/
!pytest --collect-only 2>/dev/null || echo "No tests collected"

## Essential Files

@.moai/config/config.json
@src-tauri/Settings/ADB.toml
@src-tauri/Settings/AFKJourney.toml
@pyproject.toml

---

# ADB AutoPlayer Testing Command

> Purpose: Comprehensive testing workflow for bot configurations with unit, integration, and end-to-end test execution.
> Tier: Validation (Quality Assurance)
> Integration: Delegates to adb-game-tester agent for test execution, analysis, and reporting.

## Command Purpose

Execute comprehensive testing workflows to validate ADB AutoPlayer bot configurations, verify device functionality, and ensure automation reliability. This command provides a structured testing framework that covers unit tests (fast, isolated), integration tests (device-dependent), and end-to-end tests (full workflow validation).

**Core Capabilities:**

- **Multi-Level Testing**: Support for unit, integration, and E2E test execution strategies
- **Device Validation**: Verify device connectivity, responsiveness, and automation compatibility
- **Configuration Testing**: Validate bot configuration files and game-specific settings
- **Performance Analysis**: Measure test execution time, coverage metrics, and bottleneck identification
- **Report Generation**: Produce comprehensive test reports with pass/fail metrics and recommendations
- **Failure Diagnosis**: Analyze test failures and provide actionable debugging guidance

---

## Prerequisites

Before running `/adb:test`, ensure the following requirements are met:

1. **Project Initialized**: ADB AutoPlayer project initialized via `/adb:init`
2. **Device Configuration**: At least one device configured in `ADB.toml`
3. **Bot Configuration**: Game-specific bot configuration files present
4. **Test Framework**: pytest installed with required plugins (pytest-cov, pytest-timeout)
5. **Connected Devices**: Devices accessible and authorized for E2E tests

---

## Usage Examples

### Example 1: Run All Tests (Default)

```bash
/adb:test
```

**Expected Behavior:**
- Executes all test types in sequence (unit → integration → e2e)
- Displays progress indicators for each test suite
- Generates comprehensive test report with coverage metrics
- Recommends next actions based on test results

### Example 2: Unit Tests Only (Fast Validation)

```bash
/adb:test unit
```

**Expected Behavior:**
- Runs fast unit tests without device dependencies
- Validates configuration parsing, helper functions, and core logic
- Typical execution time: 5-15 seconds
- Suitable for rapid development feedback

### Example 3: Integration Tests (Device-Dependent)

```bash
/adb:test integration
```

**Expected Behavior:**
- Tests device communication and ADB command execution
- Validates device pool management and connection stability
- Requires at least one connected device
- Execution time: 30-60 seconds

### Example 4: End-to-End Tests (Full Workflow)

```bash
/adb:test e2e
```

**Expected Behavior:**
- Simulates complete bot automation workflow
- Tests image recognition, tap actions, and game state management
- Requires device with target game installed
- Execution time: 2-5 minutes

### Example 5: Coverage Report Generation

```bash
/adb:test --coverage
```

**Expected Behavior:**
- Runs all tests with coverage tracking enabled
- Generates HTML coverage report
- Displays coverage percentage for each module
- Highlights untested code paths

---

## Step-by-Step Workflow

### PHASE 1: Pre-Test Validation (5 Steps)

#### Step 1.1: Verify Test Environment

**Objective:** Ensure testing prerequisites are met.

**Actions:**
1. Check pytest installation and version
2. Verify pytest plugins available (pytest-cov, pytest-timeout, pytest-xdist)
3. Validate test directory structure exists
4. Check for test configuration files (pytest.ini, conftest.py)

**Success Criteria:**
- pytest >= 7.0 installed
- Required plugins available
- Test directories present

**Error Handling:**
- If pytest missing: Display installation command (`uv add pytest`)
- If plugins missing: Suggest installation (`uv add pytest-cov pytest-timeout`)
- If test structure incomplete: Offer to generate boilerplate tests

**Output Example:**
```
✓ pytest Version: 8.3.4
✓ Test Plugins: pytest-cov, pytest-timeout, pytest-xdist
✓ Test Structure: Valid
  • Unit tests: 45 found
  • Integration tests: 12 found
  • E2E tests: 3 found
```

---

#### Step 1.2: Load Bot Configuration

**Objective:** Parse and validate bot configuration files.

**Actions:**
1. Read `ADB.toml` for device pool configuration
2. Load game-specific configuration (e.g., `AFKJourney.toml`)
3. Validate configuration schema and required fields
4. Check device serials are valid format

**Success Criteria:**
- Configuration files parsed successfully
- All required fields present
- Device pool contains at least one device

**Error Handling:**
- If configuration invalid: Display specific validation errors
- If devices missing: Suggest running `/adb:init` first
- If game config not found: Prompt user to select game

**Output Example:**
```
✓ Configuration Loaded
  • ADB Devices: 2 configured
  • Game: AFK Journey
  • Bot Settings: Valid
  • Test Configuration: Loaded
```

---

#### Step 1.3: Device Connectivity Check (For Integration/E2E Tests)

**Objective:** Verify devices are online and responsive.

**Actions:**
1. Execute `adb devices` to list connected devices
2. Match configured devices with available devices
3. Test basic ADB command on each device (`adb shell echo test`)
4. Measure device response time

**Success Criteria:**
- All configured devices online
- Device response time < 500ms
- ADB commands execute successfully

**Error Handling:**
- If devices offline: Skip integration/E2E tests, run unit tests only
- If response slow: Warn user about potential test timeouts
- If authorization revoked: Prompt user to re-authorize devices

**Output Example:**
```
✓ Device Connectivity Verified
  • emulator-5554: Online (response: 85ms)
  • R58N80ABCDE: Online (response: 120ms)
  • All devices ready for testing
```

---

#### Step 1.4: Select Test Type

**Objective:** Determine which test suites to execute based on user arguments.

**Actions:**
1. Parse command arguments to identify test type
2. If no argument provided, offer test type selection via AskUserQuestion
3. Store selected test types for execution

**Test Type Matrix:**

| Argument      | Test Types Executed       | Device Required | Execution Time |
|---------------|---------------------------|-----------------|----------------|
| `unit`        | Unit tests only           | No              | Fast (~10s)    |
| `integration` | Integration tests only    | Yes             | Medium (~60s)  |
| `e2e`         | End-to-end tests only     | Yes             | Slow (~5min)   |
| `--all`       | All test types            | Yes             | Full (~10min)  |
| (none)        | Interactive selection     | Varies          | Varies         |

**AskUserQuestion Format (if no argument):**

```python
AskUserQuestion({
    "questions": [{
        "question": "Select test execution strategy:",
        "header": "Test Selection",
        "multiSelect": false,
        "options": [
            {
                "label": "Unit Tests (Fast)",
                "description": "Configuration validation and logic tests (10-15s, no device required)"
            },
            {
                "label": "Integration Tests",
                "description": "Device communication and ADB command tests (30-60s, device required)"
            },
            {
                "label": "End-to-End Tests",
                "description": "Full bot workflow simulation (2-5min, device with game required)"
            },
            {
                "label": "All Tests (Comprehensive)",
                "description": "Complete test suite execution (5-10min)"
            }
        ]
    }]
})
```

**Success Criteria:**
- Test type determined
- Execution plan clear

**Output Example:**
```
✓ Test Type Selected: Integration Tests
  • Estimated Time: 30-60 seconds
  • Device Required: Yes
  • Coverage Tracking: Enabled
```

---

#### Step 1.5: Prepare Test Environment

**Objective:** Set up test execution environment and temporary directories.

**Actions:**
1. Create temporary test data directory (`.moai/temp/tests/`)
2. Clear previous test artifacts
3. Set environment variables for test execution
4. Initialize test logging

**Success Criteria:**
- Test directories created
- Environment variables set
- Logging initialized

**Error Handling:**
- If directory creation fails: Check permissions
- If artifacts remain: Force clean previous test data

**Output Example:**
```
✓ Test Environment Prepared
  • Test Directory: .moai/temp/tests/test-session-20251201-213456
  • Test Logs: .moai/logs/test-execution.log
  • Coverage Data: .moai/temp/coverage/
```

---

### PHASE 2: Test Execution (3 Steps)

#### Step 2.1: Execute Unit Tests (If Selected)

**Objective:** Run fast unit tests to validate core logic.

**Actions:**
1. Invoke pytest with unit test markers
2. Execute tests without device dependencies
3. Collect test results and coverage data
4. Parse test output for pass/fail metrics

**Test Execution Command:**
```bash
pytest tests/unit/ \
  -v \
  --cov=adb_auto_player \
  --cov-report=term \
  --cov-report=html:.moai/temp/coverage/ \
  --junit-xml=.moai/temp/tests/unit-results.xml \
  --timeout=10
```

**Success Criteria:**
- All unit tests pass
- Coverage >= 85%
- Execution time < 30 seconds

**Error Handling:**
- If tests fail: Collect failure details for report
- If coverage low: Highlight untested modules
- If timeout: Mark slow tests for investigation

**Output Example:**
```
✓ Unit Tests Complete
  • Tests Run: 45
  • Passed: 43
  • Failed: 2
  • Coverage: 87.5%
  • Execution Time: 12.3s
```

---

#### Step 2.2: Execute Integration Tests (If Selected)

**Objective:** Test device interaction and ADB command execution.

**Actions:**
1. Verify devices online before test start
2. Run integration test suite with device markers
3. Test device pool management
4. Validate ADB command execution and error handling
5. Measure device responsiveness

**Test Execution Command:**
```bash
pytest tests/integration/ \
  -v \
  --cov=adb_auto_player/device \
  --cov-append \
  --junit-xml=.moai/temp/tests/integration-results.xml \
  --timeout=60 \
  -k "not slow"
```

**Success Criteria:**
- Integration tests pass
- Device communication stable
- No device disconnections during tests

**Error Handling:**
- If device disconnects: Pause tests, attempt reconnection
- If ADB errors: Collect error logs for debugging
- If tests hang: Enforce timeout, report hanging test

**Output Example:**
```
✓ Integration Tests Complete
  • Tests Run: 12
  • Passed: 11
  • Failed: 1 (device timeout)
  • Device Stability: 91.7%
  • Execution Time: 48.2s
```

---

#### Step 2.3: Execute End-to-End Tests (If Selected)

**Objective:** Validate complete bot automation workflow.

**Actions:**
1. Verify target game installed on device
2. Run E2E test scenarios simulating bot operations
3. Test image recognition accuracy
4. Validate tap action execution
5. Verify game state transitions

**Test Execution Command:**
```bash
pytest tests/e2e/ \
  -v \
  --cov=adb_auto_player/games \
  --cov-append \
  --junit-xml=.moai/temp/tests/e2e-results.xml \
  --timeout=300 \
  --maxfail=3
```

**Success Criteria:**
- E2E scenarios complete successfully
- Image recognition accuracy >= 90%
- Tap actions execute reliably

**Error Handling:**
- If game not found: Skip E2E tests, warn user
- If image recognition fails: Collect template matching scores
- If game crashes: Capture device logs for analysis

**Output Example:**
```
✓ End-to-End Tests Complete
  • Tests Run: 3
  • Passed: 2
  • Failed: 1 (image template not found)
  • Image Recognition Accuracy: 92.3%
  • Execution Time: 4m 18s
```

---

### PHASE 3: Analysis & Reporting (4 Steps)

#### Step 3.1: Analyze Test Results

**Objective:** Process test output and identify patterns.

**Actions:**
1. Parse JUnit XML test results
2. Calculate pass/fail ratios for each test suite
3. Identify slowest tests (performance bottlenecks)
4. Detect flaky tests (inconsistent pass/fail)
5. Aggregate coverage metrics across all test types

**Success Criteria:**
- Test results parsed successfully
- Metrics calculated accurately
- Performance data collected

**Output Example:**
```
✓ Test Analysis Complete
  • Overall Pass Rate: 88.3% (53/60 tests)
  • Failed Tests: 7 (unit: 2, integration: 1, e2e: 4)
  • Slowest Tests:
    - test_afk_stages_full_clear: 4m 12s
    - test_device_reconnection: 1m 45s
    - test_template_matching_batch: 38s
  • Coverage: 89.2% (target: 85%)
```

---

#### Step 3.2: Performance Analysis

**Objective:** Measure test execution performance and identify optimization opportunities.

**Actions:**
1. Calculate total test execution time
2. Measure per-test average execution time
3. Identify tests exceeding timeout thresholds
4. Analyze device response time during tests
5. Detect potential memory leaks or resource issues

**Success Criteria:**
- Performance metrics collected
- Bottlenecks identified
- Optimization recommendations generated

**Output Example:**
```
✓ Performance Analysis Complete
  • Total Execution Time: 6m 18s
  • Average Test Time: 6.3s
  • Timeout Violations: 2
  • Device Response Time: Avg 142ms, Max 1.2s
  • Memory Usage: Peak 245 MB
```

---

#### Step 3.3: Generate Test Report

**Objective:** Create comprehensive test report with findings and recommendations.

**Actions:**
1. Compile test results into structured report
2. Include pass/fail metrics, coverage data, and performance analysis
3. Add failure diagnostics with stack traces
4. Generate actionable recommendations
5. Save report to `.moai/docs/reports/test-report-<timestamp>.md`

**Report Structure:**
```markdown
# ADB AutoPlayer Test Report

**Test Session:** 2025-12-01 21:34:56
**Configuration:** AFK Journey Bot (2 devices)
**Test Types:** Unit, Integration, E2E

## Summary

- **Total Tests:** 60
- **Passed:** 53 (88.3%)
- **Failed:** 7 (11.7%)
- **Coverage:** 89.2%
- **Execution Time:** 6m 18s

## Test Results by Suite

### Unit Tests
- Passed: 43/45 (95.6%)
- Coverage: 91.2%
- Execution Time: 12.3s

### Integration Tests
- Passed: 11/12 (91.7%)
- Coverage: 85.4%
- Execution Time: 48.2s

### End-to-End Tests
- Passed: 2/3 (66.7%)
- Coverage: 76.3%
- Execution Time: 4m 18s

## Failed Tests Analysis

1. **test_template_matching_edge_case** (Unit)
   - Error: AssertionError: Template match score 0.72 < threshold 0.8
   - Recommendation: Regenerate template with higher quality source image

2. **test_device_reconnection_timeout** (Integration)
   - Error: TimeoutError: Device emulator-5554 did not reconnect within 30s
   - Recommendation: Increase reconnection timeout or check device stability

3. **test_afk_stages_full_clear** (E2E)
   - Error: ImageNotFoundException: exit_door.png not found
   - Recommendation: Add missing template or adjust recognition threshold

## Performance Analysis

- Slowest Test: test_afk_stages_full_clear (4m 12s)
- Tests Exceeding Timeout: 2
- Device Stability: 91.7%
- Memory Usage: Peak 245 MB

## Coverage Summary

| Module                  | Coverage | Untested Lines |
|-------------------------|----------|----------------|
| device/adb_client       | 94.2%    | 12             |
| device/adb_controller   | 89.7%    | 23             |
| games/afk_journey/base  | 86.3%    | 45             |
| games/afk_journey/mixins| 78.4%    | 67             |

## Recommendations

1. ✓ **Coverage Met:** Overall coverage 89.2% exceeds target 85%
2. ⚠ **Fix Failing Tests:** Address 7 failing tests before deployment
3. ⚠ **Optimize Slow Tests:** Consider parallelization for E2E tests
4. ✓ **Device Stability:** 91.7% stability is acceptable
5. ⚠ **Update Templates:** Regenerate image templates with higher quality

## Next Steps

- Fix failing tests and rerun validation
- Consider `/adb:deploy` if all critical tests pass
- Review performance optimization opportunities
```

**Success Criteria:**
- Report generated successfully
- All sections populated with data
- Recommendations actionable

**Output Example:**
```
✓ Test Report Generated
  • Location: .moai/docs/reports/test-report-20251201-213456.md
  • Size: 8.2 KB
  • Sections: 7
  • Recommendations: 5
```

---

#### Step 3.4: Present Results & Next Steps

**Objective:** Display results to user and guide next actions.

**Actions:**
1. Display summary of test execution
2. Highlight critical failures requiring attention
3. Show coverage metrics and performance data
4. Offer next action options via AskUserQuestion

**AskUserQuestion Format:**

```python
AskUserQuestion({
    "questions": [{
        "question": "Test execution complete. What would you like to do next?",
        "header": "Next Steps",
        "multiSelect": false,
        "options": [
            {
                "label": "Deploy Bot",
                "description": "Proceed to deployment (recommended if tests pass)"
            },
            {
                "label": "Fix Failing Tests",
                "description": "Address test failures before deployment"
            },
            {
                "label": "Review Test Report",
                "description": "Open detailed test report for analysis"
            },
            {
                "label": "Re-run Tests",
                "description": "Execute tests again with different configuration"
            }
        ]
    }]
})
```

**Success Criteria:**
- Results presented clearly
- User guided to appropriate next action

**Output Example:**
```
═══════════════════════════════════════════════════════════════
              ADB AutoPlayer Test Execution Complete
═══════════════════════════════════════════════════════════════

✓ Test Summary:
  • Total Tests: 60
  • Passed: 53 (88.3%)
  • Failed: 7 (11.7%)
  • Coverage: 89.2% (Target: 85%)
  • Execution Time: 6m 18s

⚠ Critical Issues:
  • 7 tests failed (4 E2E, 2 unit, 1 integration)
  • test_afk_stages_full_clear: Image template missing
  • test_device_reconnection: Timeout exceeded

✓ Performance:
  • Average Test Time: 6.3s
  • Device Stability: 91.7%
  • Memory Usage: 245 MB peak

───────────────────────────────────────────────────────────────
                       Recommendations
───────────────────────────────────────────────────────────────

1. ⚠ Fix 7 failing tests before deployment
2. ✓ Coverage target met (89.2% >= 85%)
3. ⚠ Regenerate missing image templates
4. ⚠ Optimize slow E2E tests (4m+ execution time)

Test Report: .moai/docs/reports/test-report-20251201-213456.md

═══════════════════════════════════════════════════════════════
```

---

## Success Criteria

Test execution is considered successful when ALL of the following conditions are met:

1. **Test Execution Complete**: All selected test suites executed without crashes
2. **Pass Rate Acceptable**: Pass rate >= 80% (configurable threshold)
3. **Coverage Target Met**: Code coverage >= 85% (per project configuration)
4. **Critical Tests Pass**: All critical path tests (marked as critical) pass
5. **Report Generated**: Comprehensive test report created and saved

**Quality Gates:**

- ✓ Test suite executes to completion (no crashes)
- ✓ Pass rate >= 80%
- ✓ Coverage >= 85%
- ✓ No critical test failures
- ✓ Test report generated successfully

**Warning Scenarios (Tests run but issues detected):**

- ⚠ Pass rate between 70-80%
- ⚠ Coverage between 75-85%
- ⚠ Flaky tests detected (inconsistent results)
- ⚠ Performance degradation (tests slower than baseline)

**Failure Scenarios:**

- ✗ Test framework errors or crashes
- ✗ Pass rate < 70%
- ✗ Coverage < 75%
- ✗ Critical tests fail
- ✗ Devices not accessible for integration/E2E tests

---

## Metadata

**Tier:** Validation (Quality Assurance)

**Required Tools:**
- `adb-game-tester`: Agent for test execution and analysis
- `adb_config_validator`: Configuration validation script
- `pytest`: Test framework (with coverage plugins)

**Integration Points:**
- Reads:
  - `.moai/config/config.json` (project configuration)
  - `src-tauri/Settings/ADB.toml` (device pool)
  - `src-tauri/Settings/<Game>.toml` (game-specific config)
  - `pyproject.toml` (test dependencies)
- Writes:
  - `.moai/docs/reports/test-report-<timestamp>.md` (test report)
  - `.moai/temp/coverage/` (coverage HTML reports)
  - `.moai/temp/tests/` (JUnit XML results)
  - `.moai/logs/test-execution.log` (test logs)

**Dependencies:**
- Python 3.12+ with pytest, pytest-cov, pytest-timeout
- ADB 1.0.40+ (for integration/E2E tests)
- Connected devices (for integration/E2E tests)
- Game installed on device (for E2E tests)

**Agent Delegation:**
- Delegates to `adb-game-tester` agent for test execution orchestration
- Agent handles pytest invocation, result parsing, and analysis
- Command focuses on workflow coordination and user interaction

---

## Output Format

### Test Progress Indicators

Display real-time progress during test execution:

```
[1/4] Preparing test environment...        ✓ Complete
[2/4] Executing unit tests...              ✓ 45 tests passed
[3/4] Running integration tests...         ⏳ 8/12 tests complete...
[4/4] Generating test report...            ⏳ Pending
```

### Test Results Table

Display test results in structured format:

```
┌─────────────────┬──────────┬─────────┬─────────┬──────────┬──────────┐
│ Test Suite      │ Total    │ Passed  │ Failed  │ Coverage │ Time     │
├─────────────────┼──────────┼─────────┼─────────┼──────────┼──────────┤
│ Unit Tests      │ 45       │ 43      │ 2       │ 91.2%    │ 12.3s    │
│ Integration     │ 12       │ 11      │ 1       │ 85.4%    │ 48.2s    │
│ E2E Tests       │ 3        │ 2       │ 1       │ 76.3%    │ 4m 18s   │
├─────────────────┼──────────┼─────────┼─────────┼──────────┼──────────┤
│ Total           │ 60       │ 53      │ 7       │ 89.2%    │ 6m 18s   │
└─────────────────┴──────────┴─────────┴─────────┴──────────┴──────────┘
```

### Coverage Summary

Present coverage metrics with visual indicators:

```
Code Coverage Summary:

Overall Coverage: 89.2% ████████████████████░░░ (Target: 85%)

By Module:
  device/adb_client       ████████████████████░  94.2%
  device/adb_controller   █████████████████░░░░  89.7%
  games/afk_journey/base  ████████████████░░░░░  86.3%
  games/afk_journey/mixins███████████████░░░░░░  78.4%

Untested Lines: 147 total
```

---

## Integration with ADB Workflow

This command integrates into the ADB AutoPlayer workflow:

**Workflow Sequence:**

1. `/adb:init` - Initialize ADB project and connect devices
2. `/adb:test` - Test device connectivity and bot functionality ← YOU ARE HERE
3. `/adb:deploy` - Deploy bot to production (if tests pass)
4. `/adb:run <bot>` - Execute bot automation

**Next Step Recommendations:**

After successful testing, users should:
- **If all tests pass:** Proceed to `/adb:deploy` for production deployment
- **If tests fail:** Review test report, fix issues, and re-run tests
- **If coverage low:** Write additional tests to meet coverage target

**Error Recovery:**

If testing fails, users can:
- Review detailed test report for specific failure diagnostics
- Check device connectivity with `/adb:init --validate`
- Re-run specific test types (unit only for fast validation)
- Consult test logs in `.moai/logs/test-execution.log`

---

## Execution Directive

YOU MUST NOW EXECUTE THE COMMAND FOLLOWING THE WORKFLOW DESCRIBED ABOVE.

1. **START PHASE 1**: Execute pre-test validation (Steps 1.1-1.5)
2. **PROCEED TO PHASE 2**: Run selected test suites with progress tracking
3. **COMPLETE PHASE 3**: Analyze results and generate comprehensive report
4. **DO NOT JUST DESCRIBE**: Execute actual pytest commands and parse real test output

Follow the workflow phases sequentially and provide detailed progress updates to the user.

---

**Version:** 1.0.0
**Last Updated:** 2025-12-01
**Architecture:** ADB Domain Command (Validation Tier)
**Integration:** adb-game-tester agent, pytest framework, coverage reporting
