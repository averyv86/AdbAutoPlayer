# ADB Workflow Step Library Reference

**Version**: 1.0.0
**Status**: Complete
**Total Steps**: 12 core steps

---

## Quick Index

| # | Step | Purpose | Speed | Difficulty |
|---|------|---------|-------|------------|
| 1 | `shell_command` | Run adb shell commands | Fast | Low |
| 2 | `adb_command` | Direct adb commands | Fast | Low |
| 3 | `ui_find` | Find UI elements (hybrid) | Medium | Medium |
| 4 | `ui_tap` | Tap on UI element | Medium | Medium |
| 5 | `ui_swipe` | Swipe gesture | Fast | Low |
| 6 | `ui_input` | Type text into field | Fast | Low |
| 7 | `ui_wait` | Wait for element (blocking) | Medium | Medium |
| 8 | `ui_check` | Verify element (non-blocking) | Medium | Medium |
| 9 | `screenshot` | Capture screen | Fast | Low |
| 10 | `delay` | Wait specified seconds | - | Low |
| 11 | `app_monitor` | Monitor app process | Medium | High |
| 12 | `log_monitor` | Monitor system logs | Medium | High |

---

## Step 1: shell_command

Execute arbitrary adb shell commands and verify output.

### Purpose
Run shell commands on device and validate output/exit codes.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `script` | string | Yes | - | Shell command to execute |
| `expected_exit_code` | int | No | 0 | Expected exit code |
| `expected_pattern` | regex | No | - | Pattern to match in output |
| `expected_output` | string | No | - | Exact output to match |
| `timeout_seconds` | int | No | 30 | Command timeout |
| `on_failure` | string | No | "fail" | "fail", "continue", "retry" |
| `retry_on_failure` | bool | No | false | Retry on failure |
| `max_retries` | int | No | 0 | Maximum retry attempts |

### Input/Output

**Inputs**: None (self-contained)

**Outputs**:
- `exit_code`: Integer exit code
- `stdout`: Standard output
- `stderr`: Standard error
- `matched`: Boolean (if pattern specified)

### Examples

**Example 1: Check Magisk version**
```yaml
- name: check_magisk_version
  type: shell_command
  script: "adb shell getprop ro.magisk.version"
  expected_pattern: "\\d+\\.\\d+\\.\\d+"
  timeout_seconds: 5
```

**Example 2: Get device info**
```yaml
- name: get_device_name
  type: shell_command
  script: "adb shell getprop ro.product.model"
  expected_exit_code: 0
  timeout_seconds: 5
```

**Example 3: Check Play Integrity Fork**
```yaml
- name: verify_play_integrity
  type: shell_command
  script: "adb shell ls /data/adb/modules/ | grep -i playintegrity"
  expected_exit_code: 0
  timeout_seconds: 5
  on_failure: "alert"
```

### Error Handling

```yaml
- name: check_with_retry
  type: shell_command
  script: "adb shell pm list packages | grep com.example"
  retry_on_failure: true
  max_retries: 3
  on_failure: "screenshot_and_alert"
```

---

## Step 2: adb_command

Execute adb client commands (not shell).

### Purpose
Run adb commands like install, uninstall, push, pull, etc.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `script` | string | Yes | - | adb command |
| `timeout_seconds` | int | No | 60 | Command timeout |
| `expected_exit_code` | int | No | 0 | Expected exit code |
| `retry_on_failure` | bool | No | false | Retry on failure |
| `max_retries` | int | No | 0 | Max retries |
| `on_failure` | string | No | "fail" | Failure action |

### Input/Output

**Inputs**: None

**Outputs**:
- `exit_code`: Command exit code
- `output`: Command output
- `success`: Boolean success

### Examples

**Example 1: Install APK**
```yaml
- name: install_app
  type: adb_command
  script: "adb install /path/to/app.apk"
  timeout_seconds: 120
  on_failure: "alert"
```

**Example 2: Clear app cache**
```yaml
- name: clear_app_cache
  type: adb_command
  script: "adb shell pm clear com.example.app"
  timeout_seconds: 30
```

