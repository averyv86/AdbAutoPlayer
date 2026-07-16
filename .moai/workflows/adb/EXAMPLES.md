# ADB Workflow Examples & Future Patterns

**Version**: 1.0.0
**Last Updated**: 2025-12-02
**Status**: Reference & Future Patterns

---

## Quick Index

| Example | Complexity | Time | Steps |
|---------|-----------|------|-------|
| 1. Simple App Launch | Simple | 30s | 2-3 |
| 2. Email Login | Medium | 1-2m | 5-7 |
| 3. Magisk Module Install | Complex | 3-5m | 8-12 |
| 4. Multi-Device Login | Complex | 2-4m | 10-15 |
| 5. Conditional Bypass | Advanced | 3-5m | 12-20 |

---

## Example 1: Simple App Launch

**Goal**: Launch an app and verify it's running

**Use Case**: Basic automation, smoke tests, CI/CD verification

**Duration**: ~30 seconds

**Complexity**: Simple (1 device, 2-3 steps)

### Workflow

```yaml
name: simple_app_launch
version: 1.0.0
type: automation
target_app: com.example.app

config:
  detection_method: semantic
  input_validation: true
  screenshot_on_error: true

inputs:
  app_package:
    type: string
    required: true
    default: "com.example.app"

steps:
  launch:
    - name: launch_app
      type: adb_command
      script: "adb shell am start -n {app_package}/.MainActivity"
      timeout_seconds: 30

  verify:
    - name: wait_for_app
      type: ui_wait
      target_text: "앱 이름"  # App name in Korean
      timeout_seconds: 30
      on_failure: "screenshot_and_alert"

outputs:
  success: boolean
  app_launched: boolean
  launch_time_seconds: number

success_criteria:
  - app_launched: true
  - app_visible: true

on_failure:
  - action: take_screenshot
    output: /sdcard/launch_error.png
  - action: collect_logs
    output: /sdcard/launch_error.log

timing:
  total_timeout_seconds: 60
  inter_step_delay_seconds: 1

logging:
  level: info
  output_file: app_launch.log
```

### Testing

```bash
# Test launch
python .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .moai/workflows/adb/examples/simple_app_launch.yaml \
  --app-package "com.nexon.karrot"

# Expected output:
# ✓ App launched successfully
# ✓ Home screen visible
# Time: 25 seconds
```

### Variations

**Launch with permissions**:
```yaml
- name: grant_permissions
  type: shell_command
  script: "adb shell pm grant {app_package} android.permission.INTERNET"
  before: launch_app
```

**Launch with clear cache**:
```yaml
- name: clear_cache
  type: adb_command
  script: "adb shell pm clear {app_package}"
  before: launch_app
```

---

## Example 2: Email + Password Login

**Goal**: Automated login with email and password

**Use Case**: Account setup, testing, bot farming

**Duration**: ~1-2 minutes

**Complexity**: Medium (1 device, 5-7 steps)

### Workflow

