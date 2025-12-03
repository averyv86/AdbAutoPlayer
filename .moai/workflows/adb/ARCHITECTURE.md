# ADB Workflow Architecture & Integration Guide

**Version**: 1.0.0
**Last Updated**: 2025-12-02
**Status**: Complete Reference

---

## System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    User Interface Layer                       │
│  (CLI, Python API, YAML definitions, CI/CD integrations)    │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│              Workflow Orchestration Layer                     │
│  (Workflow executor, step resolver, device manager)         │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│               Step Library Layer (12 Steps)                   │
│  (Semantic/template/OCR, retry logic, error handling)       │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                   Skill Integration Layer                     │
│  ┌──────────────┬──────────────┬──────────────┐              │
│  │ moai-domain- │ adb-screen-  │ adb-navigation
│  │    adb       │  detection   │    -base     │              │
│  └──────────────┴──────────────┴──────────────┘              │
│  ┌──────────────┬──────────────┬──────────────┐              │
│  │ adb-uiautom- │ adb-magisk   │ adb-karrot  │              │
│  │  ator        │              │             │              │
│  └──────────────┴──────────────┴──────────────┘              │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│              Android Device Bridge (ADB) Layer               │
│  (Shell commands, intent launching, property queries)       │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                   Device Hardware Layer                       │
│  (Real phones, BlueStacks, Genymotion, Android Studio)      │
└──────────────────────────────────────────────────────────────┘
```

---

## Architecture Layers

### 1. User Interface Layer

**Entry Points**:
- CLI: `adb-run-workflow.py` script
- Python API: `WorkflowExecutor` class
- YAML: Workflow definition files
- CI/CD: GitHub Actions, Jenkins, etc

**Responsibilities**:
- Accept user input (CLI arguments, YAML files)
- Validate input parameters
- Display progress and results
- Handle logging and reporting

### 2. Workflow Orchestration Layer

**Components**:
- `WorkflowParser`: Parse YAML → Python objects
- `WorkflowExecutor`: Execute workflow phases sequentially/parallel
- `DeviceManager`: Connect/manage multiple devices
- `StateTracker`: Track workflow state for recovery

**Workflow Execution Flow**:

```
1. Parse YAML
   ↓
2. Validate structure & dependencies
   ↓
3. Connect to devices
   ↓
4. Resolve DAG (directed acyclic graph) of steps
   ↓
5. Execute phases:
   - Sequential: Phase 1 → Phase 2 → Phase 3
   - Parallel: (Phase 2A || Phase 2B) then Phase 3
   ↓
6. Collect results from all phases
   ↓
7. Aggregate output & generate report
   ↓
8. Cleanup & disconnect devices
```

### 3. Step Library Layer (12 Core Steps)

**Step Categories**:

| Category | Steps | Purpose |
|----------|-------|---------|
| **Shell** | `shell_command`, `adb_command` | Direct device control |
| **UI** | `ui_find`, `ui_tap`, `ui_swipe`, `ui_input` | User interaction |
| **Wait/Check** | `ui_wait`, `ui_check`, `delay` | Synchronization |
| **Capture** | `screenshot` | Evidence collection |
| **Monitor** | `app_monitor`, `log_monitor` | Behavior observation |

**Detection Methods** (Hybrid Fallback):

```
Step: Find "Login" button
    ↓
Method 1: Semantic (Accessibility API)
    ├─ Fast (100-300ms)
    ├─ Most reliable
    └─ If found: ✓ return
    ↓
Method 2: Template (Image matching)
    ├─ Medium speed (300-1000ms)
    ├─ UI-dependent
    └─ If found: ✓ return
    ↓
Method 3: OCR (Text recognition)
    ├─ Slow (1-3s)
    ├─ Language-aware
    └─ If found: ✓ return
    ↓
All failed: ✗ Error (timeout)
```

### 4. Skill Integration Layer

**ADB Skills Architecture**:

```
┌─ moai-domain-adb (Foundation)
│  ├─ ADB client wrapper
│  ├─ Device enumeration
│  ├─ Shell command execution
│  └─ Property queries
│
├─ adb-screen-detection (UI Detection)
│  ├─ Screenshot capture
│  ├─ Template matching
│  ├─ OCR recognition
│  └─ Coordinate extraction
│
├─ adb-navigation-base (Primitives)
│  ├─ Tap
│  ├─ Swipe
│  ├─ Wait
│  └─ Input
│
├─ adb-uiautomator (Android API)
│  ├─ Accessibility service
│  ├─ UI tree parsing
│  ├─ Resource ID matching
│  └─ Content description queries
│
├─ adb-magisk (System)
│  ├─ Magisk detection
│  ├─ Module installation
│  ├─ Zygisk management
│  └─ Property spoofing
│
├─ adb-karrot (App-Specific)
│  ├─ Karrot app commands
│  ├─ Login automation
│  ├─ Game-specific actions
│  └─ Bypass detection
│
└─ adb-workflow-orchestrator (Engine)
   ├─ Workflow execution
   ├─ Step coordination
   ├─ Result aggregation
   └─ Error recovery