**Example 3: Push file to device**
```yaml
- name: push_config
  type: adb_command
  script: "adb push /local/config.json /data/data/config.json"
  timeout_seconds: 60
  retry_on_failure: true
  max_retries: 2
```

### Error Handling

```yaml
- name: install_with_cleanup
  type: adb_command
  script: "adb install app.apk"
  timeout_seconds: 120
  on_failure: "continue"  # Don't stop workflow

- name: cleanup_after_failure
  type: shell_command
  script: "adb shell pm uninstall com.example.app"
  condition: "install_with_cleanup.exit_code != 0"
```

---

## Step 3: ui_find

Find UI elements using hybrid detection (semantic → template → OCR).

### Purpose
Locate UI elements on screen using multiple detection methods.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `method` | string | Yes | - | "semantic", "template", "ocr", or "hybrid" |
| `target_text` | string | No | - | Text to find |
| `target_class` | string | No | - | Android class to find |
| `target_resource` | string | No | - | Resource ID to find |
| `index` | int | No | 0 | Element index (for multiple) |
| `timeout_seconds` | int | No | 10 | Find timeout |
| `required` | bool | No | true | Element must exist |
| `on_failure` | string | No | "fail" | Failure action |

### Input/Output

**Inputs**: None

**Outputs**:
- `found`: Boolean (element found)
- `x`, `y`: Screen coordinates
- `bounds`: Bounding box (left, top, right, bottom)
- `text`: Detected text (if any)

### Examples

**Example 1: Find login button (hybrid)**
```yaml
- name: find_login_button
  type: ui_find
  method: hybrid
  target_text: "로그인"
  timeout_seconds: 10
  required: true
```

**Example 2: Find EditText (semantic)**
```yaml
- name: find_email_field
  type: ui_find
  method: semantic
  target_class: "android.widget.EditText"
  index: 0
  timeout_seconds: 5
```

**Example 3: Find by resource ID**
```yaml
- name: find_submit_button
  type: ui_find
  method: semantic
  target_resource: "com.example:id/submit_btn"
  timeout_seconds: 5
```

**Example 4: Find with OCR fallback**
```yaml
- name: find_with_fallback
  type: ui_find
  method: hybrid  # Tries semantic → template → ocr
  target_text: "특수문자"  # Special characters
  timeout_seconds: 15
  on_failure: "screenshot_and_alert"
```

### Detection Method Behavior

**Semantic** (Priority 1 - Fastest):
- Uses Android Accessibility API
- Works with labels, EditText, Button, etc
- ~100-300ms
- Most reliable for standard UI

**Template** (Priority 2 - Medium):
- Image matching against UI
- Good for icons, custom views
- ~300-1000ms
- Requires stable UI

**OCR** (Priority 3 - Slowest):
- Text recognition on screenshots
- Works with any text
- ~1-3 seconds
- Language-aware (Ko, En, Ja, Zh)

---

## Step 4: ui_tap

Tap on screen location or UI element.

### Purpose
Click/tap on UI elements.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `method` | string | Yes | - | Detection method |
| `target_text` | string | No | - | Text to tap |
| `target_class` | string | No | - | Class to tap |
| `target_resource` | string | No | - | Resource ID to tap |
| `x`, `y` | int | No | - | Exact coordinates |
| `index` | int | No | 0 | Element index |
| `timeout_seconds` | int | No | 5 | Find and tap timeout |
| `retry_on_failure` | bool | No | false | Retry on failure |
| `max_retries` | int | No | 0 | Max retries |
| `double_tap` | bool | No | false | Double tap |
| `long_press_ms` | int | No | 0 | Long press duration |

### Input/Output

**Inputs**: None

**Outputs**:
- `success`: Boolean
- `tapped_at`: (x, y) coordinates
- `element_text`: Text of tapped element

### Examples

**Example 1: Tap login button by text**
```yaml
- name: tap_login_button
  type: ui_tap
  method: semantic
  target_text: "로그인"
  timeout_seconds: 5
  retry_on_failure: true
  max_retries: 2
```