```yaml
name: email_password_login
version: 1.0.0
type: automation
target_app: com.example.app

config:
  detection_method: hybrid
  input_validation: true
  screenshot_on_error: true

inputs:
  email:
    type: string
    required: true
    validation: ".*@.*\\..*"

  password:
    type: string
    required: true
    validation: "length >= 6"

  auto_fill:
    type: boolean
    required: false
    default: false

steps:
  check_login_status:
    - name: check_logged_in
      type: ui_check
      target_text: "프로필"
      timeout_seconds: 2

  login_if_needed:
    - name: tap_login_button
      type: ui_tap
      method: hybrid
      target_text: "로그인"
      timeout_seconds: 10
      condition: "not check_logged_in.exists"

  enter_email:
    - name: find_email_field
      type: ui_find
      method: hybrid
      target_text: "이메일"
      timeout_seconds: 10

    - name: tap_email_input
      type: ui_tap
      method: semantic
      target_class: "android.widget.EditText"
      index: 0
      timeout_seconds: 5

    - name: clear_email
      type: ui_input
      text: " "
      clear_first: true
      timeout_seconds: 1

    - name: type_email
      type: ui_input
      text: "{email}"
      clear_first: true
      timeout_seconds: 5

  enter_password:
    - name: find_password_field
      type: ui_find
      method: hybrid
      target_text: "비밀번호"
      timeout_seconds: 10

    - name: tap_password_input
      type: ui_tap
      method: semantic
      target_class: "android.widget.EditText"
      index: 1
      timeout_seconds: 5

    - name: type_password
      type: ui_input
      text: "{password}"
      clear_first: true
      timeout_seconds: 5

  submit_login:
    - name: find_submit
      type: ui_find
      method: hybrid
      target_text: "로그인"
      timeout_seconds: 10

    - name: tap_submit
      type: ui_tap
      method: semantic
      target_text: "로그인"
      timeout_seconds: 5

    - name: wait_after_submit
      type: delay
      duration_seconds: 2
      reason: "Allow server to process login"

  verify_success:
    - name: wait_home_screen
      type: ui_wait
      target_text: "홈"
      timeout_seconds: 30
      on_failure: "screenshot_and_alert"

    - name: verify_profile_visible
      type: ui_check
      target_text: "프로필"
      timeout_seconds: 5

outputs:
  success: boolean
  logged_in: boolean
  email_used: string
  login_time_seconds: number
  error_message: string

success_criteria:
  - email_entered: true
  - password_entered: true
  - login_button_tapped: true
  - home_screen_visible: true
  - profile_visible: true

on_failure:
  - action: take_screenshot
    output: /sdcard/login_error_{{timestamp}}.png

  - action: check_error_text
    patterns:
      - "이메일 또는 비밀번호가 일치하지 않습니다"
      - "계정을 찾을 수 없습니다"
      - "로그인 횟수를 초과했습니다"

  - action: alert
    message: "Login failed. Check credentials."

timing:
  total_timeout_seconds: 180
  inter_step_delay_seconds: 1

retry_policy:
  max_attempts: 3
  exponential_backoff: true
  backoff_multiplier: 1.5

logging:
  level: info
  output_file: login.log
  include_credentials: false
```

### Testing

```bash
# Test login
python .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .moai/workflows/adb/examples/email_password_login.yaml \
  --email "test@example.com" \
  --password "TestPassword123"

# Expected output:
# ✓ Email entered
# ✓ Password entered
# ✓ Login button tapped
# ✓ Home screen reached
# ✓ Login successful
# Time: 90 seconds
```

### Variations

**With remember me**:
```yaml
- name: enable_remember_me
  type: ui_tap
  method: semantic
  target_text: "로그인 상태 유지"
  after: enter_password
```

**With social login**:
```yaml
- name: tap_google_login
  type: ui_tap
  target_text: "Google로 로그인"
  instead_of: email_password_login
```

**With auto-fill**:
```yaml
- name: use_autofill
  type: shell_command
  script: "adb shell autofill"
  before: enter_email
  condition: "inputs.auto_fill"
```

---

## Example 3: Magisk Module Installation

**Goal**: Install Magisk module (e.g., PlayIntegrityFork)

**Use Case**: Bypass detection, enable features, root management

**Duration**: ~3-5 minutes

**Complexity**: Complex (device verification, shell commands, validation)

### Workflow

```yaml
name: magisk_module_install
version: 1.0.0
type: automation
target_system: magisk

config:
  detection_method: semantic
  input_validation: true
  screenshot_on_error: true

inputs:
  module_name:
    type: string
    required: true
    description: "Module name (e.g., PlayIntegrityFork)"

  module_file:
    type: string
    required: true
    description: "Path to module ZIP file"

steps:
  pre_flight_checks:
    - name: check_magisk_installed
      type: shell_command
      script: "adb shell which magisk"
      expected_exit_code: 0
      timeout_seconds: 5
      on_failure: "alert"

    - name: get_magisk_version
      type: shell_command
      script: "adb shell getprop ro.magisk.version"
      expected_pattern: "\\d+\\.\\d+"
      timeout_seconds: 5

    - name: check_zygisk_supported
      type: shell_command
      script: "adb shell getprop ro.zygote"
      timeout_seconds: 5

  launch_magisk:
    - name: launch_magisk_app
      type: adb_command
      script: "adb shell am start -n com.topjohnwu.magisk/.ui.MainActivity"
      timeout_seconds: 30

    - name: wait_magisk_ui
      type: ui_wait
      target_text: "모듈"  # Modules
      timeout_seconds: 30
      on_failure: "screenshot_and_alert"

  install_module:
    - name: tap_modules_tab
      type: ui_tap
      method: semantic
      target_text: "모듈"
      timeout_seconds: 5

    - name: wait_module_list
      type: ui_wait
      target_text: "모듈 설치"  # Install module
      timeout_seconds: 10

    - name: tap_install_button
      type: ui_tap
      method: semantic
      target_text: "설치"
      timeout_seconds: 5

    - name: select_module_file
      type: ui_wait
      target_text: "파일 선택"  # Select file
      timeout_seconds: 10

    - name: navigate_to_file
      type: shell_command
      script: "adb push {module_file} /sdcard/Download/"
      timeout_seconds: 60

    - name: wait_installation
      type: delay
      duration_seconds: 5
      reason: "Allow module installation to complete"

  verify_installation:
    - name: check_module_installed
      type: shell_command
      script: "adb shell ls /data/adb/modules/ | grep -i {module_name}"
      expected_exit_code: 0
      timeout_seconds: 5
      on_failure: "alert"

    - name: verify_module_active
      type: shell_command
      script: "adb shell getprop ro.module.{module_name}"
      timeout_seconds: 5

  post_installation:
    - name: reboot_if_needed
      type: shell_command
      script: "adb shell getprop ro.modules.require_reboot"
      timeout_seconds: 5

    - name: screenshot_success
      type: screenshot
      output: /sdcard/module_install_success.png
      optional: true

outputs:
  success: boolean
  module_installed: boolean
  module_version: string
  magisk_version: string
  installation_time_seconds: number

success_criteria:
  - magisk_detected: true
  - module_file_found: true
  - module_installed: true
  - module_active: true

on_failure:
  - action: take_screenshot
    output: /sdcard/module_install_error.png

  - action: collect_logs
    output: /sdcard/module_install_logs.txt
    command: "adb logcat -d"

  - action: rollback
    script: "adb shell magisk module disable {module_name}"

timing:
  total_timeout_seconds: 600  # 10 minutes
  inter_step_delay_seconds: 2

logging:
  level: info
  output_file: module_install.log
```