```

**Skill Dependencies**:

```
adb-workflow-orchestrator
    ├─ adb-magisk
    │   └─ moai-domain-adb
    ├─ adb-karrot
    │   ├─ adb-screen-detection
    │   ├─ adb-navigation-base
    │   └─ moai-domain-adb
    ├─ adb-uiautomator
    │   └─ moai-domain-adb
    ├─ adb-navigation-base
    │   └─ moai-domain-adb
    └─ adb-screen-detection
        └─ moai-domain-adb
```

### 5. Android Device Bridge Layer

**ADB Capabilities**:

```
ADB Client
    ├─ Connection
    │   ├─ adb connect IP:PORT
    │   ├─ adb devices
    │   └─ adb disconnect
    │
    ├─ Shell Commands
    │   ├─ adb shell <cmd>
    │   ├─ adb shell getprop
    │   └─ adb shell setprop
    │
    ├─ App Control
    │   ├─ adb shell am start
    │   ├─ adb shell pm list
    │   └─ adb shell input
    │
    ├─ File Transfer
    │   ├─ adb push <local> <remote>
    │   └─ adb pull <remote> <local>
    │
    ├─ Debugging
    │   ├─ adb logcat
    │   └─ adb shell dumpsys
    │
    └─ Accessibility
        ├─ Android Accessibility API
        ├─ ContentProvider queries
        └─ Intent-based IPC
```

### 6. Device Hardware Layer

**Supported Devices**:

```
Real Android Phones
    ├─ USB Connection
    │   └─ adb devices (via USB)
    └─ Network Connection
        └─ adb connect IP:5555

Emulators
    ├─ BlueStacks (localhost:5555-5558)
    ├─ Genymotion (Network)
    ├─ Android Studio Emulator (localhost:5554+)
    └─ MEmu (Network)

Testing Platforms
    ├─ CloudFlare
    ├─ AWS Device Farm
    └─ BrowserStack
```

---

## Integration Points

### Integration 1: With moai-domain-adb

**How it works**:

```python
# Low-level device operations
from moai_domain_adb import ADBClient

client = ADBClient()
devices = client.list_devices()           # Get device list
output = client.shell("getprop ro.build")  # Run shell command
client.install_app("app.apk")             # Install APK
```

**Used by**: All ADB skills for device communication

### Integration 2: With adb-screen-detection

**How it works**:

```python
# UI detection with multiple methods
from adb_screen_detection import ScreenDetector

detector = ScreenDetector(device_serial)
found = detector.find_text("로그인", method="hybrid")
detector.tap_at(found.x, found.y)
```

**Used by**: `ui_find`, `ui_tap` steps

### Integration 3: With adb-uiautomator

**How it works**:

```python
# Android Accessibility API
from adb_uiautomator import UIAutomator

automator = UIAutomator(device_serial)
button = automator.find_by_text("로그인")
automator.click(button)
```

**Used by**: Semantic detection method

### Integration 4: With adb-magisk

**How it works**:

```python
# Magisk module management
from adb_magisk import MagiskManager

magisk = MagiskManager(device_serial)
magisk.install_module("PlayIntegrityFork")
magisk.enable_zygisk()
```

**Used by**: Magisk-related workflows

### Integration 5: With adb-karrot

**How it works**:

```python
# Karrot app automation
from adb_karrot import KarrotAutomation

karrot = KarrotAutomation(device_serial)
karrot.login("user@example.com", "password")
karrot.run_daily_quests()
```

**Used by**: Game-specific workflows

---

## Data Flow Patterns

### Pattern 1: Simple Sequential Flow

```
Input: workflow.yaml
    ↓
Parse YAML
    ↓
Step 1: shell_command
    ├─ Execute: adb shell getprop
    └─ Output: {exit_code: 0, stdout: "value"}
    ↓
Step 2: ui_find
    ├─ Execute: find "login" button
    └─ Output: {found: true, x: 500, y: 1000}
    ↓
Step 3: ui_tap
    ├─ Execute: tap (500, 1000)
    └─ Output: {success: true}
    ↓
Aggregate Results
    ├─ Step 1: ✓
    ├─ Step 2: ✓
    ├─ Step 3: ✓
    └─ Overall: Success
```

### Pattern 2: Parallel Phase Execution

```
Input: workflow.yaml (3 devices)
    ↓
