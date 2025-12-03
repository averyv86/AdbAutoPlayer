# Part 4: Automation

> **Quick Reference** - Detection avoidance and automation setup

---

## Emulator Setup

### BlueStacks Air (Recommended)
- Architecture: `arm64-v8a`
- Resolution: `1440x2560`
- ADB Port: `127.0.0.1:5555`
- Root: Enabled via Magisk

### ADB Connection
```bash
adb connect 127.0.0.1:5555
adb devices
```

---

## Detection Avoidance Settings

```yaml
detection_avoidance:
  random_delay:
    min_ms: 500
    max_ms: 2000

  human_like_tap:
    variance_px: 10      # ±10px random offset

  scroll_behavior:
    speed: slow
    pause_between_ms: 1000

  log_monitoring:
    keywords:
      - "LIAPP"
      - "security"
      - "tamper"
      - "integrity"
      - "root"
      - "magisk"
    interval_ms: 500
```

---

## UI Coordinates (1440x2560)

```yaml
screens:
  welcome:
    get_started: [720, 2374]
    login_link: [872, 2493]
    korea_select: [720, 1482]

  login:
    phone_input: [410, 254]
    confirm_button: [720, 2520]
    back_button: [40, 56]
```

---

## Safe Tap Function

```python
import random
import time
import subprocess

def safe_tap(x: int, y: int, variance: int = 10) -> None:
    """Human-like tap with random offset and delay"""
    # Random offset
    actual_x = x + random.randint(-variance, variance)
    actual_y = y + random.randint(-variance, variance)

    # Random delay before tap
    time.sleep(random.uniform(0.5, 2.0))

    # Execute tap
    subprocess.run([
        "adb", "shell", "input", "tap",
        str(actual_x), str(actual_y)
    ])
```

---

## Log Monitoring

```python
import subprocess
import threading

def monitor_logs(keywords: list, callback) -> None:
    """Monitor logcat for security-related keywords"""
    proc = subprocess.Popen(
        ["adb", "logcat", "-v", "brief"],
        stdout=subprocess.PIPE,
        text=True
    )

    for line in proc.stdout:
        for keyword in keywords:
            if keyword.lower() in line.lower():
                callback(f"DETECTED: {keyword} - {line}")
                break
```

---

## Login Workflow

```python
# 1. Launch app
subprocess.run(["adb", "shell", "monkey", "-p",
    "com.towneers.www", "-c",
    "android.intent.category.LAUNCHER", "1"])

# 2. Wait for welcome screen
time.sleep(3)

# 3. Tap "Log in"
safe_tap(872, 2493)
time.sleep(2)

# 4. Enter phone number
safe_tap(410, 254)  # Focus input
time.sleep(0.5)
subprocess.run(["adb", "shell", "input", "text", "01039705176"])

# 5. Tap Confirm
safe_tap(720, 2520)
```

---

## Multi-Device Support

```python
def get_devices() -> list:
    """Get list of connected ADB devices"""
    result = subprocess.run(
        ["adb", "devices"],
        capture_output=True, text=True
    )
    devices = []
    for line in result.stdout.strip().split('\n')[1:]:
        if '\tdevice' in line:
            devices.append(line.split('\t')[0])
    return devices

def run_on_device(device: str, command: list) -> None:
    """Execute command on specific device"""
    subprocess.run(["adb", "-s", device] + command)
```

---

## Error Recovery

| Error | Detection | Recovery |
|-------|-----------|----------|
| App crash | Process not found | Restart app |
| Dialog popup | Screen doesn't match | Tap back/dismiss |
| Network error | "Failed" text on screen | Retry after delay |
| Freeze | No UI change for 30s | Force stop + restart |

---

## Checklist for Other Apps

1. [ ] Find LIAPP package in APK
2. [ ] Locate termination method (RuntimeException)
3. [ ] Patch throw → return-void
4. [ ] Rebuild and sign
5. [ ] Test on emulator first
6. [ ] Map UI coordinates
7. [ ] Set up detection avoidance
8. [ ] Monitor logs during automation