**Example 2: Tap at exact coordinates**
```yaml
- name: tap_center
  type: ui_tap
  method: semantic
  x: 540
  y: 960
  timeout_seconds: 2
```

**Example 3: Double tap with retry**
```yaml
- name: double_tap_item
  type: ui_tap
  method: semantic
  target_text: "아이템"
  double_tap: true
  retry_on_failure: true
  max_retries: 3
```

**Example 4: Long press**
```yaml
- name: long_press_button
  type: ui_tap
  method: semantic
  target_text: "옵션"
  long_press_ms: 500
  timeout_seconds: 5
```

### Error Handling

```yaml
- name: tap_with_screenshot
  type: ui_tap
  method: semantic
  target_text: "ボタン"
  timeout_seconds: 5
  on_failure: "screenshot_and_alert"
  retry_on_failure: true
```

---

## Step 5: ui_swipe

Perform swipe/drag gesture on screen.

### Purpose
Scroll lists, swipe between screens, drag UI elements.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_x`, `start_y` | int | Yes | - | Start coordinates |
| `end_x`, `end_y` | int | Yes | - | End coordinates |
| `duration_ms` | int | No | 500 | Swipe duration (ms) |
| `steps` | int | No | 5 | Interpolation steps |
| `timeout_seconds` | int | No | 5 | Execution timeout |

### Input/Output

**Inputs**: None

**Outputs**:
- `success`: Boolean
- `start`: (x, y) start
- `end`: (x, y) end

### Examples

**Example 1: Scroll down**
```yaml
- name: scroll_down
  type: ui_swipe
  start_x: 540
  start_y: 1000
  end_x: 540
  end_y: 200
  duration_ms: 500
  timeout_seconds: 3
```

**Example 2: Swipe left (back)**
```yaml
- name: swipe_back
  type: ui_swipe
  start_x: 100
  start_y: 500
  end_x: 900
  end_y: 500
  duration_ms: 300
```

**Example 3: Slow scroll (game)**
```yaml
- name: slow_scroll
  type: ui_swipe
  start_x: 540
  start_y: 1200
  end_x: 540
  end_y: 400
  duration_ms: 2000
  steps: 10
```

---

## Step 6: ui_input

Type text into focused input field.

### Purpose
Enter text (email, password, search, etc).

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `text` | string | Yes | - | Text to type |
| `clear_first` | bool | No | true | Clear before typing |
| `delay_per_char_ms` | int | No | 50 | Delay per character |
| `timeout_seconds` | int | No | 5 | Typing timeout |

### Input/Output

**Inputs**: None

**Outputs**:
- `success`: Boolean
- `text_entered`: String typed
- `character_count`: Number of chars

### Examples

**Example 1: Enter email**
```yaml
- name: type_email
  type: ui_input
  text: "{email}"
  clear_first: true
  timeout_seconds: 5
```

**Example 2: Enter password (slow typing)**
```yaml
- name: type_password
  type: ui_input
  text: "{password}"
  clear_first: true
  delay_per_char_ms: 100
  timeout_seconds: 10
```

**Example 3: Type search query**
```yaml
- name: search_game
  type: ui_input
  text: "Karrot"
  clear_first: false
  timeout_seconds: 3
```

### Variables

Text supports variable substitution:
- `{email}`: From inputs.email
- `{password}`: From inputs.password
- `{timestamp}`: Current timestamp
- `{random}`: Random string
- `{device_id}`: Device serial

```yaml
- name: type_user_id
  type: ui_input
  text: "User_{timestamp}_{random}"
  timeout_seconds: 3
```

---

## Step 7: ui_wait

Wait for UI element to appear (blocking).

### Purpose
Wait for navigation, loading screens, etc.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `target_text` | string | No | - | Text to wait for |
| `target_class` | string | No | - | Class to wait for |
| `target_resource` | string | No | - | Resource ID to wait for |
| `timeout_seconds` | int | No | 30 | Max wait time |
| `on_failure` | string | No | "fail" | "fail", "continue", "screenshot_and_alert" |
| `method` | string | No | "hybrid" | Detection method |

### Input/Output

**Inputs**: None

**Outputs**:
- `appeared`: Boolean (element appeared)
- `wait_time_seconds`: Time waited

### Examples

**Example 1: Wait for home screen**
```yaml
- name: wait_home_screen
  type: ui_wait
  target_text: "홈"
  timeout_seconds: 30
  on_failure: "screenshot_and_alert"