### Testing

```bash
# Test module installation
python .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .moai/workflows/adb/examples/magisk_module_install.yaml \
  --module-name "PlayIntegrityFork" \
  --module-file "/path/to/PlayIntegrityFork.zip"

# Expected output:
# ✓ Magisk detected
# ✓ Module file verified
# ✓ Module installed
# ✓ Module active
# Time: 120 seconds
```

---

## Example 4: Multi-Device Parallel Login

**Goal**: Login to same app on multiple BlueStacks instances simultaneously

**Use Case**: Scaling, parallel testing, multi-account farming

**Duration**: ~2-4 minutes (parallel)

**Complexity**: Complex (orchestration, device management)

### Workflow

```yaml
name: multi_device_parallel_login
version: 1.0.0
type: automation
target_app: com.example.app

config:
  detection_method: hybrid
  input_validation: true
  screenshot_on_error: true

# Multiple devices
devices:
  - serial: localhost:5555
    name: "BlueStacks-1"
    port: 5555
  - serial: localhost:5556
    name: "BlueStacks-2"
    port: 5556
  - serial: localhost:5557
    name: "BlueStacks-3"
    port: 5557

execution_config:
  mode: parallel
  max_parallel: 3
  failure_mode: continue  # Continue if one device fails
  timeout_per_device: 180

inputs:
  emails:
    type: array
    required: true
    description: "List of email addresses (one per device)"

  password:
    type: string
    required: true
    description: "Password (same for all)"

steps:
  prepare_devices:
    - name: verify_all_devices
      type: shell_command
      script: "adb devices"
      expected_pattern: "device$"
      timeout_seconds: 10

  login_on_all:
    # Following steps execute on ALL devices in parallel
    - name: launch_app
      type: adb_command
      script: "adb shell am start -n com.example.app/.MainActivity"
      timeout_seconds: 30
      per_device: true

    - name: wait_for_login_screen
      type: ui_wait
      target_text: "로그인"
      timeout_seconds: 30
      per_device: true

    - name: tap_email_field
      type: ui_tap
      method: semantic
      target_class: "android.widget.EditText"
      index: 0
      timeout_seconds: 5
      per_device: true

    - name: enter_email
      type: ui_input
      text: "{emails[device_index]}"  # Use per-device email
      timeout_seconds: 5
      per_device: true

    - name: tap_password_field
      type: ui_tap
      method: semantic
      target_class: "android.widget.EditText"
      index: 1
      timeout_seconds: 5
      per_device: true

    - name: enter_password
      type: ui_input
      text: "{password}"
      timeout_seconds: 5
      per_device: true

    - name: tap_login
      type: ui_tap
      method: semantic
      target_text: "로그인"
      timeout_seconds: 5
      per_device: true

    - name: wait_home_screen
      type: ui_wait
      target_text: "홈"
      timeout_seconds: 30
      per_device: true

  verify_all_logins:
    - name: verify_profile_visible
      type: ui_check
      target_text: "프로필"
      timeout_seconds: 5
      per_device: true

outputs:
  success: boolean
  devices_logins_successful: integer
  devices_total: integer
  login_times_per_device: array
  failed_devices: array

success_criteria:
  - all_devices_connected: true
  - all_devices_logged_in: true  # Optional: at least 2 of 3

on_failure:
  - action: take_screenshot_all_devices
    output: /sdcard/login_error_{{device_name}}.png

  - action: collect_device_summary
    output: results.json

timing:
  total_timeout_seconds: 300  # 5 minutes total
  inter_device_delay_seconds: 2
  inter_step_delay_seconds: 1

logging:
  level: info
  output_file: multi_device_login.log
  per_device_logs: true
```