Device 1          Device 2          Device 3
    │                  │                 │
    ├─ launch_app      ├─ launch_app     ├─ launch_app
    │                  │                 │
    ├─ wait            ├─ wait           ├─ wait
    │                  │                 │
    ├─ login           ├─ login          ├─ login
    │                  │                 │
    └─ verify          └─ verify         └─ verify
         │                  │                 │
         └──────────────────┴─────────────────┘
                      │
            Aggregate All Results
            ├─ Device 1: ✓
            ├─ Device 2: ✓
            ├─ Device 3: ✗ (failed)
            └─ Overall: Partial Success
```

### Pattern 3: Conditional Branching

```
Input: workflow.yaml
    ↓
Step 1: check_logged_in
    └─ Output: {exists: false}
    ↓
Condition: exists == false?
    │
    ├─ YES: Execute login branch
    │   └─ Steps: tap_login → enter_email → ...
    │
    └─ NO: Execute already_logged_in branch
        └─ Steps: skip_to_home → ...
    ↓
Merge Results
    └─ Continue to next phase
```

---

## Error Handling Architecture

### Error Recovery Strategy

```
Step Execution Failure
    ↓
Check: retry_on_failure = true?
    ├─ NO
    │   └─ Check: on_failure action
    │       ├─ "fail" → Stop workflow
    │       ├─ "continue" → Continue to next step
    │       └─ "screenshot_and_alert" → Capture + alert + continue
    │
    └─ YES
        └─ Retry with exponential backoff
            ├─ Attempt 1: Wait 1s
            ├─ Attempt 2: Wait 1.5s
            ├─ Attempt 3: Wait 2.25s
            └─ Max retries exceeded? → on_failure action
```

### Retry Configuration

```yaml
steps:
  - name: flaky_step
    type: ui_tap

    # Retry policy
    retry_on_failure: true
    max_retries: 3
    backoff_multiplier: 1.5

    # Failure action
    on_failure: "screenshot_and_alert"

    # Timeout
    timeout_seconds: 5
```

**Retry Logic Example**:
```
Attempt 1: Fail, wait 1s
Attempt 2: Fail, wait 1.5s
Attempt 3: Fail, wait 2.25s
Max retries exceeded → execute on_failure action
```

---

## Performance Optimization

### Detection Method Selection

**Semantic** (Use for standard UI):
- Fastest: 100-300ms
- Most reliable: 95%+ success
- Coverage: Labels, EditText, Button, etc

**Template** (Use for icons):
- Medium: 300-1000ms
- Reliable: 90%+ success
- Coverage: Custom views, icons

**OCR** (Use for unusual text):
- Slowest: 1-3s
- Language-aware
- Coverage: Any visible text

### Optimization Techniques

**1. Method Selection**:
```yaml
# Fast (semantic only)
method: semantic
timeout_seconds: 2

# Balanced (hybrid)
method: hybrid
timeout_seconds: 10

# Thorough (try all)
method: hybrid
timeout_seconds: 30
```

**2. Parallel Execution**:
```yaml
execution_config:
  mode: parallel
  max_parallel: 3  # Run 3 devices concurrently
```

**3. Timeout Optimization**:
```yaml
# Responsive UI
timeout_seconds: 2

# Network-dependent
timeout_seconds: 30

# Reboot/long operations
timeout_seconds: 300
```

---

## Multi-Device Architecture

### Device Management

```
DeviceManager
    ├─ Connection Pool
    │   ├─ Device 1: Connected
    │   ├─ Device 2: Connected
    │   └─ Device 3: Connecting...
    │
    ├─ Execution Scheduler
    │   ├─ Sequential: Device 1 → Device 2 → Device 3
    │   └─ Parallel: Device 1 || Device 2 || Device 3
    │
    └─ Result Aggregator
        ├─ Device 1 Results
        ├─ Device 2 Results
        └─ Device 3 Results → Combined Report
```

### Parallel Execution Strategy

```
Max Parallel: 3
Queue: [Device 1, Device 2, Device 3, Device 4, Device 5]

Iteration 1:
  Slot 1: Device 1 executing
  Slot 2: Device 2 executing
  Slot 3: Device 3 executing
  Queue: [Device 4, Device 5]

Iteration 2 (when slot frees):
  Slot 1: Device 4 executing
  Slot 2: Device 2 (still executing)
  Slot 3: Device 3 (still executing)
  Queue: [Device 5]

...until all devices complete
```

---

## State Management

### Workflow State Tracking

```
WorkflowState
    ├─ workflow_id: "my_workflow_v1"
    ├─ status: "in_progress"
    ├─ start_time: 2025-12-02T10:00:00Z
    ├─ current_phase: 2
    ├─ completed_phases:
    │   ├─ Phase 1: {status: "completed", duration: 45s}
    │   └─ Phase 2: {status: "completed", duration: 120s}
    ├─ current_phase_steps:
    │   ├─ Step 1: {status: "completed"}
    │   ├─ Step 2: {status: "completed"}
    │   └─ Step 3: {status: "in_progress"}
    └─ devices:
        ├─ Device 1: {status: "idle"}
        ├─ Device 2: {status: "executing"}
        └─ Device 3: {status: "error"}