```

**Example 2: Wait for loading to finish**
```yaml
- name: wait_loading_complete
  type: ui_wait
  target_text: "로딩 완료"
  timeout_seconds: 60
  method: hybrid
```

**Example 3: Wait with fallback**
```yaml
- name: wait_with_fallback
  type: ui_wait
  target_text: "준비 완료"
  timeout_seconds: 45
  on_failure: "continue"  # Don't stop workflow

- name: check_alternative
  type: ui_check
  target_text: "다시 시도"
  timeout_seconds: 5
  condition: "not wait_with_fallback.appeared"
```

---

## Step 8: ui_check

Verify UI element exists (non-blocking).

### Purpose
Quick check if element is visible (doesn't wait).

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `target_text` | string | No | - | Text to check |
| `target_class` | string | No | - | Class to check |
| `target_resource` | string | No | - | Resource ID to check |
| `timeout_seconds` | int | No | 2 | Quick check timeout |
| `method` | string | No | "semantic" | Detection method |

### Input/Output

**Inputs**: None

**Outputs**:
- `exists`: Boolean
- `element`: Element details (if found)

### Examples

**Example 1: Check if logged in**
```yaml
- name: check_logged_in
  type: ui_check
  target_text: "프로필"
  timeout_seconds: 2

# Use result in conditional
- name: login_if_needed
  type: conditional
  condition: "not check_logged_in.exists"
  if_true:
    - name: login
      type: ui_tap
      target_text: "로그인"
```

**Example 2: Verify success**
```yaml
- name: verify_upload_success
  type: ui_check
  target_text: "업로드 완료"
  timeout_seconds: 3
```

---

## Step 9: screenshot

Capture device screen.

### Purpose
Save screenshots for debugging, reporting, or verification.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `output` | string | Yes | - | Output file path |
| `optional` | bool | No | false | Non-critical failure |
| `purpose` | string | No | "debug" | "debug", "success", "error" |
| `include_ui_tree` | bool | No | false | Include accessibility tree |

### Input/Output

**Inputs**: None

**Outputs**:
- `path`: Screenshot file path
- `size_kb`: File size
- `timestamp`: Capture time

### Examples

**Example 1: Capture success**
```yaml
- name: capture_success
  type: screenshot
  output: /sdcard/success_{{timestamp}}.png
  optional: true
  purpose: success
```

**Example 2: Capture on error**
```yaml
on_failure:
  - action: take_screenshot
    output: /sdcard/error_{{timestamp}}.png
    purpose: error
    include_ui_tree: true
```

**Example 3: Multiple screenshots**
```yaml
steps:
  capture_before:
    - name: screenshot_before
      type: screenshot
      output: /sdcard/before.png

  action:
    - name: tap_button
      type: ui_tap
      target_text: "执行"

  capture_after:
    - name: screenshot_after
      type: screenshot
      output: /sdcard/after.png
```

---

## Step 10: delay

Wait specified seconds.

### Purpose
Pause workflow (allow app to load, animations to finish, etc).

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `duration_seconds` | float | Yes | - | Seconds to wait |
| `reason` | string | No | - | Why waiting (logging) |

### Input/Output

**Inputs**: None

**Outputs**: None

### Examples

**Example 1: Wait for page load**
```yaml
- name: wait_page_load
  type: delay
  duration_seconds: 2
  reason: "Allow page to render"
```

**Example 2: Wait between actions**
```yaml
- name: tap_button_1
  type: ui_tap
  target_text: "次へ"

- name: wait_animation
  type: delay
  duration_seconds: 0.5
  reason: "Animation transition"

- name: tap_button_2
  type: ui_tap
  target_text: "続行"
```

**Example 3: Fractional second delay**
```yaml
- name: debounce
  type: delay
  duration_seconds: 0.1
  reason: "Debounce input"