### Testing

```bash
# Test multi-device login
python .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .moai/workflows/adb/examples/multi_device_login.yaml \
  --emails "user1@example.com,user2@example.com,user3@example.com" \
  --password "CommonPassword123"

# Expected output:
# Device 1: ✓ Login successful (45 seconds)
# Device 2: ✓ Login successful (48 seconds)
# Device 3: ✓ Login successful (46 seconds)
# Total time: 50 seconds (parallel)
```

---

## Example 5: Conditional Bypass Workflow

**Goal**: Detect emulator/detection and apply appropriate bypass

**Use Case**: Emulator detection avoidance, anti-cheat bypass

**Duration**: ~3-5 minutes

**Complexity**: Advanced (conditional branching, dynamic steps)

### Workflow

```yaml
name: conditional_bypass_workflow
version: 1.0.0
type: automation
target_app: com.example.app

config:
  detection_method: hybrid
  input_validation: true
  screenshot_on_error: true

inputs:
  apply_magisk_bypass:
    type: boolean
    required: false
    default: false

  spoof_device_props:
    type: boolean
    required: false
    default: false

steps:
  detect_emulator:
    - name: check_emulator_indicators
      type: shell_command
      script: "adb shell getprop ro.kernel.qemu"
      timeout_seconds: 5

    - name: check_magisk_status
      type: shell_command
      script: "adb shell which magisk"
      expected_exit_code: 0
      timeout_seconds: 5
      required: false

    - name: check_play_integrity_module
      type: shell_command
      script: "adb shell ls /data/adb/modules/ | grep -i playintegrity"
      timeout_seconds: 5
      required: false

  apply_bypass_if_needed:
    # Branch 1: Magisk + Zygisk bypass
    - name: apply_magisk_bypass
      type: conditional
      condition: "detect_emulator.qemu == 1 and inputs.apply_magisk_bypass"
      if_true:
        - name: enable_zygisk
          type: shell_command
          script: "adb shell magisk --zygisk enable"
          timeout_seconds: 10

        - name: install_play_integrity_fork
          type: shell_command
          script: "adb shell pm install /sdcard/PlayIntegrityFork.zip"
          timeout_seconds: 60

        - name: reboot_device
          type: shell_command
          script: "adb shell reboot"
          timeout_seconds: 120

    # Branch 2: Spoof device properties
    - name: spoof_device_properties
      type: conditional
      condition: "detect_emulator.qemu == 1 and inputs.spoof_device_props"
      if_true:
        - name: spoof_model
          type: shell_command
          script: "adb shell setprop ro.product.model RealDeviceModel"
          timeout_seconds: 5

        - name: spoof_manufacturer
          type: shell_command
          script: "adb shell setprop ro.product.manufacturer Samsung"
          timeout_seconds: 5

        - name: spoof_device_id
          type: shell_command
          script: "adb shell setprop ro.serialno REAL12345678"
          timeout_seconds: 5

    # Branch 3: No bypass (real device)
    - name: skip_bypass
      type: conditional
      condition: "detect_emulator.qemu != 1"
      if_true:
        - name: log_real_device
          type: delay
          duration_seconds: 1
          reason: "Real device detected, no bypass needed"

  launch_and_test:
    - name: launch_app
      type: adb_command
      script: "adb shell am start -n com.example.app/.MainActivity"
      timeout_seconds: 30

    - name: monitor_detection_errors
      type: log_monitor
      pattern: "Error-18|emulator.*detected|CLIENT_TRANSIENT_ERROR"
      log_level: error
      duration_seconds: 120
      alert_threshold: 1

    - name: wait_home_screen
      type: ui_wait
      target_text: "홈"
      timeout_seconds: 30
      on_failure: "screenshot_and_alert"

outputs:
  success: boolean
  emulator_detected: boolean
  bypass_applied: string  # "magisk", "spoof", "none"
  detection_errors: integer
  app_running: boolean

success_criteria:
  - app_launched: true
  - no_detection_errors: true
  - home_screen_visible: true

on_failure:
  - action: take_screenshot
    output: /sdcard/bypass_error.png

  - action: collect_logs
    output: /sdcard/bypass_debug.log

timing:
  total_timeout_seconds: 600  # 10 minutes for reboot
  inter_step_delay_seconds: 1

logging:
  level: info
  output_file: conditional_bypass.log
  include_all_branches: true
```