```

### Checkpoint Recovery

```
Workflow fails at Phase 3, Step 2

Recovery Options:
1. Resume from checkpoint
   └─ Skip Phase 1-2, restart Phase 3

2. Full restart
   └─ Start from Phase 1

3. Manual intervention
   └─ Fix issue, then resume
```

---

## Logging & Monitoring

### Log Hierarchy

```
Workflow Log (Top level)
    ├─ Device 1 Log
    │   ├─ Phase 1 Log
    │   │   ├─ Step 1 Log
    │   │   ├─ Step 2 Log
    │   │   └─ Step 3 Log
    │   ├─ Phase 2 Log
    │   │   └─ ...
    │   └─ Device 1 Summary
    ├─ Device 2 Log
    │   └─ ...
    └─ Workflow Summary
        ├─ Total time: 120s
        ├─ Device success rate: 66%
        ├─ Step success rate: 95%
        └─ Errors: [...]
```

### Monitoring Metrics

```
Workflow Metrics
    ├─ Execution Time
    │   ├─ Total: 120s
    │   ├─ Per Phase: [45s, 60s, 15s]
    │   └─ Per Device: [45s, 50s, 55s]
    ├─ Success Rates
    │   ├─ Overall: 66% (2/3 devices)
    │   ├─ Per Phase: [100%, 100%, 66%]
    │   └─ Per Step: [95%, 98%, 90%, ...]
    ├─ Resource Usage
    │   ├─ CPU: 45% average
    │   ├─ Memory: 2.1GB average
    │   └─ Network: 15MB total
    └─ Errors
        ├─ Count: 1
        └─ Details: [Device 3 Step 2 timeout]
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: ADB Workflow Tests

on: [push, pull_request]

jobs:
  adb-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Start Android Emulator
        run: |
          emulator -avd test-device -no-window &
          adb wait-for-device

      - name: Run ADB Workflow
        run: |
          python .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
            --workflow .moai/workflows/adb/templates/login-workflow.yaml \
            --email test@example.com \
            --password TestPassword123

      - name: Upload Results
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: workflow-results
          path: results/
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any

    stages {
        stage('Setup') {
            steps {
                sh 'adb start-server'
                sh 'adb devices'
            }
        }

        stage('Execute Workflow') {
            steps {
                sh '''
                python .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
                  --workflow .moai/workflows/adb/templates/login-workflow.yaml \
                  --email test@example.com \
                  --password TestPassword123 \
                  --report-format json \
                  --output results.json
                '''
            }
        }

        stage('Publish Results') {
            steps {
                publishHTML([
                    reportDir: 'results/',
                    reportFiles: 'report.html',
                    reportName: 'ADB Workflow Report'
                ])
            }
        }
    }
}
```

---

## Troubleshooting Guide

### Issue: Device Connection Fails

**Root Causes**:
1. ADB server not running
2. Device not in correct USB mode
3. Network firewall blocking
4. Device offline

**Solutions**:
```bash
# Restart ADB server
adb kill-server
adb start-server

# Check connection
adb devices

# For network issues
adb shell ifconfig
adb connect 192.168.1.100:5555
```

### Issue: Step Timeout

**Root Causes**:
1. UI not rendering
2. Network slow
3. Timeout too short

**Solutions**:
```yaml
# Increase timeout
timeout_seconds: 30  # Increased from 5

# Use hybrid detection
method: hybrid

# Add debug screenshot
on_failure: "screenshot_and_alert"
```

### Issue: Multi-Device Synchronization

**Root Causes**:
1. Max parallelism too high
2. Resource exhaustion
3. Device becoming unresponsive

**Solutions**:
```yaml
execution_config:
  mode: parallel
  max_parallel: 2  # Reduce from 3

  # Or use sequential
  mode: sequential
```

---

## Future Enhancements

### Planned Features

1. **Advanced State Machine Support**
   - Complex conditional logic
   - Loop support with counters
   - State persistence

2. **Enhanced Monitoring**
   - Real-time video recording
   - Network traffic analysis
   - Performance profiling

3. **Cloud Integration**
   - Remote device execution
   - Distributed workflows
   - Result aggregation from cloud

4. **AI-Assisted Automation**
   - Automatic workflow generation
   - Anomaly detection
   - Self-healing workflows

---

**Version**: 1.0.0
**Last Updated**: 2025-12-02
**Status**: Complete & Production-Ready