```

---

## Step 11: app_monitor

Monitor app process behavior.

### Purpose
Watch for crashes, ANRs, or other issues.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `monitor_crashes` | bool | No | true | Watch for crashes |
| `monitor_anrs` | bool | No | true | Watch for ANRs |
| `duration_seconds` | int | No | 60 | Monitoring duration |
| `alert_on_crash` | bool | No | true | Alert if crash found |
| `alert_on_anr` | bool | No | true | Alert if ANR found |

### Input/Output

**Inputs**: None

**Outputs**:
- `crashed`: Boolean
- `anr_detected`: Boolean
- `crash_message`: Crash details
- `anr_message`: ANR details

### Examples

**Example 1: Monitor during gameplay**
```yaml
- name: play_game
  type: ui_tap
  target_text: "플레이"

- name: monitor_gameplay
  type: app_monitor
  monitor_crashes: true
  monitor_anrs: true
  duration_seconds: 120
  alert_on_crash: true
```

**Example 2: Monitor with error collection**
```yaml
- name: monitor_app
  type: app_monitor
  duration_seconds: 60

- name: collect_crash_info
  type: shell_command
  script: "adb logcat -d '*:E' | grep FATAL"
  condition: "monitor_app.crashed"
```

---

## Step 12: log_monitor

Monitor system logs for specific patterns.

### Purpose
Watch logcat for errors, API calls, specific events.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `pattern` | regex | Yes | - | Regex pattern to watch |
| `log_level` | string | No | "all" | "error", "warn", "info", "debug", "all" |
| `duration_seconds` | int | No | 60 | Monitoring duration |
| `alert_threshold` | int | No | 0 | Alert after N matches |
| `tag_filter` | string | No | - | Filter by log tag |

### Input/Output

**Inputs**: None

**Outputs**:
- `pattern_found`: Boolean
- `match_count`: Number of matches
- `matches`: List of matched lines

### Examples

**Example 1: Monitor for emulator detection**
```yaml
- name: monitor_detection
  type: log_monitor
  pattern: "Error-18|emulator.*detected|CLIENT_TRANSIENT_ERROR"
  log_level: error
  duration_seconds: 120
  alert_threshold: 1
```

**Example 2: Monitor Play Services**
```yaml
- name: monitor_play_services
  type: log_monitor
  pattern: "PlayIntegrity|SafetyNet"
  log_level: warn
  duration_seconds: 60
  tag_filter: "PlayIntegrity"
```

**Example 3: Monitor app performance**
```yaml
- name: monitor_performance
  type: log_monitor
  pattern: "ANR|StrictMode|OutOfMemory"
  log_level: error
  duration_seconds: 300
  alert_threshold: 1
```

---

## Step Composition Patterns

### Pattern 1: Find + Tap

Combine find and tap for robust interaction:

```yaml
steps:
  interactive_login:
    - name: find_and_tap_email
      type: ui_find
      method: hybrid
      target_text: "이메일"
      timeout_seconds: 10

    - name: tap_email_field
      type: ui_tap
      method: semantic
      target_class: "android.widget.EditText"
      index: 0
      timeout_seconds: 5

    - name: type_email
      type: ui_input
      text: "{email}"
```

### Pattern 2: Verify + Action

Check state before taking action:

```yaml
steps:
  conditional_action:
    - name: check_logged_in
      type: ui_check
      target_text: "프로필"
      timeout_seconds: 2

    - name: action_if_logged_in
      type: ui_tap
      target_text: "설정"
      condition: "check_logged_in.exists"

    - name: action_if_not_logged_in
      type: ui_tap
      target_text: "로그인"
      condition: "not check_logged_in.exists"
```

### Pattern 3: Retry Loop

Robust error recovery:

```yaml
steps:
  retry_action:
    - name: attempt_action
      type: ui_tap
      target_text: "확인"
      retry_on_failure: true
      max_retries: 3

    - name: verify_action
      type: ui_wait
      target_text: "완료"
      timeout_seconds: 30
      on_failure: "screenshot_and_alert"