### Testing

```bash
# Test with Magisk bypass
python .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .moai/workflows/adb/examples/conditional_bypass.yaml \
  --apply-magisk-bypass true

# Test with property spoofing
python .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .moai/workflows/adb/examples/conditional_bypass.yaml \
  --spoof-device-props true

# Expected output:
# ✓ Emulator detected
# ✓ Magisk bypass applied
# ✓ Reboot completed
# ✓ App launched successfully
# ✓ No detection errors
```

---

## Future Workflow Patterns (Roadmap)

### Pattern 1: Game Automation (AFK Journey)

```yaml
# .moai/workflows/adb/future/game_automation_afk_journey.yaml
name: afk_journey_automation
target_app: com.lilithgames.akaonline

# Daily quest automation
# - Auto-farm stages
# - Collect rewards
# - Team setup
# - Equipment upgrade
```

### Pattern 2: Game Automation (Guitar Girl)

```yaml
# .moai/workflows/adb/future/game_automation_guitar_girl.yaml
name: guitar_girl_automation
target_app: com.glu.guitarflash

# Song playback automation
# - Auto-play songs
# - Score optimization
# - Event farming
```

### Pattern 3: Advanced Conditional Logic

```yaml
# .moai/workflows/adb/future/advanced_conditional_flow.yaml
# Multiple conditions with loop logic
# - While loops
# - For-each loops
# - Nested conditions
# - State machines
```

### Pattern 4: Custom App Integration

```yaml
# .moai/workflows/adb/future/custom_app_automation.yaml
# Deep app integration
# - IPC (Intent/ContentProvider)
# - Background services
# - Custom receivers
```

### Pattern 5: Network-Based Testing

```yaml
# .moai/workflows/adb/future/network_testing.yaml
# Combine with network monitoring
# - Monitor network calls
# - Intercept requests
# - Test offline behavior
```

---

## Best Practices for Examples

### 1. Clear Documentation

Each example should include:
- Purpose statement
- Use case description
- Time estimate
- Complexity rating
- Prerequisites

### 2. Error Handling

Every example should demonstrate:
- Retry logic
- Timeout handling
- Screenshot capture
- Logging

### 3. Variations

Provide variations showing:
- Alternative detection methods
- Optional features
- Edge cases
- Common customizations

### 4. Testing Commands

Include actual test commands:
```bash
# Copy-paste ready
python .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .moai/workflows/adb/examples/example.yaml \
  --param value
```

---

## Composition Patterns

### Sequence Pattern

```yaml
# Step 1 → Step 2 → Step 3
steps:
  phase_1:
    - step_1
  phase_2:
    - step_2
  phase_3:
    - step_3
```

### Parallel Pattern

```yaml
# (Step 1 + Step 2) → Step 3
steps:
  parallel_phase:
    - step_1
    - step_2
  merge_phase:
    - step_3
```

### Conditional Pattern

```yaml
# If condition: Step 1, Else: Step 2
steps:
  conditional:
    - if: condition
      then: step_1
      else: step_2
```

### Loop Pattern

```yaml
# While condition: Step 1
steps:
  loop:
    - while: condition
      do: step_1
      max_iterations: 100
```

---

## FAQ for Examples

**Q: Can I combine examples?**
A: Yes! Use composition patterns to create complex workflows from simple examples.

**Q: How do I add custom steps?**
A: Extend step library with custom types specific to your app.

**Q: How do I handle flaky UI?**
A: Use `retry_on_failure: true` and `max_retries: 3`.

**Q: Can I run examples in CI/CD?**
A: Yes! Examples are designed for both interactive and automated execution.

**Q: What's the cost of running examples?**
A: No cost - ADB is free. Only time cost per example.

---

**Version**: 1.0.0
**Total Examples**: 5 complete + future patterns
**Status**: Ready for production use