```

### Pattern 4: Monitor + Action

Run action while monitoring:

```yaml
steps:
  monitored_action:
    - name: monitor_crashes
      type: app_monitor
      monitor_crashes: true
      duration_seconds: 120

    - name: run_game
      type: ui_tap
      target_text: "플레이"

    - name: check_crash_result
      type: conditional
      condition: "monitor_crashes.crashed"
      if_true:
        - name: collect_crash_logs
          type: shell_command
          script: "adb logcat -d > /sdcard/crash.log"
```

---

## Error Handling in Steps

### Retry Policy

```yaml
- name: flaky_action
  type: ui_tap
  target_text: "불안정한_요소"
  retry_on_failure: true
  max_retries: 3
  timeout_seconds: 5
```

### Exponential Backoff

```yaml
- name: with_backoff
  type: adb_command
  script: "adb install app.apk"
  timeout_seconds: 120
  max_retries: 3
  backoff_multiplier: 1.5
  # Retries: 0ms → 1.5s → 2.25s → 3.37s
```

### Screenshot on Failure

```yaml
- name: critical_action
  type: ui_tap
  target_text: "결제"
  timeout_seconds: 10
  on_failure: "screenshot_and_alert"
```

### Continue on Failure

```yaml
- name: optional_action
  type: ui_tap
  target_text: "보너스"
  optional: true
  on_failure: "continue"
```

---

## Performance Tips

### 1. Detection Method Selection

```yaml
# Fast (100-300ms)
method: semantic  # Use for standard UI

# Medium (300-1000ms)
method: template  # Use for icons

# Slow (1-3s)
method: ocr      # Use for unusual text

# Balanced (auto-select)
method: hybrid   # Default, tries all three
```

### 2. Timeout Optimization

```yaml
# Short for responsive UI
timeout_seconds: 2

# Medium for app loading
timeout_seconds: 10

# Long for network operations
timeout_seconds: 30
```

### 3. Minimize Delays

```yaml
# Only delay when necessary
- type: delay
  duration_seconds: 1
  reason: "Animation transition"

# Remove unnecessary sleeps
# Use ui_wait instead
- type: ui_wait
  target_text: "로딩"
  timeout_seconds: 30
```

---

## Step Library Extension

### Adding Custom Steps

To extend beyond 12 core steps:

1. **Implement in skill**:
   ```python
   class CustomStep(BaseStep):
       def execute(self, context):
           # Custom logic
           pass
   ```

2. **Register in workflow engine**:
   ```python
   STEP_REGISTRY['custom_step'] = CustomStep
   ```

3. **Use in workflow**:
   ```yaml
   - name: my_custom
     type: custom_step
     param: value
   ```

---

## Troubleshooting Steps

### Issue: Step timeout

**Solution 1**: Increase timeout
```yaml
timeout_seconds: 60  # Increased from 10
```

**Solution 2**: Add debug screenshots
```yaml
on_failure: "screenshot_and_alert"
```

**Solution 3**: Use semantic method
```yaml
method: semantic  # Faster than template/ocr
```

### Issue: Element not found

**Solution 1**: Try hybrid detection
```yaml
method: hybrid  # Tries semantic → template → ocr
```

**Solution 2**: Use alternative selector
```yaml
# Instead of text
target_class: "android.widget.Button"
index: 0
```

**Solution 3**: Add delay before find
```yaml
- type: delay
  duration_seconds: 2

- type: ui_find
  target_text: "Element"
```

---

## FAQ

**Q: Which detection method is fastest?**
A: Semantic (100-300ms). Template (300-1000ms). OCR (1-3s).

**Q: Can I use regex in patterns?**
A: Yes for `expected_pattern` and `log_monitor.pattern`.

**Q: How do I handle flaky UI?**
A: Use `retry_on_failure: true` and `max_retries: 3`.

**Q: Can steps run in parallel?**
A: No, steps execute sequentially. Use parallel step type.

**Q: How do I know if a step succeeded?**
A: Check output fields (e.g., `ui_find.found`).

**Q: Can I skip a step conditionally?**
A: Yes, use `condition: "expression"`.

---

**Version**: 1.0.0
**Total Lines**: 600+
**Status**: Complete
